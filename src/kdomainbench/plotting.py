"""Figures: estimated vs true k, runtime / memory, and spatial domain maps."""
import matplotlib.pyplot as plt
import numpy as np


def _successful(summary):
    if summary.empty or not summary["success"].astype(bool).any():
        raise ValueError("no successful runs in the summary table; check the folder given to load_results")
    return summary[summary["success"].astype(bool)]


def plot_k_estimates(summary, ax=None, k_true=None):
    """Plot the estimated k of each method.

    One dot per run; methods are sorted by their median estimate. A dashed line marks the
    true k.

    Parameters
    ----------
    summary : pandas.DataFrame
        The table from [load_results][kdomainbench.load_results].
    ax : matplotlib.axes.Axes, optional
        Axes to draw on; default a new figure.
    k_true : int or list of int, optional
        True k to mark. Default: the ``k_true`` values in ``summary``.

    Returns
    -------
    matplotlib.axes.Axes

    Raises
    ------
    ValueError
        ``summary`` has no successful run.

    Examples
    --------
    >>> ax = kdb.pl.plot_k_estimates(summary)
    >>> ax.figure.savefig("k_estimates.png", dpi=150, bbox_inches="tight")
    """
    ok = _successful(summary).copy()
    order = ok.groupby("method")["k_estimated"].median().sort_values().index
    ax = ax or plt.subplots(figsize=(max(5, 0.6 * len(order) + 2), 3.5))[1]
    for i, m in enumerate(order):
        ks = ok.loc[ok["method"] == m, "k_estimated"].to_numpy()
        ax.scatter(np.full(len(ks), i) + np.linspace(-0.12, 0.12, len(ks)), ks, s=36, zorder=3)
    if k_true is None and "k_true" in ok and ok["k_true"].notna().any():
        k_true = ok["k_true"].dropna().unique()
    for k in np.atleast_1d(k_true if k_true is not None else []):
        ax.axhline(k, ls="--", lw=1, color="0.4", zorder=1)
    ax.set_xticks(range(len(order)), order, rotation=45, ha="right")
    ax.set_ylabel("estimated number of domains (k)")
    ax.grid(axis="y", alpha=0.3)
    return ax


def plot_runtime(summary, metric="wall_time_s", ax=None, log=True):
    """Plot run time or memory per method, CPU and GPU runs side by side.

    Parameters
    ----------
    summary : pandas.DataFrame
        The table from [load_results][kdomainbench.load_results].
    metric : str
        ``"wall_time_s"`` (run time, s) or ``"peak_rss_mb"`` (peak host memory, MB).
    ax : matplotlib.axes.Axes, optional
        Axes to draw on; default a new figure.
    log : bool
        Log-scale y axis.

    Returns
    -------
    matplotlib.axes.Axes

    Raises
    ------
    ValueError
        ``summary`` has no successful run.

    Examples
    --------
    >>> kdb.pl.plot_runtime(summary)
    >>> kdb.pl.plot_runtime(summary, metric="peak_rss_mb", log=False)
    """
    ok = _successful(summary)
    tab = ok.pivot_table(index="method", columns="device_used", values=metric, aggfunc="mean")
    tab = tab.loc[tab.mean(axis=1).sort_values().index]
    ax = ax or plt.subplots(figsize=(max(5, 0.6 * len(tab) + 2), 3.5))[1]
    tab.plot.bar(ax=ax, width=0.8, logy=log)
    ax.set_ylabel({"wall_time_s": "wall time (s)", "peak_rss_mb": "peak RAM (MB)"}.get(metric, metric))
    ax.set_xlabel("")
    ax.legend(title="device")
    return ax


def plot_spatial(clusters, h5ad, ax=None, title=None, s=8, spatial_key="spatial"):
    """Plot the spatial domains of one run on the tissue.

    Parameters
    ----------
    clusters : pandas.DataFrame
        Labels with a ``cluster`` column, indexed by spot.
    h5ad : str or path
        The input file; its ``obsm[spatial_key]`` gives the spot positions.
    ax : matplotlib.axes.Axes, optional
        Axes to draw on; default a new figure.
    title : str, optional
        Default ``"k = <number of domains>"``.
    s : float
        Marker size.
    spatial_key : str
        Key of the coordinates in ``obsm``.

    Returns
    -------
    matplotlib.axes.Axes

    Examples
    --------
    >>> kdb.pl.plot_spatial(kdb.read_clusters("kdb_results/SpaGCN/D1_151507_4k_cpu"), "D1_151507_4k.h5ad")
    """
    import anndata as ad
    adata = ad.read_h5ad(h5ad, backed="r")
    xy = np.asarray(adata.obsm[spatial_key])
    names = adata.obs_names
    adata.file.close()
    lab = clusters["cluster"].reindex(names).astype(str)
    ax = ax or plt.subplots(figsize=(4, 4))[1]
    cats = sorted(lab.dropna().unique(), key=lambda x: (len(x), x))
    cmap = plt.get_cmap("tab20" if len(cats) > 10 else "tab10")
    for i, c in enumerate(cats):
        sel = (lab == c).to_numpy()
        ax.scatter(xy[sel, 0], xy[sel, 1], s=s, color=cmap(i % cmap.N), label=c, linewidths=0)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title or f"k = {len(cats)}")
    return ax


def plot_spatial_grid(results, h5ad, ncols=5, s=4):
    """Plot the spatial domains of several runs in a grid.

    Parameters
    ----------
    results : dict
        Name -> clusters, as [run_all][kdomainbench.run_all] returns.
    h5ad : str or path
        The input file.
    ncols : int
        Maps per row.
    s : float
        Marker size.

    Returns
    -------
    matplotlib.figure.Figure

    Examples
    --------
    >>> results = kdb.run_all("D1_151507_4k.h5ad")
    >>> kdb.pl.plot_spatial_grid(results, "D1_151507_4k.h5ad").savefig("domains.png")
    """
    n = len(results)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(3 * ncols, 3 * nrows), squeeze=False)
    for ax, (name, cl) in zip(axes.flat, results.items()):
        plot_spatial(cl, h5ad, ax=ax, s=s, title=f"{name} (k={cl['cluster'].nunique()})")
    for ax in list(axes.flat)[n:]:
        ax.axis("off")
    fig.tight_layout()
    return fig
