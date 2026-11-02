# Quickstart

Five steps take you from finding a method to a figure of its domains. Step 3 runs a method;
it needs the environments from [Installation](installation.md). All outputs below are from real
runs on `D1_151507_4k.h5ad` ([Get the data](installation.md#get-the-data)).

??? tip "Words used on this site"
    spot
    :   One Visium capture spot: a row of the `.h5ad` file.

    spatial domain
    :   A group of spots with similar expression that also lie together, such as a cortical layer.

    k
    :   The number of spatial domains. The *true k* comes from the manual annotation; the
        *estimated k* is the number of distinct labels a method returns.

    kmax
    :   The largest k a method may consider. Most methods try K = 2 … kmax and pick one.

    ground truth
    :   The manual domain label of each spot, in `obs["clusters"]`.

    device
    :   `"cpu"` or `"gpu"`. Only CellCharter, DeepST and SpatialDE2 use a GPU.

    run folder
    :   The folder one run writes: `cluster_results.csv`, `run.log` and `run_info.json`.

    summary table
    :   One row per run, from `kdb.load_results`: method, device, estimated k, scores, time, memory.

!!! tip "Summary"
    ```python
    import kdomainbench as kdb

    # 1. the methods, and which can use a GPU
    kdb.list_methods()
    kdb.list_methods(gpu_only=True)

    # 2. the data: DLPFC sample 151507, true k = 7
    h5ad = "data/D1_151507_4k.h5ad"

    # 3. run a method
    clusters = kdb.run("SpaGCN", h5ad, kmax=30, device="cpu")

    # 4. score it against the ground truth
    kdb.evaluate(clusters, h5ad)

    # 5. plot its domains
    kdb.pl.plot_spatial(clusters, h5ad)
    ```

## Step 1: Discover methods

```python
import kdomainbench as kdb

kdb.list_methods()
# ['PRECAST', 'SC.MEB', 'BayesSpace', 'BNPSpace', 'DR.SC', 'iSC.MEB',
#  'CellCharter', 'DeepST', 'SpaGCN', 'SpatialDE2']
kdb.list_methods(gpu_only=True)
# ['CellCharter', 'DeepST', 'SpatialDE2']
```

`kdb.get_method` shows one method's settings:

```python
m = kdb.get_method("cellcharter")      # names are case-insensitive
m.language, m.env, m.gpu, m.uses_kmax
# ('Python', 'py', True, True)
```

[Discover methods](tutorials/discover.md) has the full table and how each method picks k.

## Step 2: Get the data

The test file comes with the code: `data/D1_151507_4k.h5ad` in the cloned repository
([Get the data](installation.md#get-the-data)). Run the steps below from the repository folder. It
is DLPFC sample 151507: 4 220 spots, 9 948 genes, and 7 annotated layers as the ground truth.

```python
h5ad = "data/D1_151507_4k.h5ad"
kdb.ground_truth(h5ad).value_counts()
# Layer3    1215
# Layer1     817
# Layer5     674
# Layer6     486
# Layer4     369
# WM         354
# Layer2     305
```

For your own data, see [Inputs](tutorials/run.md#inputs).

## Step 3: Run a method

`kdb.run` starts the method in its environment and returns one domain label per spot.

```python
clusters = kdb.run("SpaGCN", h5ad, kmax=30, device="cpu")
clusters.head(3)
#                    cluster
# spot_id
# AAACAACGAATAGTTC-1       2
# AAACAAGTATCTCCCA-1       0
# AAACAATCTACTAGCA-1       2
clusters["cluster"].nunique()     # estimated k
# 4
```

SpaGCN took 7.5 minutes on a CPU here. The run folder `kdb_results/SpaGCN/D1_151507_4k_cpu/` keeps the labels, the
method's log and `run_info.json` with the run time and peak memory.

??? note "Details"
    * `device="gpu"` runs CellCharter, DeepST and SpatialDE2 on GPU 0 (`gpu_id=` picks another).
      The other seven methods have no GPU code: they run on the CPU and warn.
    * DeepST and SpaGCN choose k by themselves and ignore `kmax`.
    * A failed method raises `kdb.MethodFailed` with the end of its log.

[Run a method](tutorials/run.md) covers the arguments, the run folder and your own data.

## Step 4: Evaluate the run

```python
kdb.evaluate(clusters, h5ad)
# {'k_estimated': 4, 'k_true': 7, 'k_error': -3,
#  'ARI': 0.42, 'NMI': 0.51, 'n_spots': 4220}
```

SpaGCN found 4 domains where the annotation has 7 (`k_error = -3`). ARI and NMI measure how well
its domains match the layers, whatever their number.

[Evaluate a run](tutorials/evaluate.md) explains the scores and how to compare many runs.

## Step 5: Plot

```python
kdb.pl.plot_spatial(clusters, h5ad, title="SpaGCN")
```

After several runs, collect them into one table and plot the estimated k of every method:

```python
summary = kdb.load_results("kdb_results")
kdb.pl.plot_k_estimates(summary)       # one dot per run, the true k dashed
```

[Load and plot results](tutorials/plot.md) shows every figure.

## Command line

The same steps without Python:

```bash title="terminal"
kdomainbench methods
kdomainbench run -m SpaGCN -i data/D1_151507_4k.h5ad -k 30 -d cpu
kdomainbench summarize --csv summary.csv --plot k.png
```

## Next steps

* Run every method and compare their k: [Benchmark the ten methods](tutorials/benchmark.md).
* Run the GPU methods on both devices: [CPU versus GPU](tutorials/cpu_vs_gpu.md).
* Bring your own Visium sample: [Your own data](tutorials/run.md#your-own-data).
* Every function and its parameters: [API reference](api.md).
