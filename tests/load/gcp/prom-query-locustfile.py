#!/usr/bin/env python3

import json
import random
from datetime import datetime
from time import time_ns

from locust import HttpUser, TaskSet, constant, task
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


class PromTest1(FastHttpUser):
    # download is quite large so even with zero wait time dashboard refresh 
    # rate would be around 1 sec anyway
    wait_time = constant(0)  # use timepad instead, for more acurate rates

    @task
    @timepad(1.0)
    def query(self):
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

        # f"[60m:{random.randint(13, 130)}ms]"
