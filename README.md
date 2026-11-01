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
* 3 environments (`envs/`), each with a version-locked file. Each environment works on both
  CPU-only and GPU machines.
* Results: `kdb.load_results`, `kdb.evaluate`, `kdb.k_accuracy`; plots in `kdb.pl`.

## Layout

```
src/kdomainbench/          package (run, results, plotting, CLI)
src/kdomainbench/methods/  one script per method (device is a flag, no CPU/GPU copies)
envs/                      kdb_py.yml, kdb_spatialde.yml, kdb_r.yml + kdb_r.lock.csv, install_envs.sh
docs/, mkdocs.yml          documentation site (mkdocs-material)
scripts/                   make_results_page.py, make_logo.py, check_docs.py
```

Documentation: https://liuchunlei0430.github.io/kDomainBench/

## Docs

```bash
pip install "mkdocs-material==9.5.*" "mkdocstrings[python]"
mkdocs serve                      # preview at http://127.0.0.1:8000
mkdocs gh-deploy --force          # publish to GitHub Pages
python scripts/check_docs.py --h5ad D1_151507_4k.h5ad --reuse <runs> --work /tmp/check   # run every doc example
```
