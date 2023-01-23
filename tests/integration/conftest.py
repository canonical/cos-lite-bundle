# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

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
