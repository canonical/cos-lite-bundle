# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import subprocess
from datetime import datetime
from typing import Dict

from flask import Flask
from lightkube.utils.quantity import parse_quantity

# Run with: `FLASK_APP=pod_top_exporter.py flask run`
app = Flask(__name__)

# For memoization
prev_time = None
prev_top_pod_data = {}
prev_restart_count_data = {}


def get_top_pod() -> dict:
    global prev_time, prev_top_pod_data
    now = datetime.now()
    if prev_top_pod_data and prev_time and (now - prev_time).total_seconds() < 15:
        return prev_top_pod_data

    # Going through `current` directly because microk8s-kubectl.wrapper creates subprocesses which
    # expect a login session
    cmd = "/snap/microk8s/current/kubectl --kubeconfig /var/snap/microk8s/current/credentials/client.config top pod -n ${JUJU_MODEL_NAME} --no-headers".split()
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(e.stdout.decode())
        return {}

    output = result.stdout.decode("utf-8").strip()

    as_list = list(map(str.split, output.splitlines()))
    # [['alertmanager-0', '1m', '51Mi'], ['catalogue-0', '1m', '38Mi'], ... ]

    as_dict = {entry[0]: {"cpu": parse_quantity(entry[1]), "mem": parse_quantity(entry[2])} for entry in as_list}
    # {'alertmanager-0': {'cpu': Decimal('0.056'), 'mem': Decimal('55574528.000')}, ...}

    prev_time = now
    prev_top_pod_data = as_dict
    # print(as_dict)
    return as_dict


def get_restart_count() -> Dict[str, Dict[str, int]]:
    """Get the restart count per container per pod."""
    global prev_time, prev_top_pod_data
    now = datetime.now()
    if prev_restart_count_data and prev_time and (now - prev_time).total_seconds() < 15:
        return prev_top_pod_data

    # Going through `current` directly because microk8s-kubectl.wrapper creates subprocesses which
    # expect a login session
    jsnopath_expr = r'{range .items[*]}{.metadata.name}{range .status.containerStatuses[*]}{","}{.name}{","}{.restartCount}{end}{"\n"}{end}'
    cmd = [
        "/snap/microk8s/current/kubectl",
        "--kubeconfig",
        "/var/snap/microk8s/current/credentials/client.config",
        "-n",
        "${JUJU_MODEL_NAME}",
        "get",
        "pod",
        f"-o=jsonpath={jsnopath_expr}",
    ]
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(e.stdout.decode())
        return {}

    output = result.stdout.decode("utf-8").strip()
    # Output looks like this:
    # modeloperator-86c5cfd684-7c2cb,juju-operator,0
    # traefik-0,charm,0,traefik,0
    # alertmanager-0,alertmanager,0,charm,0
    # loki-0,charm,1,loki,1
    # scrape-target-0,charm,1
    # prometheus-0,charm,1,prometheus,0
    # catalogue-0,catalogue,0,charm,1
    # cos-config-0,charm,1,git-sync,1
    # grafana-0,charm,0,grafana,1,litestream,1
    # scrape-config-0,charm,1

    restart_counts = {}
    for line in output.splitlines():
        # Each line is made up of pod name and pairs of container name and restart count.
        # The length may change, depending on the number of containers in the pod.
        pod_name = line.split(",")[0]
        pairs = line.split(",")[1:]
        # Convert list to dict (https://stackoverflow.com/a/12739974/3516684)
        it = iter(pairs)
        pod_restart_counts = dict(zip(it, it))
        # Convert values from str to int:
        pod_restart_counts = {k: int(v) for k, v in pod_restart_counts.items()}
        restart_counts[pod_name] = pod_restart_counts

    return restart_counts


class GaugeFamily:
    def __init__(self, name: str, help: str):
        self.name = name
        self.help = help
        self.metrics = set()

    def add(self, labels: Dict[str, str], value: float):
        labels_as_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
        self.metrics.add((labels_as_str, value))

    def __str__(self):
        """Generate the metric header."""
        output = f"# HELP {self.name} {self.help}\n"
        output += f"# TYPE {self.name} gauge\n"
        for metric in self.metrics:
            labels = metric[0]
            value = metric[1]
            output += f'{self.name}{{{labels}}} {value}\n'

        return output


@app.route("/metrics")
def metrics():
    cpu = GaugeFamily("pod_cpu", "CPU usage")
    mem = GaugeFamily("pod_mem", "Memory usage (bytes)")

    items = get_top_pod().items()
    for name, resources in items:
        cpu.add({"name": name}, resources["cpu"])
        mem.add({"name": name}, resources["mem"])

    # TODO the restart count should be a counter type, not a gauge.
    pod_restart_count = GaugeFamily("pod_restart_count", "Pod restart count")
    for pod_name, containers in get_restart_count().items():
        for container_name, restart_count in containers.items():
            pod_restart_count.add({"pod_name": pod_name, "container_name": container_name}, restart_count)

    output = str(cpu) + str(mem) + str(pod_restart_count)
    return output
