#!/usr/bin/env python3

"""
This script updates a bundle.yaml file with revisions from charmhub.
"""

import sys
import yaml
import json
from pathlib import Path
import os
import base64
from urllib.request import urlopen, Request


def obtain_charm_releases(charm_name: str) -> dict:
    """Obtain charm releases from charmhub as a dict.

    Args:
        charm_name: e.g. "grafana-k8s".
    """
    if token := os.environ.get("CHARMHUB_TOKEN"):
        macaroon = json.loads(base64.b64decode(token))['v']
    elif file := os.environ.get("CREDS_FILE"):
        macaroon = json.loads(base64.b64decode(Path(file).read_text()))['v']
    else:
        raise RuntimeError("Must set one of CHARMHUB_TOKEN, CREDS_FILE envvars.")
    headers = {"Authorization": f"Macaroon {macaroon}"}

    url = f"https://api.charmhub.io/v1/charm/{charm_name}/releases"
    with urlopen(Request(url, headers=headers), timeout=10) as response:
        body = response.read()

    # Output looks like this:
    # {
    #   "channel-map": [
    #     {
    #       "base": {
    #         "architecture": "amd64",
    #         "channel": "20.04",
    #         "name": "ubuntu"
    #       },
    #       "channel": "1.0/beta",
    #       "expiration-date": null,
    #       "progressive": {
    #         "paused": null,
    #         "percentage": null
    #       },
    #       "resources": [
    #         {
    #           "name": "grafana-image",
    #           "revision": 62,
    #           "type": "oci-image"
    #         },
    #         {
    #           "name": "litestream-image",
    #           "revision": 43,
    #           "type": "oci-image"
    #         }
    #       ],
    #       "revision": 93,
    #       "when": "2023-11-22T09:12:26Z"
    #     },
    return json.loads(body)


def obtain_revisions_from_charmhub(charm_name: str, channel: str, base_arch: str, base_channel: str) -> dict:
    """Obtain revisions for a given channel and arch.

    Args:
        charm_name: e.g. "grafana-k8s".
        channel: e.g. "latest/edge".
        base_arch: base architecture, e.g. "amd64".
        base_channel: e.g. "22.04". TODO: remove arg and auto pick the latest

    Returns: Dict of resources. Looks like this:
        {
          "grafana-k8s": {
            "revision": 106,
            "resources": {
              "grafana-image": 68,
              "litestream-image": 43
            }
          }
        }
    """
    releases = obtain_charm_releases(charm_name)
    for channel_dict in releases["channel-map"]:
        print(charm_name, channel_dict["channel"], channel_dict["base"]["architecture"], channel_dict["base"]["channel"])
        if not(channel_dict["channel"] == channel and channel_dict["base"]["architecture"] == base_arch and channel_dict["base"]["channel"] == base_channel):
            continue

        return {
            charm_name: {
                "revision": channel_dict["revision"],
                "resources": {res["name"]: res["revision"] for res in channel_dict["resources"]}
            }
        }


def freeze_bundle(bundle: dict, cleanup: bool = True):
    bundle = bundle.copy()
    for app_name in bundle["applications"]:
        app = bundle["applications"][app_name]
        charm_name = app["charm"]
        app_channel = app["channel"] if "/" in app["channel"] else f"latest/{app['channel']}"
        # TODO externalize "base_arch" as an input to the script.
        frozen_app = obtain_revisions_from_charmhub(charm_name, app_channel, "amd64", "20.04")
        app["revision"] = frozen_app[charm_name]["revision"]
        app["resources"].update(frozen_app[charm_name]["resources"])

        if cleanup:
            app.pop("constraints", None)
            app.pop("storage", None)

    return bundle


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise RuntimeError("Expecting one arg: path to bundle yaml")

    bundle_path = sys.argv[1]
    frozen = freeze_bundle(yaml.safe_load(Path(bundle_path).read_text()))
    print(yaml.safe_dump(frozen))
