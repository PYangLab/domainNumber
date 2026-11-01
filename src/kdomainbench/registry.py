"""Method registry: which script, which environment and which command line each method uses."""
from dataclasses import dataclass, field
from typing import Callable, List


@dataclass(frozen=True)
class Method:
    """One method: its script, its environment and how it is called.

    Get one with [get_method][kdomainbench.get_method]; you do not create them yourself.

    Attributes
    ----------
    name : str
        Canonical name, e.g. ``"CellCharter"``.
    language : str
        ``"R"`` or ``"Python"``.
    env : str
        Environment key: ``"r"`` (kdb_r), ``"py"`` (kdb_py) or ``"spatialde"`` (kdb_spatialde).
    script : str
        The method's script in ``kdomainbench/methods/``.
    argv : callable
        ``(h5ad, out_dir, kmax) -> list[str]``, the script's arguments.
    gpu : bool
        ``True`` if ``device="gpu"`` really runs the method on a GPU.
    uses_kmax : bool
        ``False`` if the method chooses k by itself and ignores ``kmax``.
    big_stack : bool
        ``True`` if the method needs ``ulimit -s unlimited``.
    reference : str
        The method's documentation or repository.
    aliases : tuple of str
        Other accepted names, e.g. ``("drsc",)``.
    """
    name: str
    language: str            # "R" or "Python"
    env: str                 # key in kdomainbench.config.ENVS
    script: str              # file in kdomainbench/methods/
    argv: Callable[[str, str, int], List[str]]   # (h5ad, out_dir, kmax) -> script arguments
    gpu: bool = False        # True: --device gpu really runs on the GPU
    uses_kmax: bool = True   # False: the method picks k by itself and ignores kmax
    big_stack: bool = False  # needs `ulimit -s unlimited`
    reference: str = ""
    aliases: tuple = field(default_factory=tuple)


_METHODS = [
    Method("PRECAST", "R", "r", "precast.R",
           lambda h, o, k: [h, "2", str(k), "Visium", o], big_stack=True,
           reference="https://feiyoung.github.io/PRECAST/"),
    Method("SC.MEB", "R", "r", "scmeb.R",
           lambda h, o, k: [h, "2", str(k), "Visium", o],
           reference="https://shufeyangyi2015310117.github.io/SC.MEB/", aliases=("scmeb", "sc_meb")),
    Method("BayesSpace", "R", "r", "bayesspace.R",
           lambda h, o, k: [h, o, str(k)],
           reference="https://www.ezstatconsulting.com/BayesSpace/"),
    Method("BNPSpace", "R", "r", "bnpspace.R",
           lambda h, o, k: [h, o, str(k)],
           reference="https://github.com/new-zbc/BNPSpace"),
    Method("DR.SC", "R", "r", "drsc.R",
           lambda h, o, k: [h, o, str(k), "Visium"],
           reference="https://feiyoung.github.io/DR.SC/", aliases=("drsc",)),
    Method("iSC.MEB", "R", "r", "iscmeb.R",
           lambda h, o, k: [h, "2", str(k), o], big_stack=True,
           reference="https://xiaozhangryy.github.io/iSC.MEB/", aliases=("iscmeb",)),
    Method("CellCharter", "Python", "py", "run_cellcharter.py",
           lambda h, o, k: ["--data_path", h, "--out_dir", o, "--kmax", str(k)], gpu=True,
           reference="https://cellcharter.readthedocs.io/"),
    Method("DeepST", "Python", "py", "run_deepst.py",
           lambda h, o, k: ["--data_path", h, "--save_path", o], gpu=True, uses_kmax=False,
           reference="https://github.com/JiangBioLab/DeepST"),
    Method("SpaGCN", "Python", "py", "run_spagcn.py",
           lambda h, o, k: ["--data_path", h, "--save_path", o + "/cluster_results.csv"], uses_kmax=False,
           reference="https://github.com/jianhuupenn/SpaGCN"),
    Method("SpatialDE2", "Python", "spatialde", "run_spatialde.py",
           lambda h, o, k: ["--data_path", h, "--out_dir", o, "--kmax", str(k)], gpu=True,
           reference="https://github.com/PMBio/SpatialDE", aliases=("spatialde",)),
]

METHODS = {m.name: m for m in _METHODS}
_LOOKUP = {}
for m in _METHODS:
    for key in (m.name, *m.aliases):
        _LOOKUP[key.lower()] = m


def get_method(name: str) -> Method:
    """Return one method's settings.

    Parameters
    ----------
    name : str
        Method name, case-insensitive. Aliases such as ``"drsc"``, ``"iscmeb"`` or
        ``"spatialde"`` work too.

    Returns
    -------
    Method
        Its language, environment, GPU support, use of ``kmax`` and reference.

    Raises
    ------
    ValueError
        Unknown method name.

    Examples
    --------
    >>> m = kdb.get_method("cellcharter")
    >>> m.name, m.language, m.env, m.gpu, m.uses_kmax
    ('CellCharter', 'Python', 'py', True, True)
    """
    try:
        return _LOOKUP[name.lower()]
    except KeyError:
        raise ValueError(f"unknown method {name!r}; choose from {list(METHODS)}") from None


def list_methods(gpu_only: bool = False) -> List[str]:
    """Return the names of the methods.

    Parameters
    ----------
    gpu_only : bool
        ``True`` = only the methods that can run on a GPU.

    Returns
    -------
    list of str
        Method names, R methods first.

    Examples
    --------
    >>> kdb.list_methods()
    ['PRECAST', 'SC.MEB', 'BayesSpace', 'BNPSpace', 'DR.SC', 'iSC.MEB',
     'CellCharter', 'DeepST', 'SpaGCN', 'SpatialDE2']
    >>> kdb.list_methods(gpu_only=True)
    ['CellCharter', 'DeepST', 'SpatialDE2']
    """
    return [m.name for m in _METHODS if m.gpu or not gpu_only]
