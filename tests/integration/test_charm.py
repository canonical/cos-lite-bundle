#!/usr/bin/env python3

#  Copyright 2021 Canonical Ltd.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
import json
import logging

import pytest
import requests
from helpers import (
    cli_deploy_bundle,
    get_alertmanager_alerts,
    get_alertmanager_groups,
    get_unit_address,
)

log = logging.getLogger(__name__)


juju_topology_keys = {"juju_model_uuid", "juju_model", "juju_application"}


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test):
    """Build the charm-under-test and deploy it together with related charms.

    Assert on the unit status before any relations/configurations take place.
    """
    # use CLI to deploy bundle until https://github.com/juju/python-libjuju/issues/511 is fixed.
    # await cli_deploy_bundle("lma-light")
    await cli_deploy_bundle(ops_test, "./bundle-local.yaml")

    # due to a juju bug, occasionally alertmanager finishes a startup sequence with "waiting
    # for IP address". issuing a dummy config change just to trigger an event
    await ops_test.model.applications["alertmanager"].set_config(
        {"pagerduty::service_key": "just_a_dummy"}
    )
    await ops_test.model.wait_for_idle(status="active", timeout=60)
    assert ops_test.model.applications["alertmanager"].units[0].workload_status == "active"


@pytest.mark.abort_on_fail
async def test_alertmanager_is_up(ops_test):
    address = await get_unit_address(ops_test, "alertmanager", 0)
    url = f"http://{address}:9093"
    log.info("am public address: %s", url)

    response = requests.get(f"{url}/api/v2/status")
    assert response.status_code == 200
    assert "versionInfo" in json.loads(response.text)


@pytest.mark.abort_on_fail
async def test_prometheus_is_up(ops_test):
    address = await get_unit_address(ops_test, "prometheus", 0)
    url = f"http://{address}:9090"
    log.info("prom public address: %s", url)

    response = requests.get(f"{url}/-/ready")
    assert response.status_code == 200


@pytest.mark.abort_on_fail
async def test_prometheus_sees_alertmanager(ops_test):
    am_address = await get_unit_address(ops_test, "alertmanager", 0)
    prom_address = await get_unit_address(ops_test, "prometheus", 0)

    response = requests.get(f"http://{prom_address}:9090/api/v1/alertmanagers")
    assert response.status_code == 200
    alertmanagers = json.loads(response.text)
    # an empty response looks like this:
    # {"status":"success","data":{"activeAlertmanagers":[],"droppedAlertmanagers":[]}}
    # a jsonified activeAlertmanagers looks like this:
    # [{'url': 'http://10.1.179.124:9093/api/v1/alerts'}]
    assert any(
        f"http://{am_address}:9093" in am["url"]
        for am in alertmanagers["data"]["activeAlertmanagers"]
    )


async def test_juju_topology_labels_in_alerts(ops_test):
    alerts = await get_alertmanager_alerts(ops_test, "alertmanager", 0, retries=100)

    i = -1
    for i, alert in enumerate(alerts):
        # make sure every alert has all the juju topology labels
        # NOTE this would only test alerts that are already firing while testing
        assert alert["labels"].keys() >= juju_topology_keys

        # make sure the juju topology entries are not empty
        assert all(alert["labels"][key] for key in juju_topology_keys)

    assert i >= 0  # should have at least one alarms listed (the "AlwaysFiring" alarm rule)
    log.info("juju topology test passed for %s alerts", i + 1)


async def test_alerts_are_grouped(ops_test):
    groups = await get_alertmanager_groups(ops_test, "alertmanager", 0, retries=100)
    i = -1
    for i, group in enumerate(groups):
        # make sure all groups are grouped by juju topology keys
        assert group["labels"].keys() == juju_topology_keys

    assert i >= 0  # should have at least one group listed (the "AlwaysFiring" alarm rule)
    log.info("juju topology grouping test passed for %s groups", i + 1)
