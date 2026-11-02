# API reference

The package is imported as `import kdomainbench as kdb`. Its functions form four groups
(methods, run, scores, figures) plus setup. Each name links to its reference entry,
with the parameters and examples.

## 1. Methods

| call | returns |
|---|---|
| [`kdb.list_methods(gpu_only=)`](reference/methods.md#kdomainbench.list_methods) | The method names; `gpu_only=True` keeps the three with GPU code. |
| [`kdb.get_method(name)`](reference/methods.md#kdomainbench.get_method) | One method's settings: language, environment, GPU, use of `kmax`. |
| [`kdb.Method`](reference/methods.md#kdomainbench.registry.Method) | The record `get_method` returns. |

```python
import kdomainbench as kdb
kdb.list_methods(gpu_only=True)          # ['CellCharter', 'DeepST', 'SpatialDE2']
kdb.get_method("DR.SC").uses_kmax        # True
```

## 2. Run

| call | returns |
|---|---|
| [`kdb.run(method, h5ad, kmax=, device=, out_dir=, gpu_id=)`](reference/run.md#kdomainbench.run) | The domain of each spot; the run folder keeps the log and `run_info.json`. |
| [`kdb.run_all(h5ad, kmax=, device=, methods=, out_root=)`](reference/run.md#kdomainbench.run_all) | Method name → domains, for every method that succeeded. |
| [`kdb.MethodFailed`](reference/run.md#kdomainbench.MethodFailed) | Raised by `run` when a method stops with an error. |

```python
h5ad = "data/D1_151507_4k.h5ad"
clusters = kdb.run("SpaGCN", h5ad, kmax=30, device="cpu")
results = kdb.run_all(h5ad, kmax=30, device="gpu", gpu_id=0)
```

## 3. Scores

| call | returns |
|---|---|
| [`kdb.read_clusters(path)`](reference/scores.md#kdomainbench.read_clusters) | The domains of one run folder. |
| [`kdb.ground_truth(h5ad, key=)`](reference/scores.md#kdomainbench.ground_truth) | The ground-truth domain of each spot. |
| [`kdb.evaluate(clusters, truth)`](reference/scores.md#kdomainbench.evaluate) | `k_estimated`, `k_true`, `k_error`, `ARI`, `NMI`, `n_spots`. |
| [`kdb.load_results(root, truth_key=, score=)`](reference/scores.md#kdomainbench.load_results) | One row per run under `root`, scored. |
| [`kdb.k_accuracy(summary)`](reference/scores.md#kdomainbench.k_accuracy) | One row per method: mean \|k error\|, exact-k rate, mean ARI. |

```python
kdb.evaluate(kdb.read_clusters("kdb_results/SpaGCN/D1_151507_4k_cpu"), h5ad)
summary = kdb.load_results("kdb_results")
kdb.k_accuracy(summary)
```

## 4. Figures

| call | returns |
|---|---|
| [`kdb.pl.plot_k_estimates(summary, k_true=)`](reference/plot.md#kdomainbench.plotting.plot_k_estimates) | Estimated k per method, the true k dashed. |
| [`kdb.pl.plot_runtime(summary, metric=)`](reference/plot.md#kdomainbench.plotting.plot_runtime) | Run time or peak memory per method, CPU vs GPU. |
| [`kdb.pl.plot_spatial(clusters, h5ad)`](reference/plot.md#kdomainbench.plotting.plot_spatial) | One run's domains on the tissue. |
| [`kdb.pl.plot_spatial_grid(results, h5ad)`](reference/plot.md#kdomainbench.plotting.plot_spatial_grid) | Several runs' domains in a grid. |

```python
kdb.pl.plot_k_estimates(summary).figure.savefig("k.png", dpi=150, bbox_inches="tight")
kdb.pl.plot_spatial_grid(results, h5ad, ncols=5).savefig("domains.png")
```

## Setup

| call | does |
|---|---|
| [`kdb.set_env(key, interpreter=, r_lib=)`](reference/setup.md#kdomainbench.set_env) | Points an environment at an interpreter for this session. |
| [`kdomainbench` command](reference/setup.md#command-line) | `methods`, `check`, `run` and `summarize` from the shell. |
| [Environment variables](reference/setup.md#environment-variables) | `KDB_PY_PYTHON`, `KDB_SPATIALDE_PYTHON`, `KDB_RSCRIPT`, `KDB_R_LIB`, … |
