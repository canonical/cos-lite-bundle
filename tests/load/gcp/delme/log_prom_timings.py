#!/usr/bin/env python3

import subprocess
import time
import yaml
import json

import urllib.error
import urllib.parse
import urllib.request

import syslog
from typing import Tuple

from pathlib import Path



def get_stdout(args: list):
    return subprocess.run(args, stdout=subprocess.PIPE).stdout.decode('utf-8')


def get_json_from_url(url: str, timeout: float = 5.0) -> Tuple[float, dict]:
    """Send a GET request with a timeout.

    Args:
        url: target url to GET from
        timeout: duration in seconds after which to return, regardless the result

    Raises:
        AlertmanagerBadResponse: If no response or invalid response, regardless the reason.
    """
    tic = time.time()
    try:
        response = urllib.request.urlopen(url, data=None, timeout=timeout)
        toc = time.time()
        if response.code == 200 and response.reason == "OK":
            return toc - tic, json.loads(response.read())
    except (ValueError, urllib.error.HTTPError, urllib.error.URLError):
        toc = time.time()
        return toc - tic, {}


def get_prom_address(unit="prometheus/0") -> str:
    unit_info = yaml.safe_load(get_stdout(['juju', 'show-unit', unit]))
    return unit_info[unit]["address"]


#   "status": "success",
#   "data": {
#     "activeTargets": [
#       {
#         "discoveredLabels": {
#           "__address__": "10.128.0.2:9001",
#           "__metrics_path__": "/metrics",
#           "__scheme__": "http",
#           "job": "juju_welcome_00c2b01_scrape-target_external_jobs"
#         },
#         "labels": {
#           "instance": "10.128.0.2:9001",
#           "job": "juju_welcome_00c2b01_scrape-target_external_jobs"
#         },
#         "scrapePool": "juju_welcome_00c2b01_scrape-target_external_jobs",
#         "scrapeUrl": "http://10.128.0.2:9001/metrics",
#         "globalUrl": "http://10.128.0.2:9001/metrics",
#         "lastError": "",
#         "lastScrape": "2021-10-22T03:35:27.946519841Z",
#         "lastScrapeDuration": 5.253790098,
#         "health": "up"
#       },
#       {
#         "discoveredLabels": {
#           "__address__": "10.128.0.2:9002",
#           "__metrics_path__": "/metrics",
#           "__scheme__": "http",
#           "job": "juju_welcome_00c2b01_scrape-target_external_jobs"
#         },
#         "labels": {
#           "instance": "10.128.0.2:9002",
#           "job": "juju_welcome_00c2b01_scrape-target_external_jobs"
#         },
#         "scrapePool": "juju_welcome_00c2b01_scrape-target_external_jobs",
#         "scrapeUrl": "http://10.128.0.2:9002/metrics",
#         "globalUrl": "http://10.128.0.2:9002/metrics",
#         "lastError": "",
#         "lastScrape": "2021-10-22T03:35:39.502325598Z",
#         "lastScrapeDuration": 3.425528373,
#         "health": "up"
#       },
#       {
#         "discoveredLabels": {
#           "__address__": "10.128.0.2:9003",
#           "__metrics_path__": "/metrics",
#           "__scheme__": "http",
#           "job": "juju_welcome_00c2b01_scrape-target_external_jobs"
#         },
#         "labels": {
#           "instance": "10.128.0.2:9003",
#           "job": "juju_welcome_00c2b01_scrape-target_external_jobs"
#         },
#         "scrapePool": "juju_welcome_00c2b01_scrape-target_external_jobs",
#         "scrapeUrl": "http://10.128.0.2:9003/metrics",
#         "globalUrl": "http://10.128.0.2:9003/metrics",
#         "lastError": "",
#         "lastScrape": "2021-10-22T03:35:27.60591884Z",
#         "lastScrapeDuration": 3.712132839,
#         "health": "up"
#       },
#       {
#         "discoveredLabels": {
#           "__address__": "10.128.0.2:9004",
#           "__metrics_path__": "/metrics",
#           "__scheme__": "http",
#           "job": "juju_welcome_00c2b01_scrape-target_external_jobs"
#         },
#         "labels": {
#           "instance": "10.128.0.2:9004",
#           "job": "juju_welcome_00c2b01_scrape-target_external_jobs"
#         },
#         "scrapePool": "juju_welcome_00c2b01_scrape-target_external_jobs",
#         "scrapeUrl": "http://10.128.0.2:9004/metrics",
#         "globalUrl": "http://10.128.0.2:9004/metrics",
#         "lastError": "",
#         "lastScrape": "2021-10-22T03:36:05.528271125Z",
#         "lastScrapeDuration": 4.298098459,
#         "health": "up"
#       },
#       {
#         "discoveredLabels": {
#           "__address__": "10.128.0.2:9005",
#           "__metrics_path__": "/metrics",
#           "__scheme__": "http",
#           "job": "juju_welcome_00c2b01_scrape-target_external_jobs"
#         },
#         "labels": {
#           "instance": "10.128.0.2:9005",
#           "job": "juju_welcome_00c2b01_scrape-target_external_jobs"
#         },
#         "scrapePool": "juju_welcome_00c2b01_scrape-target_external_jobs",
#         "scrapeUrl": "http://10.128.0.2:9005/metrics",
#         "globalUrl": "http://10.128.0.2:9005/metrics",
#         "lastError": "",
#         "lastScrape": "2021-10-22T03:36:12.989584938Z",
#         "lastScrapeDuration": 3.675364708,
#         "health": "up"
#       },
#       {
#         "discoveredLabels": {
#           "__address__": "10.128.0.2:9006",
#           "__metrics_path__": "/metrics",
#           "__scheme__": "http",
#           "job": "juju_welcome_00c2b01_scrape-target_external_jobs"
#         },
#         "labels": {
#           "instance": "10.128.0.2:9006",
#           "job": "juju_welcome_00c2b01_scrape-target_external_jobs"
#         },
#         "scrapePool": "juju_welcome_00c2b01_scrape-target_external_jobs",
#         "scrapeUrl": "http://10.128.0.2:9006/metrics",
#         "globalUrl": "http://10.128.0.2:9006/metrics",
#         "lastError": "",
#         "lastScrape": "2021-10-22T03:35:23.483740606Z",
#         "lastScrapeDuration": 3.390475263,
#         "health": "up"
#       },
#       {
#         "discoveredLabels": {
#           "__address__": "localhost:9090",
#           "__metrics_path__": "/metrics",
#           "__scheme__": "http",
#           "job": "prometheus"
#         },
#         "labels": {
#           "instance": "localhost:9090",
#           "job": "prometheus"
#         },
#         "scrapePool": "prometheus",
#         "scrapeUrl": "http://localhost:9090/metrics",
#         "globalUrl": "http://prometheus-0:9090/metrics",
#         "lastError": "",
#         "lastScrape": "2021-10-22T03:36:15.215124046Z",
#         "lastScrapeDuration": 0.01732004,
#         "health": "up"
#       }
#     ],
#     "droppedTargets": []
#   }
# }

def prom_dir_size(path="/var/snap/microk8s") -> float:
    root_directory = Path(path)
    return sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file()) / 1e6  # in MB

if __name__ == '__main__':
    targets_url = f"http://{get_prom_address()}:9090/api/v1/targets"

    period = 60  # sec
    error_count = 0

    while True:
        response_time, targets_info = get_json_from_url(targets_url)
        if targets_info:
            scrapeDurations = [float(target["lastScrapeDuration"]) for target in targets_info["data"]["activeTargets"]]
        else:
            error_count += 1
            scrapeDurations = [float("inf")]
        # print(response_time, sorted(scrapeDurations))
        syslog_msg = f"scrapeDuration: {response_time} {sorted(scrapeDurations)}"
        syslog.syslog(syslog_msg)
        syslog.syslog(f"prom_dir_size={prom_dir_size()}")

        if error_count * period >= 2 * 60:  # more than 2 minutes
            try:
                # address may have changed
                targets_url = f"http://{get_prom_address()}:9090/api/v1/targets"
                error_count = 0
                continue
            except:
                pass

        time.sleep(60)
