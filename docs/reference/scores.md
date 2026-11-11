# Scores

Read runs back and score them against the reference annotation. These calls need only the
`kdomainbench` package, not the method environments, except `kdb.metrics`, which runs the
paper's metric code in R and in `kdb_py`.

| Name | Summary |
|---|---|
| [`kdb.read_clusters`](#kdomainbench.read_clusters) | Read the domains of one run. |
| [`kdb.reference_annotation`](#kdomainbench.reference_annotation) | Read the reference annotation: the annotated domain of each spot. |
| [`kdb.evaluate`](#kdomainbench.evaluate) | Score one run against the reference annotation. |
| [`kdb.metrics`](#kdomainbench.metrics) | Compute the twelve metrics of the paper for one finished run. |
| [`kdb.MetricsFailed`](#kdomainbench.MetricsFailed) | The metric code stopped with an error or returned no value. |
| [`kdb.load_results`](#kdomainbench.load_results) | Collect every run under a folder into one table. |
| [`kdb.k_accuracy`](#kdomainbench.k_accuracy) | Summarize how well each method estimates k. |

::: kdomainbench.read_clusters

::: kdomainbench.reference_annotation

::: kdomainbench.evaluate

::: kdomainbench.metrics

::: kdomainbench.MetricsFailed
    options:
      members: false

::: kdomainbench.load_results

::: kdomainbench.k_accuracy
