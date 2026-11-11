"""The twelve metrics of the paper, computed by the paper's own code.

``metric_scripts/metrics.R`` (eleven metrics) and ``metric_scripts/scs.py`` (SCS, PASTE's code)
are unchanged copies of the scripts that scored the paper's benchmark. Each runs as a separate
process: the first in R, the second in ``kdb_py``, whose pandas version PASTE's code needs.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

import pandas as pd

from . import config
from .results import read_clusters

SCRIPTS = Path(__file__).resolve().parent / "metric_scripts"
METRICS = ["ARI", "spARI", "NMI", "FM", "AMI", "Purity", "HOM", "COM", "PAS", "CHAOS", "LISI", "SCS"]


class MetricsFailed(RuntimeError):
    """The metric code stopped with an error or returned no value.

    The message names the run's ``metric.log``, which holds the output of the metric code.
    """


def metrics(run, h5ad=None, recompute=False):
    """Compute the twelve metrics of the paper for one finished run.

    Eleven metrics come from ``metrics.R``, run in your R, and SCS from ``scs.py``, run in
    ``kdb_py``. The result is saved as ``metric.csv`` in the run folder, where
    [load_results][kdomainbench.load_results] picks it up, and a later call reads it back.

    The input file needs pixel coordinates in ``obs["pixel_row"]``, ``obs["pixel_col"]`` and
    ``obsm["spatial"]``, and a reference annotation in ``obs["clusters"]`` with at least two
    domains. Every spot needs both an annotation and a label from the run.

    Parameters
    ----------
    run : str or path
        A run folder with ``cluster_results.csv``.
    h5ad : str or path, optional
        The input file. Default: the path recorded in the run's ``run_info.json``. It is read
        only when the metrics are computed, not when ``metric.csv`` is read back.
    recompute : bool
        ``True`` = compute again when the run folder already has ``metric.csv``, for example
        after the annotation changed.

    Returns
    -------
    pandas.Series
        ``ARI``, ``spARI``, ``NMI``, ``FM``, ``AMI``, ``Purity``, ``HOM``, ``COM``, ``PAS``,
        ``CHAOS``, ``LISI`` and ``SCS``.

    Raises
    ------
    MetricsFailed
        The metric code stopped, for example because a package is missing or a spot has no
        label.
    FileNotFoundError
        ``run`` is not a run folder, or the input file or an environment is missing.

    Examples
    --------
    >>> kdb.metrics("kdb_results/DR.SC/D3_151509_5k_cpu").round(4).head(3)
    metric
    ARI      0.2333
    spARI    0.2110
    NMI      0.4826
    Name: value, dtype: float64
    """
    run = Path(run)
    if not (run / "cluster_results.csv").is_file():
        raise FileNotFoundError(f"{run} is not a run folder (a folder with cluster_results.csv). "
                                f"For every run under a folder: kdomainbench metrics <folder>")
    out = run / "metric.csv"
    if out.exists() and not recompute:
        return pd.read_csv(out, index_col="metric")["value"]
    if h5ad is None:
        if not (run / "run_info.json").is_file():
            raise FileNotFoundError(f"{run} has no run_info.json to name its input file: pass h5ad=")
        h5ad = json.loads((run / "run_info.json").read_text())["h5ad"]
    h5ad = Path(h5ad).resolve()
    if not h5ad.is_file():
        raise FileNotFoundError(f"input file not found: {h5ad}")
    clusters = read_clusters(run)
    metrics_r = config.configured("metrics")    # a second R for the metrics does not get KDB_R_LIB
    steps = [  # (interpreter, script, its environment), in the order of the paper's command lists
        (metrics_r or config.interpreter("r"), "metrics.R", config.child_env("R", r_library=not metrics_r)),
        (config.interpreter("py"), "scs.py", config.child_env("Python")),
    ]
    log_path = run / "metric.log"
    parts = []
    with tempfile.TemporaryDirectory() as tmp, open(log_path, "w") as log:
        log.write(f"[kdomainbench] metrics of {run} on {h5ad}\n")
        labels = Path(tmp) / "cluster_results.csv"
        clusters.to_csv(labels)                     # spot_id,cluster: the header both scripts read
        for interpreter, script, env in steps:
            part = Path(tmp) / f"{script}.csv"
            r = subprocess.run([interpreter, str(SCRIPTS / script), str(h5ad), str(labels), str(part)],
                               env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            log.write(f"[kdomainbench] {interpreter} {script}\n{r.stdout}")
            log.flush()
            if r.returncode:
                tail = "".join(r.stdout.splitlines(True)[-20:])
                raise MetricsFailed(f"{script} failed (exit {r.returncode}), see {log_path}\n{tail}")
            parts.append(pd.read_csv(part))
    table = pd.concat(parts, ignore_index=True)     # as the paper's merge_scs.py
    values = table.set_index("metric")["value"]
    # SCS compares the labels with their shuffles, so one domain has none (as in the paper's results).
    undefined = {"SCS"} if clusters["cluster"].nunique() == 1 else set()
    missing = [m for m in METRICS if pd.isna(values.get(m)) and m not in undefined]
    if missing:
        hint = " (PASTE's code returns no SCS with pandas 3 or later in kdb_py)" if missing == ["SCS"] else ""
        raise MetricsFailed(f"no value for {', '.join(missing)}{hint}, see {log_path}")
    table.to_csv(out.with_suffix(".part"), index=False)
    os.replace(out.with_suffix(".part"), out)       # a cut-short write never stands as metric.csv
    return values
