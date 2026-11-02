# kDomainBench

Benchmark of methods that estimate the **number of spatial domains (k)** in spatial
transcriptomics, behind one interface:

```python
import kdomainbench as kdb
clusters = kdb.run("CellCharter", "D1_151507_4k.h5ad", kmax=30, device="gpu")   # or device="cpu"
```

* 10 methods: PRECAST, SC.MEB, BayesSpace, BNPSpace, DR.SC, iSC.MEB (R); CellCharter, DeepST,
  SpaGCN, SpatialDE2 (Python).
* GPU: CellCharter, DeepST and SpatialDE2. With `device="gpu"`, the other seven warn and run on the CPU.
* 2 version-locked conda environments for the Python methods (`envs/`), the same on CPU-only and
  GPU machines; the R methods use your own R (packages: `Rscript envs/install_r_packages.R`).
* Results: `kdb.load_results`, `kdb.evaluate`, `kdb.k_accuracy`; plots in `kdb.pl`.

## Layout

```
src/kdomainbench/          package (run, results, plotting, CLI)
src/kdomainbench/methods/  one script per method (device is a flag, no CPU/GPU copies)
envs/                      kdb_py.yml, kdb_spatialde.yml, install_envs.sh; install_r_packages.R, kdb_r.lock.csv
docs/, mkdocs.yml          documentation site (mkdocs-material)
scripts/                   make_results_page.py, make_logo.py, check_docs.py
```

## Documentation

The repository is private, so the documentation site is built and viewed locally:

```bash
python -m venv .venv-docs && source .venv-docs/bin/activate
pip install -r docs/requirements.txt
mkdocs serve                      # open http://127.0.0.1:8000
```

On a remote server, forward the port first: `ssh -L 8000:127.0.0.1:8000 <user>@<server>`.
`mkdocs build` writes a static copy to `site/`; open `site/index.html` directly (search needs `mkdocs serve`).

Every code example of the docs can be executed with

```bash
python scripts/check_docs.py --h5ad D1_151507_4k.h5ad --reuse <finished runs> --work /tmp/check
```
