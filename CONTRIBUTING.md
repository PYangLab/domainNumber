# Contributing

Questions, bug reports and changes are welcome as issues and pull requests on GitHub:
<https://github.com/liuchunlei0430/kDomainBench/issues>.

## Ask a question or report a bug

Open an issue. For a run that failed or gave an unexpected result, attach:

* the output of `kdomainbench check`,
* `run_info.json`, `packages.txt` and the last 50 lines of `run.log` from the run folder,
* the operating system, and whether the run used a GPU.

## Make a change

Set up a development copy in the cloned folder. The package needs Python 3.10 or later, and
the site tools in `docs/requirements.txt` need Python 3.11 or later:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e . pytest -r docs/requirements.txt
```

Run the two checks before you open a pull request. They need no method environment and also run
on macOS:

```bash
python -m pytest                  # the unit tests
mkdocs build --strict             # the site builds, and every link and anchor resolves
```

Two more checks need more than a laptop:

* `KDB_TEST_METRICS=1 python -m pytest tests/test_metrics.py` computes the twelve metrics and
  compares them with the paper's values. It needs the metric R packages and `kdb_py`, and takes
  about 4 minutes.
* `python scripts/check_docs.py --h5ad data/D3_151509_5k.h5ad --reuse <finished runs> --work <scratch folder>`
  runs the code examples of the pages it lists and of the docstrings (not the home page, and
  not `kdb.metrics`, which the first check covers). It needs Linux with the environments and
  takes about an hour. It checks that each example runs, not that it prints the output the
  page shows.

Add a line to `CHANGELOG.md`, under "Unreleased", for every change a user notices.

## Rules of the repository

* The method scripts (`src/kdomainbench/methods/`) and the metric scripts
  (`src/kdomainbench/metric_scripts/`) are copies of the scripts behind the paper. Change one
  only to fix a bug, describe the change under "Method scripts" in `docs/overview.md`, and
  update its checksum in `tests/test_basic.py` (`METHOD_SCRIPTS`) or `tests/test_metrics.py`
  (`PAPER_SCRIPTS`).
* Some files are made by a script. Change the script and run it again, not the file:

  | File | Made by |
  |---|---|
  | `snippets/results_table.md`, and `summary_5k.csv` and the figures of the benchmark in `docs/assets/` | `scripts/make_results_page.py` |
  | `envs/kdb_py.yml`, `envs/kdb_spatialde.yml` | `envs/finalize_yml.py` |
  | `envs/kdb_r.lock.csv` | `envs/export_r_lock.R` |
  | `docs/assets/logo.svg`, `docs/assets/favicon.svg` | `scripts/make_logo.py` |

* The words of the site: "reference annotation" and "reference domain number" (or reference k),
  never "ground truth" or "true k". Sentences are short and plain.

## Add a method

A method is one script in `src/kdomainbench/methods/` and one `Method(...)` entry in
`src/kdomainbench/registry.py`. The entry names the script, its environment (`r`, `py` or
`spatialde`) and `argv`, the function that turns the input file, the run folder and `kmax` into
the script's arguments. The script runs in the run folder and writes `cluster_results.csv`
there, with the spot barcodes in the first column and the domain labels in a column named
`cluster`.

Add its checksum to `METHOD_SCRIPTS` in `tests/test_basic.py`, its packages to
`envs/install_r_packages.R` or the environment files, and its row to "The ten methods" in
`docs/overview.md` and to the methods table of `docs/citation.md`.
