#!/usr/bin/env python3

from prometheus_client import start_http_server, Histogram, Summary, Enum, Gauge
import subprocess
import psutil
import time
import yaml
import json
from collections import deque

import urllib.error
import urllib.parse
import urllib.request

# _percent
# _sec
# _up

# Create a metric to track time spent and requests made.
cpu_avg = deque(maxlen=10)
cpu_percent = Gauge('cpu_percent', 'CPU %')
vmem_percent = Gauge('vmem_percent', "Virtual memory %")
smem_percent = Gauge('smem_percent', "Swap memory %")
disk_percent = Gauge('disk_percent', "Disk %")
scrape_duration_sec = Gauge('scrape_duration_sec', 'Scrape duration')
scrape_duration_percent = Gauge('scrape_duration_percent', 'Scrape duration %')
scrape_interval_sec = Gauge('scrape_interval_sec', 'Scrape interval')

prom_api_req_sec = Gauge('prom_api_req_sec', 'Prom API server response time')

prom_scrape_avalanche_up = Gauge(
    'prom_scrape_avalanche_up',
    'Prom scraped avalanche successfully')

juju_up = Gauge(
    'juju_up',
    'Juju is responsive')

vmem_gb = Gauge('vmem_gb', "virtual memory [GB]")
smem_gb = Gauge('smem_gb', "swap memory [GB]")
disk_gb = Gauge('disk_gb', "disk [GB]")


def get_stdout(args: list):
    return subprocess.run(args, stdout=subprocess.PIPE).stdout.decode('utf-8')


JUJU_MODEL = json.loads(get_stdout(['juju', 'models', '--format=json']))['current-model']


def get_json_from_url(url: str, timeout: float = 5.0) -> dict:
    """Send a GET request with a timeout.

    Args:
        url: target url to GET from
        timeout: duration in seconds after which to return, regardless the result

    Raises:
        AlertmanagerBadResponse: If no response or invalid response, regardless the reason.
    """
    try:
        response = urllib.request.urlopen(url, data=None, timeout=timeout)
        if response.code == 200 and response.reason == "OK":
            return json.loads(response.read())
    except (ValueError, urllib.error.HTTPError, urllib.error.URLError):
        return {}


def get_prom_address(unit="prometheus/0"):
    try:
        unit_info = yaml.safe_load(get_stdout(['juju', 'show-unit', unit]))
        juju_up.set(1)
    except:
        juju_up.set(0)
        raise
    return unit_info[unit]["address"]


def get_scrape_duration():
    targets_url = f"http://{get_prom_address()}:9090/api/v1/targets"
    targets_info = get_json_from_url(targets_url)  # json.loads(get_stdout(["curl", "--no-progress-meter", targets_url]))
    ours = list(filter(lambda target: target["discoveredLabels"]["__address__"] == "192.168.1.101:9001", targets_info["data"]["activeTargets"]))
    prom_scrape_avalanche_up.set(int(ours[0]["health"] == "up"))
    return ours[0]["lastScrapeDuration"]


def get_scrape_interval() -> int:
    config_url = f"http://{get_prom_address()}:9090/api/v1/status/config"
    config_info = get_json_from_url(config_url)  # json.loads(get_stdout(["curl", "--no-progress-meter", config_url]))
    config_info = yaml.safe_load(config_info["data"]["yaml"])
    ours = list(
        filter(lambda scrape_config: set(scrape_config["static_configs"][0]["targets"]) >= {"192.168.1.101:9001"},
               config_info["scrape_configs"]))
    #as_str = sum([itm["scrape_interval"] for itm in ours])/len(ours)
    as_str = ours[0]["scrape_interval"]
    as_int = int(as_str[:-1])  # assuming it is always "10s" etc.
    if as_str[-1] == 'm':
        as_int *= 60
    return as_int


def get_prom_disk_usage() -> float:
    """Return size of prom folder, in GB, if kubectl succeeded; NaN otherwise."""
    args = ['microk8s.kubectl', 'exec', '-n', JUJU_MODEL, 'prometheus-0', '-c', 'prometheus', '--',
            'du', '--max-depth=0', '/var/lib/prometheus']
    try:
        s = get_stdout(args)
        return int(s.split()[0]) / 1e6
    except:
        return float("nan")


def process_sys_metrics():
    cpu_avg.append(psutil.cpu_percent())
    cpu_percent.set(sum(cpu_avg)/len(cpu_avg))

    vm = psutil.virtual_memory()
    vmem_percent.set(vm.percent)
    vmem_gb.set(vm.total / 1e9 * (vm.percent / 100))

    sm = psutil.swap_memory()
    smem_percent.set(sm.percent)
    smem_gb.set(sm.used / 1e9)

    disk = psutil.disk_usage(".")
    # disk_percent.set(disk.percent)
    # disk_gb.set(disk.used / 1e9)

    prom_disk_usage = get_prom_disk_usage()  # in GB
    disk_gb.set(prom_disk_usage)
    disk_percent.set(prom_disk_usage / (disk.total / 1e9))


if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(8000)

    while True:
        print("Trying to comm with prom...")
        try:
            si = get_scrape_interval()
            print("Success.")
            break
        except:
            time.sleep(2)

    while True:
        process_sys_metrics()
        if not int(time.time()) % si:
            try:
                tic = time.time()
                sd = get_scrape_duration()
                si = get_scrape_interval()
                toc = time.time()
                prom_api_req_sec.set((toc - tic) / 2)

                scrape_duration_sec.set(sd)
                scrape_interval_sec.set(si)
                scrape_duration_percent.set(sd/si * 100)
            except:
                prom_scrape_avalanche_up.set(0)
                prom_api_req_sec.set(float("nan"))
                scrape_duration_sec.set(float("nan"))
                scrape_interval_sec.set(float("nan"))
                scrape_duration_percent.set(float("nan"))

        time.sleep(1)
