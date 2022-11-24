#!/usr/bin/env python3

# FLASK_APP=./cos-lite-rest-server.py flask run -p 8081 --host 0.0.0.0

import functools
import subprocess
import yaml
from flask import Flask

app = Flask(__name__)


@app.route("/helper/grafana/password")
@functools.lru_cache
def get_admin_password():
    action_result = subprocess.Popen(
        ['juju', 'run-action', 'grafana/0', 'get-admin-password', '--wait'],
        stdout=subprocess.PIPE, user="ubuntu",
    )
    as_dict = yaml.safe_load(action_result.stdout.read().decode())
    return as_dict["unit-grafana-0"]["results"]["admin-password"]
