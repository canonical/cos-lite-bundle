# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import asyncio
import json
import logging
import ssl
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Union

from juju.controller import Controller
from juju.model import Model
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


# We also need an insecure context to connect to e.g. unit ip addresses directly
insecure_context = ssl.create_default_context()
insecure_context.check_hostname = False
insecure_context.verify_mode = ssl.CERT_NONE


async def cli_deploy_bundle(
    ops_test: OpsTest, name: str, *, channel: str = "edge", overlays: List[Union[str, Path]] = None
):
    """Deploy bundle from charmhub or from file."""
    # use CLI to deploy bundle until https://github.com/juju/python-libjuju/issues/511 is fixed.
    overlay_args = []
    if overlays:
        for overlay in overlays:
            overlay_args.extend(["--overlay", str(overlay)])

    run_args = [
        "juju",
        "deploy",
        "--trust",
        "-m",
        ops_test.model_full_name,
        name,
    ] + overlay_args
    if not Path(name).is_file():
        run_args.append(f"--channel={channel}")

    retcode, stdout, stderr = await ops_test.run(*run_args)
    assert retcode == 0, f"Deploy failed: {(stderr or stdout).strip()}"
    logger.info(stdout)
    # FIXME: raise_on_error should be removed (i.e. set to True) when units stop flapping to error
    await ops_test.model.wait_for_idle(timeout=1000, raise_on_error=False)


async def get_all_proxied_urls(ops_test: OpsTest) -> Dict[str, Dict[str, str]]:
    """Returns the URL assigned by Traefik over the ingress_per_unit relation interface for all proxied units."""
    action = (
        await ops_test.model.applications["traefik"].units[0].run_action("show-proxied-endpoints")
    )
    action = await action.wait()
    # Before deserialization, output looks like this:
    # '{"prom/0": {"url": "http://cluster.local:80/test-prometheus-alerts-32k4-prom-0"}, "am": {"url": "http://cluster.local:80/test-prometheus-alerts-32k4-am"}}'
    proxied_endpoints = json.loads(action.results["proxied-endpoints"])

    logging.debug(f"Endpoints proxied by Traefik/0: {proxied_endpoints}")

    return proxied_endpoints


async def get_proxied_url(ops_test: OpsTest, app_name: str, unit_num: Optional[int] = None) -> str:
    """Returns the URL assigned by Traefik over the ingress_per_unit relation interface."""
    proxied_endpoints = await get_all_proxied_urls(ops_test)

    key = f"{app_name}/{unit_num}" if unit_num is not None else app_name
    return proxied_endpoints[key]["url"]


async def get_address(ops_test: OpsTest, app_name: str, unit_num: Optional[int] = None) -> str:
    """Find unit address for any application.

    Args:
        ops_test: pytest-operator plugin
        app_name: string name of application
        unit_num: integer number of a juju unit

    Returns:
        unit address as a string
    """
    status = await ops_test.model.get_status()
    app = status["applications"][app_name]
    return (
        app.public_address
        if unit_num is None
        else app["units"][f"{app_name}/{unit_num}"]["address"]
    )


async def get_alertmanager_alerts(ops_test: OpsTest, app_name, retries=3) -> List[dict]:
    """Get a list of alerts.

    Response looks like this:
    {
        'annotations': {'description': 'test-charm-...', 'summary': 'Instance test-charm-...'},
        'endsAt': '2021-09-03T21:03:59.658Z',
        'fingerprint': '4a0016cc12a07903',
        'receivers': [{'name': 'pagerduty'}],
        'startsAt': '2021-09-03T19:37:59.658Z',
        'status': {'inhibitedBy': [], 'silencedBy': [], 'state': 'active'},
        'updatedAt': '2021-09-03T20:59:59.660Z',
        'generatorURL': 'http://prometheus-0:9090/...',
        'labels': {
            'alertname': 'AlwaysFiring',
            'instance': 'test-charm-...',
            'job': 'juju_test-charm-...',
            'juju_application': 'tester', 'juju_model': 'test-charm-...',
            'juju_model_uuid': '...',
            'juju_unit': 'tester-0',
            'severity': 'Low',
            'status': 'testing'
        }
    }
    """
    url = f"{await get_proxied_url(ops_test, app_name)}/api/v2/alerts"
    while not (
        alerts := json.loads(
            urllib.request.urlopen(url, data=None, timeout=2, context=insecure_context).read()
        )
    ):
        retries -= 1
        logger.warning("no alerts")
        if retries > 0:
            await asyncio.sleep(2)
        else:
            break

    return alerts


async def get_alertmanager_groups(ops_test: OpsTest, app_name, retries=3) -> List[dict]:
    """Get a list of groups of alerts.

    Response looks like this:
    [
        {
            'alerts': [alarm1_dict, alarm2_dict, ...],
            'labels':
                {
                    'juju_application': 'tester',
                    'juju_model': 'test-charm-...',
                    'juju_model_uuid': '...',
                },
            'receiver': {'name': 'pagerduty'}
        }
    ]
    where "alarm1_dict" etc. are the same object described in `get_alertmanager_alerts`.
    """
    # TODO consume this from alertmanager_client when becomes available
    url = f"{await get_proxied_url(ops_test, app_name)}/api/v2/alerts/groups"

    while not (
        groups := json.loads(
            urllib.request.urlopen(url, data=None, timeout=2, context=insecure_context).read()
        )
    ):
        retries -= 1
        logger.warning("no alerts")
        if retries > 0:
            await asyncio.sleep(2)
        else:
            break

    return groups


class ModelConfigChange:
    """Context manager for temporarily changing a model config option."""

    def __init__(self, ops_test: OpsTest, **kwargs):
        self.ops_test = ops_test
        self.change_to = kwargs

    async def __aenter__(self):
        """On entry, the config is set to the user provided custom values."""
        config = await self.ops_test.model.get_config()
        self.revert_to = {k: config[k] for k in self.change_to.keys()}
        await self.ops_test.model.set_config(self.change_to)
        return self

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        """On exit, the modified config options are reverted to their original values."""
        await self.ops_test.model.set_config(self.revert_to)


async def get_or_add_model(controller: Controller, model_name: str) -> Model:
    return (
        controller.get_model(model_name)
        if model_name in await controller.get_models()
        else controller.add_model(model_name)
    )
