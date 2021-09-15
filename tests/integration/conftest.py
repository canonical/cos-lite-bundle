# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.


def pytest_addoption(parser):
    # not providing the "default" arg to addoption: the bundle template already specifies defaults
    parser.addoption("--alertmanager", action="store")
    parser.addoption("--prometheus", action="store")
    parser.addoption("--grafana", action="store")
    parser.addoption("--loki", action="store")
    parser.addoption("--tester", action="store")
    parser.addoption("--channel", action="store")
