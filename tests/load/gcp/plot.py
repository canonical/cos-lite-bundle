#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import inspect
import os
from types import SimpleNamespace
from typing import Callable, Literal, Optional, Tuple

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


def fit_exp(x, a, b, c):
    # return a + b * np.exp(-x)
    # return a + b * np.log(c*x)
    return a + b * np.arctan(c * x)


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


def plot_series(
    ax,
    xlabel,
    ylabel,
    series_label: str,
    series: pandas.DataFrame,
    fit: Optional[Callable],
    **plotargs,
):
    series.plot(x=xlabel, y=ylabel, kind="scatter", ax=ax, label=series_label, **plotargs)

    if fit and len(series):
        without_nans = series[[xlabel, ylabel]].dropna().sort_values(xlabel)
        x, y = np.array(without_nans[xlabel]), np.array(without_nans[ylabel])

        popt, _ = curve_fit(fit, x, y)
        x_fit = np.linspace(min(x), max(x))
        y_fit = [fit(x_, *popt) for x_ in x_fit]
        ax.plot(x_fit, y_fit, f"{plotargs['color']}--")
        ax.text((min(x) + max(x)) / 2, (min(y) + max(y)) / 2, str(popt))
        return popt
    return None


def plot_passed_failed(
    ax,
    xlabel,
    ylabel,
    series_label,
    passed: pandas.DataFrame,
    failed: pandas.DataFrame,
    fit: Optional[Callable],
    plotargs: dict,
):
    # Passed, with fit
    plot_series(
        ax,
        xlabel,
        ylabel,
        series_label + f" ({len(passed)} passed)",
        passed,
        fit,
        **plotargs,
    )

    # Failed, without fit
    plot_series(
        ax,
        xlabel,
        ylabel,
        series_label + f" ({len(failed)} failed)",
        failed,
        None,
        **{**plotargs, **{"marker": "x"}},
    )


def vm_usage(data: pandas.DataFrame):
    data = data[(data["Disk"] == "ssd") & (data["Pass/Fail"] == "PASS")]

    ssd4cpu8gb = data[(data["CPUs"] == 4) & (data["GBs"] == 8)]
    vm4cpu8gb = SimpleNamespace(
        label="ssd-4cpu-8gb",
        loki=ssd4cpu8gb[
            (ssd4cpu8gb["Metrics datapoints / min"] < 1000) & (ssd4cpu8gb["Loki"] == "2.9.2")
        ],
        prom=ssd4cpu8gb[(ssd4cpu8gb["Log lines / min"] == 0)],
        plotopts={"marker": "s", "color": "r"},
    )

    ssd8cpu16gb = data[(data["CPUs"] == 8) & (data["GBs"] == 16)]
    vm8cpu16gb = SimpleNamespace(
        label="ssd-8cpu-16gb",
        loki=ssd8cpu16gb[
            (ssd8cpu16gb["Metrics datapoints / min"] < 1000) & (ssd8cpu16gb["Loki"] == "2.9.2")
        ],
        prom=ssd8cpu16gb[(ssd8cpu16gb["Log lines / min"] == 0)],
        plotopts={"marker": "o", "color": "k"},
    )

    fig = p.figure()

    # Loki CPU
    ax = fig.add_subplot(2, 3, 1)
    xlabel = "Log lines / min"
    ylabel = "% CPU (p99)"
    plot_series(ax, xlabel, ylabel, vm4cpu8gb.label, vm4cpu8gb.loki, None, **vm4cpu8gb.plotopts)
    plot_series(ax, xlabel, ylabel, vm8cpu16gb.label, vm8cpu16gb.loki, None, **vm8cpu16gb.plotopts)
    ax.set_ylim([0, 100])
    ax.set_xlim([0, None])
    ax.grid(linestyle="--")

    # Loki Mem
    ax = fig.add_subplot(2, 3, 2)
    xlabel = "Log lines / min"
    ylabel = "% Mem (p99)"
    plot_series(ax, xlabel, ylabel, vm4cpu8gb.label, vm4cpu8gb.loki, None, **vm4cpu8gb.plotopts)
    plot_series(ax, xlabel, ylabel, vm8cpu16gb.label, vm8cpu16gb.loki, None, **vm8cpu16gb.plotopts)
    ax.set_ylim([0, 100])
    ax.set_xlim([0, None])
    ax.grid(linestyle="--")

    # Loki storage
    ax = fig.add_subplot(2, 3, 3)
    xlabel = "Log lines / min"
    ylabel = "Storage (GiB/day)"
    plot_series(
        ax, xlabel, ylabel, vm4cpu8gb.label, vm4cpu8gb.loki, fit_linear, **vm4cpu8gb.plotopts
    )
    plot_series(
        ax, xlabel, ylabel, vm8cpu16gb.label, vm8cpu16gb.loki, fit_linear, **vm8cpu16gb.plotopts
    )
    ax.set_ylim([0, None])
    ax.set_xlim([0, None])
    ax.grid(linestyle="--")

    # Prom CPU
    ax = fig.add_subplot(2, 3, 4)
    xlabel = "Metrics datapoints / min"
    ylabel = "% CPU (p99)"
    plot_series(ax, xlabel, ylabel, vm4cpu8gb.label, vm4cpu8gb.prom, None, **vm4cpu8gb.plotopts)
    plot_series(ax, xlabel, ylabel, vm8cpu16gb.label, vm8cpu16gb.prom, None, **vm8cpu16gb.plotopts)
    ax.set_ylim([0, 100])
    ax.set_xlim([0, None])
    ax.grid(linestyle="--")

    # Prom Mem
    ax = fig.add_subplot(2, 3, 5)
    xlabel = "Metrics datapoints / min"
    ylabel = "% Mem (p99)"
    plot_series(ax, xlabel, ylabel, vm4cpu8gb.label, vm4cpu8gb.prom, None, **vm4cpu8gb.plotopts)
    plot_series(ax, xlabel, ylabel, vm8cpu16gb.label, vm8cpu16gb.prom, None, **vm8cpu16gb.plotopts)
    ax.set_ylim([0, 100])
    ax.set_xlim([0, None])
    ax.grid(linestyle="--")

    # Prom storage
    ax = fig.add_subplot(2, 3, 6)
    xlabel = "Metrics datapoints / min"
    ylabel = "Storage (GiB/day)"
    plot_series(
        ax, xlabel, ylabel, vm4cpu8gb.label, vm4cpu8gb.prom, fit_linear, **vm4cpu8gb.plotopts
    )
    plot_series(
        ax, xlabel, ylabel, vm8cpu16gb.label, vm8cpu16gb.prom, fit_linear, **vm8cpu16gb.plotopts
    )
    ax.set_ylim([0, 100])
    ax.set_xlim([0, None])
    ax.grid(linestyle="--")


def per_pod_resource_usage(data: pandas.DataFrame):
    data["Log lines / min"] = data["Log lines / min"]

    vm4cpu8gb = SimpleNamespace(
        label="ssd-4cpu-8gb",
        passed=data[
            (data["Disk"] == "ssd")
            & (data["CPUs"] == 4)
            & (data["GBs"] == 8)
            & (data["Pass/Fail"] == "PASS")
        ],
        failed=data[
            (data["Disk"] == "ssd")
            & (data["CPUs"] == 4)
            & (data["GBs"] == 8)
            & (data["Pass/Fail"] != "PASS")
        ],
        plotopts={"marker": "s", "color": "r"},
    )
    vm8cpu16gb = SimpleNamespace(
        label="ssd-8cpu-16gb",
        passed=data[
            (data["Disk"] == "ssd")
            & (data["CPUs"] == 8)
            & (data["GBs"] == 16)
            & (data["Pass/Fail"] == "PASS")
        ],
        failed=data[
            (data["Disk"] == "ssd")
            & (data["CPUs"] == 8)
            & (data["GBs"] == 16)
            & (data["Pass/Fail"] != "PASS")
        ],
        plotopts={"marker": "o", "color": "k"},
    )

    fig = p.figure()

    # Loki CPU
    ax = fig.add_subplot(2, 2, 1)
    xlabel = "Log lines / min"
    ylabel = "Loki Pod CPU"
    plot_passed_failed(
        ax,
        xlabel,
        ylabel,
        vm4cpu8gb.label,
        vm4cpu8gb.passed,
        vm4cpu8gb.failed,
        fit_linear,
        vm4cpu8gb.plotopts,
    )
    plot_passed_failed(
        ax,
        xlabel,
        ylabel,
        vm8cpu16gb.label,
        vm8cpu16gb.passed[
            (vm8cpu16gb.passed["Loki"] == "2.9.2") & (vm8cpu16gb.passed["Duration (hr)"] >= 12)
        ],
        vm8cpu16gb.failed[(vm8cpu16gb.failed["Loki"] == "2.9.2")],
        fit_exp,
        vm8cpu16gb.plotopts,
    )
    ax.grid(linestyle="--")

    # Loki Mem
    ax = fig.add_subplot(2, 2, 2)
    xlabel = "Log lines / min"
    ylabel = "Loki Pod Mem"
    plot_passed_failed(
        ax,
        xlabel,
        ylabel,
        vm4cpu8gb.label,
        vm4cpu8gb.passed,
        vm4cpu8gb.failed,
        fit_linear,
        vm4cpu8gb.plotopts,
    )
    plot_passed_failed(
        ax,
        xlabel,
        ylabel,
        vm8cpu16gb.label,
        vm8cpu16gb.passed[
            (vm8cpu16gb.passed["Loki"] == "2.9.2") & (vm8cpu16gb.passed["Duration (hr)"] >= 12)
        ],
        vm8cpu16gb.failed[(vm8cpu16gb.failed["Loki"] == "2.9.2")],
        fit_exp,
        vm8cpu16gb.plotopts,
    )
    ax.grid(linestyle="--")

    # Prom CPU
    ax = fig.add_subplot(2, 2, 3)
    xlabel = "Metrics datapoints / min"
    ylabel = "Prom Pod CPU"
    plot_passed_failed(
        ax,
        xlabel,
        ylabel,
        vm4cpu8gb.label,
        vm4cpu8gb.passed,
        vm4cpu8gb.failed,
        fit_linear,
        vm4cpu8gb.plotopts,
    )
    plot_passed_failed(
        ax,
        xlabel,
        ylabel,
        vm8cpu16gb.label,
        vm8cpu16gb.passed,
        vm8cpu16gb.failed,
        fit_linear,
        vm8cpu16gb.plotopts,
    )
    ax.grid(linestyle="--")

    # Prom Mem
    ax = fig.add_subplot(2, 2, 4)
    xlabel = "Metrics datapoints / min"
    ylabel = "Prom Pod Mem"
    plot_passed_failed(
        ax,
        xlabel,
        ylabel,
        vm4cpu8gb.label,
        vm4cpu8gb.passed,
        vm4cpu8gb.failed,
        fit_linear,
        vm4cpu8gb.plotopts,
    )
    plot_passed_failed(
        ax,
        xlabel,
        ylabel,
        vm8cpu16gb.label,
        vm8cpu16gb.passed,
        vm8cpu16gb.failed,
        fit_linear,
        vm8cpu16gb.plotopts,
    )
    ax.grid(linestyle="--")

    # series = {
    #    "ssd-4cpu-8gb": ({"marker": "s", "color": "r"}, data[(data["Pass/Fail"] == "PASS") & (data["Disk"] == "ssd") & (data["CPUs"] == 4) & (data["GBs"] == 8)]),
    #    "ssd-8cpu-16gb": ({"marker": "o", "color": "k"}, data[(data["Loki"] == "2.9.2") & (data["Pass/Fail"] == "PASS") & (data["Disk"] == "ssd") & (data["CPUs"] == 8) & (data["GBs"] == 16)]),
    # }

    # series_without_fit = {
    #    "ssd-4cpu-8gb (failed)": ({"marker": "x", "color": "r"}, data[(data["Pass/Fail"] != "PASS") & (data["Disk"] == "ssd") & (data["CPUs"] == 4) & (data["GBs"] == 8)]),
    #    "ssd-8cpu-16gb (failed)": ({"marker": "x", "color": "k"}, data[(data["Pass/Fail"] != "PASS") & (data["Disk"] == "ssd") & (data["CPUs"] == 8) & (data["GBs"] == 16)]),
    # }

    ## Plot pod CPU, mem
    # to_plot = [
    #    ("Log lines / min", "Loki Pod CPU"),
    #    ("Log lines / min", "Loki Pod Mem"),
    #    ("Metrics datapoints / min", "Prom Pod CPU"),
    #    ("Metrics datapoints / min", "Prom Pod Mem"),
    # ]
    # num_subplots = len(to_plot)
    # rows = int(2)
    # cols = int(np.ceil(num_subplots / rows))
    # fig = p.figure()
    # for i, (x_label, y_label) in enumerate(to_plot):
    #    ax = fig.add_subplot(rows, cols, i + 1)

    #    def plot_series(series, *, fit: bool):
    #        for (label, (plotargs, series_)) in series.items():
    #            series_.plot(x=x_label, y=y_label, kind="scatter", ax=ax, label=label, **plotargs)

    #            if fit:
    #                # Curve fit
    #                data_without_nans = series_[[x_label, y_label]].dropna().sort_values(x_label)
    #                x, y = np.array(data_without_nans[x_label]), np.array(data_without_nans[y_label])

    #                if "Loki" in y_label:
    #                    fit_func = fit_exp
    #                else:
    #                    fit_func = fit_linear
    #
    #                popt, _ = curve_fit(fit_func, x, y)
    #                y_fit = [fit_func(x_, *popt) for x_ in x]
    #                ax.plot(x, y_fit, f"{plotargs['color']}--")
    #                ax.text((min(x) + max(x)) / 2, (min(y) + max(y)) / 2, str(popt))

    #    plot_series(series, fit=True)
    #    plot_series(series_without_fit, fit=False)

    #    ax.grid(linestyle="--")

    fig.suptitle("Per-pod resource usage")


def total_estimation_from_per_pod(
    loglines_per_minute, datapoints_per_minute
) -> Tuple[float, float, float]:
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

    cpu_coeffs = np.array(
        [  # in vCPUs
            # (a1, b1, c), where cpu = a1*(logline per minutes) + b1 * (datapoints/min) + c
            [6.84e-6, 0, 0.483],  # loki - contributes to cpu only via loglines
            [0, 1.08e-7, 0.173],  # prom - contributes to cpu only via metric datapoints
            [0, 0, 0.25],  # grafana
            [0, 0, 0.08],  # traefik
            [0, 0, 0.1],  # host os (microk8s, ...)
        ]
    ).sum(axis=0)

    mem_coeffs = np.array(
        [  # in GB
            # (a1, b1, c), where mem = a1*(logline per minutes) + b1 * (datapoints/min)
            [3.52e-6, 0, 2.07],  # loki
            [0, 1.47e-6, 0.25],  # prom
            [0, 0, 0.2],  # grafana
            [0, 0, 0.2],  # traefik
            [0, 0, 4],  # host os (microk8s, ...)
        ]
    ).sum(axis=0)

    # (a1, b1, c), where disk = a1*(logline per minutes) + b1 * (datapoints/min)
    # From fit - c is 0 because the fit was 1e-12 which is effectively zero.
    # The initial system size - about 4gb - is eliminated by the derivative (GB/day).
    disk_coeffs = np.array([3.18e-4, 3.24e-6, 0])  # in GB/day

    return (
        cpu_coeffs[0] * loglines_per_minute
        + cpu_coeffs[1] * datapoints_per_minute
        + cpu_coeffs[2],
        mem_coeffs[0] * loglines_per_minute
        + mem_coeffs[1] * datapoints_per_minute
        + mem_coeffs[2],
        disk_coeffs[0] * loglines_per_minute
        + disk_coeffs[1] * datapoints_per_minute
        + disk_coeffs[2],
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

    cs1 = ax.contour(
        datapoints_mat,
        loglines_mat,
        cpu,
        colors="red",
        linestyles="-",
        linewidths=1,
        levels=[1, 2, 3, 4, 5, 6, 7, 8],
        label="cpu",
    )
    cs2 = ax.contour(
        datapoints_mat,
        loglines_mat,
        mem,
        colors="blue",
        linestyles="--",
        linewidths=1,
        levels=[2, 4, 6, 8, 10, 12, 14, 16],
        label="mem",
    )
    cs3 = ax.contour(
        datapoints_mat,
        loglines_mat,
        disk,
        colors="gray",
        linestyles="-.",
        linewidths=1,
        levels=[25, 50, 75, 100, 125],
        label="disk",
    )
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
        ax.imshow(
            cpu / cpu.max() + mem / mem.max() + disk / disk.max(), origin="lower", cmap="Pastel2"
        )

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
                ax.text(j, i, cell_ann, ha="center", va="center", color="k")

        ax.set_title(title)

    fig = p.figure()
    mkplot(fig.add_subplot(1, 2, 1), "VM sizing from per-pod data", cpu, mem, disk)
    mkplot(
        fig.add_subplot(1, 2, 2),
        "VM sizing (with margin)",
        np.ceil(1.1 * cpu),
        np.ceil(1.1 * mem),
        np.ceil(1.1 * disk),
    )
    fig.tight_layout()


def plot_storage(data: pandas.DataFrame):
    data = data[(data["Disk"] == "ssd") & (data["Pass/Fail"] == "PASS")]
    ssd8cpu16gb = data[(data["CPUs"] == 8) & (data["GBs"] == 16)]
    logs_only = SimpleNamespace(
        label="Logs only",
        # Taking "metrics < 1000" instead of zero due to limitation in load test provisioning logic.
        # This means that the estimated disk usage for logs is slightly higher, due to the small contribution of
        # some "stray" metrics.
        data=ssd8cpu16gb[
            (ssd8cpu16gb["Metrics datapoints / min"] < 1000) & (ssd8cpu16gb["Loki"] == "2.9.2")
        ],
        plotopts={"marker": "o", "color": "k"},
    )

    fig = p.figure()
    ax = fig.add_subplot(2, 2, 1)

    xlabel = "Log lines / min"
    ylabel = "Storage (GiB/day)"
    logs_fit = plot_series(
        ax, xlabel, ylabel, logs_only.label, logs_only.data, fit_linear, **logs_only.plotopts
    )
    ax.set_ylim([0, None])
    ax.set_xlim([0, None])
    ax.grid(linestyle="--")

    # The fit for logs-only is: [3.01e-4, 2.447e-3].
    # That was a very good fit, so use it to isolate the contribution of metrics to storage.
    data = data[(data["Disk"] == "ssd") & (data["Pass/Fail"] == "PASS")]
    ssd8cpu16gb = data[(data["CPUs"] == 8) & (data["GBs"] == 16)]
    combined_data = ssd8cpu16gb  # [(ssd8cpu16gb["Loki"] == "2.9.2")]
    m_label = "Metrics datapoints / min"
    l_label = "Log lines / min"
    s_label = "Storage (GiB/day)"
    combined_data = pandas.DataFrame(
        np.array(combined_data[[m_label, l_label, s_label]].dropna().sort_values(m_label)),
        columns=[m_label, l_label, s_label],
    )
    corrected_prom_storage = combined_data[s_label] - (
        logs_fit[0] * combined_data[l_label] + logs_fit[1]
    )
    combined_data[s_label] = corrected_prom_storage
    combined_data.pop(l_label)

    corrected_metrics = SimpleNamespace(
        label="(Corrected) metrics only",
        data=combined_data,
        plotopts={"marker": "o", "color": "k"},
    )

    ax = fig.add_subplot(2, 2, 3)

    xlabel = m_label
    ylabel = s_label
    metrics_fit = plot_series(
        ax,
        xlabel,
        ylabel,
        corrected_metrics.label,
        corrected_metrics.data,
        fit_linear,
        **corrected_metrics.plotopts,
    )
    ax.set_ylim([0, None])
    ax.set_xlim([0, None])
    ax.grid(linestyle="--")

    # Contour plot
    ax = fig.add_subplot(2, 2, (2, 4))
    xlabel = "Metrics datapoints / min"
    ylabel = "Log lines / min"

    datapoints = np.linspace(0, 6.6e6)  # "x, datapoints per minute
    loglines = np.linspace(0, 360e3)  # "y", loglines per minute
    datapoints_mat, loglines_mat = np.meshgrid(datapoints, loglines)

    disk = (
        logs_fit[0] * loglines_mat + logs_fit[1] + metrics_fit[0] * datapoints_mat + metrics_fit[1]
    )
    cs3 = ax.contour(
        datapoints_mat,
        loglines_mat,
        disk,
        colors="black",
        linestyles="-",
        linewidths=1,
        levels=np.arange(10, 151, 10),
    )

    ax.clabel(cs3, inline=True, fontsize=9)

    ax.grid(linestyle="--")
    ax.set_title("Disk size estimation (GiB/day)")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


def plot_vm_from_per_pod():
    def calc(metrics: float, logs: float) -> (float, float, float):
        """Returns (cpu, gb-mem, gb/day-disk)."""
        disk = (3.011e-4 * logs + 2.447e-3) + (3.823e-6 * metrics + 1.021)
        cpu = (
            1.442e-1
            + 1.89 * np.arctan(1.365e-4 * logs)
            + 1.059e-7 * metrics
            + 1.696e-1
            + (0.25 + 0.08 + 1.0)
        )
        mem = (
            4.851e-2
            + 2.063 * np.arctan(2.539e-3 * logs)
            + 1.464e-6 * metrics
            + 2.51e-1
            + (0.2 + 0.2 + 2.6)
        )
        return cpu, mem, disk

        # Annotated heatmap
        # https://matplotlib.org/stable/gallery/images_contours_and_fields/image_annotated_heatmap.html

    datapoints = np.linspace(0, 6e6, 7)  # "x, datapoints per minute
    loglines = np.linspace(0, 360e3, 7)  # "y", loglines per minute
    datapoints_mat, loglines_mat = np.meshgrid(datapoints, loglines)
    cpu, mem, disk = calc(datapoints_mat, loglines_mat)

    def mkplot(ax, title, cpu, mem, disk):
        ax.imshow(
            cpu / cpu.max() + mem / mem.max() + disk / disk.max(), origin="lower", cmap="Pastel2"
        )

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
                ax.text(j, i, cell_ann, ha="center", va="center", color="k")

        ax.set_title(title)

    fig = p.figure()
    # mkplot(fig.add_subplot(1, 2, 1), "VM sizing from per-pod data", cpu, mem, disk)
    mkplot(
        fig.add_subplot(1, 1, 1),
        "VM sizing from per-pod data (with 10% margin)",
        np.ceil(1.1 * cpu),
        np.ceil(1.1 * mem),
        np.ceil(1.1 * disk),
    )


if __name__ == "__main__":
    data = pandas.read_csv(f"{path}/results.csv")

    plot_storage(data)
    vm_usage(data)
    per_pod_resource_usage(data)
    plot_total_estimation()
    plot_vm_from_per_pod()

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
