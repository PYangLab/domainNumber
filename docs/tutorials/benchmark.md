# Benchmark the ten methods

This tutorial runs all ten methods on sample 151509 and asks how close each one gets to the
reference domain number (reference k). The table and figures below show the runs of the paper's
benchmark on this sample, one per method.

!!! tip "Summary"
    ```python
    import kdomainbench as kdb
    h5ad = "data/D3_151509_5k.h5ad"

    results = kdb.run_all(h5ad, kmax=30, device="cpu", out_root="bench/")
    summary = kdb.load_results("bench/")
    kdb.k_accuracy(summary)
    kdb.pl.plot_k_estimates(summary)
    kdb.pl.plot_spatial_grid(results, h5ad)
    ```

## 1. The data

`D3_151509_5k.h5ad` is sample 151509 ([Example data](../installation.md#example-data)).
Its reference annotation has 7 domains, six cortical layers and white matter: **k = 7**.

```python
import kdomainbench as kdb

h5ad = "data/D3_151509_5k.h5ad"
reference = kdb.reference_annotation(h5ad).to_frame("cluster")
kdb.pl.plot_spatial(reference, h5ad, title="Reference annotation (k = 7)", legend=True)
```

![Reference annotation of sample 151509: six cortical layers and white matter](../assets/reference_annotation.png){ width="400" }

## 2. Run every method

```python
results = kdb.run_all(h5ad, kmax=30, device="cpu", out_root="bench/")
```

All ten ran with `kmax = 30` and otherwise as their
[method scripts](../overview.md#method-scripts) set them.

## 3. Estimated k and accuracy

```python
summary = kdb.load_results("bench/")
```

--8<-- "results_table.md"

The methods are sorted by the size of their *k error* (estimated k − reference k), then by
ARI. ARI and NMI compare the domains with the annotated ones
([Evaluate a run](evaluate.md#what-each-score-measures)). The raw numbers are in
[`summary_5k.csv`](../assets/summary_5k.csv).

![Estimated k of each method on sample 151509, with the reference k of 7 as a dashed line](../assets/k_estimates.png){ width="620" }

Blue dots are below the reference k and red ones above. A dot on it would be green.

* No method returned the reference k of 7. **PRECAST** came closest, with 5 domains.
* **BayesSpace, DeepST and SpaGCN** returned 4. DeepST has the highest ARI (0.54).
* **SC.MEB and SpatialDE2** returned 10. Five of SpatialDE2's domains have 7 spots or fewer.
* **DR.SC** returned 15 domains, the largest k error.
* **BNPSpace and CellCharter** returned 2 domains and **iSC.MEB** 3. BNPSpace put 4,610 of the
  4,786 spots in one domain (ARI 0.05).

## 4. The domains on the tissue

```python
fig = kdb.pl.plot_spatial_grid(results, h5ad, ncols=5)
```

![Spatial domains of the ten methods on sample 151509](../assets/spatial_domains.png)

Compare each map with the reference annotation above. A method with fewer domains merges
layers into broad bands, and one with more splits layers into patches. Colors follow the sorted
label names, so the same color in two maps does not mean the same domain.

## 5. The twelve metrics

`kdomainbench metrics` scores every run with the twelve metrics of the paper, and
`kdb.pl.plot_metrics` draws them:

```bash title="terminal"
kdomainbench metrics bench/
```

```python
summary = kdb.load_results("bench/")      # read again, now with the metrics
kdb.pl.plot_metrics(summary)
```

![The twelve metrics of the ten methods on sample 151509 as a matrix of bars](../assets/metrics.png)

A darker bar is a better rank among the ten methods
([Evaluate a run](evaluate.md#plot-the-metrics) explains the figure).

* **DeepST** ranks first in five of the six concordance metrics.
* **SC.MEB and DR.SC**, with 10 and 15 domains, rank first and second in purity, homogeneity
  and SCS, and among the last three in completeness, LISI, PAS and CHAOS.
* **BNPSpace**, which put nearly every spot in one domain, ranks last in seven metrics and
  first in completeness, LISI, PAS and CHAOS.

!!! note "One sample, one run"
    This page shows that the pipeline works end to end. One sample with one seed per method
    does not rank the methods. The runs shown are those of the paper's benchmark, where
    CellCharter and DeepST ran on a GPU. A run of yours can differ. On sample 151507, CPU runs
    through this package gave another k for CellCharter and DeepST (4 for both, against 3 and
    5) and other domains with the same k for BayesSpace, SC.MEB and SpaGCN (BayesSpace: ARI
    0.35 against 0.28). The other five methods scored the same. The paper's runs used another
    software environment, described in the paper, and the cause of the BayesSpace and SpaGCN
    differences was not isolated.

## Reproduce

```bash title="terminal"
kdomainbench run -m all -i data/D3_151509_5k.h5ad -k 30 -d cpu -o bench/
kdomainbench summarize bench/ --csv summary.csv --plot k.png
python scripts/make_results_page.py bench/ data/D3_151509_5k.h5ad    # this page's table and figures
```

The first command runs the methods one after another.
