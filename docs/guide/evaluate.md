# Evaluate a run

A run gives one domain label per spot. `kdb.evaluate` compares them with the ground truth: how far
the estimated k is from the true k, and how well the domains match the annotated ones.

!!! tip "Summary"
    ```python
    import kdomainbench as kdb
    h5ad = "data/D1_151507_4k.h5ad"

    clusters = kdb.read_clusters("out/SpaGCN")       # or the return value of kdb.run
    kdb.evaluate(clusters, h5ad)                     # one run
    summary = kdb.load_results("out/")               # every run under out/, scored
    kdb.k_accuracy(summary)                          # one row per method
    ```

## Score one run

```python
clusters = kdb.read_clusters("out/SpaGCN")
kdb.evaluate(clusters, h5ad)
# {'k_estimated': 4, 'k_true': 7, 'k_error': -3,
#  'ARI': 0.42, 'NMI': 0.51, 'n_spots': 4220}
```

The second argument is the `.h5ad` file, whose `obs["clusters"]` holds the ground truth, or the
labels themselves as a Series indexed by spot:

```python
truth = kdb.ground_truth(h5ad)                       # obs["clusters"], NaN spots dropped
truth = kdb.ground_truth(h5ad, key="layer_guess")    # another column
kdb.evaluate(clusters, truth)
```

## What each score measures

| Score | Meaning | Best |
|---|---|---|
| `k_estimated` | number of distinct labels the method returned | — |
| `k_true` | number of distinct ground-truth labels | — |
| `k_error` | `k_estimated − k_true`; negative means too few domains | 0 |
| `ARI` | adjusted Rand index between the labels and the ground truth | 1 |
| `NMI` | normalized mutual information between the labels and the ground truth | 1 |
| `n_spots` | spots scored: those with both a label and a ground-truth label | — |

??? note "Details"
    * `k_error` is the main score of the benchmark: the question is how many domains there are.
      ARI and NMI tell whether the domains found are the right ones.
    * A method can get k right with poor domains, or k wrong with good ones. On the 4k sample,
      DR.SC found k = 7 with ARI 0.47, while DeepST found k = 4 with a higher ARI, 0.55.
    * ARI and NMI do not depend on the label names: `0, 1, 2` and `Layer1, Layer2, Layer3` are
      compared by grouping only.

## Score many runs

`kdb.load_results` reads every `run_info.json` under a folder and scores each successful run
against its own `.h5ad` file. The result has one row per run:

```python
summary = kdb.load_results("out/")
summary[["method", "device_used", "k_estimated", "k_true", "k_error",
         "ARI", "NMI", "wall_time_s", "peak_rss_mb"]]
#         method device_used  k_estimated  k_true  k_error   ARI   NMI  wall_time_s  peak_rss_mb
#       BNPSpace         cpu            1       7       -6  0.00  0.00      2508.43       5303.4
#     BayesSpace         cpu            3       7       -4  0.35  0.56      3209.30      12029.7
#    CellCharter         cpu            4       7       -3  0.49  0.65       978.14       2068.9
#          DR.SC         cpu            7       7        0  0.47  0.58       460.59       2378.4
#         DeepST         cpu            4       7       -3  0.55  0.68      3233.28       2932.7
#        PRECAST         cpu            2       7       -5  0.17  0.31      4362.37       3529.8
#         SC.MEB         cpu            7       7        0  0.41  0.53       588.43       2649.6
#         SpaGCN         cpu            4       7       -3  0.42  0.51       451.18       1413.9
#     SpatialDE2         cpu           10       7        3  0.41  0.57      4156.90       2900.3
#        iSC.MEB         cpu            2       7       -5  0.18  0.33       203.39       2939.3
```

`kdb.k_accuracy` sums it up per method, best first:

```python
kdb.k_accuracy(summary)
#              runs  mean_abs_k_error  exact_rate  mean_ARI
# method
# DR.SC           1               0.0         1.0      0.47
# SC.MEB          1               0.0         1.0      0.41
# DeepST          1               3.0         0.0      0.55
# CellCharter     1               3.0         0.0      0.49
# SpaGCN          1               3.0         0.0      0.42
# SpatialDE2      1               3.0         0.0      0.41
# BayesSpace      1               4.0         0.0      0.35
# PRECAST         1               5.0         0.0      0.17
# iSC.MEB         1               5.0         0.0      0.18
# BNPSpace        1               6.0         0.0      0.00
```

| Column | Meaning |
|---|---|
| `runs` | successful runs with a ground truth |
| `mean_abs_k_error` | mean of \|k_error\| over the runs |
| `exact_rate` | fraction of runs with exactly the true k |
| `mean_ARI` | mean ARI over the runs |

??? note "Details"
    * Failed runs stay in `summary` with `success = False`; `k_accuracy` leaves them out.
    * `load_results(root, truth_key="layer_guess")` scores against another `obs` column;
      `score=False` skips scoring and only collects the run records.
    * `kdomainbench summarize out/ --csv summary.csv` prints both tables from the command line.

## Are the numbers comparable?

* **Run time and memory** depend on the machine and on what else runs on it. Compare them only
  between runs on the same machine, ideally run one at a time.
* **One run per method** does not show how much a method varies. Several methods are stochastic
  (MCMC, neural-network training); repeat runs, or several datasets, before ranking them.
* **`kmax`** changes the answer of the eight methods that use it. Keep it the same across methods
  (the benchmark uses 30).

Next: [load and plot results](plot.md).
