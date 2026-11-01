"""Build docs/assets/*.png and snippets/results_table.md from a folder of kdomainbench runs.

Usage: python scripts/make_results_page.py <results_root> <h5ad>
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import kdomainbench as kdb  # noqa: E402

root, h5ad = sys.argv[1], sys.argv[2]
docs = Path(__file__).resolve().parents[1] / "docs"
assets = docs / "assets"
assets.mkdir(parents=True, exist_ok=True)

summary = kdb.load_results(root)
ok = summary[summary["success"]]
gpu_methods = set(kdb.list_methods(gpu_only=True))

ax = kdb.pl.plot_k_estimates(ok[ok["device_used"] == "cpu"])
ax.set_title("Estimated k on D1_151507_4k (CPU, kmax = 30)")
ax.figure.tight_layout()
ax.figure.savefig(assets / "k_estimates.png", dpi=150)
plt.close(ax.figure)

ax = kdb.pl.plot_runtime(ok)
ax.set_title("Wall time on D1_151507_4k")
ax.figure.tight_layout()
ax.figure.savefig(assets / "runtime.png", dpi=150)
plt.close(ax.figure)

cpu_runs = {r.method: kdb.read_clusters(r.out_dir) for r in ok[ok["device_used"] == "cpu"].itertuples()}
order = [m for m in kdb.list_methods() if m in cpu_runs]
fig = kdb.pl.plot_spatial_grid({m: cpu_runs[m] for m in order}, h5ad, ncols=5, s=3)
fig.savefig(assets / "spatial_domains.png", dpi=130)
plt.close(fig)

truth = kdb.ground_truth(h5ad).to_frame("cluster")
ax = kdb.pl.plot_spatial(truth, h5ad, s=6, title=f"Ground truth (k = {truth['cluster'].nunique()})")
ax.figure.tight_layout()
ax.figure.savefig(assets / "ground_truth.png", dpi=130)
plt.close(ax.figure)


def fmt(v, nd=2):
    return "–" if v != v else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))


lines = ["| Method | Device | GPU support | k estimated | k error | ARI | NMI | Wall time (s) | Peak RAM (GB) |",
         "|---|---|:---:|---:|---:|---:|---:|---:|---:|"]
for r in ok.sort_values(["method", "device_used"]).itertuples():
    lines.append(f"| {r.method} | {r.device_used.upper()} | {'✓' if r.method in gpu_methods else '–'} | "
                 f"{r.k_estimated} | {int(r.k_error):+d} | {fmt(r.ARI)} | {fmt(r.NMI)} | "
                 f"{r.wall_time_s:.0f} | {r.peak_rss_mb / 1024:.1f} |")
failed = summary[~summary["success"]]
if len(failed):
    lines += ["", "Failed runs: " + ", ".join(f"{r.method} ({r.device_used})" for r in failed.itertuples())]
(docs.parent / "snippets").mkdir(exist_ok=True)
(docs.parent / "snippets" / "results_table.md").write_text("\n".join(lines) + "\n")
# local paths (h5ad, out_dir) stay out of the published table
summary.drop(columns=["h5ad", "out_dir"], errors="ignore").to_csv(docs / "assets" / "summary_4k.csv", index=False)
print("\n".join(lines))
