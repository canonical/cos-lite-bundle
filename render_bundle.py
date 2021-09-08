#!/usr/bin/env python3

import argparse
from pathlib import Path
from typing import Dict, Tuple

from jinja2 import Template


def parse_args() -> Tuple[Path, Path, Dict[str, str]]:
    # https://stackoverflow.com/a/6209894/3516684
    # import inspect, os
    # this_script_dir = inspect.getframeinfo(inspect.currentframe()).filename

    parser = argparse.ArgumentParser(description="Render jinja2 bundle template from cli args.")
    parser.add_argument(
        "template",
        type=Path,
        help="path to the bundle template to render",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="path to the rendered bundle yaml",
    )
    bundle_args, unk_args = parser.parse_known_args()

    unk_parser = argparse.ArgumentParser()
    for arg in unk_args:
        if arg.startswith("--"):
            unk_parser.add_argument(arg.split("=", 1)[0], type=str)

    if not bundle_args.template.is_file():
        raise FileNotFoundError(f"No such file: {bundle_args.template}")

    return bundle_args.template, bundle_args.output, vars(unk_parser.parse_args(unk_args))


def render_bundle(template: Path, output: Path, variables: Dict[str, str] = None):
    if variables is None:
        variables = {}

    # for path in map(Path, variables.values()):
    #     if not path.is_file():
    #         print(f"WARNING: File does not exist: {path}")

    with open(template) as t:
        jinja_template = Template(t.read(), autoescape=True)

    # print(jinja_template.render(**variables))
    with open(output, 'wt') as o:
        jinja_template.stream(**variables).dump(o)


if __name__ == "__main__":
    render_bundle(*parse_args())
