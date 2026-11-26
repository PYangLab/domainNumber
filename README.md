# kDomainBench

Benchmark of methods that estimate the **number of spatial domains (k)** in spatial
transcriptomics, behind one interface.

Many spatial clustering methods choose the number of domains themselves, but each needs its
own software, input format and settings, which makes them hard to run and to compare.
kDomainBench runs ten such methods from one Python call or one command, each in the
environment it needs, and compares the k each one estimates with the number of domains in a
manual reference annotation. It is for researchers who want to estimate k for their own 10x
Visium samples, or to compare k-estimation methods. It does not add a method of its own.

```python
import kdomainbench as kdb
clusters = kdb.run("SpaGCN", "data/D3_151509_5k.h5ad")
kdb.evaluate(clusters, "data/D3_151509_5k.h5ad")       # k error, ARI and NMI against the annotation
```

* 10 methods: PRECAST, SC.MEB, BayesSpace, BNPSpace, DR.SC and iSC.MEB in R, and CellCharter,
  DeepST, SpaGCN and SpatialDE2 in Python. CellCharter, DeepST and SpatialDE2 can use a GPU.
* 2 version-locked conda environments for the Python methods (`envs/`), the same on CPU-only and
  GPU machines. The R methods use your own R.
* Results: `kdb.load_results`, `kdb.evaluate`, `kdb.k_accuracy`. Plots: `kdb.pl`.
* `kdb.metrics`: the twelve metrics of the paper, computed by the paper's own R and Python code
  (R ≥ 4.5 with Bioconductor ≥ 3.22).
* The `kdomainbench` command does the same from the shell.

## Installation

The methods run on Linux (x86-64) and need conda or mamba, R ≥ 4.4, a C++ compiler, `cmake`
and `git`:

```bash
git clone https://github.com/PYangLab/domainNumber.git && cd domainNumber
bash envs/install_envs.sh                 # the two Python environments, with kdomainbench in kdb_py
Rscript envs/install_r_packages.R         # the R packages, into your R
conda activate kdb_py
kdomainbench check                        # checks that every environment starts
```

To score and plot finished runs on macOS or Windows, `pip install -e .` in the cloned folder,
with Python 3.10 or later, is enough. The documentation has the details (`docs/installation.md`).

## Documentation

The repository is private, so the documentation site is built and viewed locally, with
Python 3.11 or later:

```bash
python -m venv .venv-docs && source .venv-docs/bin/activate
pip install -r docs/requirements.txt
mkdocs serve                      # open http://127.0.0.1:8000
```

On a remote server, forward the port first: `ssh -L 8000:127.0.0.1:8000 <user>@<server>`.
`mkdocs build` writes a static copy to `site/`. Open `site/index.html` directly (search needs
`mkdocs serve`).

The site has a quickstart, tutorials, how-to guides (your own data, a cluster, troubleshooting),
an explanation of how the methods are run, and the API and command-line reference.

## Citation and contributing

The paper is in preparation. Until it is published, cite the repository, the package version
and the commit, and the publication of each method you run (`docs/citation.md`).
`CONTRIBUTING.md` says how to report a bug, set up a development copy, run the checks
(`.github/workflows/checks.yml` runs the unit tests and the site build on every push) and
propose a change. `CHANGELOG.md` lists the changes.

## Third-party code

* `src/kdomainbench/methods/bnpspace_R/`: BNPSpace's code, MIT license (its `LICENSE` file).
* The PASTE section of `src/kdomainbench/metric_scripts/scs.py`: copied from
  raphael-group/paste_reproducibility, whose repository has no license file.
* `docs/javascripts/vendor/gsap.min.js`: GSAP 3.12.5, GreenSock Standard License, used by the
  documentation site only.

This repository is licensed under GPL-3.0 (see `LICENSE`).

## Layout

```
src/kdomainbench/                 package (run, results, plotting, CLI)
src/kdomainbench/methods/         one script per method (device is a flag, no CPU/GPU copies)
src/kdomainbench/metric_scripts/  the paper's metric code (metrics.R, scs.py), unchanged
envs/                             environment files and their install and export scripts
docs/, mkdocs.yml, snippets/      documentation site (mkdocs-material)
scripts/                          make_results_page.py, make_logo.py, check_docs.py
tests/                            unit tests and their small test files
```
