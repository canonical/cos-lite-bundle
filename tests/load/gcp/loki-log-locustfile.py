#!/usr/bin/env python3

import json

from datetime import datetime
from locust import HttpUser, TaskSet, task, between
from locust.contrib.fasthttp import FastHttpUser

from time import time_ns
import random


class LogGenerator:
    population = [
        "Query Execution Time:0.0022099018096924",
        "Configuration variable date.timezone is not set, guessed timezone America/Sao_Paulo. Please set date.timezone='America/Argentina/Buenos Aires in php.ini!",
        "Query:SELECT users.* FROM users WHERE users.id = '99bcc163-034c-ab4f-f1f3-5f7362bd45de' AND users.deleted=0 LIMIT 0,1",
        "SugarBean constructor error: Object has not fields in dictionary. Object name was: Audit",
        "Query:SELECT u1.first_name, u1.last_name from users u1, users u2 where u1.id = u2.reports_to_id AND u2.id = '99bcc163-034c-ab4f-f1f3-5f7362bd45de' and u1.deleted=0",
        "Query:SELECT gcoop_salesopportunity.* FROM gcoop_salesopportunity WHERE gcoop_salesopportunity.id = '35063c55-1c51-ff9a-473f-5f7610e7ea10' AND gcoop_salesopportunity.deleted=0 LIMIT 0,1",
        "SMTP server settings required first."
        "Query:SHOW INDEX FROM aow_workflow",
        "Query:SHOW TABLES LIKE 'aow_processed'",
        "You're using 'root' as the web-server user. This should be avoided for security reasons. Review allowed_cron_users configuration in config.php.",
    ]

    @staticmethod
    def _stamp(line: str, num:int):
        level=random.choice(["DEBUG", "INFO", "WARNING", "ERROR"])
        date_time=datetime.now().isoformat()
        return f"{date_time} - [{level}] - [{num}]: {line}"

    @staticmethod
    def _pack_log(line: str, num: int):
        return [str(time_ns()), LogGenerator._stamp(line, num)]

    @staticmethod
    def _get_sample(num: int):
        return [LogGenerator._pack_log(random.choice(LogGenerator.population), num) for _ in range(num)]

    @staticmethod
    def generate():
        num = 100  # random.randint(50, 150)
        return LogGenerator._get_sample(num)


class LokiTest1(FastHttpUser):
    wait_time = between(1, 1)

    HEADERS = {
        'Content-Type': 'application/json',
    }

    @task
    def logfile1(self):
        data = {
            "streams": [
                {
                    "stream": {"filename": "/var/log/pepetest"},
                    "values": LogGenerator.generate()
                }
            ]
        }

        self.client.post('/loki/api/v1/push',
                         data=json.dumps(data),
                         headers=self.HEADERS)
