"""Run one method on one h5ad file in the environment it needs."""
import json
import os
import signal
import subprocess
import sys
import threading
import time
import warnings
from datetime import datetime
from pathlib import Path

from . import __version__, config
from .registry import get_method, list_methods
from .results import read_clusters

METHODS_DIR = Path(__file__).resolve().parent / "methods"
# Variables that change what a method does: run_info.json records them (a test checks the list
# against the method scripts).
RECORDED_ENV = ("KDB_METHODS_DIR", "CUDA_VISIBLE_DEVICES", "CUDA_DEVICE_ORDER", "R_LIBS", "PRECAST_CORES",
                "SCMEB_PARALLEL", "SCMEB_CORES")
# The methods with big_stack recurse deeply in C++ and need an unlimited stack
_BIG_STACK = ('ulimit -s unlimited 2>/dev/null || echo "[kdomainbench] could not raise the stack limit '
              '(ulimit -s: $(ulimit -s)); the method may stop with a stack error"; exec "$@"')


class MethodFailed(RuntimeError):
    """A method exited with an error or wrote no labels to ``cluster_results.csv``.

    The message names the run's ``run.log`` and ends with its last 20 lines. ``log`` is the path
    of that ``run.log``.
    """

    def __init__(self, message, log=None):
        super().__init__(message)
        self.log = log


def _build_env(method, device, gpu_id):
    env = config.child_env(method.language)
    env["KDB_METHODS_DIR"] = str(METHODS_DIR)
    if device != "gpu":
        env["CUDA_VISIBLE_DEVICES"] = ""
    elif gpu_id is not None or not env.get("CUDA_VISIBLE_DEVICES"):
        env["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"   # GPU index = nvidia-smi index
        env["CUDA_VISIBLE_DEVICES"] = str(0 if gpu_id is None else gpu_id)
    # else: keep the GPUs a scheduler assigned through CUDA_VISIBLE_DEVICES
    return env


def _check(method, h5ad, kmax, device):
    """Raise, before anything runs, when ``method`` (a Method record) cannot run with these settings."""
    if device not in ("cpu", "gpu"):
        raise ValueError(f"device must be 'cpu' or 'gpu', not {device!r}")
    if method.uses_kmax and kmax < 2:
        raise ValueError("kmax must be at least 2")
    if method.kmax_limit and kmax > method.kmax_limit:
        raise ValueError(f"{method.name} accepts kmax up to {method.kmax_limit}")
    hint = "A Space Ranger folder becomes an .h5ad file as in 'Your own data', step 1"
    if h5ad.is_dir():
        raise FileNotFoundError(f"{h5ad} is a folder, not an .h5ad file. {hint}")
    if not h5ad.is_file():
        raise FileNotFoundError(f"input file not found: {h5ad}")
    if h5ad.suffix != ".h5ad":
        raise ValueError(f"{h5ad} is not an .h5ad file. {hint}")


def _run_dir(out_root, method, h5ad, device):
    """The run folder of one method on one file: ``<out_root>/<method>/<dataset>_<device>``."""
    return Path(out_root) / method.name / f"{Path(h5ad).stem}_{device}"


def _write_packages(interp, language, out, env):
    """``packages.txt``: the packages and versions of the method's environment."""
    if language == "R":
        cmd = [interp, "-e", 'write.csv(installed.packages()[, c("Package", "Version", "LibPath")], row.names = FALSE)']
    else:                                   # the standard library, so also a Python without pip
        cmd = [interp, "-c", "import importlib.metadata as m; print('\\n'.join(sorted("
               "{f'{d.metadata[\"Name\"]}=={d.version}' for d in m.distributions()}, key=str.lower)))"]
    with open(out / "packages.txt", "w") as f:
        subprocess.run(cmd, cwd=out, env=env, stdout=f, stderr=subprocess.STDOUT)


def run(method, h5ad, kmax=30, device="cpu", out_root="kdb_results", gpu_id=None, verbose=True):
    """Run one method on one ``.h5ad`` file and return its spatial domains.

    The method runs in the environment it needs, as a separate process, and writes to its run
    folder ``<out_root>/<method>/<dataset>_<device>``. A run into a folder that already holds
    a run replaces it.

    Parameters
    ----------
    method : str
        Method name, case-insensitive, from [list_methods][kdomainbench.list_methods].
    h5ad : str or path
        Input ``.h5ad`` file with raw counts in ``X``. The R methods read ``obs["array_row"]``
        and ``obs["array_col"]``, SpaGCN ``obs["pixel_row"]`` and ``obs["pixel_col"]``, and
        CellCharter, DeepST and SpatialDE2 ``obsm["spatial"]``. An AnnData object in memory is
        not accepted: save it with ``adata.write_h5ad(...)`` first.
    kmax : int
        Largest number of domains the method may consider, at least 2. DeepST and SpaGCN
        ignore it. BNPSpace starts from it and accepts at most 30.
    device : str
        ``"cpu"`` or ``"gpu"``. With ``"gpu"``, CellCharter, DeepST and SpatialDE2 are started
        with a GPU visible. The other methods have no GPU code and run on the CPU, with a
        warning.
    out_root : str or path
        Folder that collects the run folders, the same as for [run_all][kdomainbench.run_all].
    gpu_id : int or str, optional
        GPU to use with ``device="gpu"``, as numbered by ``nvidia-smi``. Default: the GPUs
        already named in ``CUDA_VISIBLE_DEVICES``, as a job scheduler sets it, else GPU 0.
    verbose : bool
        Print the method's output while it runs.

    Returns
    -------
    pandas.DataFrame
        One row per spot, indexed by ``spot_id``, with the domain label (as a string) in
        ``cluster``.

    Raises
    ------
    MethodFailed
        The method stopped with an error or wrote no labels. ``run_info.json`` records the
        run with ``"success": false``.
    FileNotFoundError
        ``h5ad`` does not exist or is a folder, or the method's environment is missing.
        Nothing is written.
    ValueError
        Unknown method or device, an input file that is not ``.h5ad``, or a ``kmax`` the
        method does not accept.

    Warns
    -----
    UserWarning
        ``device="gpu"`` for a method without GPU code.

    Notes
    -----
    The run folder holds:

    * ``cluster_results.csv``: the label of each spot.
    * ``run.log``: everything the method printed.
    * ``packages.txt``: the packages and versions of the method's environment.
    * ``run_info.json``, with these fields:

        - ``method``, ``dataset`` (the file name without ``.h5ad``), ``h5ad`` (the input
          path), ``kmax``.
        - ``device_requested``, and ``device_used``, which is ``"cpu"`` for a method without
          GPU code. ``gpu_id``: the GPU of a GPU run.
        - ``started``, ``wall_time_s`` (the whole run, data loading included) and
          ``peak_rss_mb`` (peak memory of the method's largest process, 1 GB = 1024 MB,
          without its worker processes and the GPU).
        - ``returncode`` and ``success``. A successful run adds ``n_spots`` (spots with a
          label) and ``k_estimated``.
        - ``kdomainbench`` (the package version), ``command`` (the call of the method script,
          started in the run folder, to rerun it by hand) and ``env`` (the environment
          variables that change what the method does).

    Examples
    --------
    >>> clusters = kdb.run("SpaGCN", "data/D3_151509_5k.h5ad", kmax=30)
    >>> clusters["cluster"].nunique()
    4
    >>> kdb.run("CellCharter", "data/D3_151509_5k.h5ad", device="gpu", gpu_id=0)
    """
    m = get_method(method)
    kmax, h5ad = int(kmax), Path(h5ad).absolute()
    _check(m, h5ad, kmax, device)
    interp = config.interpreter(m.env)      # before anything is written: a missing environment leaves no trace
    used = device
    if device == "gpu" and not m.gpu:
        warnings.warn(f"{m.name} has no GPU implementation. It runs on the CPU.", stacklevel=2)
        used = "cpu"
    if not m.uses_kmax and verbose:
        print(f"[kdomainbench] note: {m.name} selects k by itself, so kmax={kmax} is not used.")

    out = _run_dir(out_root, m, h5ad, device).resolve()
    out.mkdir(parents=True, exist_ok=True)
    cmd = [interp, str(METHODS_DIR / m.script), *m.argv(str(h5ad), str(out), kmax)]
    if m.gpu:
        cmd += ["--device", used]
    if m.big_stack:
        cmd = ["bash", "-c", _BIG_STACK, "bash", *cmd]      # the second "bash" is $0, the rest is "$@"
    env = _build_env(m, used, gpu_id)
    gpus = env["CUDA_VISIBLE_DEVICES"] if used == "gpu" else None

    if verbose:
        print(f"[kdomainbench] {m.name} on {used.upper()}{f' (GPU {gpus})' if gpus else ''} -> {out}")
    log_path, csv, info_path = out / "run.log", out / "cluster_results.csv", out / "run_info.json"
    for stale in (csv, out / "metric.csv"):     # an earlier run's labels and metrics must not pass for this run's
        stale.unlink(missing_ok=True)
    _write_packages(interp, m.language, out, env)
    t0 = time.time()
    info = dict(method=m.name, dataset=h5ad.stem, h5ad=str(h5ad), kmax=kmax,
                device_requested=device, device_used=used,
                gpu_id=int(gpus) if gpus and gpus.isdigit() else gpus,
                returncode=None, wall_time_s=None, peak_rss_mb=None,
                started=datetime.fromtimestamp(t0).isoformat(timespec="seconds"),
                kdomainbench=__version__, command=cmd,
                env={k: env[k] for k in RECORDED_ENV if k in env}, success=False)
    info_path.write_text(json.dumps(info, indent=2))    # stands as the record if the run is killed

    def _terminate(signum, frame):          # scancel, a time limit, a closed terminal: stop the method too
        raise SystemExit(128 + signum)
    stops = ()
    if threading.current_thread() is threading.main_thread():      # signal.signal works only there
        # a signal the caller ignores (nohup) stays ignored
        stops = tuple(s for s in (signal.SIGTERM, signal.SIGHUP) if signal.getsignal(s) is not signal.SIG_IGN)
    previous = [signal.signal(sig, _terminate) for sig in stops]
    try:
        with open(log_path, "w", buffering=1) as log:   # line-buffered: tail -f works
            proc = subprocess.Popen(cmd, cwd=out, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, bufsize=1, start_new_session=True)
            try:
                for line in proc.stdout:
                    log.write(line)
                    if verbose:
                        sys.stdout.write(line)
                        sys.stdout.flush()
                proc.stdout.close()
                # os.wait4, not proc.wait(): it also returns the peak memory (rusage). It collects the
                # process itself, so Popen is told the return code by hand.
                _, status, rusage = os.wait4(proc.pid, 0)
                proc.returncode = os.waitstatus_to_exitcode(status)
            except BaseException:
                os.killpg(proc.pid, signal.SIGKILL)     # the method and the workers it started
                raise
    finally:
        for sig, handler in zip(stops, previous):
            signal.signal(sig, handler)
    wall = time.time() - t0

    rss_per_mb = 1024 ** 2 if sys.platform == "darwin" else 1024    # ru_maxrss: bytes on macOS, KB on Linux
    info.update(returncode=proc.returncode, wall_time_s=round(wall, 2),
                peak_rss_mb=round(rusage.ru_maxrss / rss_per_mb, 1))
    problem = f"exit {proc.returncode}"
    if proc.returncode == 0:
        try:
            clusters = read_clusters(csv)
            problem = "no labels in cluster_results.csv" if clusters.empty else None
        except FileNotFoundError:
            problem = "no cluster_results.csv written"
        except ValueError as e:
            problem = str(e)
    info["success"] = problem is None
    if info["success"]:
        info["n_spots"] = int(len(clusters))
        info["k_estimated"] = int(clusters["cluster"].nunique())
    info_path.write_text(json.dumps(info, indent=2))
    if problem:
        tail = "".join(log_path.read_text().splitlines(True)[-20:])
        raise MethodFailed(f"{m.name} failed ({problem}), see {log_path}\n{tail}", log=log_path)
    if verbose:
        print(f"[kdomainbench] {m.name}: k = {info['k_estimated']}  ({wall:.0f} s)")
    return clusters


def run_all(h5ad, kmax=30, device="cpu", methods=None, out_root="kdb_results", gpu_id=None, verbose=True):
    """Run several methods on one ``.h5ad`` file, one after another.

    A method that fails, or whose environment is missing, is reported and skipped, so it
    does not stop the others. At the end one warning names every method that did not finish.

    Parameters
    ----------
    h5ad : str or path
        Input file, see [run][kdomainbench.run].
    kmax : int
        Largest number of domains the methods may consider. BNPSpace accepts at most 30: for a
        larger ``kmax``, leave it out with ``methods=``.
    device : str
        ``"cpu"`` or ``"gpu"``, see [run][kdomainbench.run].
    methods : str or list of str, optional
        Methods to run. Default: all ten. Each one runs again, also when ``out_root``
        already holds a run of it.
    out_root : str or path
        Each method writes to ``<out_root>/<method>/<dataset>_<device>``.
    gpu_id : int or str, optional
        GPU for ``device="gpu"``, see [run][kdomainbench.run].
    verbose : bool
        Print the methods' output while they run.

    Returns
    -------
    dict
        Method name -> its clusters, for the methods that succeeded.

    Raises
    ------
    FileNotFoundError
        ``h5ad`` does not exist or is a folder.
    ValueError
        An unknown method or device, an input file that is not ``.h5ad``, or a ``kmax`` that
        one of the methods does not accept. Raised before the first method starts.

    Warns
    -----
    UserWarning
        Some methods did not finish. The warning names them and their logs.

    Examples
    --------
    >>> results = kdb.run_all("data/D3_151509_5k.h5ad", kmax=30)
    >>> results = kdb.run_all("data/D3_151509_5k.h5ad", methods=["DR.SC", "SC.MEB"])
    >>> sorted(results)
    ['DR.SC', 'SC.MEB']
    """
    if isinstance(methods, str):
        methods = [methods]
    kmax, h5ad = int(kmax), Path(h5ad).absolute()
    todo = [get_method(name) for name in (list_methods() if methods is None else methods)]
    for m in todo:                              # before the first method starts, not hours later
        _check(m, h5ad, kmax, device)
    results, problems = {}, []
    for m in todo:
        try:
            results[m.name] = run(m.name, h5ad, kmax=kmax, device=device, out_root=out_root, gpu_id=gpu_id,
                                  verbose=verbose)
        except MethodFailed as e:
            print(f"[kdomainbench] {e}")
            problems.append(f"{m.name} failed, see {e.log}")
        except FileNotFoundError as e:          # the method's environment is missing
            print(f"[kdomainbench] {m.name} not run: {e}")
            problems.append(f"{m.name} not run: {e}")
    if problems:
        sys.stdout.flush()                      # the warning (stderr) after the methods' output, also in a log file
        warnings.warn(f"{len(problems)} of {len(todo)} methods did not finish:\n  " + "\n  ".join(problems),
                      stacklevel=2)
    return results
