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


@pytest.fixture(autouse=True, scope="module")
async def setup_env(ops_test: OpsTest):
    # Prevent "update-status" from interfering with the test:
    # - if fired "too quickly", traefik will flip between active/idle and maintenance;
    # - make sure charm code does not rely on update-status for correct operation.
    await ops_test.model.set_config(
        {"update-status-hook-interval": "60m", "logging-config": "<root>=WARNING; unit=DEBUG"}
    )


@pytest.fixture(scope="module")
async def rendered_bundle() -> Path:
    """Returns the pathlib.Path for the rendered bundle file."""
    # If a bundle.yaml file already exists, use it (do no render anything).
    user_bundle = get_this_script_dir() / ".." / ".." / "bundle.yaml"
    if not user_bundle.exists():
        raise FileNotFoundError("Expected a 'bundle.yaml' to be present")

    return user_bundle
