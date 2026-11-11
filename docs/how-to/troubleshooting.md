# Troubleshooting

Each section starts with the message you see. A failed run keeps its whole output in `run.log`
in its run folder, and a failed metric call in `metric.log`.

## A method stopped

```text
MethodFailed: <method> failed (exit <code>), see <run folder>/run.log
```

The method itself stopped. The message ends with the last lines of its log. `run_info.json`
records the run with `"success": false`.

## An environment is not found

```text
FileNotFoundError: conda env 'kdb_py' not found: create it with 'bash envs/install_envs.sh' ...
FileNotFoundError: Rscript not found: install R 4.4 or later, or load it ...
```

Create the environment ([Installation](../installation.md#step-2-create-the-environments)), or
point kDomainBench to it with the matching variable
([Environment variables](../reference/setup.md#environment-variables)).

## A variable points to the wrong file

```text
FileNotFoundError: KDB_PY_PYTHON points to <path>, which is not an interpreter
```

The variable holds a path that does not exist or cannot be executed. It must be the
environment's `python` (or `Rscript` for `KDB_RSCRIPT`), not its folder.

## The labels and the annotation share no spot

```text
ValueError: the clusters and the reference annotation share no spot. Both must be indexed by the same spot barcodes
```

The labels and the annotation use different spot barcodes, for example with and without the
`-1` suffix. Both must be indexed by the `obs_names` of the input file.

## The file has no annotation

```text
KeyError: no reference annotation: obs has no column 'clusters' (its columns: ...)
```

The input file has no `obs["clusters"]`. Add the annotation
([Your own data](own_data.md#4-if-you-have-an-annotation)), or name the column that holds it
with `reference_key=`.

## BNPSpace and `kmax`

```text
ValueError: BNPSpace accepts kmax up to 30
```

BNPSpace's own code allows at most 30 domains. Run it with `kmax=30` or less.

## The stack limit

```text
[kdomainbench] could not raise the stack limit ...
```

PRECAST and iSC.MEB need more stack memory than most systems allow by default, and
kDomainBench raises the limit for them (`ulimit -s unlimited`). This line in their log means
your system forbids it. The method may then stop with a stack error. Ask your administrator to
raise the hard stack limit (`ulimit -Hs` shows it).

## The first R run is slow, or fails without internet

zellkonverter reads `.h5ad` files through a Python environment that basilisk downloads on first
use into `~/.cache/R/basilisk`, several hundred MB. `kdomainbench check` triggers the download,
so run it once where there is internet. `BASILISK_EXTERNAL_DIR` moves the folder.

## Installing `louvain` fails

SpaGCN needs `louvain`, which has no prebuilt package (wheel) for Python 3.12, so `pip` builds it
from source. That needs a C++ compiler and `cmake` on `PATH`.

## PRECAST uses too many cores

It forks workers. `PRECAST_CORES` caps them (default 4).

## The twelve metrics fail

```text
MetricsFailed: metrics.R failed (exit 1), see <run folder>/metric.log
MetricsFailed: no value for SCS (PASTE's code returns no SCS with pandas 3 or later in kdb_py), see <run folder>/metric.log
```

The first is most often a missing R package: install them as in
[The metric packages](../installation.md#the-metric-packages) and run
`kdomainbench check --metrics`. The second means the Python that runs `scs.py` has pandas 3 or
later. It must be `kdb_py`, or a Python named in `KDB_PY_PYTHON` with pandas below 3.

More questions: [FAQ](../faq.md).
