"""kdomainbench: benchmark of spatial-domain number (k) estimation methods.

    import kdomainbench as kdb
    clusters = kdb.run("SpaGCN", "data/D3_151509_5k.h5ad", kmax=30)
"""
__version__ = "0.1.0"                           # first: runner records it, and pyproject.toml reads it

from .config import set_env  # noqa: E402
from .paper_metrics import MetricsFailed, metrics  # noqa: E402
from .registry import METHODS, Method, get_method, list_methods  # noqa: E402
from .results import evaluate, k_accuracy, load_results, read_clusters, reference_annotation  # noqa: E402
from .runner import MethodFailed, run, run_all  # noqa: E402
from . import plotting as pl  # noqa: E402

__all__ = ["run", "run_all", "list_methods", "get_method", "Method", "METHODS", "set_env", "MethodFailed",
           "read_clusters", "reference_annotation", "evaluate", "metrics", "MetricsFailed", "load_results",
           "k_accuracy", "pl"]
