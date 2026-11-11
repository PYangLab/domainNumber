"""Fast tests that need no method environment."""
import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
import warnings
from pathlib import Path

import pandas as pd
import pytest

import kdomainbench as kdb
from kdomainbench import cli, config, runner
from kdomainbench.registry import get_method

# The method scripts are the paper's, with only the changes listed in docs/overview.md,
# "Method scripts". A change to a script needs an entry there and its new checksum here.
METHOD_SCRIPTS = {
    "bayesspace.R": "4cfe6928586f57f239d919e9e3ce9e3453ceeac4192ee0e59c8f9fa13095ba38",
    "bnpspace.R": "79c33760d817ed9c3a8d1542e4aaaac28a060bf0834414fa0675484065a54fab",
    "bnpspace_R/fix_clusters_model.cpp": "048470645b5bea4b283f0c805cedf58a600bdb930f86927ec53be91e7432ec99",
    "bnpspace_R/main.R": "51cb6d35aaa04799745ee9928a103da95c375f507311c0bc9abd7d1391984bd0",
    "bnpspace_R/model.cpp": "d555d092214a7d22e3490b67c52b84e886956af0976c3af403b3d09ff84e229f",
    "bnpspace_R/utils.R": "684fe64045d31a2dbd97270a3a216d68d803c4b822085fa37db28f1a60889790",
    "drsc.R": "8225ddfec0d85d7562b6acdbdde4383ff4a03fbcf824699cda2c1842148bda0f",
    "iscmeb.R": "e754646687087f8596ff730b2ca655b0329665ca19819a64dc7ad80f96978533",
    "precast.R": "669a61e40b21af7ffb1e6d7988aaf5f55559875f70a05b87bc13f031c8f69b83",
    "run_cellcharter.py": "95d1b99f3736d7051700105a8256012d9bb58dc5efde531117f679bbe7e29d33",
    "run_deepst.py": "0eb068b60e688adb2e0b65ab86c643c30ff87d83702532e82004708968e638c4",
    "run_spagcn.py": "ec35294078616d83b7fdfa2834d37458b90801a0f58a7fb4afa29f4fc23607d8",
    "run_spatialde.py": "db24b5c789ebc7203d34738fbc50fbff0d3f19eb4270626b18ec0f9c74bc8151",
    "scmeb.R": "bcb9d891b8811ceef2db723528da66dfb572952fef733a9242a8933e11f02035",
}


def _sample(path, n=6):
    """A small annotated .h5ad file with spot coordinates, and its AnnData object."""
    import anndata
    import numpy as np
    adata = anndata.AnnData(np.ones((n, 2), dtype="float32"))
    adata.obs_names = [f"s{i}" for i in range(n)]
    adata.obs["clusters"] = ["x"] * (n // 2) + ["y"] * (n - n // 2)
    adata.obsm["spatial"] = np.arange(2 * n, dtype=float).reshape(n, 2)
    adata.write_h5ad(path)
    return adata


def _finished_run(root, h5ad, method="DR.SC", labels=("0", "0", "0", "1", "1", "1"), success=True):
    run = root / method / f"{h5ad.stem}_cpu"
    run.mkdir(parents=True)
    (run / "cluster_results.csv").write_text("spot_id,cluster\n" + "".join(f"s{i},{v}\n" for i, v in enumerate(labels)))
    (run / "run_info.json").write_text(json.dumps(dict(method=method, dataset=h5ad.stem, h5ad=str(h5ad),
                                                       device_requested="cpu", device_used="cpu", success=success,
                                                       wall_time_s=1.0, peak_rss_mb=1.0, k_estimated=2)))
    return run


def test_method_scripts_are_pinned():
    import hashlib
    scripts = {str(f.relative_to(runner.METHODS_DIR)) for f in runner.METHODS_DIR.rglob("*")
               if f.suffix in (".R", ".py", ".cpp")}
    assert scripts == set(METHOD_SCRIPTS)
    for name, sha in METHOD_SCRIPTS.items():
        assert hashlib.sha256((runner.METHODS_DIR / name).read_bytes()).hexdigest() == sha, name


def test_every_setting_a_method_script_reads_is_recorded():
    names = set()
    for f in runner.METHODS_DIR.rglob("*"):
        if f.suffix in (".R", ".py"):
            names.update(re.findall(r"""(?:Sys\.getenv\(|os\.environ(?:\.get\(|\[))["']([A-Z_]+)""", f.read_text()))
    assert names and names <= set(runner.RECORDED_ENV)


def test_registry():
    assert len(kdb.list_methods()) == 10
    assert kdb.list_methods(gpu_only=True) == ["CellCharter", "DeepST", "SpatialDE2"]
    assert get_method("iscmeb").name == "iSC.MEB"
    with pytest.raises(ValueError):
        get_method("nope")


# ---- environments -------------------------------------------------------------------------

def test_device_env(monkeypatch):
    m = get_method("DeepST")
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    assert runner._build_env(m, "cpu", None)["CUDA_VISIBLE_DEVICES"] == ""
    env = runner._build_env(m, "gpu", None)                 # nothing assigned: GPU 0
    assert env["CUDA_VISIBLE_DEVICES"] == "0" and env["CUDA_DEVICE_ORDER"] == "PCI_BUS_ID"
    assert runner._build_env(m, "gpu", 2)["CUDA_VISIBLE_DEVICES"] == "2"


def test_gpu_assigned_by_a_scheduler_is_kept(monkeypatch):
    m = get_method("DeepST")
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "3")
    assert runner._build_env(m, "gpu", None)["CUDA_VISIBLE_DEVICES"] == "3"
    assert runner._build_env(m, "gpu", 1)["CUDA_VISIBLE_DEVICES"] == "1"    # an explicit choice wins
    assert runner._build_env(m, "cpu", None)["CUDA_VISIBLE_DEVICES"] == ""


def test_environment_next_to_the_running_one_is_found(tmp_path, monkeypatch):
    for name in ("kdb_py", "kdb_spatialde"):
        (tmp_path / name / "bin").mkdir(parents=True)
        (tmp_path / name / "bin" / "python").touch()
    monkeypatch.setattr(config.sys, "prefix", str(tmp_path / "kdb_py"))
    for var in ("KDB_SPATIALDE_PYTHON", "CONDA_EXE", "MAMBA_EXE", "CONDA_PREFIX"):
        monkeypatch.delenv(var, raising=False)
    assert config.interpreter("spatialde") == str(tmp_path / "kdb_spatialde" / "bin" / "python")


def test_rscript_is_found_on_path_or_named(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "_overrides", {})
    for var in ("KDB_RSCRIPT", "KDB_METRICS_RSCRIPT"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(FileNotFoundError, match="module load R"):
        config.interpreter("metrics")                   # the metrics use the methods' R unless told otherwise
    (tmp_path / "Rscript").write_text("#!/bin/sh\necho 'Package,Version'\n")
    (tmp_path / "Rscript").chmod(0o755)
    assert config.interpreter("metrics") == config.interpreter("r") == str(tmp_path / "Rscript")
    runner._write_packages(str(tmp_path / "Rscript"), "R", tmp_path, {"PATH": str(tmp_path)})
    assert (tmp_path / "packages.txt").read_text() == "Package,Version\n"


# ---- running ------------------------------------------------------------------------------

class _Stop(Exception):
    """Raised in place of starting the method."""


def _capture_launch(monkeypatch):
    """Record the command and environment a run starts its method with, and stop there."""
    seen = {}

    def fake_popen(cmd, env, **kw):
        seen.update(cmd=cmd, env=env)
        raise _Stop

    monkeypatch.setattr(runner.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(runner, "_write_packages", lambda *a: None)
    monkeypatch.setattr(runner.config, "interpreter", lambda key: "python")
    return seen


def test_cpu_only_method_warns_on_gpu(tmp_path, monkeypatch):
    """A CPU-only method asked for the GPU warns and is launched with no GPU visible."""
    seen = _capture_launch(monkeypatch)
    h5ad = tmp_path / "x.h5ad"
    h5ad.touch()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        with pytest.raises(_Stop):
            kdb.run("PRECAST", h5ad, device="gpu", out_root=tmp_path / "o", verbose=False)
    assert any("no GPU implementation" in str(x.message) for x in w)
    assert seen["env"]["CUDA_VISIBLE_DEVICES"] == ""
    assert "--device" not in seen["cmd"]
    # the run that never finished is on record as a failed run
    assert json.loads((tmp_path / "o" / "PRECAST" / "x_gpu" / "run_info.json").read_text())["success"] is False


def _fake_method(tmp_path, monkeypatch, body):
    """Make SpaGCN a small Python script run by this interpreter."""
    scripts = tmp_path / "methods"
    scripts.mkdir()
    (scripts / "run_spagcn.py").write_text(body)
    monkeypatch.setattr(runner, "METHODS_DIR", scripts)
    monkeypatch.setattr(runner.config, "interpreter", lambda key: sys.executable)
    h5ad = tmp_path / "x.h5ad"
    h5ad.touch()
    return h5ad


WRITE = "import sys\nopen(sys.argv[sys.argv.index('--save_path') + 1], 'w').write({!r})\n"


def test_run_reads_the_labels_and_records_the_run(tmp_path, monkeypatch):
    h5ad = _fake_method(tmp_path, monkeypatch, WRITE.format("spot_id,cluster\na,0\nb,1\nc,NA\n"))
    clusters = kdb.run("SpaGCN", h5ad, out_root=tmp_path / "o", verbose=False)
    assert clusters["cluster"].tolist() == ["0", "1"]       # the spot without a label is no domain
    summary = kdb.load_results(tmp_path, score=False)
    assert summary.loc[0, "k_estimated"] == 2 and summary.loc[0, "n_spots"] == 2
    assert summary.loc[0, "peak_rss_mb"] < 1e5
    with pytest.warns(UserWarning, match="no successful run could be scored"):
        assert kdb.k_accuracy(summary).empty      # no reference annotation: nothing to rank, no error
    info = json.loads((tmp_path / "o" / "SpaGCN" / "x_cpu" / "run_info.json").read_text())
    assert info["kdomainbench"] == kdb.__version__ and info["env"]["KDB_METHODS_DIR"] == str(runner.METHODS_DIR)
    assert "pandas==" in (tmp_path / "o" / "SpaGCN" / "x_cpu" / "packages.txt").read_text()


@pytest.mark.parametrize("output", ["", "spot_id,cluster\n", "spot_id,label\na,0\n"])
def test_a_run_without_labels_fails_and_stays_on_record(tmp_path, monkeypatch, output):
    """Labels left by an earlier run are not read back, and the failed run shows in the table."""
    body = WRITE.format(output) if output else "pass\n"
    h5ad = _fake_method(tmp_path, monkeypatch, body)
    out = tmp_path / "o" / "SpaGCN" / "x_cpu"
    out.mkdir(parents=True)
    (out / "cluster_results.csv").write_text("spot_id,cluster\na,0\nb,1\n")
    (out / "metric.csv").write_text("metric,value\nARI,0.9\n")
    with pytest.raises(kdb.MethodFailed) as failed:
        kdb.run("SpaGCN", h5ad, out_root=tmp_path / "o", verbose=False)
    assert failed.value.log == out.resolve() / "run.log"         # what run_all's warning names
    summary = kdb.load_results(tmp_path)
    assert len(summary) == 1 and not summary.loc[0, "success"]
    assert not (out / "metric.csv").exists()          # nor the metrics of the earlier labels


def test_a_run_that_cannot_start_leaves_an_earlier_run_alone(tmp_path, monkeypatch):
    monkeypatch.setenv("KDB_PY_PYTHON", str(tmp_path / "no" / "python"))
    h5ad = tmp_path / "x.h5ad"
    h5ad.touch()
    out = tmp_path / "o" / "SpaGCN" / "x_cpu"
    out.mkdir(parents=True)
    (out / "cluster_results.csv").write_text("spot_id,cluster\na,0\n")
    with pytest.raises(FileNotFoundError):
        kdb.run("SpaGCN", h5ad, out_root=tmp_path / "o", verbose=False)
    assert (out / "cluster_results.csv").exists()
    with pytest.raises(FileNotFoundError):
        kdb.run("SpaGCN", h5ad, out_root=tmp_path / "new", verbose=False)
    assert not (tmp_path / "new").exists()


def test_the_settings_are_checked_before_anything_runs(tmp_path):
    """By kdb.run, and by kdb.run_all, which the command line uses."""
    h5 = tmp_path / "filtered_feature_bc_matrix.h5"
    h5.touch()
    for start in (lambda path, **kw: kdb.run("SpaGCN", path, **kw),
                  lambda path, **kw: kdb.run_all(path, methods=["SpaGCN"], **kw)):
        with pytest.raises(FileNotFoundError, match="is a folder.*Space Ranger"):
            start(tmp_path)
        with pytest.raises(ValueError, match="not an .h5ad file.*Space Ranger"):
            start(h5)
        with pytest.raises(FileNotFoundError, match="input file not found"):
            start(tmp_path / "typo.h5ad")
        with pytest.raises(ValueError, match="device must be"):
            start(tmp_path, device="tpu")
    assert not (tmp_path / "kdb_results").exists()


def test_kmax_is_checked_before_anything_runs(tmp_path):
    h5ad = tmp_path / "x.h5ad"
    h5ad.touch()
    with pytest.raises(ValueError, match="at least 2"):
        kdb.run("DR.SC", h5ad, kmax=1)
    for kmax in (31, "31"):                     # from the command line or a config file it may be text
        with pytest.raises(ValueError, match="BNPSpace accepts kmax up to 30"):
            kdb.run_all(h5ad, kmax=kmax, out_root=tmp_path / "r")
    assert not (tmp_path / "r").exists()


def _start_a_long_run(tmp_path, **popen):
    """kdb.run in its own Python process, with a method that sleeps for a minute."""
    scripts = tmp_path / "methods"
    scripts.mkdir()
    (scripts / "run_spagcn.py").write_text("import os, time\nprint(os.getpid(), flush=True)\ntime.sleep(60)\n")
    (tmp_path / "x.h5ad").touch()
    driver = ("import sys, kdomainbench as kdb\nfrom kdomainbench import runner\nfrom pathlib import Path\n"
              f"runner.METHODS_DIR = Path({str(scripts)!r})\nrunner.config.interpreter = lambda key: sys.executable\n"
              f"kdb.run('SpaGCN', {str(tmp_path / 'x.h5ad')!r}, out_root={str(tmp_path / 'o')!r})\n")
    return subprocess.Popen([sys.executable, "-c", driver], stdout=subprocess.PIPE, text=True, **popen)


@pytest.mark.parametrize("sig", [signal.SIGTERM, signal.SIGHUP])
def test_a_terminated_run_stops_the_method_and_stays_on_record(tmp_path, sig):
    """scancel, a time limit or a closed terminal must not leave the method running or unrecorded."""
    with _start_a_long_run(tmp_path) as p:
        for line in p.stdout:                   # the method prints its pid once it is running
            if line.strip().isdigit():
                method_pid = int(line)
                break
        p.send_signal(sig)
        assert p.wait(timeout=20) == 128 + sig
    time.sleep(0.5)
    with pytest.raises(ProcessLookupError):
        os.kill(method_pid, 0)
    assert json.loads((tmp_path / "o" / "SpaGCN" / "x_cpu" / "run_info.json").read_text())["success"] is False


def test_a_run_under_nohup_survives_a_hangup(tmp_path):
    """SIGHUP is ignored under nohup, and a run must not undo that."""
    with _start_a_long_run(tmp_path, preexec_fn=lambda: signal.signal(signal.SIGHUP, signal.SIG_IGN)) as p:
        for line in p.stdout:
            if line.strip().isdigit():
                break
        p.send_signal(signal.SIGHUP)
        time.sleep(1)
        assert p.poll() is None                 # still running
        p.send_signal(signal.SIGTERM)
        assert p.wait(timeout=20) == 128 + signal.SIGTERM


def test_run_all_goes_on_when_an_environment_is_missing(tmp_path, monkeypatch):
    labels = pd.DataFrame({"cluster": ["0"]}, index=pd.Index(["a"], name="spot_id"))
    calls = []

    def fake_run(name, h5ad, **kw):
        calls.append(name)
        if name == "SpaGCN":
            raise FileNotFoundError("conda env 'kdb_py' not found")
        return labels

    monkeypatch.setattr(runner, "run", fake_run)
    h5ad = tmp_path / "x.h5ad"
    h5ad.touch()
    with pytest.warns(UserWarning, match="1 of 3 methods did not finish:\n  SpaGCN not run"):
        assert list(kdb.run_all(h5ad, methods=["DR.SC", "SpaGCN", "SC.MEB"])) == ["DR.SC", "SC.MEB"]
    assert list(kdb.run_all(h5ad, methods="drsc")) == ["DR.SC"]          # one name, any spelling
    calls.clear()
    assert kdb.run_all(h5ad, methods=[]) == {} and calls == []          # nothing asked, nothing run


def test_run_all_goes_on_when_a_method_fails(tmp_path, monkeypatch):
    def fake_run(name, h5ad, **kw):
        if name == "DR.SC":
            raise kdb.MethodFailed("DR.SC failed (exit 1)", log=log)
        return pd.DataFrame({"cluster": ["0"]}, index=pd.Index(["a"], name="spot_id"))

    monkeypatch.setattr(runner, "run", fake_run)
    (tmp_path / "x.h5ad").touch()
    log = tmp_path.resolve() / "o" / "DR.SC" / "x_cpu" / "run.log"
    with pytest.warns(UserWarning, match=f"1 of 2 methods did not finish:\n  DR.SC failed, see {re.escape(str(log))}"):
        assert list(kdb.run_all(tmp_path / "x.h5ad", methods=["DR.SC", "SC.MEB"], out_root=tmp_path / "o")) == ["SC.MEB"]


def test_cli_run_uses_one_folder_layout_and_reports_failures(tmp_path, monkeypatch):
    calls = []

    def fake_run_all(h5ad, methods=None, out_root=None, **kw):
        calls.append((methods, out_root))
        return {"DR.SC": None}

    monkeypatch.setattr(kdb, "run_all", fake_run_all)
    cli.main(["run", "-m", "drsc", "-i", "x.h5ad", "-o", str(tmp_path)])
    assert calls[-1] == (["DR.SC"], str(tmp_path))
    with pytest.raises(SystemExit) as stop:                     # SC.MEB did not finish
        cli.main(["run", "-m", "DR.SC", "SC.MEB", "-i", "x.h5ad"])
    assert calls[-1] == (["DR.SC", "SC.MEB"], "kdb_results") and stop.value.code not in (0, None)


@pytest.mark.parametrize("flags", [[], ["--gpu"]])
def test_check_reports_every_environment(tmp_path, monkeypatch, capsys, flags):
    """check answers for all three environments, with and without --gpu, and fails when one does."""
    rscript = tmp_path / "Rscript"
    rscript.write_text("#!/bin/sh\necho 'reads .h5ad files: 3 spots'\n")
    rscript.chmod(0o755)
    monkeypatch.setattr(config, "interpreter", lambda key: str(rscript) if key == "r" else sys.executable)
    with pytest.raises(SystemExit) as stop:
        cli.main(["check", *flags])
    out = capsys.readouterr().out
    assert all(f"[{key}]" in out for key in ("py", "spatialde", "r")) and "reads .h5ad files" in out
    assert stop.value.code == 1                 # this Python has no torch: the check must say so


def test_check_looks_for_every_package_the_r_scripts_load():
    packages = cli._r_packages()
    assert {"PRECAST", "SC.MEB", "BayesSpace", "DR.SC", "iSC.MEB", "zellkonverter",   # the methods
            "flexclust", "scran", "RcppArmadillo"} <= set(packages)                    # BNPSpace's helpers


# ---- scoring ------------------------------------------------------------------------------

def test_read_clusters_and_evaluate(tmp_path):
    (tmp_path / "cluster_results.csv").write_text("cell_id,cluster\na,1\nb,1\nc,2\nd,2\n")
    cl = kdb.read_clusters(tmp_path)
    assert list(cl.index) == ["a", "b", "c", "d"]
    res = kdb.evaluate(cl, pd.Series(["x", "x", "y", "y"], index=list("abcd")))
    assert res["k_estimated"] == 2 and res["k_error"] == 0 and res["ARI"] == 1.0


def test_evaluate_rejects_runs_that_share_no_spot():
    """Mismatched barcodes are an error, not a perfect score on zero spots."""
    clusters = pd.DataFrame({"cluster": ["1", "1", "2"]}, index=["a-1", "b-1", "c-1"])
    reference = pd.Series(["x", "x", "y"], index=["a", "b", "c"])
    with pytest.raises(ValueError, match="share no spot"):
        kdb.evaluate(clusters, reference)


def test_evaluate_rejects_duplicate_barcodes():
    labels = pd.Series(["1", "1", "2"], index=["a", "a", "b"])
    with pytest.raises(ValueError, match="occurs twice"):
        kdb.evaluate(labels, pd.Series(["x", "y"], index=["a", "b"]))


def test_barcodes_that_look_like_numbers_are_matched(tmp_path):
    (tmp_path / "cluster_results.csv").write_text("spot_id,cluster\n1000,1\n1001,1\n1002,2\n1003,2\n")
    reference = pd.Series(["x", "x", "y", "y"], index=["1000", "1001", "1002", "1003"])
    res = kdb.evaluate(kdb.read_clusters(tmp_path), reference)
    assert res["n_spots_scored"] == 4 and res["ARI"] == 1.0


def test_k_estimated_counts_every_label_the_method_returned():
    """A domain that lies only on spots without a reference label still counts in k."""
    clusters = pd.DataFrame({"cluster": ["1", "1", "2", "2", "3"]}, index=list("abcde"))
    reference = pd.Series(["x", "x", "y", "y"], index=list("abcd"))      # spot e is not annotated
    res = kdb.evaluate(clusters, reference)
    assert (res["k_estimated"], res["k_reference"], res["k_error"], res["n_spots_scored"]) == (3, 2, 1, 4)


def test_missing_labels_and_annotations_are_not_domains():
    labels = pd.Series(["1", "1", "2", "2", None, "3"], index=list("abcdef"))
    reference = pd.Series(["x", "x", "y", "y", "y", None], index=list("abcdef"))
    res = kdb.evaluate(labels, reference)
    assert (res["k_estimated"], res["k_reference"], res["n_spots_scored"]) == (3, 2, 4)


def test_load_results_scores_against_a_moved_input_file(tmp_path):
    _sample(tmp_path / "here.h5ad")
    run = _finished_run(tmp_path / "runs", tmp_path / "S.h5ad", method="M")
    info = json.loads((run / "run_info.json").read_text())
    (run / "run_info.json").write_text(json.dumps(dict(info, h5ad="/gone/S.h5ad")))
    (tmp_path / "runs" / "broken").mkdir()
    (tmp_path / "runs" / "broken" / "run_info.json").write_text("")      # a record cut short

    summary = kdb.load_results(tmp_path / "runs").set_index("method")
    assert "input file not found" in summary.loc["M", "score_error"]
    assert summary["success"].tolist() == [True, False]                  # the broken record is listed as failed
    for h5ad in (tmp_path / "here.h5ad", {"S": tmp_path / "here.h5ad"}):
        summary = kdb.load_results(tmp_path / "runs", h5ad=h5ad).set_index("method")
        assert summary.loc["M", "ARI"] == 1.0 and summary.loc["M", "k_error"] == 0
    with pytest.raises(ValueError, match="without a run"):               # a dataset name with no run
        kdb.load_results(tmp_path / "runs", h5ad={"T": tmp_path / "here.h5ad"})
    _finished_run(tmp_path / "runs", tmp_path / "T.h5ad", method="M")
    with pytest.raises(ValueError, match="2 datasets"):                   # one file would score both
        kdb.load_results(tmp_path / "runs", h5ad=tmp_path / "here.h5ad")


# ---- figures ------------------------------------------------------------------------------

def test_the_k_figure_has_one_row_per_method():
    import matplotlib
    matplotlib.use("Agg")
    summary = pd.DataFrame(dict(method=["B", "A"], k_estimated=[5, 3], success=True))
    ax = kdb.pl.plot_k_estimates(summary)
    assert ax.collections[0].get_offsets().tolist() == [[3, 0], [5, 1]]       # sorted by k, the smallest on top
    assert [t.get_text() for t in ax.get_yticklabels()] == ["A", "B"] and ax.get_legend() is None
    ax = kdb.pl.plot_k_estimates(summary, k_reference=5)                       # a file without an annotation
    assert ax.get_legend().get_texts()[0].get_text() == "reference domain number (5)"


def test_the_k_figure_shows_the_k_error_for_several_reference_numbers():
    import matplotlib
    matplotlib.use("Agg")
    summary = pd.DataFrame(dict(method=["A", "A", "A", "B"], k_estimated=[5, 4, 9, 6],
                                k_reference=[5, 4, 7, None], success=True))
    ax = kdb.pl.plot_k_estimates(summary)
    dots = ax.collections[0]
    assert ax.get_xlabel().startswith("k error")
    assert dots.get_offsets().tolist() == [[0, 0], [2, 0]]                     # B has no annotation
    assert dots.get_sizes()[0] == 2 * dots.get_sizes()[1]                      # two runs of A at 0
    assert [t.get_text() for t in ax.get_legend().get_texts()] == [
        "estimated k = reference k", "as many domains", "more domains", "1 run", "2 runs"]


def test_the_k_figure_is_about_the_runs_with_a_reference_annotation():
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.colors import to_rgba
    summary = pd.DataFrame(dict(method=["A", "A", "B", "B"], k_estimated=[5, 6, 9, 3],
                                k_reference=[7, None, 7, None], success=True))
    dots = kdb.pl.plot_k_estimates(summary).collections[0]
    assert dots.get_offsets().tolist() == [[5, 0], [9, 1]]                  # the two runs without an annotation are left out
    assert [tuple(c) for c in dots.get_facecolors()] == [to_rgba("#3A6BA5"), to_rgba("#C65A36")]    # fewer, more
    ax = kdb.pl.plot_k_estimates(summary.assign(k_reference=None))          # no annotation at all: every run, in gray
    assert len(ax.collections[0].get_offsets()) == 4 and ax.get_legend() is None
    assert {tuple(c) for c in ax.collections[0].get_facecolors()} == {to_rgba("0.55")}
    ax = kdb.pl.plot_k_estimates(summary.iloc[[0]].assign(k_estimated=7))   # one dot, on the reference: whole numbers of k
    assert [t for t in ax.get_xticks() if t != int(t)] == [] and 7 in ax.get_xticks()


def test_the_metric_figure_ranks_the_methods_within_a_metric():
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.colors import to_rgba
    from matplotlib.container import BarContainer
    summary = pd.DataFrame(dict(method=["A", "B", "C", "A"], success=True, ARI=[0.2, 0.6, 0.4, 0.4],
                                PAS=[0.1, 0.3, 0.2, 0.1], SCS=[5.0, None, 3.0, 7.0]))
    ax = kdb.pl.plot_metrics(summary)
    texts = [t.get_text() for t in ax.texts]
    assert [t.get_text() for t in ax.get_yticklabels()] == ["A", "B", "C"]
    assert {"Concordance", "Spatial\ncoherence", "Stability", "n/a", "whisker: standard deviation", "0.6"} <= set(texts)
    assert "Completeness" not in texts and texts.count("n/a") == 1             # B has no SCS
    ari, scs, pas = [c for c in ax.containers if isinstance(c, BarContainer)][1:]
    assert ari.patches[1].get_facecolor() == pytest.approx(to_rgba("#D66713"), abs=0.01)    # B, the highest ARI
    assert ari.patches[0].get_facecolor() == pytest.approx(to_rgba("#F7F7F7"), abs=0.01)    # A (mean 0.3), the lowest
    assert pas.patches[0].get_facecolor() == pytest.approx(to_rgba("#4A4A4A"), abs=0.01)    # lower is better
    assert len(scs.patches) == 2
    with pytest.raises(ValueError, match="kdomainbench metrics"):
        kdb.pl.plot_metrics(summary[["method", "success"]])
    # equal means share a rank, also when their sums differ in the last digit (0.19999999999999998, 0.20000000000000004)
    tie = pd.DataFrame(dict(method=["A"] * 3 + ["B"] * 3, success=True, ARI=[0.1, 0.2, 0.3, 0.2, 0.2, 0.2]))
    a, b = [c for c in kdb.pl.plot_metrics(tie).containers if isinstance(c, BarContainer)][1].patches
    assert a.get_facecolor() == b.get_facecolor()
    # a value that is rounding noise is 0: no bar, and no axis blown up to 2e-16
    noise = pd.DataFrame(dict(method=["A"], success=True, HOM=[1.97e-16], COM=[1.0]))
    ax = kdb.pl.plot_metrics(noise)
    hom, com = [c for c in ax.containers if isinstance(c, BarContainer)][1:]
    assert hom.patches[0].get_width() == 0 and com.patches[0].get_width() > 0.8
    assert "bar: value of the metric" in [t.get_text() for t in ax.texts]      # no whisker drawn, none in the key


def test_a_gpu_method_is_told_its_device(tmp_path, monkeypatch):
    seen = _capture_launch(monkeypatch)
    (tmp_path / "x.h5ad").touch()
    with pytest.raises(_Stop):
        kdb.run("DeepST", tmp_path / "x.h5ad", device="gpu", out_root=tmp_path, verbose=False)
    assert seen["cmd"][-2:] == ["--device", "gpu"]


def test_set_env_and_the_isolated_r_library(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "_overrides", {})
    for var in ("KDB_PY_PYTHON", "KDB_R_LIB"):
        monkeypatch.delenv(var, raising=False)
    kdb.set_env("py", sys.executable, r_lib=tmp_path)
    assert config.interpreter("py") == sys.executable
    env = config.child_env("R")
    assert env["R_LIBS"] == str(tmp_path) and env["R_LIBS_USER"] == env["R_LIBS_SITE"] == "/nonexistent"
    assert "R_LIBS" not in config.child_env("Python")
    monkeypatch.setenv("KDB_PY_PYTHON", str(tmp_path / "no" / "python"))     # the variable wins
    with pytest.raises(FileNotFoundError, match="KDB_PY_PYTHON"):
        config.interpreter("py")
    with pytest.raises(ValueError, match="must be one of"):
        kdb.set_env("julia", sys.executable)


def test_natural_inputs_are_accepted(tmp_path):
    adata = _sample(tmp_path / "s.h5ad")
    run = _finished_run(tmp_path / "runs", tmp_path / "s.h5ad")
    for clusters in (run, str(run), kdb.read_clusters(run)):
        for reference in (tmp_path / "s.h5ad", adata, kdb.reference_annotation(adata), run, kdb.read_clusters(run)):
            assert kdb.evaluate(clusters, reference)["ARI"] == 1.0     # the last two: another run
    with pytest.raises(TypeError, match="without a 'cluster' column"):
        kdb.evaluate(kdb.load_results(tmp_path / "runs"), adata)
    with pytest.raises(ValueError, match="not an .h5ad file"):              # a run's csv is no reference file
        kdb.evaluate(run, run / "cluster_results.csv")
    with pytest.raises(KeyError, match="its columns: clusters"):
        kdb.reference_annotation(adata, reference_key="layer")
    with pytest.raises(ValueError, match="is an input file"):
        kdb.read_clusters(tmp_path / "s.h5ad")
    with pytest.raises(FileNotFoundError, match="not a run folder"):
        kdb.metrics(tmp_path)


def test_load_results_keeps_its_columns_and_refuses_a_missing_folder(tmp_path):
    with pytest.raises(FileNotFoundError, match="no such folder"):
        kdb.load_results(tmp_path / "typo")
    (tmp_path / "empty").mkdir()
    empty = kdb.load_results(tmp_path / "empty")
    assert empty.empty and {"k_reference", "k_error", "ARI", "NMI", "score_error"} <= set(empty)
    with pytest.raises(TypeError, match="table from kdb.load_results"):
        kdb.k_accuracy(str(tmp_path))


def test_k_accuracy_ranks_by_k_error_then_ari():
    summary = pd.DataFrame(dict(method=["A", "A", "B", "C", "D"], success=[True, True, True, True, False],
                                k_reference=[7, 7, 7, 7, 7], k_error=[0, -2, 1, -1, 0], ARI=[0.5, 0.3, 0.2, 0.6, 0.9]))
    acc = kdb.k_accuracy(summary)
    assert list(acc.index) == ["C", "A", "B"]         # |error| 1 and ARI 0.6 before |error| 1 and ARI 0.4
    assert acc.loc["A", "runs"] == 2 and acc.loc["A", "exact_rate"] == 0.5


def test_the_figures(tmp_path):
    import matplotlib
    matplotlib.use("Agg")
    adata = _sample(tmp_path / "s.h5ad")
    run = _finished_run(tmp_path / "runs", tmp_path / "s.h5ad")
    summary = kdb.load_results(tmp_path / "runs")
    ax = kdb.pl.plot_k_estimates(summary)
    assert ax.get_legend().get_texts()[0].get_text() == "reference domain number (2)"
    assert "Concordance" in [t.get_text() for t in kdb.pl.plot_metrics(summary).texts]    # ARI and NMI
    assert kdb.pl.plot_runtime(summary).get_ylabel() == "run time (s)"
    with pytest.raises(ValueError, match="has a value in 'wall_time_s'"):       # runs without a time record
        kdb.pl.plot_runtime(summary.assign(wall_time_s=None))
    assert kdb.pl.plot_spatial(run, adata).get_title() == "k = 2"
    fig = kdb.pl.plot_spatial_grid({"DR.SC": run, "again": kdb.read_clusters(run)}, tmp_path / "s.h5ad", ncols=2)
    assert [a.get_title() for a in fig.axes] == ["DR.SC (k=2)", "again (k=2)"]
    with pytest.raises(ValueError, match="same spot barcodes"):
        kdb.pl.plot_spatial(pd.Series(["1"], index=["other"]), adata)
    with pytest.raises(KeyError, match="spatial_key"):
        kdb.pl.plot_spatial(run, adata, spatial_key="xy")
    with pytest.raises(TypeError, match="plot_spatial_grid"):
        kdb.pl.plot_spatial({"DR.SC": run}, adata)
    with pytest.raises(TypeError, match="as kdb.run_all returns"):
        kdb.pl.plot_spatial_grid(summary, adata)
    with pytest.raises(ValueError, match="no runs to plot"):
        kdb.pl.plot_spatial_grid({}, adata)
    with pytest.raises(TypeError, match="table from kdb.load_results"):
        kdb.pl.plot_k_estimates("runs/")


def test_cli_summarize(tmp_path, capsys):
    _sample(tmp_path / "s.h5ad")
    _finished_run(tmp_path / "runs", tmp_path / "s.h5ad")
    cli.main(["summarize", str(tmp_path / "runs"), "--csv", str(tmp_path / "t.csv"), "--plot", str(tmp_path / "k.png")])
    out = capsys.readouterr().out
    assert "mean_abs_k_error" in out and (tmp_path / "t.csv").exists() and (tmp_path / "k.png").exists()
    _finished_run(tmp_path / "runs", tmp_path / "gone.h5ad", method="M")
    cli.main(["summarize", str(tmp_path / "runs")])
    assert "not scored (1 of 2): input file not found" in capsys.readouterr().out    # once, below the table
    cli.main(["summarize", str(tmp_path / "runs"), "--h5ad", str(tmp_path / "s.h5ad")])    # matched by its name
    with pytest.raises(SystemExit, match="without a run"):
        cli.main(["summarize", str(tmp_path / "runs"), "--h5ad", str(tmp_path / "other.h5ad")])
    _finished_run(tmp_path / "failed", tmp_path / "s.h5ad", success=False)
    with pytest.raises(SystemExit, match="no successful run"):    # also before the plot is attempted
        cli.main(["summarize", str(tmp_path / "failed"), "--plot", str(tmp_path / "k2.png")])


def test_the_docs_checker_keeps_the_real_run_of_a_fast_method(tmp_path, monkeypatch):
    """scripts/check_docs.py gives a page the run a fast method made, not a reused one."""
    import importlib.util
    import types
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "")      # what the checker sets, restored after the test
    spec = importlib.util.spec_from_file_location("check_docs", Path(__file__).resolve().parents[1] / "scripts/check_docs.py")
    check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check)
    h5ad = tmp_path / "x.h5ad"
    h5ad.touch()
    for method in ("SpaGCN", "DR.SC"):
        _finished_run(tmp_path / "reuse", h5ad, method=method)
    check.ARGS, check.FAST = types.SimpleNamespace(reuse=tmp_path / "reuse"), {"SpaGCN"}
    check.REAL_RUN = lambda m, h5ad, out_root, **kw: _finished_run(Path(out_root), Path(h5ad), method=m, labels="77")
    monkeypatch.chdir(tmp_path)
    assert check.stub_run("SpaGCN", h5ad, out_root="o")["cluster"].tolist() == ["7", "7"]       # its own run
    assert check.stub_run("DR.SC", h5ad, out_root="o")["cluster"].tolist() == list("000111")    # a reused run


def test_the_cli_page_names_every_option():
    page = (Path(__file__).resolve().parents[1] / "docs/reference/cli.md").read_text()
    sections = dict(re.findall(r"^## kdomainbench (\w+)\n(.*?)(?=^## |\Z)", page, flags=re.M | re.S))
    commands = next(a for a in cli.parser()._actions if isinstance(a, argparse._SubParsersAction)).choices
    assert set(sections) == set(commands)
    for name, sub in commands.items():
        for action in sub._actions:
            for option in action.option_strings or [action.dest]:
                assert option in ("-h", "--help") or f"`{option}" in sections[name], (name, option)
