"""Figures: estimated vs reference k, the metrics, run time / memory, and spatial domain maps."""
import re

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.ticker import LogLocator, MaxNLocator, ScalarFormatter

from .results import _check_table, _labels, _read

__all__ = ["plot_k_estimates", "plot_metrics", "plot_runtime", "plot_spatial", "plot_spatial_grid"]


def __dir__():          # tab completion of kdb.pl shows the plots, not the imports
    return __all__


def _successful(summary):
    _check_table(summary)
    if summary.empty or not summary["success"].astype(bool).any():
        raise ValueError("no successful runs in the summary table. Check the folder given to load_results")
    return summary[summary["success"].astype(bool)]


def plot_k_estimates(summary, ax=None, k_reference=None):
    """Plot the estimated k of each method against the reference domain number.

    One row per method and one dot per estimate, laid out as Fig. 2b and 2c of the paper. A
    dashed line marks the reference domain number. A dot is blue when the method returned
    fewer domains than the reference, green when it returned as many, and red when it
    returned more. Methods are sorted by the median of their dots.

    Parameters
    ----------
    summary : pandas.DataFrame
        The table from [load_results][kdomainbench.load_results].
    ax : matplotlib.axes.Axes, optional
        Axes to draw on. Default: a new figure.
    k_reference : int, optional
        Reference domain number of every run, for a file without an annotation. Default: the
        ``k_reference`` column of ``summary``.

    Returns
    -------
    matplotlib.axes.Axes
        The plot. ``ax.figure.savefig(..., bbox_inches="tight")`` saves it with its legend.

    Raises
    ------
    TypeError
        ``summary`` is not a table.
    ValueError
        ``summary`` has no successful run.

    Notes
    -----
    * Runs of a method at the same place on the x axis share one dot, and its area gives
      their number.
    * When the runs have different reference domain numbers (several datasets), the x axis
      is the k error, estimated k − reference k.
    * Runs without a reference annotation are left out when other runs have one. When no
      run has one, the dots are gray and there is no line.
    * The paper's panels also shade a dot by the size of its error. Here the position on the
      x axis gives the size, and the color only the direction.

    Examples
    --------
    >>> ax = kdb.pl.plot_k_estimates(summary)
    >>> ax.figure.savefig("k_estimates.png", dpi=150, bbox_inches="tight")
    """
    ok = _successful(summary)
    k = ok["k_estimated"].astype(float)
    dev = (k - (ok.get("k_reference", np.nan) if k_reference is None else k_reference)).astype(float)
    scored = dev.notna()
    if scored.any():                                    # then the figure is about the runs with a reference
        ok, k, dev = ok[scored], k[scored], dev[scored]
    references = (k - dev).dropna().unique()
    several = len(references) > 1                       # then only the k error is comparable
    runs = ok.assign(x=dev if several else k, side=np.sign(dev))
    order = list(runs.groupby("method")["x"].median().sort_values(kind="stable").index)
    dots = runs.groupby(["method", "x"], as_index=False).agg(side=("side", "first"), runs=("x", "size"))
    most = dots["runs"].max()
    area = (60 if most == 1 else 170) / most            # of one run: the largest dot fits its row
    sides = {-1: ("#3A6BA5", "fewer domains"), 0: ("#659B72", "as many domains"), 1: ("#C65A36", "more domains")}  # Fig. 2b
    ax = ax or plt.subplots(figsize=(5.2, 0.3 * len(order) + 1.2))[1]
    ax.scatter(dots["x"], dots["method"].map(order.index), s=area * dots["runs"], zorder=3, edgecolors="black",
               linewidths=0.6, c=[sides[s][0] if s in sides else "0.55" for s in dots["side"]])
    marks, handles, names = list(dots["x"]), [], []
    if len(references):
        marks.append(0 if several else references[0])
        handles.append(ax.axvline(marks[-1], ls="--", lw=1, color="0.45", zorder=1))
        names.append("estimated k = reference k" if several else f"reference domain number ({references[0]:g})")
        for side in sorted(set(dots["side"])):          # what the colors mean
            handles.append(Line2D([], [], ls="", marker="o", ms=7, mfc=sides[side][0], mec="black", mew=0.6))
            names.append(sides[side][1])
    if most > 1:                                        # what the dot areas mean
        for n in sorted({1, int(most)}):
            handles.append(ax.scatter([], [], s=area * n, color="0.8", edgecolors="black", linewidths=0.6))
            names.append("1 run" if n == 1 else f"{n} runs")
    if handles:
        ax.legend(handles, names, frameon=False, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
    ax.set_yticks(range(len(order)), order)
    ax.set_ylim(len(order) - 0.4, -0.6)                 # the smallest estimate on top
    span = max(marks) - min(marks)
    pad = max(0.6, 0.06 * span, 1 - span / 2)           # room for the dots, and at least two whole numbers of k
    ax.set_xlim(min(marks) - pad, max(marks) + pad)
    ax.set_xlabel("k error (estimated k − reference k)" if several else "estimated number of domains (k)")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="y", color="0.92", lw=0.8)
    ax.set_axisbelow(True)
    return ax


# Fig. 2f of the paper: the four groups of metrics with their colors, in the figure's column order.
_METRIC_GROUPS = {"Concordance": ("#D66713", ["spARI", "ARI", "NMI", "FM", "AMI", "Purity"]),
                  "Completeness": ("#4E88C7", ["HOM", "COM"]),
                  "Spatial coherence": ("#7651A8", ["LISI", "SCS"]),
                  "Stability": ("#4A4A4A", ["PAS", "CHAOS"])}
_LOWER_IS_BETTER = {"LISI", "PAS", "CHAOS"}


def _axis_top(high):
    """A round number at or above ``high``: the right end of a metric's axis."""
    if high <= 0:
        return 1
    step = 10 ** np.floor(np.log10(high)) / 2
    return np.ceil(high / step - 1e-9) * step


def plot_metrics(summary, ax=None):
    """Plot the metrics of each method as a matrix of bars.

    One row per method and one column per metric, laid out as Fig. 2f of the paper. The length
    of a bar is the value of the metric, on the metric's own axis below the column. The fill is
    the rank of the method among the methods for that metric: the darker, the better. The
    arrow above a column says whether higher or lower is better.

    Parameters
    ----------
    summary : pandas.DataFrame
        The table from [load_results][kdomainbench.load_results]. The columns of the twelve
        metrics are there for the runs scored with [metrics][kdomainbench.metrics]. A method
        whose runs were not scored has ``n/a`` in the other columns, and a table without any
        scored run shows ``ARI`` and ``NMI`` only.
    ax : matplotlib.axes.Axes, optional
        Axes to draw on. Default: a new figure.

    Returns
    -------
    matplotlib.axes.Axes
        The plot. ``ax.figure.savefig(..., bbox_inches="tight")`` saves it.

    Raises
    ------
    TypeError
        ``summary`` is not a table.
    ValueError
        ``summary`` has no successful run, or none of its runs has a metric value.

    Notes
    -----
    * With several runs per method, a bar is the mean over the runs that have a value, and
      the whisker is their standard deviation. Filter ``summary`` first to compare within one
      dataset or device. In the paper the datasets of each data source are averaged first, and
      a bar is the mean over the five sources.
    * An axis runs from 0 to a round number above the highest value, and from below 0 when a
      value is negative. The axes of the paper's panel are set by hand and do not all start
      at 0.
    * Methods are listed in the order of their first successful run in ``summary``.
    * Methods with the same value share the better rank. ``n/a`` marks a metric without a
      value, such as SCS of a run with one domain.

    Examples
    --------
    >>> summary = kdb.load_results("kdb_results")
    >>> ax = kdb.pl.plot_metrics(summary)
    >>> ax.figure.savefig("metrics.png", dpi=150, bbox_inches="tight")
    """
    ok = _successful(summary)
    groups = {g: (color, [m for m in ms if m in ok and ok[m].notna().any()]) for g, (color, ms) in _METRIC_GROUPS.items()}
    groups = {g: v for g, v in groups.items() if v[1]}
    if not groups:
        raise ValueError("no run in the summary has a metric value. kdb.metrics(run) computes them, "
                         "or from the shell: kdomainbench metrics <folder>")
    methods = list(dict.fromkeys(ok["method"]))
    y = np.arange(len(methods))[::-1]                           # the first method on top
    width, x = 0.84, 0                                          # of a bar's cell, and its left edge
    right = sum(len(ms) for _, ms in groups.values()) + 0.6 * (len(groups) - 1) - 0.08
    ax = ax or plt.subplots(figsize=(0.52 * max(right, 7.4) + 1.2, 0.3 * len(methods) + 2.4))[1]
    ax.barh(y[1::2], right + 0.16, left=-0.08, height=1, color="#F0F0F0", zorder=0)     # every second row
    top, whiskers = len(methods) - 0.5, False
    for g, (color, ms) in groups.items():
        shade = LinearSegmentedColormap.from_list(g, ["#F7F7F7", color])
        more = 0.3 * (len(ms) == 1)                             # a title is wider than one column
        ax.add_patch(FancyBboxPatch((x - more, top + 0.75), len(ms) - 1 + width + 2 * more, 0.95, fc=color, ec="none",
                                    boxstyle="round,pad=0,rounding_size=0.15", clip_on=False))
        ax.text(x + (len(ms) - 1 + width) / 2, top + 1.22, g.replace(" ", "\n"), color="white", ha="center",
                va="center", fontsize="x-small" if more else "small", linespacing=0.95)
        for m in ms:
            runs = ok[m].astype(float).groupby(ok["method"])
            # 12 decimals: sums that differ only by rounding (0.19999999999999998, 0.2, 2e-16, 0) are one value
            mean, sd = runs.mean().reindex(methods).round(12), runs.std().reindex(methods)
            lower = m in _LOWER_IS_BETTER
            rank = (mean if lower else -mean).rank(method="min")
            fill = shade(1 - (rank - 1) / max(rank.count() - 1, 1))
            spread = sd.fillna(0)
            lo, hi = min((mean - spread).min(), 0), _axis_top((mean + spread).max())
            at = lambda v: x + width * (v - lo) / (hi - lo)     # noqa: E731  the metric's axis inside its cell
            has = mean.notna().to_numpy()
            ax.barh(y[has], (at(mean) - at(0))[has], left=at(0), height=width, color=fill[has],
                    edgecolor="black", linewidth=0.6, zorder=2)
            several = sd.notna().to_numpy()
            whiskers = whiskers or several.any()
            ax.errorbar(at(mean)[several], y[several], xerr=(width * sd / (hi - lo))[several], fmt="none",
                        ecolor="black", elinewidth=0.8, capsize=2, zorder=3)
            for row in y[~has]:
                ax.text(x + width / 2, row, "n/a", ha="center", va="center", fontsize="x-small", color="0.45")
            ax.text(x + width / 2, top + 0.36, "↓" if lower else "↑", ha="center", va="center",
                    color="#C0392B" if lower else "black", fontweight="bold")
            ax.hlines(-0.8, x, x + width, color="black", lw=0.6)            # the axis of the column,
            ax.vlines([at(0), x + width], -0.88, -0.72, color="black", lw=0.6)  # with a tick at 0 and at its end
            ax.text(at(0), -1.0, "0", ha="left", va="top", fontsize="x-small")
            ax.text(x + width, -1.0, f"{hi:g}", ha="right", va="top", fontsize="x-small")
            ax.text(x + width / 2, -1.55, m, ha="right", va="top", rotation=45, rotation_mode="anchor")
            x += 1
        x += 0.6
    ax.add_patch(Rectangle((-0.08, -0.5), right + 0.16, len(methods), fill=False, ec="black", lw=0.6, zorder=4))
    # the key, below the matrix: one ramp per group, then the arrows and the whisker
    ax.text(0, -3.4, "Rank among the methods", va="center", fontsize="small", fontweight="bold")
    for i, (g, (color, _)) in enumerate(groups.items()):
        ax.pcolormesh(np.linspace(0, 3, 51), [-3.98 - 0.3 * i, -3.76 - 0.3 * i], np.linspace(0, 1, 50)[None],
                      cmap=LinearSegmentedColormap.from_list(g, ["#F7F7F7", color]), rasterized=True)
    ax.text(0, -4.1 - 0.3 * i, "worst", ha="left", va="top", fontsize="small")
    ax.text(3, -4.1 - 0.3 * i, "best", ha="right", va="top", fontsize="small")
    shown = {m for _, ms in groups.values() for m in ms}
    notes = ["↑  higher is better"] * bool(shown - _LOWER_IS_BETTER) + ["↓  lower is better"] * bool(shown & _LOWER_IS_BETTER)
    notes += ["bar: mean over the runs", "whisker: standard deviation"] if whiskers else ["bar: value of the metric"]
    for i, note in enumerate(notes):
        ax.text(3.9, -3.4 - 0.55 * i, note, va="center", fontsize="small", color="#C0392B" if note[0] == "↓" else "black")
    ax.set_xlim(-0.08, max(right + 0.08, 7.4))
    ax.set_ylim(min(-4.35 - 0.3 * len(groups), -3.15 - 0.55 * len(notes)), top + 1.75)
    ax.set_yticks(y, methods)
    ax.set_xticks([])
    ax.tick_params(length=0)
    ax.spines[:].set_visible(False)
    return ax


def plot_runtime(summary, metric="wall_time_s", ax=None, log=True):
    """Plot run time or memory per method, CPU and GPU runs side by side.

    Parameters
    ----------
    summary : pandas.DataFrame
        The table from [load_results][kdomainbench.load_results].
    metric : str
        ``"wall_time_s"`` (run time, s), ``"peak_rss_mb"`` (peak host memory, MB), or another
        numeric column of ``summary``.
    ax : matplotlib.axes.Axes, optional
        Axes to draw on. Default: a new figure.
    log : bool
        Log-scale y axis.

    Returns
    -------
    matplotlib.axes.Axes
        The plot.

    Raises
    ------
    TypeError
        ``summary`` is not a table.
    KeyError
        ``summary`` has no column ``metric``.
    ValueError
        ``summary`` has no successful run, or none with a value in ``metric``.

    Examples
    --------
    >>> kdb.pl.plot_runtime(summary)
    >>> kdb.pl.plot_runtime(summary, metric="peak_rss_mb", log=False)
    """
    ok = _successful(summary)
    if not ok[metric].notna().any():
        raise ValueError(f"no successful run has a value in {metric!r}")
    tab = ok.pivot_table(index="method", columns="device_used", values=metric, aggfunc="mean")
    tab = tab.loc[tab.mean(axis=1).sort_values().index]
    ax = ax or plt.subplots(figsize=(max(5, 0.6 * len(tab) + 2), 3.5))[1]
    tab.plot.bar(ax=ax, width=0.8, logy=log)
    if log:                                         # plain numbers at 1, 2 and 5 per decade
        ax.yaxis.set_major_locator(LogLocator(subs=(1, 2, 5)))
        ax.yaxis.set_major_formatter(ScalarFormatter())
        ax.minorticks_off()
    ax.set_ylabel({"wall_time_s": "run time (s)", "peak_rss_mb": "peak memory (MB)"}.get(metric, metric))
    ax.set_xlabel("")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    ax.legend(title="device")
    return ax


def plot_spatial(clusters, h5ad, ax=None, title=None, s=8, spatial_key="spatial", legend=False):
    """Plot the spatial domains of one run on the tissue.

    Parameters
    ----------
    clusters : pandas.DataFrame or pandas.Series or path
        Labels indexed by spot: what [run][kdomainbench.run] returns, a Series, or a run
        folder.
    h5ad : str or path or anndata.AnnData
        The input file or the data in memory. Its ``obsm[spatial_key]`` gives the spot
        positions.
    ax : matplotlib.axes.Axes, optional
        Axes to draw on. Default: a new figure.
    title : str, optional
        Default ``"k = <number of domains>"``.
    s : float
        Marker size.
    spatial_key : str
        Key of the coordinates in ``obsm``.
    legend : bool
        Name the domains in a legend beside the map.

    Returns
    -------
    matplotlib.axes.Axes
        The map.

    Raises
    ------
    KeyError
        ``obsm`` has no ``spatial_key``.
    TypeError
        ``clusters`` holds several runs. [plot_spatial_grid][kdomainbench.plotting.plot_spatial_grid]
        draws those.
    ValueError
        No label belongs to a spot of the file: the two do not use the same barcodes.

    Examples
    --------
    >>> kdb.pl.plot_spatial("kdb_results/SpaGCN/D3_151509_5k_cpu", "data/D3_151509_5k.h5ad")
    """
    if isinstance(clusters, dict):
        raise TypeError("clusters holds several runs: kdb.pl.plot_spatial_grid draws them")
    obs, xy = _read(h5ad, spatial_key)
    lab = _labels(clusters).reindex(obs.index.astype(str))     # spots without a label are not drawn
    if lab.isna().all():
        raise ValueError("no label belongs to a spot of the file. Both must use the same spot barcodes")
    ax = ax or plt.subplots(figsize=(4, 4))[1]
    # natural order: 2 before 10, Layer1 ... Layer6 before WM
    cats = sorted(lab.dropna().unique(), key=lambda x: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", x)])
    colors = plt.get_cmap("tab10").colors
    if len(cats) > 10:                          # 40 distinct colours: enough for kmax = 30
        colors = plt.get_cmap("tab20").colors + plt.get_cmap("tab20b").colors
    for i, c in enumerate(cats):
        sel = (lab == c).to_numpy()
        ax.scatter(xy[sel, 0], xy[sel, 1], s=s, color=colors[i % len(colors)], label=c, linewidths=0)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title or f"k = {len(cats)}")
    if legend:
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5), frameon=False, markerscale=2)
    return ax


def plot_spatial_grid(results, h5ad, ncols=5, s=4, spatial_key="spatial"):
    """Plot the spatial domains of several runs in a grid.

    Parameters
    ----------
    results : dict
        Name -> clusters or run folder, as [run_all][kdomainbench.run_all] returns. For
        finished runs: ``{name: folder}``.
    h5ad : str or path or anndata.AnnData
        The input file or the data in memory.
    ncols : int
        Maps per row.
    s : float
        Marker size.
    spatial_key : str
        Key of the coordinates in ``obsm``.

    Returns
    -------
    matplotlib.figure.Figure
        The grid. ``fig.savefig(...)`` saves it.

    Raises
    ------
    TypeError
        ``results`` is not a dict of runs.
    ValueError
        ``results`` is empty, or the labels of a run do not use the barcodes of the file.

    Examples
    --------
    >>> results = kdb.run_all("data/D3_151509_5k.h5ad")
    >>> kdb.pl.plot_spatial_grid(results, "data/D3_151509_5k.h5ad").savefig("domains.png")
    """
    if not isinstance(results, dict):
        raise TypeError(f"results must be {{name: clusters}}, as kdb.run_all returns, not a {type(results).__name__}")
    if not results:
        raise ValueError("no runs to plot: results is empty")
    n = len(results)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(3 * ncols, 3 * nrows), squeeze=False)
    for ax, (name, cl) in zip(axes.flat, results.items()):
        labels = _labels(cl)
        plot_spatial(labels, h5ad, ax=ax, s=s, title=f"{name} (k={labels.nunique()})", spatial_key=spatial_key)
    for ax in list(axes.flat)[n:]:
        ax.axis("off")
    fig.tight_layout()
    return fig
