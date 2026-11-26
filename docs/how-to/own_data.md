# Your own data

This guide takes one 10x Visium sample from its Space Ranger folder to spatial domains on the
tissue. It needs no annotation. If you have one, the last step also scores the methods.
[Key terms](../quickstart.md#key-terms) explains the words used here, such as `kmax`.

!!! tip "Summary"
    ```python
    import kdomainbench as kdb
    h5ad = "my_sample.h5ad"                         # built in step 1

    results = kdb.run_all(h5ad, methods=["DR.SC", "SpaGCN", "iSC.MEB"], out_root="my_results/")
    summary = kdb.load_results("my_results/")       # the k of each method
    kdb.pl.plot_k_estimates(summary)
    kdb.pl.plot_spatial_grid(results, h5ad)         # their domains on the tissue
    ```

## 1. Make the input file

Space Ranger writes one `outs/` folder per sample. Start Python in the `kdb_py` environment
(`conda activate kdb_py`), which has scanpy, and turn the folder into one `.h5ad` file:

```python
import scanpy as sc

adata = sc.read_visium("path/to/sample/outs")     # reads filtered_feature_bc_matrix.h5 and spatial/
adata.var_names_make_unique()
adata = adata[adata.obs["in_tissue"] == 1].copy()

adata.obs["pixel_row"] = adata.obsm["spatial"][:, 1]
adata.obs["pixel_col"] = adata.obsm["spatial"][:, 0]
adata.obs["array_row"] = adata.obs["array_row"].astype(int)
adata.obs["array_col"] = adata.obs["array_col"].astype(int)

adata.write_h5ad("my_sample.h5ad")
print(adata)
# AnnData object with n_obs × n_vars = <spots> × <genes>
#     obs: 'in_tissue', 'array_row', 'array_col', 'pixel_row', 'pixel_col'
#     var: 'gene_ids', 'feature_types', 'genome'
#     uns: 'spatial'
#     obsm: 'spatial'
```

The file now holds the raw counts and the three sets of coordinates the methods read
([Inputs](../tutorials/run.md#inputs)). Keep the counts raw. The method scripts expect them and
do their own normalization.

## 2. Run methods

Start with three methods to see that everything works:

```python
import kdomainbench as kdb

h5ad = "my_sample.h5ad"
results = kdb.run_all(h5ad, methods=["DR.SC", "SpaGCN", "iSC.MEB"], out_root="my_results/")
```

Each method prints its output and, when it finishes, one line with its estimated k. A method
that fails is reported as `failed` or `not run` and does not stop the others
([Run several methods](../tutorials/run.md#run-several-methods)).

Each call runs the methods it names and leaves the other runs in `my_results/` alone, so more
methods can follow later, for example `methods=["PRECAST", "SC.MEB"]`. Without `methods`, all
ten run.

## 3. Read the result

`kdb.load_results` collects every run of the folder, in this session or a later one:

```python
summary = kdb.load_results("my_results/")
summary[["method", "k_estimated"]]
#     method  k_estimated
# 0    DR.SC           15
# 1   SpaGCN            4
# 2  iSC.MEB            3

ok = summary[summary["success"]]
results = {m: kdb.read_clusters(d) for m, d in zip(ok["method"], ok["out_dir"])}
```

The example output is that of the paper's benchmark runs on sample 151509. Without an
annotation the `k_error`, `ARI` and `NMI` columns are empty, and the `score_error` column says
`no reference annotation`.

Plot the estimates and the domains, and save the figures:

```python
ax = kdb.pl.plot_k_estimates(summary)                      # one dot per method
ax.figure.savefig("k_estimates.png", dpi=150, bbox_inches="tight")

fig = kdb.pl.plot_spatial_grid(results, h5ad, ncols=3)     # one map per method
fig.savefig("domains.png", dpi=150)

kdb.pl.plot_spatial(results["SpaGCN"], h5ad, legend=True)  # one method, with its labels named
```

### The methods will disagree

Different methods return different numbers of domains for the same sample
([Benchmark the ten methods](../tutorials/benchmark.md#3-estimated-k-and-accuracy)).
Read the estimates as candidates, not as the answer.

**Check the domain sizes.** A domain of a few spots adds to k without being a tissue region.

```python
{name: sorted(c["cluster"].value_counts(), reverse=True) for name, c in results.items()}
# {'DR.SC': [773, 718, 647, 468, 460, 270, 269, 236, 224, 157, 149, 137, 122, 106, 50],
#  'SpaGCN': [1556, 1513, 1288, 429],
#  'iSC.MEB': [3342, 1275, 169]}
```

**Check how far the methods agree.** The ARI between the domains of two methods is 1 when they
are the same and near 0 when they are no more alike than by chance:

```python
import pandas as pd

agreement = pd.DataFrame({a: {b: kdb.evaluate(results[a], results[b])["ARI"] for b in results}
                          for a in results})
agreement.round(2)
```

A cross table shows where two methods differ. Each row is a SpaGCN domain and each column a
DR.SC domain, so a row spread over two columns is a domain that DR.SC splits:

```python
pd.crosstab(results["SpaGCN"]["cluster"].rename("SpaGCN"), results["DR.SC"]["cluster"].rename("DR.SC"))
```

**Compare each map with what you know of the tissue**: the histology image, marker genes, the
expected anatomy. This draws the domains on the image:

```python
import matplotlib.pyplot as plt
import scanpy as sc

adata = sc.read_h5ad(h5ad)
for name, labels in results.items():
    adata.obs[name] = labels["cluster"].reindex(adata.obs_names).astype("category")
sc.pl.spatial(adata, color=["SpaGCN", "DR.SC"], show=False)    # add a gene name to see a marker gene
plt.savefig("domains_on_image.png", dpi=150, bbox_inches="tight")
```

Keep `kmax` the same across the methods that use it, and report the k of every method you
ran, not one number chosen afterwards. This site does not rank the methods. The paper compares
them across many datasets ([Citation](../citation.md)).

## 4. If you have an annotation

A manual annotation, for example exported from Loupe Browser as a CSV file with one row per
barcode, becomes the reference annotation in `obs["clusters"]`:

```python
import anndata as ad
import pandas as pd

adata = ad.read_h5ad("my_sample.h5ad")
labels = pd.read_csv("annotation.csv", index_col=0).iloc[:, 0]     # barcode, label
labels.index.isin(adata.obs_names).mean()                           # 1.0: every barcode is a spot of the file
adata.obs["clusters"] = labels.reindex(adata.obs_names)             # spots without a label stay empty
adata.write_h5ad("my_sample.h5ad")
```

The runs need not be repeated. `load_results` reads the annotation from the file and now scores
each run:

```python
summary = kdb.load_results("my_results/")
summary[["method", "k_estimated", "k_reference", "k_error", "ARI", "NMI"]]
kdb.k_accuracy(summary)
```

[Evaluate a run](../tutorials/evaluate.md) explains the scores.
