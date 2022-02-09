#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

# pytest depends on this to make fixtures work
# with custom decorators
import asyncio
import functools
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Tuple

import pytest
from juju.juju import Juju
from pytest_operator import OpsTest, check_deps

logger = logging.getLogger(__name__)


class NoCompatibleDeploymentError(Exception):
    """Raise an exception if a matching controller+cloud cannot be found."""

    pass


class Store(defaultdict):
    def __init__(self):
        super(Store, self).__init__(Store)

    def __getattr__(self, key):
        """Override __getattr__ so dot syntax works on keys."""
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        """Override __setattr__ so dot syntax works on keys."""
        self[key] = value


store = Store()


def pytest_addoption(parser):
    # not providing the "default" arg to addoption: the bundle template already specifies defaults
    parser.addoption("--alertmanager", action="store")
    parser.addoption("--prometheus", action="store")
    parser.addoption("--grafana", action="store")
    parser.addoption("--loki", action="store")
    parser.addoption("--avalanche", action="store")
    parser.addoption("--channel", action="store")


def pytest_configure(config: pytest.Config):
    """Map out Juju controller->cloud mappings."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_juju_controller_details())


async def set_juju_controller_details() -> None:
    """Map out Juju controller->cloud mappings."""
    info = {
        "machine": {},
        "kubernetes": {},
        "both": {},
    }
    juju_client = Juju()
    controllers = juju_client.get_controllers()
    for controller in list(controllers.keys()):
        types = {}
        c = await controller.get_controller(controller)
        clouds = await c.clouds()["clouds"]
        for cl_name, cl_type in dict(clouds.items()):
            types[cl_name] = cl_type

        if len(types.values()) > 1 and "kubernetes" in types.values():
            info["both"][c.controller_name] = types
        elif "kubernetes" in types.values():
            info["kubernetes"][c.controller_name] = types
        else:
            info["machine"][c.controller_name] = types

    store.controllers = info


def get_deployment_details_by_type(cloud_type: str) -> Tuple[str, str]:
    """Get an appropriate controller by name and cloud name."""
    if not store.controllers[cloud_type]:
        raise NoCompatibleDeploymentError(
            "No suitable combination of controller and cloud could be matched to deploy the charm!"
        )

    controller, cloud = next(iter(store.controllers[cloud_type].items()))
    return controller, cloud


def timed_memoizer(func) -> Any:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        fname = func.__qualname__
        logger.info("Started: %s" % fname)
        start_time = datetime.now()
        if fname in store.keys():
            ret = store[fname]
        else:
            logger.info("Return for {} not cached".format(fname))
            ret = await func(*args, **kwargs)
            store[fname] = ret
        logger.info("Finished: {} in: {} seconds".format(fname, datetime.now() - start_time))
        return ret

    return wrapper


@pytest.fixture(scope="session", autouse=True, name="store")
def _get_store(request):
    return store


# Override opstest so we can pick appropriately
@pytest.fixture(scope="module")
@pytest.mark.asyncio
def ops_test() -> Any:
    async def wrapped(request, tmp_path_factory, cloud_type):
        check_deps("juju", "charmcraft")
        controller, cloud = get_deployment_details_by_type(cloud_type)
        request.config.option.controller = controller
        request.config.option.cloud = cloud
        ops_test = OpsTest(request, tmp_path_factory)
        await ops_test._setup_model()
        OpsTest._instance = ops_test
        yield ops_test
        OpsTest._instance = None
        await ops_test._cleanup_model()

    return wrapped
