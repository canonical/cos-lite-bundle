#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import inspect
import os
from typing import Literal, Tuple

import numpy as np
import pandas
from matplotlib import pyplot as p
from scipy.optimize import curve_fit

filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))


def fit_linear(x, a, b):
    return a * x + b


def fit_bilinear(x_mat, a1, a2, b):
    x, y = x_mat
    return a1 * x + a2 * y + b


def add_subplot(ax, param: str, vmin: float = None, vmax: float = None):
    # fig, ax = p.subplots()

    xlabel = "Metrics datapoints / min"
    ylabel = "Log lines / min"

    ax.grid(linestyle="--")
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

                ax.scatter(x, y, s=(10 + (scaled_z * 30)) ** 2, c=scaled_z, alpha=0.5, marker="s")

                for i in range(len(z)):
                    if np.isnan(z[i]):
                        continue
                    # ax.annotate(z[i], (x[i], y[i]))
                    zi = int(np.ceil(z[i]))
                    ax.text(
                        x[i], y[i], zi, horizontalalignment="center", verticalalignment="center"
                    )

                # Curve-fit for VM CPU
                data_without_nans = data[[xlabel, ylabel, param]].dropna().sort_values(xlabel)
                x = np.array(data_without_nans[xlabel])
                y = np.array(data_without_nans[ylabel])
                z = np.array(data_without_nans[param])
                popt, _ = curve_fit(fit_bilinear, (x, y), z, bounds=(0, 10))
                print(param, popt)
                x_span, y_span = max(x) - min(x), max(y) - min(y)
                x_ = np.arange(min(x) - 0.1 * x_span, max(x) + 0.1 * x_span, x_span / 50)
                y_ = np.arange(min(y) - 0.1 * y_span, max(y) + 0.1 * y_span, y_span / 50)
                x_mat, y_mat = np.meshgrid(x_, y_)
                z_mat = popt[0] * x_mat + popt[1] * y_mat + popt[2]

                cs = ax.contour(x_mat, y_mat, z_mat, colors="gray", linestyles="--", linewidths=1)
                ax.clabel(cs, inline=True, fontsize=9)

            elif kind == "failed":
                ax.scatter(x, y, c="red", marker="x")
            else:
                ax.scatter(x, y, c="black", marker=".")

    plot_data("passed", data[(data["Pass/Fail"] == "PASS")])
    plot_data("failed", data[(data["Pass/Fail"] == "FAIL")])
    plot_data("other", data[(data["Pass/Fail"] != "PASS") & (data["Pass/Fail"] != "FAIL")])


def per_pod_resource_usage(data: pandas.DataFrame):
    series = {
        "ssd-4cpu-8gb": ({"marker": "s", "color": "r"}, data[(data["Pass/Fail"] == "PASS") & (data["Disk"] == "ssd") & (data["CPUs"] == 4) & (data["GBs"] == 8)]),
        "ssd-8cpu-16gb": ({"marker": "o", "color": "k"}, data[(data["Loki"] == "2.9.2") & (data["Pass/Fail"] == "PASS") & (data["Disk"] == "ssd") & (data["CPUs"] == 8) & (data["GBs"] == 16)]),
    }

    series_without_fit = {
        "ssd-4cpu-8gb (failed)": ({"marker": "x", "color": "r"}, data[(data["Pass/Fail"] != "PASS") & (data["Disk"] == "ssd") & (data["CPUs"] == 4) & (data["GBs"] == 8)]),
        "ssd-8cpu-16gb (failed)": ({"marker": "x", "color": "k"}, data[(data["Pass/Fail"] != "PASS") & (data["Disk"] == "ssd") & (data["CPUs"] == 8) & (data["GBs"] == 16)]),
    }

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

        def plot_series(series, *, fit: bool):
            for (label, (plotargs, serie)) in series.items():
                serie.plot(x=x_label, y=y_label, kind="scatter", ax=ax, label=label, **plotargs)

                if fit:
                    # Curve fit
                    data_without_nans = serie[[x_label, y_label]].dropna().sort_values(x_label)
                    x, y = np.array(data_without_nans[x_label]), np.array(data_without_nans[y_label])

                    popt, _ = curve_fit(fit_linear, x, y)
                    y_fit = [fit_linear(x_, *popt) for x_ in x]
                    ax.plot(x, y_fit, f"{plotargs['color']}--")
                    ax.text((min(x) + max(x)) / 2, (min(y) + max(y)) / 2, str(popt))

        plot_series(series, fit=True)
        plot_series(series_without_fit, fit=False)

        ax.grid(linestyle="--")

    fig.suptitle("Per-pod resource usage")


def total_estimation_from_per_pod(loglines_per_minute, datapoints_per_minute) -> Tuple[float, float, float]:
    # Return a 3-tuple: (cpu, mem_gb, storage_gb_per_day).

    # If loglines_per_minute and datapoints_per_minute were scalars, we could have used matrix multiplication:
    # (cpu, mem, disk) = A.dot(x) + idle_coeffs

    # / cpu [vCPUs]   \     /  -- cpu coeffs --  \  / loglines/min   \     /  cos idle cpu           \
    # | mem [GB]      |  =  |  -- mem coeffs --  |  | datapoints/min |  +  |  cos, microk8s idle mem |
    # \ disk [GB/day] /     \  -- disk coeffs -- /  \                /     \  host disk fill rate    /
    #
    #        y           =             A          *         x           +                b
    #      [3x1]                     [3x2]                [2x1]                        [3x1]

    # But because they are matrices (from meshgrid), we calculate manually.

    cpu_coeffs = np.array([  # in vCPUs
        # (a1, b1, c), where cpu = a1*(logline per minutes) + b1 * (datapoints/min) + c
        [6.84e-6, 0, 0.483],  # loki - contributes to cpu only via loglines
        [0, 1.08e-7, 0.173],  # prom - contributes to cpu only via metric datapoints
        [0, 0, 0.25],  # grafana
        [0, 0, 0.08],  # traefik
        [0, 0, 0.1],  # host os (microk8s, ...)
    ]).sum(axis=0)

    mem_coeffs = np.array([  # in GB
        # (a1, b1, c), where mem = a1*(logline per minutes) + b1 * (datapoints/min)
        [3.52e-6, 0, 2.07],  # loki
        [0, 1.47e-6, 0.25],  # prom
        [0, 0, 0.2],  # grafana
        [0, 0, 0.2],  # traefik
        [0, 0, 4],  # host os (microk8s, ...)
    ]).sum(axis=0)

    # (a1, b1, c), where disk = a1*(logline per minutes) + b1 * (datapoints/min)
    # From fit - c is 0 because the fit was 1e-12 which is effectively zero.
    # The initial system size - about 4gb - is eliminated by the derivative (GB/day).
    disk_coeffs = np.array([3.18e-4, 3.24e-6, 0])  # in GB/day

    return (
        cpu_coeffs[0] * loglines_per_minute + cpu_coeffs[1] * datapoints_per_minute + cpu_coeffs[2],
        mem_coeffs[0] * loglines_per_minute + mem_coeffs[1] * datapoints_per_minute + mem_coeffs[2],
        disk_coeffs[0] * loglines_per_minute + disk_coeffs[1] * datapoints_per_minute + disk_coeffs[2],
    )


def plot_total_estimation():
    xlabel = "Metrics datapoints / min"
    ylabel = "Log lines / min"

    datapoints = np.linspace(0, 6e6)  # "x, datapoints per minute
    loglines = np.linspace(0, 360e3)  # "y", loglines per minute
    datapoints_mat, loglines_mat = np.meshgrid(datapoints, loglines)

    cpu, mem, disk = total_estimation_from_per_pod(loglines_mat, datapoints_mat)

    fig = p.figure()
    ax = fig.add_subplot(1, 1, 1)

    cs1 = ax.contour(datapoints_mat, loglines_mat, cpu, colors="red", linestyles="-", linewidths=1, levels=[1,2,3,4,5,6,7,8], label="cpu")
    cs2 = ax.contour(datapoints_mat, loglines_mat, mem, colors="blue", linestyles="--", linewidths=1, levels=[2,4,6,8,10,12,14,16], label="mem")
    cs3 = ax.contour(datapoints_mat, loglines_mat, disk, colors="gray", linestyles="-.", linewidths=1, levels=[25,50,75,100,125], label="disk")
    # p.legend(labels=["cpu", "mem", "disk"])

    ax.clabel(cs1, inline=True, fontsize=9)
    ax.clabel(cs2, inline=True, fontsize=9)
    ax.clabel(cs3, inline=True, fontsize=9)

    # labels = ['cpu', 'mem', 'disk']
    # cs1.collections[0].set_label(labels[0])
    # cs2.collections[1].set_label(labels[1])
    # cs3.collections[2].set_label(labels[2])
    # # for i in range(len(labels)):
    # #     CS.collections[i].set_label(labels[i])

    # ax.legend(loc='upper left')

    ax.grid(linestyle="--")
    ax.set_title("VM size estimation from per-pod data")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # Annotated heatmap
    # https://matplotlib.org/stable/gallery/images_contours_and_fields/image_annotated_heatmap.html

    datapoints = np.linspace(0, 6e6, 5)  # "x, datapoints per minute
    loglines = np.linspace(0, 360e3, 5)  # "y", loglines per minute
    datapoints_mat, loglines_mat = np.meshgrid(datapoints, loglines)
    cpu, mem, disk = total_estimation_from_per_pod(loglines_mat, datapoints_mat)

    def mkplot(ax, title, cpu, mem, disk):
        im = ax.imshow(cpu / cpu.max() + mem / mem.max() + disk / disk.max(), origin="lower", cmap="Pastel2")

        x_labels = [f"{dp / 1e6:.0f}M" for dp in datapoints]
        y_labels = [f"{ll / 1e3:.0f}k" for ll in loglines]
        ax.set_xticks(np.arange(len(x_labels)), labels=x_labels)
        ax.set_yticks(np.arange(len(y_labels)), labels=y_labels)
        ax.set_xlabel("Datapoints/min")
        ax.set_ylabel("Log lines/min")

        # Loop over data dimensions and create text annotations.
        for i in range(len(loglines)):
            for j in range(len(datapoints)):
                cpu_ann = f"{cpu[i, j]:.1f} cpu"
                mem_ann = f"{mem[i, j]:.1f} gb"
                disk_ann = f"{disk[i, j]:.0f} gb/day"
                cell_ann = f"{cpu_ann}\n{mem_ann}\n{disk_ann}"
                text = ax.text(j, i, cell_ann, ha="center", va="center", color="k")

        ax.set_title(title)

    fig = p.figure()
    mkplot(fig.add_subplot(1, 2, 1), "VM sizing from per-pod data", cpu, mem, disk)
    mkplot(fig.add_subplot(1, 2, 2), "VM sizing (with margin)", np.ceil(1.1*cpu), np.ceil(1.1*mem), np.ceil(1.1*disk))
    fig.tight_layout()


if __name__ == "__main__":
    data = pandas.read_csv(f"{path}/results.csv")

    per_pod_resource_usage(data)
    plot_total_estimation()

    # Filter out. TODO: make this a cli arg
    data = data[(data["Disk"] == "ssd") & (data["CPUs"] == 8) & (data["GBs"] == 16)]
    print(data)

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

    p.show()
