# Run a method

`kdb.run` runs one method on one `.h5ad` file in the method's own environment, waits for it,
and returns one domain label per spot.

!!! tip "Summary"
    ```python
    import kdomainbench as kdb
    h5ad = "data/D1_151507_4k.h5ad"

    clusters = kdb.run("SpaGCN", h5ad, kmax=30, device="cpu")
    clusters = kdb.run("CellCharter", h5ad, kmax=30, device="gpu", gpu_id=0)
    results  = kdb.run_all(h5ad, kmax=30)      # all ten
    ```

## Run one method

```python
clusters = kdb.run("SpaGCN", h5ad, kmax=30, device="cpu")
```

| Argument | Meaning |
|---|---|
| `method` | method name, case-insensitive; aliases such as `drsc`, `iscmeb`, `spatialde` work |
| `h5ad` | input `.h5ad` file (see [Inputs](#inputs)) |
| `kmax` | largest k the method may consider (default 30); DeepST and SpaGCN ignore it |
| `device` | `"cpu"` (default) or `"gpu"` |
| `gpu_id` | which GPU to use with `device="gpu"` (default 0, in PCI-bus order) |
| `out_dir` | run folder; default `kdb_results/<method>/<dataset>_<device>` |
| `verbose` | print the method's output while it runs (default `True`) |

## What run returns

A DataFrame indexed by `spot_id` with one `cluster` column:

```python
clusters.head(3)
#                    cluster
# spot_id
# AAACAACGAATAGTTC-1       2
# AAACAAGTATCTCCCA-1       0
# AAACAATCTACTAGCA-1       2
clusters["cluster"].value_counts().sort_index()
# 0    1522
# 1    1579
# 2     770
# 3     349
```

The number of distinct labels is the method's estimated k (here 4).

The run folder keeps everything about the run:

```text
kdb_results/SpaGCN/D1_151507_4k_cpu/
├── cluster_results.csv   # spot_id,cluster
├── run.log               # everything the method printed
└── run_info.json         # see below
```

```json title="run_info.json"
{
  "method": "SpaGCN",
  "dataset": "D1_151507_4k",
  "h5ad": "/path/to/kDomainBench/data/D1_151507_4k.h5ad",
  "kmax": 30,
  "device_requested": "cpu",
  "device_used": "cpu",
  "gpu_id": null,
  "returncode": 0,
  "wall_time_s": 451.18,
  "peak_rss_mb": 1413.9,
  "started": "2026-10-29T11:02:55",
  "command": ["/path/to/envs/kdb_py/bin/python", "/path/to/methods/run_spagcn.py",
              "--data_path", "/path/to/kDomainBench/data/D1_151507_4k.h5ad",
              "--save_path", "/path/to/kdb_results/SpaGCN/D1_151507_4k_cpu/cluster_results.csv"],
  "success": true,
  "n_spots": 4220,
  "k_estimated": 4
}
```

`wall_time_s` is the whole run, data loading included. `peak_rss_mb` is the peak host memory of
the method's process; GPU memory is not included. `command` is the exact call, to rerun the
method by hand. `kdb.read_clusters("kdb_results/SpaGCN/D1_151507_4k_cpu")` reads the labels back
later.

??? note "When a method fails"
    `kdb.run` raises `kdb.MethodFailed`. The message names the log and ends with its last lines:

    ```text
    MethodFailed: BayesSpace failed (exit 1); see /path/to/kdb_results/BayesSpace/D1_151507_4k_cpu/run.log
    ...
    ```

    `run_info.json` is written anyway, with `"success": false`.

## Run several methods

```python
results = kdb.run_all(h5ad, kmax=30, device="cpu")
# {'PRECAST': <clusters>, 'SC.MEB': <clusters>, ...}
results = kdb.run_all(h5ad, methods=["DR.SC", "SC.MEB"])
```

Each method gets its own run folder, `kdb_results/<method>/<dataset>_<device>`. `run_all` reports a
failed method and goes on with the next one. The methods run one after another.

## Inputs

The methods were written for 10x Visium data. The `.h5ad` file needs:

| Field | Used by | Content |
|---|---|---|
| `X` | all | **raw counts** (sparse or dense) |
| `obs_names` | all | unique spot barcodes; they become `spot_id` |
| `var_names` | all | gene names |
| `obs["array_row"]`, `obs["array_col"]` | PRECAST, SC.MEB, BayesSpace, BNPSpace, DR.SC, iSC.MEB | integer Visium grid coordinates |
| `obs["pixel_row"]`, `obs["pixel_col"]` | SpaGCN | pixel coordinates |
| `obsm["spatial"]` | CellCharter, DeepST, SpatialDE2, plotting | 2-D coordinates (spots × 2) |
| `obs["clusters"]` | scoring only (optional) | ground-truth domain labels |

## Your own data

A Space Ranger output folder becomes an input file in a few lines:

```python
import scanpy as sc

adata = sc.read_visium("path/to/spaceranger_out")
adata.var_names_make_unique()
adata = adata[adata.obs["in_tissue"] == 1].copy()

adata.obs["pixel_row"] = adata.obsm["spatial"][:, 1]
adata.obs["pixel_col"] = adata.obsm["spatial"][:, 0]
adata.obs["array_row"] = adata.obs["array_row"].astype(int)
adata.obs["array_col"] = adata.obs["array_col"].astype(int)
# adata.obs["clusters"] = <manual annotation>, if you have one

adata.write_h5ad("my_sample.h5ad")
```

Then run it like the tutorial data. Without `obs["clusters"]`, kDomainBench still records the
estimated k, run time and memory, but cannot score the labels.

??? note "Other platforms than Visium"
    The R scripts build Visium (hexagonal) neighbor graphs, and CellCharter uses a 6-neighbor
    grid. For ST, Slide-seq or imaging data, change the `platform` argument in the R scripts
    under `src/kdomainbench/methods/`, or the CellCharter `spatial_neighbors` call.

## GPU or CPU?

CellCharter, DeepST and SpatialDE2 can run on a GPU; `gpu_id` picks which one:

```python
kdb.run("CellCharter", h5ad, kmax=30, device="gpu", gpu_id=0)
```

The other seven methods have no GPU code. With `device="gpu"` they still run, on the CPU, and warn:

```python
kdb.run("PRECAST", h5ad, kmax=30, device="gpu")
# UserWarning: PRECAST has no GPU implementation; running it on the CPU.
```

A GPU run is faster but can give a different result: on the 4k sample, DeepST found k = 4 on
the CPU and k = 5 on the GPU. Compare methods on the same device.

## Command line

```bash title="terminal"
kdomainbench run -m SpaGCN -i data/D1_151507_4k.h5ad -k 30 -d cpu
kdomainbench run -m CellCharter DeepST -i data/D1_151507_4k.h5ad -d gpu --gpu-id 0
kdomainbench run -m all -i data/D1_151507_4k.h5ad -d cpu
```

Without `-o`, every run goes to `kdb_results/<method>/<dataset>_<device>`, as from Python, and
`kdomainbench summarize` reads `kdb_results/` by default. `-o DIR` changes the place: with one
method `DIR` is its run folder, with several each method writes to `DIR/<method>`, and with
`-m all` to `DIR/<method>/<dataset>_<device>`.

Next: [evaluate the run](evaluate.md).
