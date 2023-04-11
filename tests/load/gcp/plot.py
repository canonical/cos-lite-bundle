#!/usr/bin/env python3

import pandas
import inspect
import os
from matplotlib import pyplot as p
import numpy as np
from typing import Literal
from scipy.optimize import curve_fit
import functools
import operator

filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))


def fit_linear(x, a, b):
    return a*x + b


def fit_bilinear(X, a1, a2, b):
    x, y = X
    return a1*x + a2*y + b


data = pandas.read_csv(f"{path}/var_ssd-4cpu-8gb.csv")


def add_subplot(ax, param: str, vmin: float = None, vmax: float = None):
    # fig, ax = p.subplots()

    xlabel = "Metrics datapoints / min"
    ylabel = "Log lines / min"

    ax.grid(linestyle='--')
    ax.set_title(param)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    def plot_data(kind: Literal["passed", "failed", "other"], data):
        x = np.array(data[xlabel])
        y = np.array(data[ylabel])
        z = np.array(data[param])

        if not all(np.isnan(z)):
            if kind == "passed":
                nonlocal vmin, vmax
                if not vmin:
                    vmin = min(z)
                if not vmax:
                    vmax = max(z)

                # Rescale to 0-1
                scaled_z = (z - vmin) / (vmax - vmin)

                ax.scatter(x, y, s=(10+(scaled_z*30))**2, c=scaled_z, alpha=0.5, marker='s')

                for i in range(len(z)):
                    if np.isnan(z[i]):
                        continue
                    # ax.annotate(z[i], (x[i], y[i]))
                    zi = int(np.ceil(z[i]))
                    ax.text(x[i], y[i], zi, horizontalalignment='center',
                            verticalalignment='center')

                # Curve-fit for VM CPU
                data_without_nans = data[[xlabel, ylabel, param]].dropna().sort_values(xlabel)
                x = np.array(data_without_nans[xlabel])
                y = np.array(data_without_nans[ylabel])
                z = np.array(data_without_nans[param])
                popt, _ = curve_fit(fit_bilinear, (x, y), z, bounds=(0, 10))
                print(param, popt)
                x_span, y_span = max(x)-min(x), max(y)-min(y)
                x_ = np.arange(min(x)-0.1*x_span, max(x)+0.1*x_span, x_span/50)
                y_ = np.arange(min(y)-0.1*y_span, max(y)+0.1*y_span, y_span/50)
                X, Y = np.meshgrid(x_, y_)
                Z = popt[0]*X + popt[1]*Y + popt[2]

                CS = ax.contour(X, Y, Z, colors='gray', linestyles="--", linewidths=1)
                ax.clabel(CS, inline=True, fontsize=9)

            elif kind == "failed":
                ax.scatter(x, y, c="red", marker='x')
            else:
                ax.scatter(x, y, c="black", marker='.')

    plot_data("passed", data[(data["Pass/Fail"] == "PASS")])
    plot_data("failed", data[(data["Pass/Fail"] == "FAIL")])
    plot_data("other", data[(data["Pass/Fail"] != "PASS") & (data["Pass/Fail"] != "FAIL")])


to_plot = [
    ("% CPU (p99)", 0, 100),
    ("% Mem (p99)", 0, 100),
    ("Storage (GiB/day)",),
    ("HTTP request times (p99) (ms)",),
]

num_subplots = len(to_plot)
rows = int(2)
cols = int(np.ceil(num_subplots / rows))
fig = p.figure()
for i in range(num_subplots):
    ax = p.subplot(rows, cols, i + 1)
    add_subplot(ax, *to_plot[i])
fig.suptitle("VM resource usage")

# Plot pod CPU, mem
to_plot = [
    ("Log lines / min", "Loki Pod CPU"),
    ("Log lines / min", "Loki Pod Mem"),
    ("Metrics datapoints / min", "Prom Pod CPU"),
    ("Metrics datapoints / min", "Prom Pod Mem"),
]
num_subplots = len(to_plot)
rows = int(2)
cols = int(np.ceil(num_subplots / rows))
fig = p.figure()
for i, (x_label, y_label) in enumerate(to_plot):
    ax = fig.add_subplot(rows, cols, i + 1)
    data.plot(x=x_label, y=y_label, kind="scatter", ax=ax)
    ax.grid(linestyle='--')

    # Curve fit
    data_without_nans = data[[x_label, y_label]].dropna().sort_values(x_label)
    x, y = np.array(data_without_nans[x_label]), np.array(data_without_nans[y_label])

    popt, _ = curve_fit(fit_linear, x, y)
    y_fit = list(map(lambda x_: fit_linear(x_, *popt), x))
    ax.plot(x, y_fit, 'k--')
    ax.text((min(x) + max(x))/2, (min(y) + max(y))/2, str(popt))
fig.suptitle("Per-pod resource usage")

p.show()

