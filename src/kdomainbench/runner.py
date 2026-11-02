"""Run one method on one h5ad file in its own environment."""
import json
import os
import subprocess
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

from . import config
from .registry import get_method
from .results import read_clusters

METHODS_DIR = Path(__file__).resolve().parent / "methods"


class MethodFailed(RuntimeError):
    """A method exited with an error or wrote no ``cluster_results.csv``.

    The message names the run's ``run.log`` and ends with its last 20 lines.
    """


def _build_env(method, device, gpu_id):
    env = dict(os.environ)
    env["KDB_METHODS_DIR"] = str(METHODS_DIR)
    if device == "gpu":
        env["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"   # GPU index = nvidia-smi index
        env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    else:
        env["CUDA_VISIBLE_DEVICES"] = ""
    if method.language == "Python":
        env["PYTHONNOUSERSITE"] = "1"           # keep ~/.local packages out of the method env
        env["PYTHONUNBUFFERED"] = "1"           # stream the log while the method runs
        env.pop("PYTHONPATH", None)
    else:
        lib = config.r_lib()
        if lib:                                 # isolated R library: hide user/site libraries
            env.update(R_LIBS=lib, R_LIBS_USER="/nonexistent", R_LIBS_SITE="/nonexistent")
    return env


def run(method, h5ad, kmax=30, device="cpu", out_dir=None, gpu_id=0, verbose=True):
    """Run one method on one ``.h5ad`` file and return its spatial domains.

    The method runs in its own environment, as a separate process. Its run folder gets
    ``cluster_results.csv``, ``run.log`` and ``run_info.json`` (device, run time, peak memory,
    estimated k).

    Parameters
    ----------
    method : str
        Method name, case-insensitive; see [list_methods][kdomainbench.list_methods].
    h5ad : str or path
        Input file: raw counts in ``X`` and the spatial fields the method reads.
    kmax : int
        Largest number of domains the method may consider. DeepST and SpaGCN ignore it.
    device : str
        ``"cpu"`` or ``"gpu"``. With ``"gpu"``, CellCharter, DeepST and SpatialDE2 run on GPU
        ``gpu_id``; the other methods have no GPU code and run on the CPU, with a warning.
    out_dir : str or path, optional
        Run folder. Default ``kdb_results/<method>/<dataset>_<device>``.
    gpu_id : int
        GPU to use with ``device="gpu"``, as numbered by ``nvidia-smi``.
    verbose : bool
        Print the method's output while it runs.

    Returns
    -------
    pandas.DataFrame
        One row per spot, indexed by ``spot_id``, with the domain label in ``cluster``.

    Raises
    ------
    MethodFailed
        The method stopped with an error; ``run_info.json`` is still written.
    FileNotFoundError
        ``h5ad`` or the method's environment is missing.
    ValueError
        Unknown method or device.

    Warns
    -----
    UserWarning
        ``device="gpu"`` for a method without GPU code.

    Examples
    --------
    >>> clusters = kdb.run("SpaGCN", "D1_151507_4k.h5ad", kmax=30)
    >>> clusters["cluster"].nunique()
    4
    >>> kdb.run("CellCharter", "D1_151507_4k.h5ad", device="gpu", gpu_id=0)
    """
    m = get_method(method)
    if device not in ("cpu", "gpu"):
        raise ValueError("device must be 'cpu' or 'gpu'")
    h5ad = Path(h5ad).resolve()
    if not h5ad.exists():
        raise FileNotFoundError(f"input file not found: {h5ad}")
    used = device
    if device == "gpu" and not m.gpu:
        warnings.warn(f"{m.name} has no GPU implementation; running it on the CPU.", stacklevel=2)
        used = "cpu"
    if not m.uses_kmax and verbose:
        print(f"[kdomainbench] note: {m.name} selects k by itself; kmax={kmax} is not used.")

    out = Path(out_dir or Path("kdb_results") / m.name / f"{h5ad.stem}_{device}").resolve()
    out.mkdir(parents=True, exist_ok=True)

    interp = config.interpreter(m.env)
    cmd = [interp, str(METHODS_DIR / m.script), *m.argv(str(h5ad), str(out), int(kmax))]
    if m.gpu:
        cmd += ["--device", used]
    if m.big_stack:  # PRECAST / iSC.MEB recurse deeply in C++
        cmd = ["bash", "-c", 'ulimit -s unlimited 2>/dev/null || true; exec "$@"', "bash", *cmd]

    if verbose:
        print(f"[kdomainbench] {m.name} on {used.upper()}"
              f"{f' (GPU {gpu_id})' if used == 'gpu' else ''} -> {out}")
    log_path = out / "run.log"
    t0 = time.time()
    with open(log_path, "w", buffering=1) as log:   # line-buffered: tail -f works
        proc = subprocess.Popen(cmd, cwd=out, env=_build_env(m, used, gpu_id),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        try:
            for line in proc.stdout:
                log.write(line)
                if verbose:
                    sys.stdout.write(line)
                    sys.stdout.flush()
            _, status, rusage = os.wait4(proc.pid, 0)
            proc.returncode = os.waitstatus_to_exitcode(status)
        except BaseException:
            proc.kill()
            raise
    wall = time.time() - t0

    info = dict(method=m.name, dataset=h5ad.stem, h5ad=str(h5ad), kmax=int(kmax),
                device_requested=device, device_used=used, gpu_id=gpu_id if used == "gpu" else None,
                returncode=proc.returncode, wall_time_s=round(wall, 2),
                peak_rss_mb=round(rusage.ru_maxrss / 1024, 1),   # Linux: KB
                started=datetime.fromtimestamp(t0).isoformat(timespec="seconds"),
                command=cmd)
    csv = out / "cluster_results.csv"
    info["success"] = proc.returncode == 0 and csv.exists()
    if info["success"]:
        clusters = read_clusters(csv)
        info["n_spots"] = int(len(clusters))
        info["k_estimated"] = int(clusters["cluster"].nunique())
    (out / "run_info.json").write_text(json.dumps(info, indent=2))
    if not info["success"]:
        tail = "".join(log_path.read_text().splitlines(True)[-20:])
        raise MethodFailed(f"{m.name} failed (exit {proc.returncode}); see {log_path}\n{tail}")
    if verbose:
        print(f"[kdomainbench] {m.name}: k = {info['k_estimated']}  ({wall:.0f} s)")
    return clusters
