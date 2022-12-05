#!/usr/bin/env python3

# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import asyncio
import inspect
import json
import logging
import os
import urllib.request
from pathlib import Path

import juju
import juju.utils
import pytest
from helpers import (
    ModelConfigChange,
    cli_deploy_bundle,
    get_alertmanager_alerts,
    get_alertmanager_groups,
    get_proxied_unit_url,
    get_unit_address,
    reenable_metallb,
)
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)
juju_topology_keys = {"juju_model_uuid", "juju_model", "juju_application"}


def get_this_script_dir() -> Path:
    filename = inspect.getframeinfo(inspect.currentframe()).filename  # type: ignore[arg-type]
    path = os.path.dirname(os.path.abspath(filename))
    return Path(path)


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest, pytestconfig):
    """Build the charm-under-test and deploy it together with related charms.

    Assert on the unit status before any relations/configurations take place.
    """
    await ops_test.model.set_config({"logging-config": "<root>=WARNING; unit=DEBUG"})

    await reenable_metallb()

    logger.info("Rendering bundle %s", get_this_script_dir() / ".." / ".." / "bundle.yaml.j2")

    async def build_charm_if_is_dir(option: str) -> str:
        if Path(option).is_dir():
            logger.info("Building charm from source: %s", option)
            option = str(await ops_test.build_charm(option))
        return option

    charms = dict(
        traefik=pytestconfig.getoption("traefik"),
        alertmanager=pytestconfig.getoption("alertmanager"),
        prometheus=pytestconfig.getoption("prometheus"),
        grafana=pytestconfig.getoption("grafana"),
        loki=pytestconfig.getoption("loki"),
        avalanche=pytestconfig.getoption("avalanche"),
    )

    additional_args = dict(
        channel=pytestconfig.getoption("channel"),
    )

    context = {k: await build_charm_if_is_dir(v) for k, v in charms.items() if v is not None}
    context.update(additional_args)

    # set the "testing" template variable so the template renders for testing
    context["testing"] = "true"

    logger.debug("context: %s", context)

    rendered_bundle = ops_test.render_bundle(
        get_this_script_dir() / ".." / ".." / "bundle.yaml.j2", context=context
    )

    # use CLI to deploy bundle until https://github.com/juju/python-libjuju/issues/511 is fixed.
    await cli_deploy_bundle(ops_test, str(rendered_bundle))
    # FIXME: raise_on_error should be removed (i.e. set to True) when units stop flapping to error
    await ops_test.model.wait_for_idle(status="active", timeout=1000, raise_on_error=False)

    prometheus_0_url = await get_proxied_unit_url(ops_test, app_name="prometheus", unit_num=0)

    logger.info(f"Trying to connect to Prometheus over 'traefik/0': {prometheus_0_url}")

    response = urllib.request.urlopen(prometheus_0_url, data=None, timeout=2.0)
    assert response.code == 200

    # effectively disable the update status from firing
    await ops_test.model.set_config({"update-status-hook-interval": "60m"})


@pytest.mark.abort_on_fail
async def test_alertmanager_is_up(ops_test: OpsTest):
    # TODO Change this when AM is exposed over the ingress
    address = await get_unit_address(ops_test, "alertmanager", 0)
    # With ingress in place, need to use model-app as ingress-per-app subpath
    url = f"http://{address}:9093/{ops_test.model_name}-alertmanager"
    logger.info("am public address: %s", url)

    response = urllib.request.urlopen(f"{url}/api/v2/status", data=None, timeout=2.0)
    assert response.code == 200
    assert "versionInfo" in json.loads(response.read())


@pytest.mark.abort_on_fail
async def test_prometheus_is_up(ops_test: OpsTest):
    url = await get_proxied_unit_url(ops_test, "prometheus", 0)

    logger.info("Prometheus public address: %s", url)

    response = urllib.request.urlopen(f"{url}/-/ready", data=None, timeout=2.0)
    assert response.code == 200


@pytest.mark.abort_on_fail
async def test_prometheus_sees_alertmanager(ops_test: OpsTest):
    prom_url = await get_proxied_unit_url(ops_test, "prometheus", 0)

    response = urllib.request.urlopen(f"{prom_url}/api/v1/alertmanagers", data=None, timeout=2.0)
    assert response.code == 200
    # an empty response looks like this:
    # {"status":"success","data":{"activeAlertmanagers":[],"droppedAlertmanagers":[]}}
    # a jsonified activeAlertmanagers looks like this:
    # [{'url': 'http://<ingress:80 or fqdn:9093>/api/v2/alerts'}]
    assert f"/{ops_test.model_name}-alertmanager/api/v2/alerts" in response.read().decode("utf8")


async def test_juju_topology_labels_in_alerts(ops_test: OpsTest):
    alerts = await get_alertmanager_alerts(
        ops_test, "alertmanager", 0, retries=100, path=f"/{ops_test.model_name}-alertmanager"
    )

    i = -1
    for i, alert in enumerate(alerts):
        # make sure every alert has all the juju topology labels
        # NOTE this would only test alerts that are already firing while testing
        assert alert["labels"].keys() >= juju_topology_keys

        # make sure the juju topology entries are not empty
        assert all(alert["labels"][key] for key in juju_topology_keys)

    assert i >= 0  # should have at least one alarms listed (the "AlwaysFiring" alarm rule)
    logger.info("juju topology test passed for %s alerts", i + 1)


async def test_alerts_are_grouped(ops_test: OpsTest):
    groups = await get_alertmanager_groups(
        ops_test, "alertmanager", 0, retries=100, path=f"/{ops_test.model_name}-alertmanager"
    )
    i = -1
    for i, group in enumerate(groups):
        # make sure all groups are grouped by juju topology keys
        assert group["labels"].keys() == juju_topology_keys

    assert i >= 0  # should have at least one group listed (the "AlwaysFiring" alarm rule)
    logger.info("juju topology grouping test passed for %s groups", i + 1)


async def test_alerts_are_fired_from_non_leader_units_too(ops_test: OpsTest):
    """The list of alerts must include an "AlwaysFiring" alert from each avalanche unit."""

    async def all_alerts_fire():
        alerts = await get_alertmanager_alerts(
            ops_test, "alertmanager", 0, retries=100, path=f"/{ops_test.model_name}-alertmanager"
        )
        alerts = list(
            filter(
                lambda itm: itm["labels"]["alertname"] == "AlwaysFiringDueToNumericValue", alerts
            )
        )
        units_firing = sorted([alert["labels"]["juju_unit"] for alert in alerts])
        logger.info("Units firing as of this moment: %s", units_firing)
        return units_firing == ["avalanche/0", "avalanche/1"]

    await juju.utils.block_until_with_coroutine(all_alerts_fire, timeout=300, wait_period=15)


async def test_bundle_charms_can_handle_frequent_update_status(ops_test: OpsTest):
    async with ModelConfigChange(ops_test, **{"update-status-hook-interval": "10s"}):
        # Wait for a considerable amount of time to make sure charms can repeatedly handle this.
        # If all goes well, `wait_for_idle` would raise a timeout error
        soak_time = 5 * 60  # 5 min
        try:
            await ops_test.model.wait_for_idle(
                status="active",
                raise_on_error=True,
                timeout=soak_time,
                idle_period=soak_time,
                check_freq=0.5,
            )
        except asyncio.TimeoutError:
            # Good, this means no error during the soak time
            pass

    # After update-status frequency is restored to default, make sure all charms settle into active
    await ops_test.model.wait_for_idle(status="active")


async def test_prometheus_scrapes_loki_through_traefik(ops_test: OpsTest):
    """Prometheus should correctly scrape Loki through its traefik endpoint."""
    prom_url = await get_proxied_unit_url(ops_test, "prometheus", 0)
    loki_url = await get_proxied_unit_url(ops_test, "loki", 0)

    response = urllib.request.urlopen(f"{prom_url}/api/v1/targets", data=None, timeout=2.0)
    assert response.code == 200
    targets = json.loads(response.read())["data"]["activeTargets"]
    targets_summary = [(t["scrapeUrl"], t["health"]) for t in targets]
    assert (f"{loki_url}/metrics", "up") in targets_summary
    logger.info("prometheus is successfully scraping loki through traefik")


async def test_loki_receives_logs_through_traefik(ops_test: OpsTest):
    """Loki should be able to receive logs through its traefik endpoint."""
    loki_url = await get_proxied_unit_url(ops_test, "loki", 0)

    ops_test.model.deploy("zinc-k8s", application_name="zinc", channel="stable", trust=True)
    await ops_test.model.wait_for_idle(status="active")
    # Create the relation
    await ops_test.model.add_relation("loki", "zinc")
    await ops_test.model.wait_for_idle(status="active")
    # Check that logs are coming in
    response = urllib.request.urlopen(f"{loki_url}/api/v1/series")
    assert response.code == 200
    series = json.loads(response.read())["data"]
    series_charms = [s["juju_charm"] for s in series]
    assert "zinc-k8s" in series_charms
    logger.info("loki is successfully receiving zinc logs through traefik")
