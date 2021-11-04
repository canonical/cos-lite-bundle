#!/usr/bin/env python3

import json

from datetime import datetime
from locust import HttpUser, TaskSet, task, constant
from locust.contrib.fasthttp import FastHttpUser

from time import time_ns
import random


class PromTest1(FastHttpUser):
    wait_time = constant(0)

    @task
    def query(self):
        # ~10MB
        # /api/v1/query?query=rate(avalanche_metric_mmmmm_0_0[5m])[60m:130ms]
        #
        # ~100MB
        # /api/v1/query?query=rate(avalanche_metric_mmmmm_0_0[5m])[60m:13ms]
        upper = 130
        lower = 13
        mid = int(lower + (upper - lower)/2)
        seq = [lower, mid, upper]

        self.client.get(
            "/api/v1/query?query=rate(avalanche_metric_mmmmm_0_0[5m])"
            f"[60m:{random.choice(seq)}ms]"
        )

        # f"[60m:{random.randint(13, 130)}ms]"
