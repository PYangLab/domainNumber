"""Read cluster_results.csv / run_info.json files and score them against the reference annotation."""
import json
import warnings
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
        Indexed by ``spot_id``, with the label (as a string) in ``cluster``. Spots without
        a label are left out.

    Raises
    ------
    FileNotFoundError
        There is no such folder or file, or the run did not finish.
    ValueError
        The file has no ``cluster`` column, or it is the input ``.h5ad`` file.

    Examples
    --------
    >>> clusters = kdb.read_clusters("kdb_results/SpaGCN/D3_151509_5k_cpu")
    >>> clusters["cluster"].nunique()
    4
    """
    path = Path(path)
    if path.is_dir():
        path = path / "cluster_results.csv"
    if path.suffix == ".h5ad":
        raise ValueError(f"{path} is an input file: read_clusters reads a run folder or its cluster_results.csv")
    if not path.is_file():
        if path.name == "cluster_results.csv" and (path.parent / "run_info.json").is_file():
            raise FileNotFoundError(f"{path.parent} has no cluster_results.csv: the run did not finish, "
                                    f"see {path.parent / 'run.log'}")
        raise FileNotFoundError(f"{path} not found: read_clusters reads one run folder "
                                f"(<out_root>/<method>/<dataset>_<device>) or its cluster_results.csv. "
                                f"kdb.load_results(folder)['out_dir'] lists the run folders under a folder")
    df = pd.read_csv(path, dtype=str)                       # barcodes stay text, also when they look like numbers
    if "cluster" not in df:
        raise ValueError(f"no 'cluster' column in {path}")
    df = df.rename(columns={df.columns[0]: "spot_id"})      # iSC.MEB writes cell_id
    return df[["spot_id", "cluster"]].dropna(subset=["cluster"]).set_index("spot_id")


def _labels(clusters):
    """The labels of a run as text, indexed by barcode as text, without spots that have none."""
    if isinstance(clusters, (str, Path)):
        clusters = read_clusters(clusters)
    if isinstance(clusters, pd.DataFrame) and "cluster" in clusters:
        clusters = clusters["cluster"]
    if not isinstance(clusters, pd.Series):
        raise TypeError(f"expected the labels of one run (a run folder, or what kdb.run or kdb.read_clusters "
                        f"returns), not a {type(clusters).__name__}"
                        + (" without a 'cluster' column" if isinstance(clusters, pd.DataFrame) else ""))
    labels = clusters.dropna().astype(str)
    labels.index = labels.index.astype(str)
    return labels


def _check_table(summary, *columns):
    """Raise unless ``summary`` is the table of load_results, with these columns."""
    if not isinstance(summary, pd.DataFrame):
        raise TypeError(f"summary must be the table from kdb.load_results, not a {type(summary).__name__}")
    missing = [c for c in ("method", "success", *columns) if c not in summary]
    if missing:
        raise KeyError(f"summary has no column {', '.join(map(repr, missing))}: pass the whole table from "
                       f"kdb.load_results, not a selection of its columns")


def _read(h5ad, obsm_key=None):
    """``obs``, and the array ``obsm[obsm_key]``, of an AnnData object or an ``.h5ad`` file."""
    import numpy as np
    if hasattr(h5ad, "obs"):
        adata = h5ad
    else:
        import anndata as ad
        if not Path(h5ad).is_file():
            raise FileNotFoundError(f"input file not found: {h5ad}")
        if Path(h5ad).suffix != ".h5ad":
            raise ValueError(f"{h5ad} is not an .h5ad file")
        adata = ad.read_h5ad(h5ad, backed="r")
    try:
        if obsm_key is None:
            return adata.obs, None
        if obsm_key not in adata.obsm:
            raise KeyError(f"obsm has no {obsm_key!r} (it has {list(adata.obsm)}): name the spot "
                           f"coordinates with spatial_key=")
        return adata.obs, np.asarray(adata.obsm[obsm_key])
    finally:
        if adata is not h5ad:
            adata.file.close()


def reference_annotation(h5ad, reference_key="clusters"):
    """Read the reference annotation: the annotated domain of each spot.

    Parameters
    ----------
    h5ad : str or path or anndata.AnnData
        The input file, or the data already in memory.
    reference_key : str
        Column of ``obs`` that holds the annotation.

    Returns
    -------
    pandas.Series
        Label (as a string) per spot. Spots without a label are dropped.

    Raises
    ------
    FileNotFoundError
        ``h5ad`` is not a file.
    KeyError
        ``obs`` has no column ``reference_key``. The message lists the columns it has.
    ValueError
        ``h5ad`` is not an ``.h5ad`` file.

    Examples
    --------
    >>> kdb.reference_annotation("data/D3_151509_5k.h5ad").nunique()
    7
    """
    obs, _ = _read(h5ad)
    if reference_key not in obs:
        raise KeyError(f"no reference annotation: obs has no column {reference_key!r} "
                       f"(its columns: {', '.join(map(str, obs.columns)) or 'none'})")
    return obs[reference_key].dropna().astype(str)


def evaluate(clusters, reference):
    """Score one run against the reference annotation.

    ``k_estimated`` counts every label the method returned and ``k_reference`` every annotated
    domain. ARI and NMI use the spots that have both a label and an annotation. NMI is
    normalized by the arithmetic mean of the two entropies (the scikit-learn default).

    Parameters
    ----------
    clusters : pandas.DataFrame or pandas.Series or path
        The run's labels, as returned by [run][kdomainbench.run] or
        [read_clusters][kdomainbench.read_clusters], or its run folder.
    reference : path or anndata.AnnData or pandas.Series or pandas.DataFrame
        The ``.h5ad`` file or AnnData object (its ``obs["clusters"]`` is read), the labels
        from [reference_annotation][kdomainbench.reference_annotation], or another run (its
        labels or its run folder) to see how far two methods agree. For another ``obs``
        column, pass ``kdb.reference_annotation(h5ad, reference_key=...)``.

    Returns
    -------
    dict
        ``k_estimated``, ``k_reference``, ``k_error`` (estimated − reference), ``ARI`` and
        ``NMI`` (rounded to 4 digits, while [metrics][kdomainbench.metrics] gives full
        precision) and ``n_spots_scored`` (the spots ARI and NMI were computed on).

    Raises
    ------
    FileNotFoundError
        The run folder or the ``.h5ad`` file is missing.
    KeyError
        The file has no ``obs["clusters"]``.
    TypeError
        ``clusters`` or ``reference`` is not one of the types above.
    ValueError
        No spot has both a label and an annotation (the two do not use the same barcodes),
        a barcode occurs twice, or the file is not an ``.h5ad`` file.

    Examples
    --------
    >>> kdb.evaluate("kdb_results/SpaGCN/D3_151509_5k_cpu", "data/D3_151509_5k.h5ad")
    {'k_estimated': 4, 'k_reference': 7, 'k_error': -3, 'ARI': 0.4487, 'NMI': 0.5694, 'n_spots_scored': 4786}
    """
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    if isinstance(reference, (str, Path)) and Path(reference).is_dir():
        reference = read_clusters(reference)                # another run
    elif not isinstance(reference, (pd.Series, pd.DataFrame)):
        reference = reference_annotation(reference)
    pred, reference = _labels(clusters), _labels(reference)
    if pred.index.has_duplicates or reference.index.has_duplicates:
        raise ValueError("a spot barcode occurs twice in the clusters or in the reference annotation")
    common = pred.index.intersection(reference.index)
    if common.empty:
        raise ValueError("the clusters and the reference annotation share no spot. "
                         "Both must be indexed by the same spot barcodes")
    p, r = pred.loc[common], reference.loc[common]
    k_est, k_ref = pred.nunique(), reference.nunique()
    return dict(k_estimated=int(k_est), k_reference=int(k_ref), k_error=int(k_est - k_ref),
                ARI=round(float(adjusted_rand_score(r, p)), 4),
                NMI=round(float(normalized_mutual_info_score(r, p)), 4),
                n_spots_scored=int(len(common)))


def load_results(root="kdb_results", reference_key="clusters", score=True, h5ad=None):
    """Collect every run under a folder into one table.

    Reads each ``run_info.json`` under ``root``, at any depth. Each successful run is scored
    against the reference annotation of its own ``.h5ad`` file.

    Parameters
    ----------
    root : str or path
        Folder that holds the run folders.
    reference_key : str
        Column of ``obs`` with the reference annotation.
    score : bool
        ``False`` = only collect the run records, without scoring.
    h5ad : str or path or dict, optional
        Where the input file is now, when the runs were made elsewhere: one file when all
        runs are of one dataset, else ``{dataset: file}``. Default: the path recorded in each
        ``run_info.json``.

    Returns
    -------
    pandas.DataFrame
        One row per run, always with ``method``, ``dataset``, ``device_requested``,
        ``device_used``, ``kmax``, ``k_estimated``, ``k_reference``, ``k_error``, ``ARI``,
        ``NMI``, ``wall_time_s``, ``peak_rss_mb``, ``success``, ``n_spots_scored``,
        ``score_error`` and ``out_dir`` (the run folder), then the other fields of
        ``run_info.json`` except ``command`` (``n_spots`` is the number of labeled spots). A run
        that could not be scored, for example because its file has no annotation, has the
        reason in ``score_error`` and no ``k_reference``, ``k_error``, ``ARI`` or ``NMI``. With
        ``reference_key="clusters"``, a run with a ``metric.csv`` from
        [metrics][kdomainbench.metrics] also has the ten other metrics of the paper as columns.
        The table is empty, with the columns above, when ``root`` holds no run.

    Raises
    ------
    FileNotFoundError
        ``root`` is not a folder, or a file given as ``h5ad`` does not exist.
    ValueError
        ``h5ad`` is one file and the runs are of several datasets, or ``h5ad`` names a
        dataset that has no run under ``root``.

    Examples
    --------
    >>> summary = kdb.load_results("kdb_results")
    >>> summary[["method", "k_estimated", "k_error", "ARI"]].head(3)
            method  k_estimated  k_error     ARI
    0     BNPSpace            2       -5  0.0480
    1   BayesSpace            4       -3  0.3745
    2  CellCharter            2       -5  0.3657
    """
    from .paper_metrics import METRICS          # here, since paper_metrics imports this module
    if not Path(root).is_dir():
        raise FileNotFoundError(f"no such folder: {root}")
    if h5ad is not None:
        for file in h5ad.values() if isinstance(h5ad, dict) else [h5ad]:
            if not Path(file).is_file():
                raise FileNotFoundError(f"input file not found: {file}")
    rows = []
    for info_file in sorted(Path(root).rglob("run_info.json")):
        try:
            info = json.loads(info_file.read_text())
        except ValueError:                      # a record cut short, e.g. by a full disk
            info = dict(success=False, score_error=f"run_info.json cannot be read: {info_file.parent}")
        info["out_dir"] = str(info_file.parent)
        info.pop("command", None)               # a long list, of no use as a table column
        rows.append(info)
    datasets = sorted({info["dataset"] for info in rows if "dataset" in info})
    if isinstance(h5ad, dict) and set(h5ad) - set(datasets):
        raise ValueError(f"h5ad names datasets without a run under {root}: {sorted(set(h5ad) - set(datasets))} "
                         f"(the runs are of {datasets})")
    if h5ad is not None and not isinstance(h5ad, dict) and len(datasets) > 1:   # one file would score them all
        raise ValueError(f"the runs under {root} are of {len(datasets)} datasets ({', '.join(datasets)}): "
                         f"pass h5ad={{dataset: file}}")
    references = {}
    for info in rows:
        if info.get("success") and score:
            file = h5ad.get(info["dataset"], info["h5ad"]) if isinstance(h5ad, dict) else h5ad or info["h5ad"]
            try:
                if file not in references:
                    references[file] = reference_annotation(file, reference_key)
                info.update(evaluate(read_clusters(info["out_dir"]), references[file]))
            except (OSError, KeyError, ValueError) as e:
                info["score_error"] = e.args[0] if isinstance(e, KeyError) else str(e)
            metric_csv = Path(info["out_dir"]) / "metric.csv"
            if reference_key == "clusters" and metric_csv.exists():   # metrics.R scores against obs["clusters"]
                metric = pd.read_csv(metric_csv, index_col="metric")["value"]
                info.update(metric.drop(["ARI", "NMI"]))                # the same two as evaluate's
    cols = ["method", "dataset", "device_requested", "device_used", "kmax", "k_estimated", "k_reference",
            "k_error", *METRICS, "wall_time_s", "peak_rss_mb", "success", "n_spots_scored", "score_error", "out_dir"]
    df = pd.DataFrame(rows)
    for c in cols:                              # always there, except the ten metrics that need a metric.csv
        if c not in df and (c not in METRICS or c in ("ARI", "NMI")):
            df[c] = pd.NA
    for c in ("k_estimated", "k_reference", "k_error", "n_spots", "n_spots_scored"):   # integers, also when some runs have none
        if c in df:
            df[c] = df[c].astype("Int64")
    return df[[c for c in cols if c in df] + [c for c in df if c not in cols]]


def k_accuracy(summary):
    """Summarize how well each method estimates k.

    Each method is summarized over all its runs in ``summary``. Filter the table first to
    compare within one dataset or device. Failed runs and runs without a reference
    annotation are left out.

    Parameters
    ----------
    summary : pandas.DataFrame
        The table from [load_results][kdomainbench.load_results].

    Returns
    -------
    pandas.DataFrame
        One row per method, best first (smallest mean absolute k error, then highest mean ARI):
        ``runs``, ``mean_abs_k_error``, ``exact_rate`` (fraction of runs with exactly the
        reference k) and ``mean_ARI``. Empty when no run has a reference annotation.

    Raises
    ------
    TypeError
        ``summary`` is not a table, for example a folder name.
    KeyError
        ``summary`` lacks a column of the [load_results][kdomainbench.load_results] table.

    Warns
    -----
    UserWarning
        There are successful runs, but none of them could be scored. The warning quotes
        the first ``score_error``.

    Examples
    --------
    >>> kdb.k_accuracy(kdb.load_results("kdb_results")).head(3)
             runs  mean_abs_k_error  exact_rate  mean_ARI
    method
    PRECAST     1               2.0         0.0    0.2615
    DeepST      1               3.0         0.0    0.5416
    SpaGCN      1               3.0         0.0    0.4487
    """
    _check_table(summary, "k_reference", "k_error", "ARI")
    done = summary[summary["success"].astype(bool)]
    ok = done[done["k_reference"].notna()]
    if len(done) and ok.empty:
        reason = done.get("score_error", pd.Series(dtype=object)).dropna()     # a table made by hand may lack it
        warnings.warn("no successful run could be scored" + (f": {reason.iloc[0]}" if len(reason) else ""),
                      stacklevel=2)
    return (ok.assign(abs_err=ok["k_error"].abs(), exact=ok["k_error"].eq(0))
              .groupby("method")
              .agg(runs=("k_error", "size"), mean_abs_k_error=("abs_err", "mean"),
                   exact_rate=("exact", "mean"), mean_ARI=("ARI", "mean"))
              .round({"mean_ARI": 4})
              .sort_values(["mean_abs_k_error", "mean_ARI"], ascending=[True, False]))
