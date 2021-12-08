#!/usr/bin/env python3

# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import random
from datetime import datetime
from time import time_ns

from locust import HttpUser, TaskSet, constant_pacing, task
from locust.contrib.fasthttp import FastHttpUser


def normalize(*args):
    """Scale a sequence of occurrences into probabilities that sum up to 1."""
    total = sum(args)
    return [arg / total for arg in args]

def probabilities_to_weights(*args):
    """Scale a sequence of probabilities into integer weights.
    
    Locust's `@task` decorator takes integer weight rather than probability.
    """
    # Rescale args such that the lowest arg becomes 1, then multiply by
    # 10 before casting to int, such that the first decimal would be accounted
    # for rather than truncated.
    # This was the lowest arg is scaled to 10, and the rest - proportionally.
    scale_factor = 10.0 / min(args)
    return [int(scale_factor * arg) for arg in args]


GRAFANA_DASHBOARD_REFRESH_PERIOD = ${REFRESH_INTERVAL}  # seconds

# simulate a "full timeseries" fetch (large query) every 10 minutes (per panel)
entire_panel_fetch_period = 10 * 60  # 10 minutes
incremental_fetch_period = GRAFANA_DASHBOARD_REFRESH_PERIOD

entire_panel_fetch_weight, incremental_fetch_weight = probabilities_to_weights(
    *normalize(1.0 / entire_panel_fetch_period, 1.0 / incremental_fetch_period)
)


# Each panel displays one metric; assumed to be less than num of metrics otherwise the response would be blank
ASSUMED_NUM_WORKERS = ${USERS}


class PromTest1(FastHttpUser):
    wait_time = constant_pacing(GRAFANA_DASHBOARD_REFRESH_PERIOD)

    @task(weight=incremental_fetch_weight)
    def query_incremental(self):
        """Only query point received during the past scrape interval (that's how grafana updates panels)."""
        
        # Fetching the double of GRAFANA_DASHBOARD_REFRESH_PERIOD to account for potentially missed 
        # data points missed around interval boundaries or lost packets
        # A factor of 2 might be an overkill but is still small enough to not care much about it.
        self.client.get(
            "/api/v1/query?query=avalanche_metric_mmmmm_0_{}".format(random.randint(0, ASSUMED_NUM_WORKERS - 1)) + \
            "{series_id='0'}" + "[{}s]".format(2 * GRAFANA_DASHBOARD_REFRESH_PERIOD)
        )

    @task(weight=entire_panel_fetch_weight)
    def query_panel_starup(self):
        """"Get lots of data, representing a query for a newly loaded panel."""
        # ~10MB
        # /api/v1/query?query=rate(avalanche_metric_mmmmm_0_0[5m])[60m:130ms]
        #
        # ~100MB
        # /api/v1/query?query=rate(avalanche_metric_mmmmm_0_0[5m])[60m:13ms]
        upper = 130
        lower = 13
        mid = int(lower + (upper - lower) / 2)
        seq = [lower, mid, upper]

        self.client.get(
            "/api/v1/query?query=rate(avalanche_metric_mmmmm_0_0[5m])"
            f"[60m:{random.choice(seq)}ms]"
        )

