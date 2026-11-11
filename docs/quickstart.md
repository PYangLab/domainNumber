# Quickstart

Five steps take you from finding a method to a figure of its domains. Only step 3 runs a
method. It needs Linux and the environments from [Installation](installation.md). The outputs
shown are those of the paper's benchmark run on sample 151509
([Example data](installation.md#example-data)), and a run of yours can differ a little
([FAQ](faq.md#will-i-get-the-same-result-twice)).

For a sample of your own, with or without an annotation, see
[Your own data](how-to/own_data.md). [Key terms](#key-terms) at the end of this page explains
the words used on this site.

Run the code from the cloned repository folder, in Python or in Jupyter
([FAQ](faq.md#can-i-use-jupyter)), with the `kdb_py` environment active.

```python
import kdomainbench as kdb

# 1. the methods, and which can use a GPU
kdb.list_methods()                  # ['PRECAST', 'SC.MEB', ..., 'SpaGCN', 'SpatialDE2']
kdb.list_methods(gpu_only=True)     # ['CellCharter', 'DeepST', 'SpatialDE2']

# 2. the example data: DLPFC sample 151509, reference k = 7
h5ad = "data/D3_151509_5k.h5ad"

# 3. run a method
clusters = kdb.run("SpaGCN", h5ad, kmax=30, device="cpu")
clusters["cluster"].nunique()       # 4, the estimated k

# 4. score it against the reference annotation
kdb.evaluate(clusters, h5ad)
# {'k_estimated': 4, 'k_reference': 7, 'k_error': -3,
#  'ARI': 0.4487, 'NMI': 0.5694, 'n_spots_scored': 4786}

# 5. plot its domains and save the figure
ax = kdb.pl.plot_spatial(clusters, h5ad, title="SpaGCN")
ax.figure.savefig("spagcn.png", dpi=150, bbox_inches="tight")
```

1. [Discover methods](tutorials/discover.md) covers the method table and how each method picks k.
2. [Run a method](tutorials/run.md) covers the arguments, the run folder, the input file and
   the GPU.
3. [Evaluate a run](tutorials/evaluate.md) covers what each score measures and how to compare
   many runs.

## Command line

The same steps without Python:

```bash title="terminal"
kdomainbench methods
kdomainbench run -m SpaGCN -i data/D3_151509_5k.h5ad -k 30 -d cpu
kdomainbench summarize --csv summary.csv --plot k.png
```

## Next steps

* [Benchmark the ten methods](tutorials/benchmark.md): every method on sample 151509,
  with the table and the figures.
* [Your own data](how-to/own_data.md): from a Space Ranger folder to domains on the tissue.
* [API reference](api.md): every function and its parameters.

## Key terms

`.h5ad` file
:   The file format of AnnData, which scanpy uses: the counts of one sample, with `obs` (one
    row per spot), `var` (one row per gene) and `obsm["spatial"]` (the spot coordinates).

spot
:   One Visium capture spot: a row of the `.h5ad` file.

spatial domain
:   A group of spots with similar expression that also lie together, such as a cortical layer.

k
:   The number of spatial domains. The *estimated k* is the number of distinct labels a
    method returns.

reference annotation
:   The manual domain label of each spot, in `obs["clusters"]`. Its number of domains is
    the *reference domain number*, or reference k.

k error
:   Estimated k minus reference k. Negative means fewer domains than the annotation.

ARI, NMI
:   Two scores of how well a method's domains agree with the annotated ones. 1 is full
    agreement.

`kmax`
:   The largest k a method may consider, 30 by default. Most methods try k = 2 … `kmax`
    and pick one.

device
:   `"cpu"` or `"gpu"`. Only CellCharter, DeepST and SpatialDE2 can use a GPU.

conda environment
:   A folder with its own Python and packages. kDomainBench uses two, `kdb_py` and
    `kdb_spatialde` ([Installation](installation.md#step-2-create-the-environments)).

run folder
:   The folder one run writes: `cluster_results.csv`, `run.log`, `packages.txt` and
    `run_info.json` ([The run folder](tutorials/run.md#the-run-folder)).

summary table
:   One row per run, from `kdb.load_results`, with the method, the estimated k and the scores.
