# API reference

The package is imported as `import kdomainbench as kdb`. Its functions form four groups
(methods, run, scores, figures) plus setup. Each name links to its reference entry,
with the parameters and examples.

## 1. Methods

| call | returns |
|---|---|
| [`kdb.list_methods(gpu_only=)`](reference/methods.md#kdomainbench.list_methods) | The method names. `gpu_only=True` keeps the three with GPU code. |
| [`kdb.get_method(name)`](reference/methods.md#kdomainbench.get_method) | One method's settings: language, environment, GPU, use of `kmax`. |
| [`kdb.Method`](reference/methods.md#kdomainbench.registry.Method) | The record `get_method` returns. |
| [`kdb.METHODS`](reference/methods.md#all-methods) | Every method's record, by name. |

```python
import kdomainbench as kdb
kdb.list_methods(gpu_only=True)          # ['CellCharter', 'DeepST', 'SpatialDE2']
kdb.get_method("DR.SC").uses_kmax        # True
```

## 2. Run

| call | returns |
|---|---|
| [`kdb.run(method, h5ad, kmax=, device=, out_root=, gpu_id=)`](reference/run.md#kdomainbench.run) | The domain of each spot. The run folder keeps the log and `run_info.json`. |
| [`kdb.run_all(h5ad, kmax=, device=, methods=, out_root=, gpu_id=)`](reference/run.md#kdomainbench.run_all) | Method name → domains, for every method that succeeded. |
| [`kdb.MethodFailed`](reference/run.md#kdomainbench.MethodFailed) | Raised by `run` when a method stops with an error. |

```python
h5ad = "data/D3_151509_5k.h5ad"
clusters = kdb.run("SpaGCN", h5ad, kmax=30, device="cpu")
results = kdb.run_all(h5ad, kmax=30, device="gpu", gpu_id=0, out_root="kdb_results_gpu")
```

## 3. Scores

| call | returns |
|---|---|
| [`kdb.read_clusters(path)`](reference/scores.md#kdomainbench.read_clusters) | The domains of one run folder. |
| [`kdb.reference_annotation(h5ad, reference_key=)`](reference/scores.md#kdomainbench.reference_annotation) | The annotated domain of each spot. |
| [`kdb.evaluate(clusters, reference)`](reference/scores.md#kdomainbench.evaluate) | `k_estimated`, `k_reference`, `k_error`, `ARI`, `NMI`, `n_spots_scored`. |
| [`kdb.metrics(run, h5ad=, recompute=)`](reference/scores.md#kdomainbench.metrics) | The twelve metrics of the paper for one run, saved as `metric.csv`. |
| [`kdb.MetricsFailed`](reference/scores.md#kdomainbench.MetricsFailed) | Raised by `metrics` when the metric code stops. |
| [`kdb.load_results(root, reference_key=, score=, h5ad=)`](reference/scores.md#kdomainbench.load_results) | One row per run under `root`, scored. |
| [`kdb.k_accuracy(summary)`](reference/scores.md#kdomainbench.k_accuracy) | One row per method: mean \|k error\|, exact-k rate, mean ARI. |

```python
kdb.evaluate(kdb.read_clusters("kdb_results/SpaGCN/D3_151509_5k_cpu"), h5ad)
summary = kdb.load_results("kdb_results")
kdb.k_accuracy(summary)
```

## 4. Figures

| call | returns |
|---|---|
| [`kdb.pl.plot_k_estimates(summary, k_reference=)`](reference/plot.md#kdomainbench.plotting.plot_k_estimates) | Estimated k per method, the reference k dashed. |
| [`kdb.pl.plot_metrics(summary)`](reference/plot.md#kdomainbench.plotting.plot_metrics) | The metrics per method as a matrix of bars. |
| [`kdb.pl.plot_runtime(summary, metric=)`](reference/plot.md#kdomainbench.plotting.plot_runtime) | Run time or peak memory per method, CPU vs GPU. |
| [`kdb.pl.plot_spatial(clusters, h5ad, legend=)`](reference/plot.md#kdomainbench.plotting.plot_spatial) | One run's domains on the tissue. |
| [`kdb.pl.plot_spatial_grid(results, h5ad)`](reference/plot.md#kdomainbench.plotting.plot_spatial_grid) | Several runs' domains in a grid. |

```python
kdb.pl.plot_k_estimates(summary).figure.savefig("k.png", dpi=150, bbox_inches="tight")
kdb.pl.plot_spatial_grid(results, h5ad, ncols=5).savefig("domains.png")
```

## Setup

| call | does |
|---|---|
| [`kdb.set_env(key, interpreter=, r_lib=)`](reference/setup.md#kdomainbench.set_env) | Points an environment at an interpreter for this session. |
| [`kdomainbench` command](reference/cli.md) | `methods`, `check`, `run`, `metrics` and `summarize` from the shell. |
| [Environment variables](reference/setup.md#environment-variables) | `KDB_PY_PYTHON`, `KDB_SPATIALDE_PYTHON`, `KDB_RSCRIPT`, `KDB_R_LIB`, … |
