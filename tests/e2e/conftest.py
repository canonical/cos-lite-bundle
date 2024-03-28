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


@pytest.fixture(scope="module")
async def rendered_bundle() -> Path:
    """Returns the pathlib.Path for the rendered bundle file."""
    # If a bundle.yaml file already exists, use it (do no render anything).
    user_bundle = get_this_script_dir() / ".." / ".." / "bundle.yaml"
    if not user_bundle.exists():
        raise FileNotFoundError("Expected a 'bundle.yaml' to be present")

    return user_bundle
