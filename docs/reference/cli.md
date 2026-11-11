# Command line

The `kdomainbench` command does from the shell what the Python API does. It is installed with
the package, in `kdb_py`.

| Command | Does | Python |
|---|---|---|
| [`kdomainbench methods`](#kdomainbench-methods) | Print the methods: language, environment, GPU, use of `kmax`. | [`kdb.list_methods`](methods.md#kdomainbench.list_methods) |
| [`kdomainbench check`](#kdomainbench-check) | Start each environment once and print its key packages. | |
| [`kdomainbench run`](#kdomainbench-run) | Run methods on an `.h5ad` file. | [`kdb.run_all`](run.md#kdomainbench.run_all) |
| [`kdomainbench metrics`](#kdomainbench-metrics) | Compute the twelve metrics of every finished run. | [`kdb.metrics`](scores.md#kdomainbench.metrics) |
| [`kdomainbench summarize`](#kdomainbench-summarize) | Score every run and print the tables. | [`kdb.load_results`](scores.md#kdomainbench.load_results), [`kdb.k_accuracy`](scores.md#kdomainbench.k_accuracy) |

`check`, `run`, `metrics` and `summarize` exit with an error code when an environment is
missing, a method did not finish, a metric could not be computed or no run succeeded, so a job
script can test it. `kdomainbench --version` prints the package version, and
`kdomainbench <command> --help` the options below.

## kdomainbench methods

```text
kdomainbench methods
```

Prints one line per method ([Discover methods](../tutorials/discover.md#list-the-methods)).

## kdomainbench check

```text
kdomainbench check [--gpu] [--gpu-id N] [--metrics]
```

Starts each environment once, prints its key packages, looks for every R package the method
scripts load and reads a small `.h5ad` file from R ([Installation](../installation.md#step-3-verify-the-install)).

| Option | Meaning |
|---|---|
| `--gpu` | Check with the GPU visible, and fail when none is. |
| `--gpu-id N` | GPU to make visible. Default: those in `CUDA_VISIBLE_DEVICES`, else 0. |
| `--metrics` | Also compute the twelve metrics on a small test sample. |

## kdomainbench run

```text
kdomainbench run -m METHOD [METHOD ...] -i FILE [-k KMAX] [-d {cpu,gpu}] [--gpu-id N] [-o DIR]
```

Runs the methods one after another, as [`kdb.run_all`](run.md#kdomainbench.run_all) does.

| Option | Meaning |
|---|---|
| `-m`, `--method` | Method names, or `all` for all ten. |
| `-i`, `--input` | Input `.h5ad` file. |
| `-k`, `--kmax` | Largest number of domains a method may consider. Default: 30. |
| `-d`, `--device` | `cpu` or `gpu`. Default: `cpu`. |
| `--gpu-id N` | GPU for `-d gpu`. Default: those in `CUDA_VISIBLE_DEVICES`, else 0. |
| `-o`, `--out` | Results folder. Each run goes to `DIR/<method>/<dataset>_<device>`. Default: `kdb_results`. |

```bash title="terminal"
kdomainbench run -m SpaGCN DR.SC -i data/D3_151509_5k.h5ad -k 30
```

## kdomainbench metrics

```text
kdomainbench metrics [--h5ad FILE] [--force] [root]
```

Computes the twelve metrics of the paper for every finished run under `root` that has no
`metric.csv` yet, and prints them ([Evaluate a run](../tutorials/evaluate.md#the-twelve-metrics-of-the-paper)).

| Option | Meaning |
|---|---|
| `root` | Results folder. Default: `kdb_results`. |
| `--h5ad FILE` | The input file, when the runs were made on another machine. It is used for the runs of the dataset of its name: `D3_151509_5k.h5ad` for those of `D3_151509_5k`. Repeat it for several datasets. |
| `--force` | Compute again for runs that already have `metric.csv`. |

## kdomainbench summarize

```text
kdomainbench summarize [--h5ad FILE] [--reference-key COLUMN] [--csv FILE] [--plot FILE] [root]
```

Prints the main columns of the summary table of every run under `root`, why runs could not be
scored, and the `k_accuracy` table ([Evaluate a run](../tutorials/evaluate.md#score-many-runs)).
`--csv` saves every column.

| Option | Meaning |
|---|---|
| `root` | Results folder. Default: `kdb_results`. |
| `--h5ad FILE` | The input file, when the runs were made on another machine, as for `metrics`. |
| `--reference-key COLUMN` | `obs` column with the reference annotation. Default: `clusters`. |
| `--csv FILE` | Also save the table of runs as a CSV file. |
| `--plot FILE` | Also save the k-estimate figure (PNG or PDF). |

```bash title="terminal"
kdomainbench summarize --csv summary.csv --plot k.png
```
