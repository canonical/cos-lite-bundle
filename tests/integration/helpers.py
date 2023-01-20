# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import asyncio
import grp
import json
import logging
import subprocess
import urllib.request
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)

try:
    # In classically-confined microk8s, the group name is "microk8s"
    microk8s_group = grp.getgrnam("microk8s")
except KeyError:
    # In strictly-confined microk8s, the group name is "snap_microk8s"
    microk8s_group = "snap_microk8s"


async def disable_metallb():
    try:
        cmd = ["sg", microk8s_group, "-c", "microk8s disable metallb"]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.error(e.stdout.decode())
        raise

    await asyncio.sleep(30)  # why? just because, for now


async def enable_metallb():
    cmd = [
        "sh",
        "-c",
        "ip -4 -j route get 2.2.2.2 | jq -r '.[] | .prefsrc'",
    ]
    result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ip = result.stdout.decode("utf-8").strip()

    try:
        cmd = ["sg", microk8s_group, "-c", f"microk8s enable metallb:{ip}-{ip}"]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.error(e.stdout.decode())
        raise

    await asyncio.sleep(30)  # why? just because, for now
    return ip


async def cli_deploy_bundle(ops_test: OpsTest, name: str, channel: str = "edge"):
    # use CLI to deploy bundle until https://github.com/juju/python-libjuju/issues/511 is fixed.
    run_args = [
        "juju",
        "deploy",
        "--trust",
        "-m",
        ops_test.model_full_name,
        name,
    ]
    if not Path(name).is_file():
        run_args.append(f"--channel={channel}")

    retcode, stdout, stderr = await ops_test.run(*run_args)
    assert retcode == 0, f"Deploy failed: {(stderr or stdout).strip()}"
    logger.info(stdout)
    # FIXME: raise_on_error should be removed (i.e. set to True) when units stop flapping to error
    await ops_test.model.wait_for_idle(timeout=1000, raise_on_error=False)


async def get_proxied_unit_url(ops_test: OpsTest, app_name: str, unit_num: int) -> str:
    """Returns the URL assigned by Traefik over the ingress_per_unit relation interface."""
    action = (
        await ops_test.model.applications["traefik"].units[0].run_action("show-proxied-endpoints")
    )
    action = await action.wait()
    proxied_endpoints = json.loads(action.results["proxied-endpoints"])

    logging.debug(f"Endpoints proxied by Traefik/0: {proxied_endpoints}")

    unit_url = proxied_endpoints[f"{app_name}/{unit_num}"]["url"]

    # Replace the external, metallb URL with the one of traefik, to skip a lot of
    # routing "fun"
    traefik_0_address = await get_unit_address(ops_test, "traefik", 0)
    url = urlparse(unit_url)

    final_url = f"{url.scheme}://{traefik_0_address}:{url.port}{url.path}"
    logging.debug(f"Routing over traefik/0 using: {final_url}")

    return final_url


async def get_unit_address(ops_test: OpsTest, app_name: str, unit_num: int) -> str:
    # return ops_test.model.applications[app_name].units[unit_num].data["private-address"]
    status = await ops_test.model.get_status()  # noqa: F821
    return status["applications"][app_name]["units"][f"{app_name}/{unit_num}"]["address"]


async def get_alertmanager_alerts(
    ops_test: OpsTest, unit_name, unit_num, retries=3, path=""
) -> List[dict]:
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
    # TODO consume this from alertmanager_client when becomes available
    address = await get_unit_address(ops_test, unit_name, unit_num)
    path = "/" + path.lstrip("/").rstrip("/")
    url = f"http://{address}:9093{path}/api/v2/alerts"
    while not (alerts := json.loads(urllib.request.urlopen(url, data=None, timeout=2).read())):
        retries -= 1
        logger.warning("no alerts")
        if retries > 0:
            await asyncio.sleep(2)
        else:
            break

    return alerts


async def get_alertmanager_groups(
    ops_test: OpsTest, unit_name, unit_num, retries=3, path=""
) -> List[dict]:
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
    address = await get_unit_address(ops_test, unit_name, unit_num)
    path = "/" + path.lstrip("/").rstrip("/")
    url = f"http://{address}:9093{path}/api/v2/alerts/groups"
    while not (groups := json.loads(urllib.request.urlopen(url, data=None, timeout=2).read())):
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
