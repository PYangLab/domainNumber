"""Tests of kdb.metrics. The fast ones replace the metric scripts, and the last one runs the real code."""
import hashlib
import json
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

import kdomainbench as kdb
from kdomainbench import cli, config
from kdomainbench import paper_metrics as metrics_module

HERE = Path(__file__).resolve().parent
REAL_INTERPRETER = config.interpreter
EXAMPLE = HERE.parent / "data" / "D3_151509_5k.h5ad"

# The metric scripts are copies of the paper's qc/metric/metrics.R and qc/metric/scs.py.
# A change to either file is a change to the benchmark's metrics: update the copy and these together.
PAPER_SCRIPTS = {
    "metrics.R": "b7fb38d45e6b326eca388a3e5fca50faa5868e363bb6aa614382ab6d0c01b453",
    "scs.py": "713445724300f0588e0e15ba52bbd7a25b8591465dc1fc2f261545b486634a81",
}

# metric.csv of DR.SC on dataset D3 in the paper's results (tests/data holds its labels).
PAPER_D3_DRSC = {
    "ARI": 0.233265302446607, "spARI": 0.211016280561398, "NMI": 0.48259560098472,
    "FM": 0.378045386521507, "AMI": 0.397963237138457, "Purity": 0.704763894692854,
    "HOM": 0.607838761280657, "COM": 0.400146700755049, "PAS": 0.133096531550355,
    "CHAOS": 0.0609726156709374, "LISI": 1.49277225532274,
}


def test_the_metric_scripts_are_the_papers():
    for name, sha in PAPER_SCRIPTS.items():
        assert hashlib.sha256((metrics_module.SCRIPTS / name).read_bytes()).hexdigest() == sha, name


# Stand-ins run by this Python: same arguments as the real scripts (h5ad, labels, output).
FAKE_R = ("import sys\nassert open(sys.argv[2]).readline().strip() == 'spot_id,cluster'\n"
          "names = 'ARI spARI NMI FM AMI Purity HOM COM PAS CHAOS LISI'.split()\n"
          "open(sys.argv[3], 'w').write('metric,value\\n' + ''.join(f'{n},0.5\\n' for n in names))\nprint('R side done')\n")
FAKE_SCS = "import sys\nopen(sys.argv[3], 'w').write('metric,value\\nSCS,{}\\n')\n"


@pytest.fixture
def run_folder(tmp_path, monkeypatch):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "metrics.R").write_text(FAKE_R)
    (scripts / "scs.py").write_text(FAKE_SCS.format(12.5))
    monkeypatch.setattr(metrics_module, "SCRIPTS", scripts)
    monkeypatch.setattr(config, "interpreter", lambda key: sys.executable)
    (tmp_path / "x.h5ad").touch()
    run = tmp_path / "runs" / "M" / "x_cpu"
    run.mkdir(parents=True)
    (run / "cluster_results.csv").write_text("cell_id,cluster\na,0\nb,1\n")     # iSC.MEB's header
    (run / "run_info.json").write_text(json.dumps(dict(
        method="M", dataset="x", h5ad=str(tmp_path / "x.h5ad"), device_requested="cpu", success=True)))
    return run


def test_metrics_are_computed_stored_and_listed(run_folder):
    values = kdb.metrics(run_folder)
    assert list(values.index) == metrics_module.METRICS and values["SCS"] == 12.5
    assert "R side done" in (run_folder / "metric.log").read_text()

    (metrics_module.SCRIPTS / "metrics.R").write_text("raise SystemExit('boom')\n")
    assert kdb.metrics(run_folder)["SCS"] == 12.5               # read back, not computed again
    summary = kdb.load_results(run_folder.parents[1], score=True)
    assert summary.loc[0, "SCS"] == 12.5 and summary.loc[0, "PAS"] == 0.5

    with pytest.raises(kdb.MetricsFailed, match="metrics.R failed"):
        kdb.metrics(run_folder, recompute=True)
    assert kdb.metrics(run_folder)["SCS"] == 12.5               # a failed recompute keeps the earlier file

    # metrics.R scored against obs["clusters"]: another annotation gets none of its values
    other = kdb.load_results(run_folder.parents[1], reference_key="layer_guess")
    assert "PAS" not in other


def test_a_separate_metrics_r_is_enough_and_keeps_its_own_library(run_folder, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "interpreter", REAL_INTERPRETER)
    monkeypatch.setenv("PATH", str(tmp_path))                   # no Rscript for the methods
    monkeypatch.delenv("KDB_RSCRIPT", raising=False)
    monkeypatch.setenv("KDB_METRICS_RSCRIPT", sys.executable)
    monkeypatch.setenv("KDB_PY_PYTHON", sys.executable)
    monkeypatch.setenv("KDB_R_LIB", str(tmp_path / "methods_library"))
    (metrics_module.SCRIPTS / "metrics.R").write_text("import os\nprint('R_LIBS', os.environ.get('R_LIBS'))\n" + FAKE_R)
    kdb.metrics(run_folder)
    assert "methods_library" not in (run_folder / "metric.log").read_text()


def test_a_missing_value_is_an_error(run_folder):
    """PASTE's code under pandas >= 3 writes an empty SCS: that must not pass as a result."""
    (metrics_module.SCRIPTS / "scs.py").write_text(FAKE_SCS.format(""))
    with pytest.raises(kdb.MetricsFailed, match="no value for SCS"):
        kdb.metrics(run_folder)
    assert not (run_folder / "metric.csv").exists()


def test_one_domain_has_no_scs(run_folder):
    """Every shuffle of one label is the same labelling: the paper's results leave SCS empty there."""
    (metrics_module.SCRIPTS / "scs.py").write_text(FAKE_SCS.format(""))
    (run_folder / "cluster_results.csv").write_text("cell_id,cluster\na,1\nb,1\n")
    values = kdb.metrics(run_folder)
    assert pd.isna(values["SCS"]) and values["PAS"] == 0.5
    assert pd.isna(kdb.metrics(run_folder)["SCS"])              # and reads back the same


def test_cli_metrics_fills_in_the_missing_ones(run_folder, capsys):
    root = str(run_folder.parents[1])
    cli.main(["metrics", root])
    assert "SCS" in capsys.readouterr().out and (run_folder / "metric.csv").exists()
    (metrics_module.SCRIPTS / "scs.py").write_text("raise SystemExit('boom')\n")
    cli.main(["metrics", root])                                 # nothing to compute: no failure
    with pytest.raises(SystemExit) as stop:
        cli.main(["metrics", root, "--force"])
    assert stop.value.code not in (0, None)


@pytest.mark.skipif(os.environ.get("KDB_TEST_METRICS") != "1",
                    reason="needs the metric R packages and kdb_py, and about 4 minutes: set KDB_TEST_METRICS=1")
def test_the_real_code_reproduces_the_papers_values(tmp_path):
    (tmp_path / "cluster_results.csv").write_bytes((HERE / "data" / "D3_drsc_cluster_results.csv").read_bytes())
    values = kdb.metrics(tmp_path, EXAMPLE)
    for name, expected in PAPER_D3_DRSC.items():
        assert values[name] == pytest.approx(expected, rel=1e-9), name
    assert values["SCS"] > 100          # a permutation Z-score: its exact value differs between machines
