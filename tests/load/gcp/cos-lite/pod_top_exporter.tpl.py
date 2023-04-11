# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import subprocess
from typing import Dict
from datetime import datetime
from flask import Flask
from lightkube.utils.quantity import parse_quantity

# Run with: `FLASK_APP=pod_top_exporter.py flask run`
app = Flask(__name__)

# For memoization
prev_time = None
prev_data = {}


def get_top_pod() -> dict:
    global prev_time, prev_data
    now = datetime.now()
    if prev_time and (now - prev_time).total_seconds() < 15:
        return prev_data

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
    prev_data = as_dict
    # print(as_dict)
    return as_dict


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

    output = str(cpu) + str(mem)
    return output
