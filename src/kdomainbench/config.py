"""Where the three method environments live.

Each environment is found, in order, from
  1. an environment variable (KDB_PY_PYTHON, KDB_SPATIALDE_PYTHON, KDB_RSCRIPT, KDB_R_LIB, and
     KDB_METRICS_RSCRIPT for the metric code, which otherwise runs in the R of the methods),
  2. a value set with ``kdomainbench.set_env(...)``,
  3. a conda env with the default name (kdb_py, kdb_spatialde) next to the environment
     kdomainbench runs in or under the usual conda roots, and ``Rscript`` on PATH for R.
"""
import os
import shutil
import sys
from pathlib import Path

DEFAULT_ENV_NAMES = {"py": "kdb_py", "spatialde": "kdb_spatialde"}
_ENV_VARS = {"py": "KDB_PY_PYTHON", "spatialde": "KDB_SPATIALDE_PYTHON", "r": "KDB_RSCRIPT",
             "metrics": "KDB_METRICS_RSCRIPT"}
_overrides = {}


def set_env(key, interpreter=None, r_lib=None):
    """Point one method environment at an interpreter, for this Python session.

    An environment variable (``KDB_PY_PYTHON``, ``KDB_SPATIALDE_PYTHON``, ``KDB_RSCRIPT``,
    ``KDB_METRICS_RSCRIPT``, ``KDB_R_LIB``) still wins over this setting.

    Parameters
    ----------
    key : str
        ``"py"`` (kdb_py), ``"spatialde"`` (kdb_spatialde), ``"r"`` (your R) or ``"metrics"``
        (the R of the metric code, when it is not the R of the methods).
    interpreter : str or path, optional
        The environment's ``python``, or ``Rscript`` for ``"r"`` and ``"metrics"``. It is
        checked when a method starts, not here.
    r_lib : str or path, optional
        An isolated R library for the R methods, whatever ``key`` is. They then see only this
        library and base R. The metric code uses it too, unless ``"metrics"`` names its own
        ``Rscript``.

    Raises
    ------
    ValueError
        Unknown key.

    Examples
    --------
    >>> kdb.set_env("spatialde", "/opt/envs/kdb_spatialde/bin/python")
    >>> kdb.set_env("r", "/usr/bin/Rscript", r_lib="/path/to/R/library")
    """
    if key not in _ENV_VARS:
        raise ValueError(f"key must be one of {list(_ENV_VARS)}, not {key!r}")
    if interpreter:
        _overrides[key] = str(interpreter)
    if r_lib:
        _overrides["r_lib"] = str(r_lib)


def _env_dirs():
    """Folders that may hold the conda envs: first the one this Python's own env is in."""
    dirs = [Path(sys.prefix).parent]
    for var in ("CONDA_EXE", "MAMBA_EXE"):
        if os.environ.get(var):
            dirs.append(Path(os.environ[var]).resolve().parent.parent / "envs")
    if os.environ.get("CONDA_PREFIX"):
        p = Path(os.environ["CONDA_PREFIX"])
        dirs.append(p.parent if p.parent.name == "envs" else p / "envs")
    home = Path.home()
    dirs += [home / d / "envs" for d in ("anaconda3", "miniconda3", "mambaforge", "miniforge3", ".conda")]
    return list(dict.fromkeys(dirs))


def configured(key):
    """The interpreter set by environment variable or set_env, else None."""
    for source, path in ((_ENV_VARS[key], os.environ.get(_ENV_VARS[key])),
                         (f"set_env({key!r}, ...)", _overrides.get(key))):
        if path:
            if not shutil.which(path):
                raise FileNotFoundError(f"{source} points to {path}, which is not an interpreter")
            return path
    return None


def interpreter(key):
    """The interpreter of ``"py"``, ``"spatialde"``, ``"r"`` or ``"metrics"``, looked up in the order of the
    module docstring. ``"metrics"`` without a setting of its own is ``"r"``. The FileNotFoundError says how to
    install or name it."""
    path = configured(key)
    if path:
        return path
    if key == "metrics":
        return interpreter("r")
    if key == "r":
        found = shutil.which("Rscript")
        if found:
            return found
        raise FileNotFoundError("Rscript not found: install R 4.4 or later, or load it (for example "
                                "'module load R'), or set KDB_RSCRIPT=/path/to/Rscript")
    name = DEFAULT_ENV_NAMES[key]
    for d in _env_dirs():
        py = d / name / "bin" / "python"
        if py.exists():
            return str(py)
    raise FileNotFoundError(f"conda env {name!r} not found: create it with 'bash envs/install_envs.sh' "
                            f"(Installation, step 2), or set {_ENV_VARS[key]}=/path/to/python")


def r_lib():
    """Optional isolated R library (only this library + base R are visible to the R methods)."""
    return os.environ.get("KDB_R_LIB") or _overrides.get("r_lib")


def child_env(language, r_library=True):
    """The environment variables for a method or metric process, without the caller's own packages."""
    env = dict(os.environ)
    if language == "Python":
        env["PYTHONNOUSERSITE"] = "1"           # keep ~/.local packages out of the environment
        env["PYTHONUNBUFFERED"] = "1"           # stream the log while the process runs
        env.pop("PYTHONPATH", None)
    elif r_library and r_lib():                 # isolated R library: hide user and site libraries
        env.update(R_LIBS=r_lib(), R_LIBS_USER="/nonexistent", R_LIBS_SITE="/nonexistent")
    return env
