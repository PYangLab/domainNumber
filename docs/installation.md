# Installation

`kdomainbench` is a Python package. It runs on Linux, on CPU-only and GPU machines alike.
The package itself lives in the `kdb_py` environment. The Python methods run in two conda
environments, and the R methods in your own R. kDomainBench calls each for you.

!!! tip "Summary"
    ```bash
    git clone --single-branch https://github.com/liuchunlei0430/kDomainBench.git && cd kDomainBench
    bash envs/install_envs.sh                 # the two Python environments
    Rscript envs/install_r_packages.R         # the R packages, into your R
    conda activate kdb_py
    kdomainbench check                        # every environment answers
    ```

## Step 1: Get the code

```bash title="terminal"
git clone --single-branch https://github.com/liuchunlei0430/kDomainBench.git
cd kDomainBench
```

The repository holds the package (`src/kdomainbench/`), one script per method
(`src/kdomainbench/methods/`), the environment files (`envs/`) and the 4k test file
(`data/`). `--single-branch` skips the `data` branch, which holds 700 MB of larger test files
([Get the data](#get-the-data)).

## Step 2: Create the environments

Each method runs in one of three environments, so their dependencies never conflict:

| Environment | Methods | Main contents |
|---|---|---|
| `kdb_py` | CellCharter, DeepST, SpaGCN (and `kdomainbench` itself) | Python 3.12.8, torch 2.5.1 + CUDA 12.4, torch_geometric 2.8.1, scanpy 1.10.3, scvi-tools 1.4.1, cellcharter 0.3.7, deepstkit 2.0.3, SpaGCN 1.2.7, squidpy 1.8.3 |
| `kdb_spatialde` | SpatialDE2 | Python 3.10, tensorflow[and-cuda] 2.15.1, tensorflow-probability 0.23.0, gpflow 2.9.2, numpy 1.26.4, SpatialDE 2.0.0 |
| your R | PRECAST, SC.MEB, BayesSpace, BNPSpace, DR.SC, iSC.MEB | R ≥ 4.4 with the packages below |

### The Python environments

```bash title="terminal"
bash envs/install_envs.sh
```

This creates the conda environments `kdb_py` and `kdb_spatialde`, with the package versions
fixed in `envs/`, and installs the `kdomainbench` package into `kdb_py`. The script runs these
three commands, which you can also run yourself:

```bash title="terminal"
conda env create -n kdb_py        -f envs/kdb_py.yml
conda env create -n kdb_spatialde -f envs/kdb_spatialde.yml
conda run -n kdb_py pip install --no-deps -e .
```

!!! success "The same environments work on CPU and GPU machines"
    One set of environments serves both kinds of machine. On a GPU machine they need only an
    NVIDIA driver (≥ 525): the GPU libraries come with the environments, so no separate CUDA
    install is needed. Without a GPU, they run on the CPU. Together they take about 12 GB of disk.

### R

The R methods use the R you already have (R ≥ 4.4, Bioconductor 3.19 or later). Install the
packages they need into it:

```bash title="terminal"
Rscript envs/install_r_packages.R
```

The script installs only what is missing, from CRAN and Bioconductor, in the usual way:

| Source | Packages |
|---|---|
| CRAN | PRECAST, DR.SC, iSC.MEB, Seurat, Rcpp, RcppArmadillo, flexclust, philentropy, fastcluster, dynamicTreeCut, purrr, deldir, glue, ggplot2, cowplot |
| Bioconductor | BayesSpace, zellkonverter, SingleCellExperiment, scran, scater, scuttle, BiocSingular |
| CRAN archive | SC.MEB 1.1 (no longer on CRAN) |

BNPSpace is not a package: its C++ code ships with kDomainBench and is compiled on its first run.

??? note "The versions we used"
    The benchmark ran with R 4.4.1, Bioconductor 3.19, PRECAST 1.7, DR.SC 3.6, iSC.MEB 1.0,
    SC.MEB 1.1, BayesSpace 1.14.0, Seurat 5.3.0 and zellkonverter 1.14.1. `envs/kdb_r.lock.csv`
    lists every R package with its version.

??? note "Keep the R packages apart from your own"
    Install them into a separate library, and point kDomainBench at it:

    ```bash title="terminal"
    Rscript envs/install_r_packages.R ~/kdb_r/library
    export KDB_R_LIB=~/kdb_r/library
    ```

    With `KDB_R_LIB` set, the R methods see only this library and base R, not your user and
    site libraries.

??? note "Lock files"
    | File | What it locks |
    |---|---|
    | `envs/kdb_py.yml` | conda + pip packages of `kdb_py`, with the PyTorch cu124 and PyG wheel indexes |
    | `envs/kdb_spatialde.yml` | conda + pip packages of `kdb_spatialde`, with SpatialDE pinned to commit `6dbdb55` |
    | `envs/kdb_r.lock.csv` | the R packages and versions of the benchmark (reference) |

## Step 3: Verify the install

```bash title="terminal"
conda activate kdb_py
python -c "import kdomainbench as kdb; print(kdb.__version__)"    # 0.1.0
kdomainbench check
```

`kdomainbench check` starts each environment once and prints what it finds:

```text
[py] /opt/conda/envs/kdb_py/bin/python
    torch 2.5.1+cu124 | CUDA available: False
[spatialde] /opt/conda/envs/kdb_spatialde/bin/python
    tensorflow 2.15.1 | GPUs: 0
[r] /usr/bin/Rscript
    PRECAST 1.7
    SC.MEB 1.1
    BayesSpace 1.14.0
    DR.SC 3.6
    iSC.MEB 1.0
    zellkonverter 1.14.1
    RcppArmadillo 15.0.2.2
```

On a GPU machine, `kdomainbench check --gpu` should report `CUDA available: True` and `GPUs: 1`.

??? note "Where kDomainBench looks for the environments"
    By default it uses the conda environments `kdb_py` and `kdb_spatialde` under the usual conda
    roots, and `Rscript` from `PATH`. Environment variables override each of them:

    ```bash title="terminal"
    export KDB_PY_PYTHON=/path/to/envs/kdb_py/bin/python
    export KDB_SPATIALDE_PYTHON=/path/to/envs/kdb_spatialde/bin/python
    export KDB_RSCRIPT=/path/to/bin/Rscript
    export KDB_R_LIB=/path/to/isolated/R/library      # optional
    ```

    or, from Python, `kdb.set_env("r", "/usr/bin/Rscript", r_lib="/path/to/library")`.

## Get the data

The tutorials use the DLPFC Visium sample **151507** from the spatialLIBD study
([Maynard et al., *Nature Neuroscience* 2021](https://doi.org/10.1038/s41593-020-00787-0);
[spatialLIBD](http://spatial.libd.org/spatialLIBD/)). Its 4 220 spots carry the manual
cortical-layer annotation of the study, Layer1–Layer6 and white matter (WM), which is the
ground truth (**k = 7**).

| File | Spots | Size | Content | Where |
|---|---:|---:|---|---|
| `D1_151507_4k.h5ad` | 4 220 | 13 MB | sample 151507 | `main` branch, `data/` |
| `D1_151507_8k.h5ad` | 8 440 | 17 MB | 2 tiled copies of 151507 | `data` branch |
| `D1_151507_16k.h5ad` | 16 880 | 33 MB | 4 copies | `data` branch |
| `D1_151507_25k.h5ad` | 25 320 | 49 MB | 6 copies | `data` branch |
| `D1_151507_37k.h5ad` | 37 980 | 73 MB | 9 copies | `data` branch |
| `D1_151507_50k.h5ad` | 50 640 | 97 MB | 12 copies | `data` branch |
| `D1_151507_67k.h5ad` | 67 520 | 129 MB | 16 copies | `data` branch, 2 parts |
| `D1_151507_84k.h5ad` | 84 400 | 162 MB | 20 copies | `data` branch, 2 parts |
| `D1_151507_105k.h5ad` | 105 500 | 202 MB | 25 copies | `data` branch, 3 parts |

The larger files repeat sample 151507 as tiles (`obs["tile_id"]`), so the true k stays 7 while
the number of spots grows. They are for runtime and memory scaling; the tutorials use the 4k file.

The 4k file comes with the code: after Step 1 it is `data/D1_151507_4k.h5ad`. The larger files
are on the `data` branch of the same repository. Files over 100 MB are split into parts there
(GitHub's file size limit), so join them after the download:

```bash title="terminal"
git clone --branch data --single-branch --depth 1 \
    https://github.com/liuchunlei0430/kDomainBench.git kDomainBench-data
cd kDomainBench-data
for f in D1_151507_67k D1_151507_84k D1_151507_105k; do
    cat $f.h5ad.part* > $f.h5ad && rm $f.h5ad.part*
done
md5sum -c md5sums.txt          # every file: OK
```

!!! note "Private repository"
    The repository is private: `git clone` asks for your GitHub login, and works only for
    members. Use a [personal access token](https://github.com/settings/tokens) as the password,
    or clone over SSH (`git@github.com:liuchunlei0430/kDomainBench.git`).

??? note "What each file contains"
    * `X`: raw UMI counts, 9 948 genes
    * `obs["array_row"]`, `obs["array_col"]`: Visium grid coordinates
    * `obsm["spatial"]`: 2-D spot coordinates
    * `obs["clusters"]`: the ground-truth layer of each spot (`Layer1` … `Layer6`, `WM`)
    * `obs["pixel_row"]`, `obs["pixel_col"]`: pixel coordinates, **4k file only**. SpaGCN reads
      them, so it cannot run on the larger files as they are.

    [Run a method](guide/run.md#inputs) lists which field each method reads.

## Troubleshooting

`MethodFailed: <method> failed (exit <code>); see <run folder>/run.log`
:   The method itself stopped. The message ends with the last lines of its log; the whole log is
    `run.log` in the run folder.

`FileNotFoundError: conda env 'kdb_py' not found` or `Rscript not found`
:   kDomainBench did not find an environment. Create it (Step 2), or set the matching
    `KDB_*` variable (see *Where kDomainBench looks for the environments* above).

PRECAST or iSC.MEB crash with a stack error
:   Both need `ulimit -s unlimited`. kDomainBench sets it for them; if your hard limit forbids it,
    raise the limit or ask your administrator.

The first R run is slow
:   zellkonverter reads `.h5ad` files through a small Python environment that basilisk creates
    in `~/.cache/R/basilisk` on first use (about 100 MB).

Installing `louvain` fails
:   SpaGCN needs `louvain`, which has no wheel for Python 3.12 and is built from source. `pip`
    needs a C++ compiler and `cmake` on `PATH`.

PRECAST uses too many cores
:   It forks workers; `PRECAST_CORES` caps them (default 4).
