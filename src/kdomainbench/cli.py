"""Run the ten k-estimation methods, compute their metrics and summarize the runs.

  kdomainbench check                          do the environments start?
  kdomainbench run -m all -i sample.h5ad      one run folder per method under kdb_results/
  kdomainbench metrics                        the twelve metrics of the paper for every run
  kdomainbench summarize --csv summary.csv    the runs, scored against the reference annotation

Exit status: 0 done, 1 an environment, a method or a metric failed, a file is missing or a value
cannot be used (an unknown method, a kmax out of range), 2 the command line cannot be parsed.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

from . import __version__, config
from .paper_metrics import METRICS, MetricsFailed, metrics
from .plotting import plot_k_estimates
from .registry import METHODS, get_method
from .results import k_accuracy, load_results
from .runner import METHODS_DIR, _build_env


def _methods(_):
    print(f"{'method':<12}{'language':<9}{'env':<11}{'GPU':<5}uses kmax")
    for m in METHODS.values():
        print(f"{m.name:<12}{m.language:<9}{m.env:<11}{'yes' if m.gpu else '-':<5}{'yes' if m.uses_kmax else 'no (auto)'}")


_CHECKS = {
    "py": "import torch, cellcharter, deepstkit, SpaGCN; print('torch', torch.__version__, '| CUDA available:', torch.cuda.is_available())",
    "spatialde": "import SpatialDE, tensorflow as tf; print('tensorflow', tf.__version__, '| GPUs:', len(tf.config.list_physical_devices('GPU')))",
    # R: every package the method scripts load is there, and an .h5ad file can be read
    # (zellkonverter fetches its reader on first use, which needs internet once)
    "r": """args <- commandArgs(trailingOnly = TRUE)
pk <- strsplit(args[2], ",")[[1]]
miss <- pk[!vapply(pk, requireNamespace, logical(1), quietly = TRUE)]
for (p in setdiff(intersect(c("PRECAST", "SC.MEB", "BayesSpace", "DR.SC", "iSC.MEB", "zellkonverter"), pk), miss))
  cat(p, as.character(packageVersion(p)), "\n")
if (length(miss)) stop("missing R packages: ", paste(miss, collapse = ", "),
                       ". Install them with 'Rscript envs/install_r_packages.R' (Installation, step 2)")
x <- suppressMessages(zellkonverter::readH5AD(args[1]))
cat("reads .h5ad files:", ncol(x), "spots\n")""",
}
_NO_GPU = 3     # exit code of the two snippets below
_NEEDS_GPU = {
    "py": f"; import sys; sys.exit(0 if torch.cuda.is_available() else {_NO_GPU})",
    "spatialde": f"; import sys; sys.exit(0 if tf.config.list_physical_devices('GPU') else {_NO_GPU})",
}


def _r_packages():
    """Every package the R method scripts load: library(x), x::f and Rcpp::depends(x)."""
    names = set()
    for f in METHODS_DIR.rglob("*"):
        if f.suffix == ".R":
            text = f.read_text()
            names.update(re.findall(r"^[^#\n]*\b(?:library|require)\(\"?([A-Za-z][\w.]*)", text, flags=re.M))
            names.update(re.findall(r"^[^#\n]*?\b([A-Za-z][\w.]*)::", text, flags=re.M))
        elif f.suffix == ".cpp":
            names.update(re.findall(r"Rcpp::depends\((\w+)\)", f.read_text()))
    return sorted(names)


def _check(args):
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for key, code in _CHECKS.items():
            try:
                interp = config.interpreter(key)
            except FileNotFoundError as e:
                print(f"[{key}] MISSING: {e}")
                ok = False
                continue
            if key == "r":
                import anndata           # slow to import, and needed by `check` only
                h5ad = Path(tmp) / "check.h5ad"
                anndata.AnnData(np.ones((3, 2), dtype="float32")).write_h5ad(h5ad)
                cmd = [interp, "-e", code, str(h5ad), ",".join(_r_packages())]
            else:
                cmd = [interp, "-c", code + (_NEEDS_GPU[key] if args.gpu else "")]
            m = next(m for m in METHODS.values() if m.env == key)     # any method of this environment
            env = _build_env(m, "gpu" if args.gpu else "cpu", args.gpu_id)
            r = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if r.returncode in (0, _NO_GPU):
                lines = r.stdout.strip().splitlines() + (["no GPU visible"] if r.returncode else [])
            else:
                lines = r.stdout.strip().splitlines() + ["FAILED"] + r.stderr.strip().splitlines()[-3:]
            print(f"[{key}] {interp}\n    " + "\n    ".join(lines))
            ok &= r.returncode == 0
        if args.metrics:
            ok &= _check_metrics(Path(tmp))
    sys.exit(0 if ok else 1)


def _check_metrics(tmp):
    """Compute the twelve metrics on a small made-up sample: the real test of the metric code."""
    import anndata
    row, col = np.divmod(np.arange(200), 20)            # a 10 x 20 grid of spots
    obs = pd.DataFrame({"clusters": np.where(col < 10, "left", "right"), "pixel_row": row * 10.0,
                        "pixel_col": col * 10.0}, index=[f"spot{i}" for i in range(200)])
    adata = anndata.AnnData(np.ones((200, 2), dtype="float32"), obs=obs)
    adata.obsm["spatial"] = obs[["pixel_col", "pixel_row"]].to_numpy()
    adata.write_h5ad(tmp / "sample.h5ad")
    (tmp / "run").mkdir()
    pd.DataFrame({"spot_id": obs.index, "cluster": row // 4}).to_csv(tmp / "run" / "cluster_results.csv", index=False)
    try:
        values = metrics(tmp / "run", tmp / "sample.h5ad")
    except (MetricsFailed, FileNotFoundError) as e:
        print("[metrics] FAILED\n    " + str(e).strip().replace("\n", "\n    "))
        return False
    print(f"[metrics] {config.interpreter('metrics')} and {config.interpreter('py')}\n"
          f"    compute the {len(values)} metrics on a test sample")
    return True


def _run(args):
    from . import run_all                   # looked up at each call: the tests replace kdb.run_all
    everything = [name.lower() for name in args.method] == ["all"]
    # each method once, under its own name: the count below needs it
    methods = None if everything else list(dict.fromkeys(get_method(name).name for name in args.method))
    done = run_all(args.input, kmax=args.kmax, device=args.device, methods=methods,
                   out_root=args.out, gpu_id=args.gpu_id)
    if len(done) < len(methods or METHODS):      # run_all's warning has named them
        sys.exit(1)


def _inputs(args):
    """``--h5ad`` files as ``{dataset: file}``: each scores the runs of the dataset of its name."""
    return {Path(f).stem: f for f in args.h5ad or []}


def _metrics(args):
    files = _inputs(args)
    runs = load_results(args.root, score=False, h5ad=files)      # h5ad= for its checks: a missing file, a name without a run
    runs = runs[runs["success"].astype(bool)]
    if runs.empty:
        sys.exit(f"kdomainbench: error: no successful run under {args.root!r} (looked for run_info.json files)")
    rows, failed = {}, []
    for r in runs.itertuples():
        name = os.path.relpath(r.out_dir, args.root)          # unique, also for two runs of one method
        print(f"[kdomainbench] metrics of {name}", flush=True)
        try:
            rows[name] = metrics(r.out_dir, h5ad=files.get(r.dataset), recompute=args.force)
        except (MetricsFailed, FileNotFoundError) as e:
            print(f"[kdomainbench] {e}")
            failed.append(name)
    if rows:
        print("\n" + pd.DataFrame(rows).T[METRICS].round(4).to_string())
    if failed:
        sys.exit(f"kdomainbench: error: no metrics for: {', '.join(failed)}")


def _summarize(args):
    df = load_results(args.root, reference_key=args.reference_key, h5ad=_inputs(args))
    if df.empty:
        sys.exit(f"kdomainbench: error: no run under {args.root!r} (looked for run_info.json files)")
    shown = ["method", "dataset", "device_used", "k_estimated", "k_reference", "k_error", "ARI", "NMI",
             "wall_time_s", "peak_rss_mb", "success"]                # the CSV has every column
    print(df[shown].to_string(index=False))
    for reason, n in df["score_error"].dropna().value_counts().items():
        print(f"not scored ({n} of {len(df)}): {reason}")
    if df["score_error"].notna().any():
        print("--h5ad FILE gives an input file that is elsewhere, --reference-key COLUMN another annotation column")
    if args.csv:
        df.to_csv(args.csv, index=False)
    if not df["success"].any():
        sys.exit(f"kdomainbench: error: no successful run under {args.root!r}")
    if args.plot:
        matplotlib.use("Agg")
        plot_k_estimates(df).figure.savefig(args.plot, dpi=150, bbox_inches="tight")
    if df["k_error"].notna().any():         # else the lines above say why no run was scored
        print("\n" + k_accuracy(df).to_string())


def parser():
    """The argument parser of the ``kdomainbench`` command."""
    p = argparse.ArgumentParser(prog="kdomainbench", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"kdomainbench {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("methods", help="list the methods",
                   description="Print one line per method: language, environment, GPU support and use of kmax."
                   ).set_defaults(fn=_methods)
    c = sub.add_parser("check", help="check that the three environments start",
                       description="Start each of the three environments once and print its key packages. "
                                   "Exits 1 when one is missing or fails.")
    c.add_argument("--gpu", action="store_true", help="check with the GPU visible, and fail when none is")
    c.add_argument("--gpu-id", metavar="N", help="GPU to make visible with --gpu (default: those in CUDA_VISIBLE_DEVICES, else 0)")
    c.add_argument("--metrics", action="store_true", help="also compute the twelve metrics on a small test sample")
    c.set_defaults(fn=_check)
    r = sub.add_parser("run", help="run methods on an .h5ad file",
                       description="Run methods on an .h5ad file, one after another, each into its own run folder. "
                                   "Exits 1 when a method did not finish.")
    r.add_argument("-m", "--method", nargs="+", required=True, metavar="METHOD",
                   help="method names as 'kdomainbench methods' prints them (case-insensitive), or 'all'")
    r.add_argument("-i", "--input", required=True, metavar="FILE", help="input .h5ad file")
    r.add_argument("-k", "--kmax", type=int, default=30,
                   help="largest number of domains a method may consider, at least 2 (default: %(default)s). "
                        "BNPSpace accepts at most 30, and DeepST and SpaGCN do not use it")
    r.add_argument("-d", "--device", choices=["cpu", "gpu"], default="cpu",
                   help="device. A method without GPU code runs on the CPU and warns (default: %(default)s)")
    r.add_argument("--gpu-id", metavar="N", help="GPU for -d gpu (default: those in CUDA_VISIBLE_DEVICES, else 0)")
    r.add_argument("-o", "--out", default="kdb_results", metavar="DIR",
                   help="results folder. Each run goes to DIR/<method>/<dataset>_<device> and replaces a run "
                        "already there (default: %(default)s)")
    r.set_defaults(fn=_run)
    q = sub.add_parser("metrics", help="compute the twelve metrics of every finished run",
                       description="Print the twelve metrics of the paper for every finished run under root. "
                                   "A run without metric.csv is computed first.")
    q.add_argument("root", nargs="?", default="kdb_results", help="results folder (default: %(default)s)")
    inputs = dict(action="append", metavar="FILE",
                  help="input file named <dataset>.h5ad, for runs whose recorded input file is not on this "
                       "machine. Repeat it for several datasets")
    q.add_argument("--h5ad", **inputs)
    q.add_argument("--force", action="store_true", help="compute again for runs that already have metric.csv")
    q.set_defaults(fn=_metrics)
    s = sub.add_parser("summarize", help="score every run and print the tables",
                       description="Print the table of the runs under root, why runs were not scored, and the "
                                   "k accuracy of each method.")
    s.add_argument("root", nargs="?", default="kdb_results", help="results folder (default: %(default)s)")
    s.add_argument("--h5ad", **inputs)
    s.add_argument("--reference-key", default="clusters", metavar="COLUMN",
                   help="obs column with the reference annotation (default: %(default)s)")
    s.add_argument("--csv", metavar="FILE", help="also save the table of runs, with every column, as a CSV file")
    s.add_argument("--plot", metavar="FILE",
                   help="also save the k-estimate figure. The extension gives the format (png, pdf, svg)")
    s.set_defaults(fn=_summarize)
    sub.metavar = "{" + ",".join(sub.choices) + "}"       # else a bare "kdomainbench" asks for "cmd"
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    with warnings.catch_warnings():     # a warning prints as one message, without Python's source line
        warnings.showwarning = lambda message, *_: print(f"kdomainbench: warning: {message}", file=sys.stderr)
        try:
            args.fn(args)
        except (ValueError, OSError) as e:      # a wrong argument or a missing file: one line, no traceback
            sys.exit(f"kdomainbench: error: {e}")


if __name__ == "__main__":
    main()
