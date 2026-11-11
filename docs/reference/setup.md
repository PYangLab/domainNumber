# Setup

Tell kDomainBench where the method environments are. The `kdomainbench` command has its own
page, [Command line](cli.md).

| Name | Summary |
|---|---|
| [`kdb.set_env`](#kdomainbench.set_env) | Point one method environment at an interpreter, for this Python session. |
| [Environment variables](#environment-variables) | The same for every session, and the settings of PRECAST and SC.MEB. |

::: kdomainbench.set_env

## Environment variables

| Variable | Meaning | Default |
|---|---|---|
| `KDB_PY_PYTHON` | `python` of `kdb_py` | the conda env `kdb_py` |
| `KDB_SPATIALDE_PYTHON` | `python` of `kdb_spatialde` | the conda env `kdb_spatialde` |
| `KDB_RSCRIPT` | `Rscript` for the R methods | `Rscript` on `PATH` |
| `KDB_R_LIB` | separate R library. The R methods see only it and base R | none |
| `KDB_METRICS_RSCRIPT` | `Rscript` for the metric code, when it is not the R of the methods. `KDB_R_LIB` is not applied to it | the R of the methods |
| `PRECAST_CORES` | worker processes of PRECAST | 4 |
| `SCMEB_PARALLEL` | `TRUE` = run SC.MEB in parallel, as the original script did (faster, not reproducible) | `FALSE` |
| `SCMEB_CORES` | worker processes of SC.MEB when `SCMEB_PARALLEL=TRUE` | 3 |

Without the variables, the conda envs are looked for next to the environment `kdomainbench`
runs in, then under `$CONDA_EXE`, `$MAMBA_EXE`, `$CONDA_PREFIX` and `~/anaconda3`,
`~/miniconda3`, `~/mambaforge`, `~/miniforge3`, `~/.conda`. Environments created together by
`envs/install_envs.sh` are therefore found without any setting, also in a folder given with
`KDB_ENVS_DIR`.
