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

# simulate a "full timeseries" fetch (large query) every 5 minutes (per panel)
entire_panel_fetch_period = 5 * 60  # 5 minutes
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
        metric_num = random.randint(0, ASSUMED_NUM_WORKERS - 1)
        incremental_period = 2 * GRAFANA_DASHBOARD_REFRESH_PERIOD
        self.client.get(
            "/api/v1/query?query=avalanche_metric_mmmmm_0_{}".format(metric_num) + \
            "{series_id='0'}" + "[{}s]".format(incremental_period)
        )

    @task(weight=entire_panel_fetch_weight)
    def query_panel_startup(self):
        """"Get lots of data, representing a query for a newly loaded panel."""
        # Sensible timeseries resolution is 11k points
        # "This is sufficient for 60s resolution for a week or 1h resolution for a year."
        # Ref: https://www.robustperception.io/limiting-promql-resource-usage

        # NOTE: assuming '--series-count=10', so when not specifying the series label, we're
        # actually getting 10 timeseries in one query. See variables.tf file.
        query_range = 11000. / 10 * ${REFRESH_INTERVAL}
        range_vector = f"[{query_range}s:${REFRESH_INTERVAL}s]"  #  renders as e.g. [16500s:15s]
        self.client.get(f"/api/v1/query?query=rate(avalanche_metric_mmmmm_0_0[5m]){range_vector}")
