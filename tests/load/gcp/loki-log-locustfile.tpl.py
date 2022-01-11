#!/usr/bin/env python3

# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import random
from datetime import datetime
from time import time_ns

from locust import constant_pacing, events, task
from locust.contrib.fasthttp import FastHttpUser


class LogGenerator:
    population = [
        "Query Execution Time:0.0022099018096924",
        "Configuration variable date.timezone is not set, guessed timezone America/Sao_Paulo. Please set date.timezone='America/Argentina/Buenos Aires in php.ini!",
        "Query:SELECT users.* FROM users WHERE users.id = '99bcc163-034c-ab4f-f1f3-5f7362bd45de' AND users.deleted=0 LIMIT 0,1",
        "SugarBean constructor error: Object has not fields in dictionary. Object name was: Audit",
        "Query:SELECT u1.first_name, u1.last_name from users u1, users u2 where u1.id = u2.reports_to_id AND u2.id = '99bcc163-034c-ab4f-f1f3-5f7362bd45de' and u1.deleted=0",
        "Query:SELECT gcoop_salesopportunity.* FROM gcoop_salesopportunity WHERE gcoop_salesopportunity.id = '35063c55-1c51-ff9a-473f-5f7610e7ea10' AND gcoop_salesopportunity.deleted=0 LIMIT 0,1",
        "SMTP server settings required first." "Query:SHOW INDEX FROM aow_workflow",
        "Query:SHOW TABLES LIKE 'aow_processed'",
        "You're using 'root' as the web-server user. This should be avoided for security reasons. Review allowed_cron_users configuration in config.php.",
    ]

    @staticmethod
    def _stamp(line: str, num: int):
        level = random.choice(["DEBUG", "INFO", "WARNING", "ERROR"])
        date_time = datetime.now().isoformat()
        return f"{date_time} - [{level}] - [{num}]: {line}"

    @classmethod
    def _pack_log(cls, line: str, num: int):
        return [str(time_ns()), cls._stamp(line, num)]

    @classmethod
    def _get_sample(cls, num: int):
        return [cls._pack_log(random.choice(LogGenerator.population), num) for _ in range(num)]

    @classmethod
    def generate(cls, num: int):
        return cls._get_sample(num)


@events.init_command_line_parser.add_listener
def _(parser):
    """Add custom command line to be passed to the locustfile."""
    # num log lines is analogous to promtail's `[batchsize: <int> | default = 1048576]`
    parser.add_argument("--log-lines", type=int, help="Log lines per seconds to post to loki")


# Ideally locust would expose the worker id, but rolling my own since it doesn't
# https://github.com/locustio/locust/issues/1601
NUM_WORKERS = ${USERS}


class LokiTest1(FastHttpUser):
    # equivalent to promtail's `[batchwait: <duration> | default = 1s]`
    # https://grafana.com/docs/loki/latest/clients/promtail/configuration/#clients
    wait_time = constant_pacing(1.0)

    HEADERS = {
        "Content-Type": "application/json",
    }

    @task
    def logfile1(self):
        filenum = random.randint(0, NUM_WORKERS - 1)
        data = {
            "streams": [
                {
                    "stream": {"filename": f"/var/log/pepetest_{filenum}"},
                    "values": LogGenerator.generate(self.environment.parsed_options.log_lines),
                }
            ]
        }

        self.client.post("/loki/api/v1/push", data=json.dumps(data), headers=self.HEADERS)

