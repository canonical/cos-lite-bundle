# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

import pytest
from helpers import disable_metallb, enable_metallb

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    # not providing the "default" arg to addoption: the bundle template already specifies defaults
    parser.addoption("--traefik", action="store")
    parser.addoption("--alertmanager", action="store")
    parser.addoption("--prometheus", action="store")
    parser.addoption("--grafana", action="store")
    parser.addoption("--loki", action="store")
    parser.addoption("--avalanche", action="store")
    parser.addoption("--channel", action="store")


@pytest.fixture(scope="module", autouse=True)
async def reenable_metallb():
    logger.info("First, disable metallb, in case it's enabled")
    await disable_metallb()
    logger.info("Now enable metallb")
    await enable_metallb()
