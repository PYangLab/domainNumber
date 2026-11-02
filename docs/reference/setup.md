# Setup

Tell kDomainBench where the method environments are, and use it from the shell.

::: kdomainbench.set_env

## Environment variables

| Variable | Meaning | Default |
|---|---|---|
| `KDB_PY_PYTHON` | `python` of `kdb_py` | the conda env `kdb_py` |
| `KDB_SPATIALDE_PYTHON` | `python` of `kdb_spatialde` | the conda env `kdb_spatialde` |
| `KDB_RSCRIPT` | `Rscript` for the R methods | `Rscript` on `PATH` |
| `KDB_R_LIB` | isolated R library; the R methods see only it and base R | none |
| `PRECAST_CORES` | worker processes of PRECAST | 4 |
| `SCMEB_PARALLEL` | `TRUE` = run SC.MEB in parallel, as the original script did (faster, not reproducible) | `FALSE` |
| `SCMEB_CORES` | worker processes of SC.MEB when `SCMEB_PARALLEL=TRUE` | 3 |

The conda envs are looked for under `$CONDA_EXE`, `$MAMBA_EXE`, `$CONDA_PREFIX` and
`~/anaconda3`, `~/miniconda3`, `~/mambaforge`, `~/miniforge3`, `~/.conda`.

## Command line

| Command | Does |
|---|---|
| `kdomainbench methods` | Print the methods: language, environment, GPU, use of `kmax`. |
| `kdomainbench check [--gpu] [--gpu-id N]` | Start each environment once and print its key packages; with `--gpu`, with GPU `N` visible. |
| `kdomainbench run -m M [M …] -i FILE [-k KMAX] [-d cpu\|gpu] [--gpu-id N] [-o DIR]` | Run methods; `-m all` runs all ten. |
| `kdomainbench summarize [ROOT] [--csv FILE] [--plot FILE]` | Print the summary table and `k_accuracy`; save the table and the k figure. |

```bash title="terminal"
kdomainbench check --gpu --gpu-id 0
kdomainbench run -m all -i data/D1_151507_4k.h5ad -k 30 -d cpu
kdomainbench summarize --csv summary.csv --plot k.png
```
