#!/usr/bin/env python3

import json
import random
from datetime import datetime
from time import time_ns

from locust import HttpUser, TaskSet, constant_pacing, task
from locust.contrib.fasthttp import FastHttpUser


def timepad(pad: float):
    """Decorator that guarantees a function won't return before some minimum time has elapsed.
    Args:
        pad: minimum time in seconds that should elapse before the wrapped function returns.
    """
    pad = max(0, pad)
    def decorator(func):
        from functools import wraps
        import time
        @wraps(func)
        def inner(*args, **kwargs):
            tic = time.time()
            func(*args, **kwargs)
            toc = time.time()
            time.sleep(max(0, pad - (toc - tic)))
        return inner
    return decorator


def scale_probabilities(*args):
    """Scale a sequence of occurrences into probabilities that sum up to 1."""
    scale_factor = 1.0 / sum(args)
    return [scale_factor * arg for arg in args]

def probabilities_to_weights(*args):
    """Scale a sequence of probabilites into integer weights."""
    scale_factor = 10.0 / min(args)
    return [int(scale_factor * arg) for arg in args]


GRAFANA_DASHBOARD_REFRESH_PERIOD = ${REFRESH_INTERVAL}  # seconds

# simulate a "full timeseries" fetch (large query) every 10 minutes (per panel)
entire_panel_fetch_period = 10 * 60  # 10 minutes
incremental_fetch_period = GRAFANA_DASHBOARD_REFRESH_PERIOD

entire_panel_fetch_weight, incremental_fetch_weight = probabilities_to_weights(
    *scale_probabilities(1.0 / entire_panel_fetch_period, 1.0 / incremental_fetch_period)
)


# Each panel displays one metric; assumed to be less than num of metrics otherwise the response would be blank
ASSUMED_NUM_WORKERS = ${USERS}  # TODO add assertion in terraform confirming this is less than num of metrics


class PromTest1(FastHttpUser):
    wait_time = constant_pacing(GRAFANA_DASHBOARD_REFRESH_PERIOD)

    @task(weight=incremental_fetch_weight)
    def query_incremental(self):
        """Only query point recevied during the past scrape interval (that's how grafana updates panels)."""
        
        self.client.get(
            "/api/v1/query?query=avalanche_metric_mmmmm_0_{}".format(random.randint(0, ASSUMED_NUM_WORKERS - 1)) + \
            "{series_id='0'}" + "[{}s]".format(GRAFANA_DASHBOARD_REFRESH_PERIOD)
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

