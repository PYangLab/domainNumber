"""Read cluster_results.csv / run_info.json files and score them against the ground truth."""
import json
from pathlib import Path

import pandas as pd


def read_clusters(path):
    """Read the domains of one run.

    Parameters
    ----------
    path : str or path
        A run folder, or its ``cluster_results.csv``.

    Returns
    -------
    pandas.DataFrame
        Indexed by ``spot_id``, with the label (as a string) in ``cluster``.

    Examples
    --------
    >>> clusters = kdb.read_clusters("kdb_results/SpaGCN/D1_151507_4k_cpu")
    >>> clusters["cluster"].nunique()
    4
    """
    path = Path(path)
    if path.is_dir():
        path = path / "cluster_results.csv"
    df = pd.read_csv(path)
    first = df.columns[0]
    if first != "spot_id":          # iSC.MEB writes cell_id
        df = df.rename(columns={first: "spot_id"})
    df = df[["spot_id", "cluster"]].set_index("spot_id")
    df["cluster"] = df["cluster"].astype(str)
    return df


def ground_truth(h5ad, key="clusters"):
    """Read the ground-truth domain of each spot.

    Parameters
    ----------
    h5ad : str or path
        Input file.
    key : str
        Column of ``obs`` that holds the ground truth.

    Returns
    -------
    pandas.Series
        Label (as a string) per spot; spots without a label are dropped.

    Raises
    ------
    KeyError
        ``obs`` has no column ``key``.

    Examples
    --------
    >>> kdb.ground_truth("D1_151507_4k.h5ad").nunique()
    7
    """
    import anndata as ad
    adata = ad.read_h5ad(h5ad, backed="r")
    truth = adata.obs[key].dropna().astype(str)
    adata.file.close()
    return truth


def evaluate(clusters, truth):
    """Score one run against the ground truth.

    Only spots that have both a label and a ground-truth label are scored.

    Parameters
    ----------
    clusters : pandas.DataFrame or pandas.Series
        The run's labels, as returned by [run][kdomainbench.run] or
        [read_clusters][kdomainbench.read_clusters].
    truth : str, path or pandas.Series
        The ``.h5ad`` file (its ``obs["clusters"]`` is read), or the labels from
        [ground_truth][kdomainbench.ground_truth].

    Returns
    -------
    dict
        ``k_estimated``, ``k_true``, ``k_error`` (estimated − true), ``ARI``, ``NMI`` and
        ``n_spots``.

    Examples
    --------
    >>> kdb.evaluate(clusters, "D1_151507_4k.h5ad")
    {'k_estimated': 4, 'k_true': 7, 'k_error': -3, 'ARI': 0.42, 'NMI': 0.51, 'n_spots': 4220}
    """
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    if not isinstance(truth, pd.Series):
        truth = ground_truth(truth)
    pred = clusters["cluster"] if isinstance(clusters, pd.DataFrame) else clusters
    common = pred.index.intersection(truth.index)
    p, t = pred.loc[common].astype(str), truth.loc[common]
    k_est, k_true = p.nunique(), t.nunique()
    return dict(k_estimated=int(k_est), k_true=int(k_true), k_error=int(k_est - k_true),
                ARI=float(adjusted_rand_score(t, p)), NMI=float(normalized_mutual_info_score(t, p)),
                n_spots=int(len(common)))


def load_results(root="kdb_results", truth_key="clusters", score=True):
    """Collect every run under a folder into one table.

    Reads each ``run_info.json`` under ``root``, at any depth. Each successful run is scored
    against the ground truth of its own ``.h5ad`` file.

    Parameters
    ----------
    root : str or path
        Folder that holds the run folders.
    truth_key : str
        Column of ``obs`` with the ground truth.
    score : bool
        ``False`` = only collect the run records, without scoring.

    Returns
    -------
    pandas.DataFrame
        One row per run: ``method``, ``dataset``, ``device_requested``, ``device_used``,
        ``kmax``, ``k_estimated``, ``k_true``, ``k_error``, ``ARI``, ``NMI``, ``wall_time_s``,
        ``peak_rss_mb``, ``success`` and the other fields of ``run_info.json``.

    Examples
    --------
    >>> summary = kdb.load_results("kdb_results")
    >>> summary[["method", "k_estimated", "k_error", "ARI", "wall_time_s"]]
    """
    rows, truths = [], {}
    for info_file in sorted(Path(root).rglob("run_info.json")):
        info = json.loads(info_file.read_text())
        info["out_dir"] = str(info_file.parent)
        info.pop("command", None)
        if info.get("success") and score:
            h5ad = info["h5ad"]
            try:
                if h5ad not in truths:
                    truths[h5ad] = ground_truth(h5ad, truth_key)
                info.update(evaluate(read_clusters(info_file.parent), truths[h5ad]))
            except (FileNotFoundError, KeyError) as e:
                info["score_error"] = repr(e)
        rows.append(info)
    cols = ["method", "dataset", "device_requested", "device_used", "kmax", "k_estimated", "k_true",
            "k_error", "ARI", "NMI", "wall_time_s", "peak_rss_mb", "success"]
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=cols)
    return df[[c for c in cols if c in df] + [c for c in df if c not in cols]]


def k_accuracy(summary):
    """Summarise how well each method estimates k.

    Failed runs and runs without a ground truth are left out.

    Parameters
    ----------
    summary : pandas.DataFrame
        The table from [load_results][kdomainbench.load_results].

    Returns
    -------
    pandas.DataFrame
        One row per method, best first: ``runs``, ``mean_abs_k_error``, ``exact_rate``
        (fraction of runs with exactly the true k) and ``mean_ARI``.

    Examples
    --------
    >>> kdb.k_accuracy(kdb.load_results("kdb_results"))
    """
    ok = summary[summary["success"] & summary["k_true"].notna()]
    return (ok.assign(abs_err=ok["k_error"].abs(), exact=ok["k_error"].eq(0))
              .groupby("method")
              .agg(runs=("k_error", "size"), mean_abs_k_error=("abs_err", "mean"),
                   exact_rate=("exact", "mean"), mean_ARI=("ARI", "mean"))
              .sort_values("mean_abs_k_error"))

