#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Utility for rendering the bundle yaml template."""

import argparse
import inspect
import os
from pathlib import Path
from typing import Dict, Set, Tuple, Union

from jinja2 import Environment, Template, meta

# https://stackoverflow.com/a/6209894/3516684
this_script_dir = os.path.dirname(inspect.getframeinfo(inspect.currentframe()).filename)  # type: ignore[arg-type]
BUNDLE_TEMPLATE_PATH = os.path.join(this_script_dir, "bundle.yaml.j2")


def read_bundle_template(
    filename: Union[str, Path] = BUNDLE_TEMPLATE_PATH
) -> Tuple[str, Set[str]]:
    """Read the template file from disk.

    Returns:
        A 2-tuple of the contents and a list of the template variables.
    """
    env = Environment()
    with open(filename) as t:
        contents = t.read()

    # get template variables
    ast = env.parse(contents)
    template_variables = meta.find_undeclared_variables(ast)

    return contents, template_variables


def parse_args() -> Tuple[Path, Path, Dict[str, str]]:
    """Parse CLI args, dynamically adding the list of bundle template variables as parsed args.

    Returns:
        A 3-tuple of the template path, the rendered output path and a mapping of template vars.
    """
    parser = argparse.ArgumentParser(description="Render jinja2 bundle template from cli args.")
    parser.add_argument(
        "--template",
        type=Path,
        help="path to the bundle template to render",
        default=BUNDLE_TEMPLATE_PATH,
    )
    parser.add_argument(
        "output",
        type=Path,
        help="path to the rendered bundle yaml",
    )
    bundle_args, var_args = parser.parse_known_args()

    if not bundle_args.template.is_file():
        raise FileNotFoundError(f"No such file: {bundle_args.template}")

    bundle_variables = read_bundle_template(bundle_args.template)[1]

    variable_parser = argparse.ArgumentParser()
    for var in bundle_variables:
        variable_parser.add_argument("--" + var, type=str)

    # Parse variable args and keep only the once that are not None, otherwise they will be passed
    # to the template and be considered as "defined", resulting in:
    # jinja2.exceptions.UndefinedError: 'None' has no attribute 'endswith'
    variables = {
        k: v for k, v in vars(variable_parser.parse_args(var_args)).items() if v is not None
    }

    return bundle_args.template, bundle_args.output, variables


def render_bundle(template: Path, output: Path, variables: Dict[str, str] = None):
    """The main function for rendering the bundle template."""
    if variables is None:
        variables = {}

    # for path in map(Path, variables.values()):
    #     if not path.is_file():
    #         print(f"WARNING: File does not exist: {path}")

    with open(template) as t:
        jinja_template = Template(t.read(), autoescape=True)

    # print(jinja_template.render(**variables))
    with open(output, "wt") as o:
        jinja_template.stream(**variables).dump(o)


if __name__ == "__main__":
    render_bundle(*parse_args())
