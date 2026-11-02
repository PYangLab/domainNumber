"""Where the three method environments live.

Each environment is found, in order, from
  1. an environment variable (KDB_PY_PYTHON, KDB_SPATIALDE_PYTHON, KDB_RSCRIPT, KDB_R_LIB),
  2. a value set with ``kdomainbench.set_env(...)``,
  3. a conda env with the default name (kdb_py, kdb_spatialde) under the usual conda roots,
     and ``Rscript`` on PATH for R.
"""
import os
import shutil
from pathlib import Path

DEFAULT_ENV_NAMES = {"py": "kdb_py", "spatialde": "kdb_spatialde"}
_ENV_VARS = {"py": "KDB_PY_PYTHON", "spatialde": "KDB_SPATIALDE_PYTHON", "r": "KDB_RSCRIPT"}
_overrides = {}


def set_env(key, interpreter=None, r_lib=None):
    """Point one method environment at an interpreter, for this Python session.

    An environment variable (``KDB_PY_PYTHON``, ``KDB_SPATIALDE_PYTHON``, ``KDB_RSCRIPT``,
    ``KDB_R_LIB``) still wins over this setting.

    Parameters
    ----------
    key : str
        ``"py"`` (kdb_py), ``"spatialde"`` (kdb_spatialde) or ``"r"`` (your R).
    interpreter : str or path, optional
        The environment's ``python``, or ``Rscript`` for ``"r"``.
    r_lib : str or path, optional
        An isolated R library. The R methods then see only this library and base R.

    Raises
    ------
    ValueError
        Unknown key.

    Examples
    --------
    >>> kdb.set_env("spatialde", "/opt/envs/kdb_spatialde/bin/python")
    >>> kdb.set_env("r", "/usr/bin/Rscript", r_lib="/opt/kdb_r/library")
    """
    if key not in _ENV_VARS:
        raise ValueError(f"env must be one of {list(_ENV_VARS)}")
    if interpreter:
        _overrides[key] = str(interpreter)
    if r_lib:
        _overrides["r_lib"] = str(r_lib)


def _conda_roots():
    roots = []
    for var in ("CONDA_EXE", "MAMBA_EXE"):
        if os.environ.get(var):
            roots.append(Path(os.environ[var]).resolve().parent.parent)
    if os.environ.get("CONDA_PREFIX"):
        p = Path(os.environ["CONDA_PREFIX"])
        roots.append(p.parent.parent if p.parent.name == "envs" else p)
    home = Path.home()
    roots += [home / d for d in ("anaconda3", "miniconda3", "mambaforge", "miniforge3", ".conda")]
    return list(dict.fromkeys(roots))


def interpreter(key):
    if os.environ.get(_ENV_VARS[key]):
        return os.environ[_ENV_VARS[key]]
    if key in _overrides:
        return _overrides[key]
    if key == "r":
        found = shutil.which("Rscript")
        if found:
            return found
        raise FileNotFoundError("Rscript not found; set KDB_RSCRIPT or kdomainbench.set_env('r', ...)")
    name = DEFAULT_ENV_NAMES[key]
    for root in _conda_roots():
        py = root / "envs" / name / "bin" / "python"
        if py.exists():
            return str(py)
    raise FileNotFoundError(f"conda env {name!r} not found; create it from envs/{name}.yml "
                            f"or set {_ENV_VARS[key]}=/path/to/python")


def r_lib():
    """Optional isolated R library (only this library + base R are visible to the R methods)."""
    return os.environ.get("KDB_R_LIB") or _overrides.get("r_lib")
