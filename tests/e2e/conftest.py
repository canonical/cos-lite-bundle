# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import inspect
import logging
import os
from pathlib import Path

import pytest
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


def get_this_script_dir() -> Path:
    filename = inspect.getframeinfo(inspect.currentframe()).filename  # type: ignore[arg-type]
    path = os.path.dirname(os.path.abspath(filename))
    return Path(path)


def pytest_addoption(parser):
    # not providing the "default" arg to addoption: the bundle template already specifies defaults
    parser.addoption("--traefik", action="store")
    parser.addoption("--alertmanager", action="store")
    parser.addoption("--prometheus", action="store")
    parser.addoption("--grafana", action="store")
    parser.addoption("--loki", action="store")
    parser.addoption("--avalanche", action="store")
    parser.addoption("--channel", action="store")


@pytest.fixture(scope="module")
async def rendered_bundle(ops_test: OpsTest, pytestconfig) -> Path:
    """Returns the pathlib.Path for the rendered bundle file."""
    logger.info("Rendering bundle %s", get_this_script_dir() / ".." / ".." / "bundle.yaml.j2")

    async def build_charm_if_is_dir(option: str) -> str:
        if Path(option).is_dir():
            logger.info("Building charm from source: %s", option)
            option = str(await ops_test.build_charm(option))
        return option

    charms = {
        "traefik": pytestconfig.getoption("traefik"),
        "alertmanager": pytestconfig.getoption("alertmanager"),
        "prometheus": pytestconfig.getoption("prometheus"),
        "grafana": pytestconfig.getoption("grafana"),
        "loki": pytestconfig.getoption("loki"),
        "avalanche": pytestconfig.getoption("avalanche"),
    }

    additional_args = {
        "channel": pytestconfig.getoption("channel"),
    }

    context = {k: await build_charm_if_is_dir(v) for k, v in charms.items() if v is not None}
    context.update(additional_args)
    logger.debug("context: %s", context)

    rendered_bundle = ops_test.render_bundle(
        get_this_script_dir() / ".." / ".." / "bundle.yaml.j2", context=context
    )

    return rendered_bundle
