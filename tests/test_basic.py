"""Fast tests that need no method environment."""
import warnings

import pandas as pd
import pytest

import kdomainbench as kdb
from kdomainbench import runner
from kdomainbench.registry import get_method


def test_registry():
    assert len(kdb.list_methods()) == 10
    assert kdb.list_methods(gpu_only=True) == ["CellCharter", "DeepST", "SpatialDE2"]
    assert get_method("iscmeb").name == "iSC.MEB"
    with pytest.raises(ValueError):
        get_method("nope")


def test_device_env():
    m = get_method("DeepST")
    assert runner._build_env(m, "cpu", 0)["CUDA_VISIBLE_DEVICES"] == ""
    env = runner._build_env(m, "gpu", 0)
    assert env["CUDA_VISIBLE_DEVICES"] == "0" and env["CUDA_DEVICE_ORDER"] == "PCI_BUS_ID"


def test_cpu_only_method_warns_on_gpu(tmp_path, monkeypatch):
    """A CPU-only method asked for the GPU warns and is launched with no GPU visible."""
    seen = {}

    class Stop(Exception):
        pass

    def fake_popen(cmd, env, **kw):
        seen.update(cmd=cmd, env=env)
        raise Stop

    monkeypatch.setattr(runner.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(runner.config, "interpreter", lambda key: "python")
    h5ad = tmp_path / "x.h5ad"
    h5ad.touch()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        with pytest.raises(Stop):
            kdb.run("PRECAST", h5ad, device="gpu", out_dir=tmp_path / "o", verbose=False)
    assert any("no GPU implementation" in str(x.message) for x in w)
    assert seen["env"]["CUDA_VISIBLE_DEVICES"] == ""
    assert "--device" not in seen["cmd"]


def test_read_clusters_and_evaluate(tmp_path):
    (tmp_path / "cluster_results.csv").write_text("cell_id,cluster\na,1\nb,1\nc,2\nd,2\n")
    cl = kdb.read_clusters(tmp_path)
    assert list(cl.index) == ["a", "b", "c", "d"]
    res = kdb.evaluate(cl, pd.Series(["x", "x", "y", "y"], index=list("abcd")))
    assert res["k_estimated"] == 2 and res["k_error"] == 0 and res["ARI"] == 1.0
