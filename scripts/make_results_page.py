"""Build the table and figures of the benchmark tutorial from a folder of kdomainbench runs.

Usage: python scripts/make_results_page.py <results_root> <h5ad>

Uses the runs of <h5ad> under <results_root>, without its GPU runs. Writes
snippets/results_table.md and, in docs/assets/, summary_5k.csv, k_estimates.png,
spatial_domains.png and reference_annotation.png, and metrics.png when the runs were scored
with `kdomainbench metrics`. The pages show no run times, so the table and the CSV file leave
them out.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import kdomainbench as kdb  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
ASSETS = REPO / "docs" / "assets"


def save(fig, name, dpi=150):
    fig.savefig(ASSETS / name, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def table(summary):
    """Markdown table of the successful runs, the smallest k error first."""
    ok = summary[summary["success"]]
    ok = ok.assign(abs_err=ok["k_error"].abs()).sort_values(["abs_err", "ARI"], ascending=[True, False])
    lines = ["| Method | Estimated k | k error | ARI | NMI |", "|---|---:|---:|---:|---:|"]
    for r in ok.itertuples():
        lines.append(f"| {r.method} | {r.k_estimated} | {r.k_error:+d} | {r.ARI:.2f} | {r.NMI:.2f} |")
    failed = summary[~summary["success"]]
    if len(failed):
        lines += ["", "Failed runs: " + ", ".join(failed["method"])]
    return "\n".join(lines).replace("| +0 |", "| 0 |") + "\n"


def summary_figures(ok):
    """Estimated k and, where the runs have them, the twelve metrics per method."""
    device = "CPU, " if ok["device_used"].eq("cpu").all() else ""
    ax = kdb.pl.plot_k_estimates(ok)
    ax.set_title(f"Estimated k on {ok['dataset'].iloc[0]} ({device}kmax = {ok['kmax'].iloc[0]})")
    save(ax.figure, "k_estimates.png")
    if "spARI" in ok:                   # a column of load_results when a run has its metric.csv
        save(kdb.pl.plot_metrics(ok).figure, "metrics.png")


def domain_maps(ok, h5ad):
    """The domains of every successful run, and the reference annotation, on the tissue."""
    runs = {r.method: kdb.read_clusters(r.out_dir) for r in ok.itertuples()}
    fig = kdb.pl.plot_spatial_grid({m: runs[m] for m in kdb.list_methods() if m in runs}, h5ad, ncols=5, s=3)
    save(fig, "spatial_domains.png", dpi=130)
    reference = kdb.reference_annotation(h5ad).to_frame("cluster")
    ax = kdb.pl.plot_spatial(reference, h5ad, s=6, legend=True,
                             title=f"Reference annotation (k = {reference['cluster'].nunique()})")
    save(ax.figure, "reference_annotation.png", dpi=130)


if __name__ == "__main__":
    root, h5ad = sys.argv[1], sys.argv[2]
    summary = kdb.load_results(root)
    summary = summary[(summary["dataset"] == Path(h5ad).stem) & (summary["device_requested"].fillna("cpu") == "cpu")]
    ok = summary[summary["success"]]
    (REPO / "snippets" / "results_table.md").write_text(table(summary))
    summary_figures(ok)
    domain_maps(ok, h5ad)
    # local paths, run times and columns without any value stay out of the published table
    hidden = ["h5ad", "out_dir", "wall_time_s", "started"]
    summary.drop(columns=hidden, errors="ignore").dropna(axis=1, how="all").to_csv(ASSETS / "summary_5k.csv", index=False)
    print(table(summary))
