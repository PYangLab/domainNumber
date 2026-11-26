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

`kdomainbench --version` prints the package version, and `kdomainbench <command> --help` the
options below. [Environment variables](setup.md#environment-variables) tell the command where
the environments are.

| Exit status | Meaning |
|---|---|
| 0 | Done. `summarize` also returns 0 when runs failed or could not be scored, as long as one run succeeded: its `not scored` lines say why. |
| 1 | An environment is missing or fails (`check`, `run`), a method did not finish (`run`), a metric could not be computed (`metrics`), no run succeeded (`metrics`, `summarize`), a file or folder was not found, or a value cannot be used (an unknown method, a `kmax` a method does not accept, an `--h5ad` file that matches no run). |
| 2 | The command line cannot be parsed: an unknown command or option, a missing argument, a value of the wrong kind (`-k abc`, `-d tpu`). The usage line is printed. |
| 128 + signal | `run` was stopped by a signal, for example by `scancel` or a time limit. |

A fatal error is one line that starts with `kdomainbench: error:`. `run` names the methods that
did not finish in a `kdomainbench: warning:` line, and `check` marks an environment as `MISSING`
or `FAILED`.

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
| `--gpu-id N` | GPU to make visible with `--gpu`. Default: those in `CUDA_VISIBLE_DEVICES`, else 0. |
| `--metrics` | Also compute the twelve metrics on a small test sample. |

## kdomainbench run

```text
kdomainbench run -m METHOD [METHOD ...] -i FILE [-k KMAX] [-d {cpu,gpu}] [--gpu-id N] [-o DIR]
```

Runs the methods one after another, as [`kdb.run_all`](run.md#kdomainbench.run_all) does.

| Option | Meaning |
|---|---|
| `-m`, `--method` | Method names as `kdomainbench methods` prints them (case-insensitive), or `all` for all ten. |
| `-i`, `--input` | Input `.h5ad` file. |
| `-k`, `--kmax` | Largest number of domains a method may consider, at least 2. Default: 30. BNPSpace accepts at most 30, and DeepST and SpaGCN do not use it. |
| `-d`, `--device` | `cpu` or `gpu`. A method without GPU code runs on the CPU and warns. Default: `cpu`. |
| `--gpu-id N` | GPU for `-d gpu`. Default: those in `CUDA_VISIBLE_DEVICES`, else 0. |
| `-o`, `--out` | Results folder. Each run goes to `DIR/<method>/<dataset>_<device>` and replaces a run already there. Default: `kdb_results`. |

```bash title="terminal"
kdomainbench run -m SpaGCN DR.SC -i data/D3_151509_5k.h5ad -k 30
```

## kdomainbench metrics

```text
kdomainbench metrics [--h5ad FILE] [--force] [root]
```

Prints the twelve metrics of the paper for every finished run under `root`, one row per run
([Evaluate a run](../tutorials/evaluate.md#the-twelve-metrics-of-the-paper)). A run without
`metric.csv` is computed first, which needs the metric packages
([Installation](../installation.md#the-metric-packages)) and the annotation in `obs["clusters"]`.

| Option | Meaning |
|---|---|
| `root` | Results folder. Default: `kdb_results`. |
| `--h5ad FILE` | An input file named `<dataset>.h5ad`, for runs whose recorded input file is not on this machine: `D3_151509_5k.h5ad` for the runs of `D3_151509_5k`. Repeat it for several datasets. |
| `--force` | Compute again for runs that already have `metric.csv`. |

## kdomainbench summarize

```text
kdomainbench summarize [--h5ad FILE] [--reference-key COLUMN] [--csv FILE] [--plot FILE] [root]
```

Prints the main columns of the summary table of every run under `root`, why runs could not be
scored, and the `k_accuracy` table ([Evaluate a run](../tutorials/evaluate.md#score-many-runs)).

| Option | Meaning |
|---|---|
| `root` | Results folder. Default: `kdb_results`. |
| `--h5ad FILE` | An input file named `<dataset>.h5ad`, as for `metrics`. |
| `--reference-key COLUMN` | `obs` column with the reference annotation. Default: `clusters`. |
| `--csv FILE` | Also save the table of runs, with every column, as a CSV file. |
| `--plot FILE` | Also save the k-estimate figure. The extension gives the format (PNG, PDF, SVG). |

```bash title="terminal"
kdomainbench summarize --csv summary.csv --plot k.png
```
