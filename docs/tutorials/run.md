# Run a method

`kdb.run` runs one method on one `.h5ad` file in the environment the method needs, waits for
it, and returns one domain label per spot.

!!! tip "Summary"
    ```python
    import kdomainbench as kdb
    h5ad = "data/D3_151509_5k.h5ad"

    clusters = kdb.run("SpaGCN", h5ad, kmax=30, device="cpu")
    results  = kdb.run_all(h5ad, kmax=30)      # all ten
    ```

## Run one method

```python
clusters = kdb.run("SpaGCN", h5ad, kmax=30, device="cpu")
```

The method name is case-insensitive, and aliases such as `drsc` work. `kmax` is the largest k
the method may consider (for BNPSpace, the k it starts from). The [reference entry](../reference/run.md#kdomainbench.run) lists every
argument and its default.

While the method runs, its output is printed. The lines that start with `[kdomainbench]` come
from kDomainBench:

```text
[kdomainbench] note: SpaGCN selects k by itself, so kmax=30 is not used.
[kdomainbench] SpaGCN on CPU -> /path/to/kdb_results/SpaGCN/D3_151509_5k_cpu
...
```

The outputs on this page are those of the paper's benchmark run of SpaGCN on sample 151509.

## What `kdb.run` returns

A DataFrame indexed by `spot_id` with one `cluster` column:

```python
clusters.head(3)
#                      cluster
# spot_id
# AAACAAGTATCTCCCA-1.2       2
# AAACAATCTACTAGCA-1.2       1
# AAACACCAATAACTGC-1.2       0
clusters["cluster"].value_counts().sort_index()
# 0    1556
# 1    1513
# 2    1288
# 3     429
```

The number of distinct labels is the method's estimated k (here 4).

## The run folder

Each run writes to `<out_root>/<method>/<dataset>_<device>`, by default under `kdb_results/`.
`<dataset>` is the name of the input file without `.h5ad`:

```text
kdb_results/SpaGCN/D3_151509_5k_cpu/
├── cluster_results.csv   # spot_id,cluster
├── run.log               # everything the method printed
├── packages.txt          # the packages of the method's environment
└── run_info.json         # the record of the run: what ran, and with which settings
```

```json title="run_info.json"
{
  "method": "SpaGCN",
  "dataset": "D3_151509_5k",
  "h5ad": "/path/to/kDomainBench/data/D3_151509_5k.h5ad",
  "kmax": 30,
  "device_requested": "cpu",
  "device_used": "cpu",
  "gpu_id": null,
  "returncode": 0,
  "kdomainbench": "0.1.0",
  "command": ["/path/to/envs/kdb_py/bin/python", "/path/to/methods/run_spagcn.py",
              "--data_path", "/path/to/kDomainBench/data/D3_151509_5k.h5ad",
              "--save_path", "/path/to/kdb_results/SpaGCN/D3_151509_5k_cpu/cluster_results.csv"],
  "env": {"KDB_METHODS_DIR": "/path/to/kdomainbench/methods", "CUDA_VISIBLE_DEVICES": ""},
  "success": true,
  "n_spots": 4786,
  "k_estimated": 4
}
```

The record holds more fields than shown here. The Notes of
[`kdb.run`](../reference/run.md#kdomainbench.run) explain each one.
`kdb.read_clusters("kdb_results/SpaGCN/D3_151509_5k_cpu")` reads the labels back later.

A second run into the same folder replaces the first. To keep both, give the second one another
`out_root`, for example `kdb.run("DR.SC", h5ad, out_root="kdb_results_kmax20", kmax=20)`.

??? note "When a method fails"
    `kdb.run` raises `kdb.MethodFailed`. The message names the log and ends with its last lines:

    ```text
    MethodFailed: BayesSpace failed (exit 1), see /path/to/kdb_results/BayesSpace/D3_151509_5k_cpu/run.log
    ...
    ```

    `run_info.json` records the run with `"success": false`, also when the run was killed, for
    example by a time limit. [Troubleshooting](../how-to/troubleshooting.md) lists the common
    errors.

## Run several methods

```python
results = kdb.run_all(h5ad, kmax=30, device="cpu")
# {'PRECAST': <clusters>, 'SC.MEB': <clusters>, ...}
results = kdb.run_all(h5ad, methods=["DR.SC", "SC.MEB"])
```

The methods run one after another, each into its own run folder under the same `out_root`.
`run_all` reports a method that fails, or whose environment is missing, goes on with the next
one, and ends with one warning that names every method that did not finish.

## Inputs

The methods were written for 10x Visium data. The `.h5ad` file needs:

| Field | Used by | Content |
|---|---|---|
| `X` | all | **raw counts** (sparse or dense) |
| `obs_names` | all | unique spot barcodes. They become `spot_id` |
| `var_names` | all | gene names |
| `obs["array_row"]`, `obs["array_col"]` | PRECAST, SC.MEB, BayesSpace, BNPSpace, DR.SC, iSC.MEB | integer Visium grid coordinates |
| `obs["pixel_row"]`, `obs["pixel_col"]` | SpaGCN | pixel coordinates |
| `obsm["spatial"]` | CellCharter, DeepST, SpatialDE2, plotting | 2-D coordinates (spots × 2) |
| `obs["clusters"]` | scoring only (optional) | reference annotation: the annotated domain of each spot |

[Your own data](../how-to/own_data.md) builds such a file from a Space Ranger folder.

??? note "Other platforms than Visium"
    The R scripts build Visium (hexagonal) neighbor graphs, and CellCharter uses a 6-neighbor
    grid. For ST, Slide-seq or imaging data, change the `platform` argument in the R scripts
    under `src/kdomainbench/methods/`, or the CellCharter `spatial_neighbors` call.

## GPU or CPU?

CellCharter, DeepST and SpatialDE2 can run on a GPU. The examples below write to their own
`out_root`, so that [Evaluate a run](evaluate.md) compares the CPU runs only:

```python
kdb.run("CellCharter", h5ad, kmax=30, device="gpu", out_root="kdb_results_gpu")
# [kdomainbench] CellCharter on GPU (GPU 0) -> /path/to/kdb_results_gpu/CellCharter/D3_151509_5k_gpu
```

`gpu_id` picks the GPU ([reference entry](../reference/run.md#kdomainbench.run)), and
`kdomainbench check --gpu` tells you beforehand whether a GPU is visible.

The other seven methods have no GPU code. With `device="gpu"` they still run, on the CPU, and warn:

```python
kdb.run("PRECAST", h5ad, kmax=30, device="gpu", out_root="kdb_results_gpu")
# UserWarning: PRECAST has no GPU implementation. It runs on the CPU.
```

## Command line

```bash title="terminal"
kdomainbench run -m SpaGCN -i data/D3_151509_5k.h5ad -k 30 -d cpu
kdomainbench run -m CellCharter DeepST -i data/D3_151509_5k.h5ad -d gpu --gpu-id 0 -o kdb_results_gpu
kdomainbench run -m all -i data/D3_151509_5k.h5ad -d cpu
```

The runs go to the same folders as from Python, and `-o DIR` replaces `kdb_results`
([Command line](../reference/cli.md#kdomainbench-run)).

Next: [Evaluate a run](evaluate.md).
