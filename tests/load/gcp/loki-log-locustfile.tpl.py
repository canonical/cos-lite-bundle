#!/usr/bin/env python3

# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""A locustfile for posting fake log data directly to loki, using fmtlog format."""

import json
from math import ceil
from time import time_ns

from faker import Faker
from locust import constant_pacing, events, task
from locust.contrib.fasthttp import FastHttpUser
from logfmter import Logfmter

# Convert terraform template variable to int. Initially placing inside quotes so linting passes.
posting_period = float("${POSTING_PERIOD}")

fake = Faker(['en_US', 'zh_CN', 'hi_IN', 'es_ES', 'fr_FR', 'ar_SA', 'uk_UA'])


def level():
    return fake.random_element(["DEBUG", "INFO", "WARNING", "ERROR"])


def totally_random():
    return Logfmter.format_params({
        "at": level(),
        **fake.pydict(),
    })


def generate(num: int = 1):
    return [[str(time_ns()), totally_random()] for _ in range(num)]


@events.init_command_line_parser.add_listener
def _(parser):
    """Add custom command line to be passed to the locustfile."""
    # num log lines is analogous to promtail's `[batchsize: <int> | default = 1048576]`
    parser.add_argument("--log-lines", type=int, help="Log lines per seconds to post to loki")
    parser.add_argument("--num-logging-sources", type=int, help="Num of (virtual) logging sources")


class LokiTest1(FastHttpUser):
    # equivalent to promtail's `[batchwait: <duration> | default = 1s]`
    # https://grafana.com/docs/loki/latest/clients/promtail/configuration/#clients
    wait_time = constant_pacing(posting_period)

    HEADERS = {
        "Content-Type": "application/json",
    }

    @task
    def logfile1(self):
        # Ideally locust would expose the worker id, but rolling my own since it doesn't
        # https://github.com/locustio/locust/issues/1601
        # num_logging_sources = self.environment.parsed_options.num_users
        num_logging_sources = self.environment.parsed_options.num_logging_sources  # a.k.a. streams

        num_logs_per_period = ceil(posting_period * self.environment.parsed_options.log_lines)
        data = {
            "streams": [
                {
                    "stream": {"filename": f"/var/log/pepetest_{filenum}"},
                    "values": generate(num_logs_per_period),
                }
                for filenum in range(num_logging_sources)
            ]
        }

        self.client.post("/loki/api/v1/push", data=json.dumps(data), headers=self.HEADERS)
