# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import asyncio
import json
import logging
import urllib.request
from typing import List

log = logging.getLogger(__name__)


async def cli_deploy_and_wait(
    ops_test, name: str, alias: str = "", wait_for_status: str = None, channel="edge"
):
    if not alias:
        alias = name
    retcode, stdout, stderr = await ops_test._run(
        "juju",
        "deploy",
        "-m",
        ops_test.model_full_name,
        name,
        alias,
        f"--channel={channel}",
    )
    assert retcode == 0, f"Deploy failed: {(stderr or stdout).strip()}"
    log.info(stdout)
    await ops_test.model.wait_for_idle(apps=[alias], status=wait_for_status, timeout=60)


async def cli_deploy_bundle(ops_test, name: str, channel: str = "edge"):
    retcode, stdout, stderr = await ops_test._run(
        "juju",
        "deploy",
        "-m",
        ops_test.model_full_name,
        name,
        f"--channel={channel}",
    )
    assert retcode == 0, f"Deploy failed: {(stderr or stdout).strip()}"
    log.info(stdout)
    await ops_test.model.wait_for_idle(timeout=120)


async def get_unit_address(ops_test, app_name: str, unit_num: int) -> str:
    # return ops_test.model.applications[app_name].units[unit_num].data["private-address"]
    status = await ops_test.model.get_status()  # noqa: F821
    return status["applications"][app_name]["units"][f"{app_name}/{unit_num}"]["address"]


async def get_alertmanager_alerts(ops_test, unit_name, unit_num, retries=3) -> List[dict]:
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
    url = f"http://{address}:9093/api/v2/alerts"
    while not (alerts := json.loads(urllib.request.urlopen(url, data=None, timeout=2).read())):
        retries -= 1
        log.warning("no alerts")
        if retries > 0:
            await asyncio.sleep(2)
        else:
            break

    return alerts


async def get_alertmanager_groups(ops_test, unit_name, unit_num, retries=3) -> List[dict]:
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
    url = f"http://{address}:9093/api/v2/alerts/groups"
    while not (groups := json.loads(urllib.request.urlopen(url, data=None, timeout=2).read())):
        retries -= 1
        log.warning("no alerts")
        if retries > 0:
            await asyncio.sleep(2)
        else:
            break

    return groups
