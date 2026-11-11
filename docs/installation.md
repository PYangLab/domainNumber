# Installation

`kdomainbench` is a Python package, installed into the `kdb_py` conda environment. The ten
methods run in three environments: two conda environments for the Python methods and your own
R for the R methods. kDomainBench starts each method in the right one.

| You need | For |
|---|---|
| Linux (x86-64) | running the methods. The environments are built for it |
| conda or mamba | the two Python environments, about 12 GB of disk |
| A C++ compiler, `cmake` and `git` | building `louvain` for SpaGCN, fetching SpatialDE2, and the R packages |
| R ≥ 4.4 | the six R methods. The four Python methods run without it |
| R ≥ 4.5 with Bioconductor ≥ 3.22 (optional) | the twelve metrics of the paper ([The metric packages](#the-metric-packages)) |
| An NVIDIA GPU (optional) | CellCharter, DeepST and SpatialDE2 can use one |

!!! info "Before you start"
    Most users install kDomainBench on a Linux server or cluster. If you do not manage the
    server yourself, ask its administrators whether conda (or mamba) and R are available,
    for example as modules (`module avail`). Without conda, install
    [Miniforge](https://conda-forge.org/download/) in your home folder, then run
    `conda init bash` once and open a new terminal. For a cluster, see also
    [Run on a cluster](how-to/cluster.md).

!!! note "macOS and Windows"
    The methods run on Linux only. To score and plot finished runs on another system, a plain
    Python environment with Python 3.10 or later is enough (tested on macOS), in the cloned
    folder. The Python that comes with macOS is 3.9 (`python3 --version` shows it), so install
    Miniforge first, as in Before you start:

    ```bash
    python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -e .
    ```

    For the twelve metrics of the paper, also name a Python with anndata, networkx, scipy and
    pandas below 3 in `KDB_PY_PYTHON` ([The metric packages](#the-metric-packages)).

!!! tip "Summary"
    ```bash
    git clone https://github.com/liuchunlei0430/kDomainBench.git && cd kDomainBench
    bash envs/install_envs.sh                 # the two Python environments
    Rscript envs/install_r_packages.R         # the R packages, into your R
    conda activate kdb_py
    kdomainbench check                        # checks that every environment starts
    ```

## Step 1: Get the code

```bash title="terminal"
git clone https://github.com/liuchunlei0430/kDomainBench.git
cd kDomainBench
```

The repository holds the package (`src/kdomainbench/`), one script per method
(`src/kdomainbench/methods/`), the environment files (`envs/`) and the example file
(`data/`, see [Example data](#example-data)).

!!! note "Private repository"
    The repository is private. `git clone` asks for your GitHub login and works only for
    members. Use a [personal access token](https://github.com/settings/tokens) as the password,
    or clone over SSH (`git@github.com:liuchunlei0430/kDomainBench.git`).

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

`KDB_ENVS_DIR=/project/envs bash envs/install_envs.sh` creates them in that folder instead of
conda's default one, for example to keep them out of a small home folder.

!!! success "One set of environments for CPU and GPU machines"
    On a GPU machine the environments need only an NVIDIA driver (≥ 525). The GPU libraries
    come with them, so no separate CUDA install is needed. Without a GPU, they run on the CPU.

### R

The R methods use the R you already have (R ≥ 4.4, with Bioconductor 3.19 or later, the
repository of R packages for genomics).
`Rscript -e 'R.version.string'` prints its version. Install the packages the methods need:

```bash title="terminal"
Rscript envs/install_r_packages.R
```

The script installs only what is missing, from CRAN and Bioconductor, at their current
versions. It installs into R's main library, or into your personal library when the main one
is read-only, as with an R from a module.

| Source | Packages |
|---|---|
| CRAN | PRECAST, DR.SC, iSC.MEB, Seurat, Rcpp, RcppArmadillo, flexclust, philentropy, fastcluster, dynamicTreeCut, purrr, deldir, glue, ggplot2, mclust (plus remotes and BiocManager to install the rest) |
| Bioconductor | BayesSpace, zellkonverter, SingleCellExperiment, SummarizedExperiment, scran, scater, scuttle, BiocSingular |
| CRAN archive | SC.MEB 1.1 (no longer on CRAN) |

BNPSpace is not a package. Its C++ code ships with kDomainBench and is compiled at the start
of each run.

??? note "A separate R library"
    To keep these packages apart from your other R work, give the script a folder and tell
    kDomainBench about it. The R methods then see only this library and base R.

    ```bash title="terminal"
    Rscript envs/install_r_packages.R /project/kdb_rlib
    export KDB_R_LIB=/project/kdb_rlib
    ```

??? note "The R versions behind this site's results"
    The results on this site were produced with R 4.4.1, Bioconductor 3.19, PRECAST 1.7,
    DR.SC 3.6, iSC.MEB 1.0, SC.MEB 1.1, BayesSpace 1.14.0, Seurat 5.3.0 and zellkonverter
    1.14.1. `envs/kdb_r.lock.csv` lists every R package with its version. Unlike the Python
    environments, your R is not pinned to these versions, so a newer package can give
    different domains.

### The metric packages

This step is optional. `kdb.evaluate` scores a run with k error, ARI and NMI and needs nothing
more. The twelve metrics of the paper ([Evaluate a run](tutorials/evaluate.md#the-twelve-metrics-of-the-paper))
are computed by the paper's R code, which needs these packages:

| Source | Packages |
|---|---|
| CRAN | clevr, aricode, ClusterR |
| Bioconductor | spARI, zellkonverter, SummarizedExperiment, HDF5Array, rhdf5 |
| GitHub, at the commits used for the paper | lisi, SPARK, SpatialPCA |

spARI is in Bioconductor from release 3.22, which needs R ≥ 4.5. The command that installs
them depends on your R:

| Your R (`Rscript -e 'BiocManager::version()'` gives the Bioconductor release) | What to do |
|---|---|
| R ≥ 4.5 on Bioconductor ≥ 3.22 | `Rscript envs/install_r_packages.R --metrics`. With a separate library, add its folder: `Rscript envs/install_r_packages.R --metrics $KDB_R_LIB` |
| R ≥ 4.5 on Bioconductor 3.21 | update Bioconductor first: `Rscript -e 'BiocManager::install(version = "3.22")'` |
| R 4.4 or older | install R ≥ 4.5 next to it and run `/path/to/R-4.5/bin/Rscript envs/install_r_packages.R --metrics`, then `export KDB_METRICS_RSCRIPT=/path/to/R-4.5/bin/Rscript` |

`kdomainbench check --metrics` computes the twelve metrics on a small test sample.

## Step 3: Verify the install

```bash title="terminal"
conda activate kdb_py
python -c "import kdomainbench as kdb; print(kdb.__version__)"    # the package version
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
    reads .h5ad files: 3 spots
```

For R it checks every package the method scripts load, then reads a small `.h5ad` file. The
first read downloads the reader that zellkonverter uses, which needs internet access once
([Troubleshooting](how-to/troubleshooting.md#the-first-r-run-is-slow-or-fails-without-internet)).

An environment that is missing or broken prints `MISSING` or `FAILED` with the reason, and the
command exits with an error. On a GPU machine, `kdomainbench check --gpu` should report
`CUDA available: True` and `GPUs: 1`, and fails when no GPU is visible. With `--metrics` it
also checks the metric packages.

## Example data

The tutorials use the DLPFC Visium sample **151509** from the spatialLIBD study
([Maynard et al., *Nature Neuroscience* 2021](https://doi.org/10.1038/s41593-020-00787-0) and
[spatialLIBD](http://spatial.libd.org/spatialLIBD/)). Each spot carries the study's manual
annotation of six cortical layers (Layer1–Layer6) and white matter (WM). This is the reference
annotation. It has 7 domains, so the reference domain number is **k = 7**.

The file comes with the code as `data/D3_151509_5k.h5ad` (14 MB). It is the benchmark's copy of
the sample, filtered beforehand. It holds 4,786 spots and the 10,486 genes that had at least
100 UMIs when the file was built (`var["n_counts"]`). The script that built it is not in this
repository.

??? note "What the file contains"
    * `X`: raw UMI counts
    * `obs["array_row"]`, `obs["array_col"]`: Visium grid coordinates
    * `obsm["spatial"]`: 2-D spot coordinates
    * `obs["clusters"]`: the annotated domain of each spot (`Layer1` … `Layer6`, `WM`)
    * `obs["pixel_row"]`, `obs["pixel_col"]`: pixel coordinates (read by SpaGCN)

    [Run a method](tutorials/run.md#inputs) lists which field each method reads.

When a step fails, see [Troubleshooting](how-to/troubleshooting.md).
