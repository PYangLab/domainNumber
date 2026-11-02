"""kdomainbench: benchmark of spatial-domain number (k) estimation methods.

    import kdomainbench as kdb
    clusters = kdb.run("CellCharter", "D1_151507_4k.h5ad", kmax=30, device="gpu")
"""
from .config import set_env
from .registry import METHODS, Method, get_method, list_methods
from .results import evaluate, ground_truth, k_accuracy, load_results, read_clusters
from .runner import MethodFailed, run
from . import plotting as pl

__version__ = "0.1.0"
__all__ = ["run", "run_all", "list_methods", "get_method", "Method", "METHODS", "set_env", "MethodFailed",
           "read_clusters", "ground_truth", "evaluate", "load_results", "k_accuracy", "pl"]


def run_all(h5ad, kmax=30, device="cpu", methods=None, out_root="kdb_results", **kw):
    """Run several methods on one ``.h5ad`` file, one after another.

    A method that fails is reported and skipped, so one failure does not stop the others.

    Parameters
    ----------
    h5ad : str or path
        Input file.
    kmax : int
        Largest number of domains the methods may consider.
    device : str
        ``"cpu"`` or ``"gpu"``; see [run][kdomainbench.run].
    methods : list of str, optional
        Methods to run. Default: all ten.
    out_root : str or path
        Each method writes to ``<out_root>/<method>/<dataset>_<device>``.
    **kw
        Passed to [run][kdomainbench.run], e.g. ``gpu_id`` or ``verbose``.

    Returns
    -------
    dict
        Method name -> its clusters, for the methods that succeeded.

    Examples
    --------
    >>> results = kdb.run_all("D1_151507_4k.h5ad", kmax=30)
    >>> results = kdb.run_all("D1_151507_4k.h5ad", methods=["DR.SC", "SC.MEB"])
    """
    from pathlib import Path
    out = {}
    for name in methods or list_methods():
        m = get_method(name)
        try:
            out[m.name] = run(m.name, h5ad, kmax=kmax, device=device,
                              out_dir=Path(out_root) / m.name / f"{Path(h5ad).stem}_{device}", **kw)
        except MethodFailed as e:
            print(f"[kdomainbench] {e}")
    return out
