# Changelog

Changes that users of kdomainbench notice, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased

### Added

- `kdb.metrics` and `kdomainbench metrics`: the twelve metrics of the paper, computed by the
  paper's own `metrics.R` and `scs.py`. `kdomainbench check --metrics` tests them, and
  `Rscript envs/install_r_packages.R --metrics` installs their R packages.
- A run folder records the package version and the settings that change a method
  (`run_info.json` fields `kdomainbench` and `env`), and the packages of the method's
  environment (`packages.txt`).
- `kdb.run_all` ends with one warning that names every method that did not finish.
- `load_results(h5ad=)` and `kdomainbench summarize --h5ad` score runs made on another machine.
  On the command line each file scores the runs of the dataset of its name, and `--h5ad` can
  be repeated. `summarize --reference-key` scores against another `obs` column.
- `kdb.pl.plot_metrics`: the metrics of every run as a matrix of bars, laid out as Fig. 2f of
  the paper.
- `kdomainbench --version`.
- `kdb.evaluate`, `kdb.reference_annotation` and the plots accept an AnnData object for the
  input file and a run folder for the labels. `kdb.evaluate` also compares two runs.
- `kdomainbench check` looks for every R package the method scripts load and reads an `.h5ad`
  file from R. `check --gpu` fails when no GPU is visible.
- Pages: the how-to guides Your own data, Run on a cluster and Troubleshooting, the Command
  line reference, FAQ, Citation, Contributing and Changelog.
- `CONTRIBUTING.md`, and a GitHub Actions workflow that runs the tests and builds the site.

### Changed

- Breaking: `kdb.run` takes `out_root` instead of `out_dir`, with the folder layout of
  `kdb.run_all` and `kdomainbench run -o`: `<out_root>/<method>/<dataset>_<device>`.
- Breaking, to the terms of the paper: `ground_truth` is now `reference_annotation` (its `key`
  is `reference_key`), `k_true` is `k_reference`, `truth_key` is `reference_key`,
  `evaluate(truth=)` is `evaluate(reference=)`, and the `n_spots` of `evaluate` is
  `n_spots_scored`. `plot_k_estimates(k_true=)` is
  `plot_k_estimates(k_reference=)`.
- `kdb.pl.plot_k_estimates` has one row per method and colors each dot by its distance from
  the reference k, as Fig. 2b of the paper. Runs of several datasets are drawn as k errors.
  Breaking: `k_reference` takes one number, not a list.
- `gpu_id` defaults to the GPUs a scheduler names in `CUDA_VISIBLE_DEVICES`, else GPU 0.
- `kmax` is checked before any method starts: at least 2, and at most 30 for BNPSpace.
- A run that is stopped or fails stays on record with `"success": false`, and labels or
  metrics of an earlier run in the same folder are deleted first.
- `load_results` raises `FileNotFoundError` for a folder that does not exist and always returns
  the score columns. It raises `ValueError` when one `h5ad` file is given for runs of several
  datasets.
- `kdb.run` and `kdb.run_all` stop before any method starts when the input is a folder or not
  an `.h5ad` file.
- `kdomainbench summarize` prints the main columns, and each reason a run was not scored once.
  `--csv` keeps every column. Warnings print without Python's source line.
- `kdomainbench run`, `metrics` and `summarize` exit with an error code when a method did not
  finish, a metric could not be computed or no run succeeded.
- A fatal error of `kdomainbench` is one line that starts with `kdomainbench: error:`, and a
  method named twice runs once.
- `kdb.read_clusters`, `kdb.load_results(h5ad=)`, `kdb.k_accuracy` and the plots say what is
  wrong with their input: a run that did not finish, an input file that does not exist, a
  table without the columns of `load_results`.
- `kdb.pl.plot_spatial_grid` titles each map `<method> (k = n)`.
- `drsc.R` no longer reads `obs["clusters"]`, so it runs on files without an annotation.
- Python 3.10 or later.

### Removed

- The `docs` extra of `pyproject.toml`. Use `docs/requirements.txt`.
- cowplot from `envs/install_r_packages.R`: no method script loads it.

## 0.1.0 (2026-11-02)

First version: ten methods behind `kdb.run`, `kdb.run_all` and `kdomainbench run`, scoring with
`kdb.evaluate`, `kdb.load_results` and `kdb.k_accuracy`, and the plots in `kdb.pl`.
