"""Execute the code examples of the documentation and report each one.

Every ```python block of a page runs in order, in one namespace per page, inside a scratch
folder that holds `data/D3_151509_5k.h5ad`. For "Your own data" and the FAQ the folder also
holds `my_sample.h5ad` (the same sample without its annotation, with a blank tissue image),
a Space Ranger `outs/` folder of it, and the annotation as `annotation.csv` / `my_labels.csv`.
Shell blocks run line by line when they are `kdomainbench ...` or `python -c ...` commands,
with the `kdomainbench` of the Python that runs this script. Docstring examples of the public
API run too.

To keep it to about an hour and off the GPU:
* fast methods (FAST below) really run, once per method and input file; later calls reuse
  that run;
* slow methods reuse finished runs from --reuse (a folder of <method>/<run>/ run folders);
* device="gpu" never starts a GPU job: it reuses the CPU run. Shell commands with --gpu /
  -d gpu, and `-m all`, are skipped.
Each stand-in run first checks its arguments as kdb.run does.

It checks that each example runs. It does not compare what an example prints with the output
shown on the page, which comes from the site's own runs.

    python scripts/check_docs.py --h5ad D3_151509_5k.h5ad --reuse kdb_test/results --work /tmp/check
"""
import argparse
import contextlib
import io
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASICS = ["tutorials/discover.md", "tutorials/run.md", "tutorials/evaluate.md"]
PAGES = ["installation.md", "quickstart.md", *BASICS, "tutorials/benchmark.md", "how-to/own_data.md", "faq.md",
         "api.md", "reference/methods.md", "reference/setup.md", "reference/cli.md"]
FAST = {"SpaGCN", "DR.SC", "SC.MEB", "iSC.MEB"}
SKIP_SHELL = re.compile(r"--gpu|-d gpu|-m all")

os.environ["CUDA_VISIBLE_DEVICES"] = ""          # nothing in this process may touch a GPU
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import kdomainbench as kdb  # noqa: E402
from kdomainbench import runner  # noqa: E402

REAL_RUN = runner.run
# shell blocks call the kdomainbench command of the Python that runs this script, not another one on PATH
SHELL_ENV = dict(os.environ, PATH=f"{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}")
_cache = {}          # (method, input file) -> finished run folder (real or reused)
LOG = []


def note(msg):
    LOG.append(msg)
    print("    " + msg, flush=True)


def stub_run(method, h5ad, kmax=30, device="cpu", out_root="kdb_results", gpu_id=None, verbose=True):
    m = kdb.get_method(method)
    runner._check(m, Path(h5ad).absolute(), int(kmax), device)      # the arguments the page passes
    out = runner._run_dir(out_root, m, h5ad, device).resolve()
    key = (m.name, Path(h5ad).resolve())    # a fast method really runs on each input file, e.g. one without annotation
    if key not in _cache and m.name in FAST:
        note(f"REAL RUN {m.name} (cpu) -> {runner._run_dir(out_root, m, h5ad, 'cpu')}")
        t = time.time()
        REAL_RUN(m.name, h5ad, kmax=kmax, device="cpu", out_root=out_root, verbose=False)
        note(f"  finished in {time.time() - t:.0f} s")
        _cache[key] = runner._run_dir(out_root, m, h5ad, "cpu").resolve()
    elif key not in _cache:
        src = next((p for p in sorted((ARGS.reuse / m.name).glob("*")) if (p / "run_info.json").exists()), None)
        if src is None:
            raise RuntimeError(f"no finished run of {m.name} to reuse under {ARGS.reuse}")
        _cache[key] = src
    src = _cache[key]
    if src != out:
        if src in out.parents:
            raise RuntimeError(f"{out} lies inside the run folder {src}; the docs nest run folders")
        shutil.copytree(src, out, dirs_exist_ok=True)
        note(f"reused {m.name} run ({'GPU not run; CPU result' if device == 'gpu' else 'cpu'}) -> {out}")
    return kdb.read_clusters(out)


def blocks(md):
    """(kind, code) for each fenced block; kind is 'python' or 'shell'."""
    text = (ROOT / "docs" / md).read_text()
    for m in re.finditer(r"^( *)```(\w+)[^\n]*\n(.*?)^\1```", text, re.S | re.M):
        indent, lang, body = m.group(1), m.group(2), m.group(3)
        body = "\n".join(line[len(indent):] for line in body.splitlines())
        if lang == "python":
            yield "python", body
        elif lang in ("bash", "console"):
            yield "shell", body


SCALE = {"spot_diameter_fullres": 5.0, "tissue_hires_scalef": 1.0}


def blank_image(xy):
    """A light grey tissue image that covers the spot coordinates ``xy``."""
    return np.full((int(xy.max()) + 20, int(xy.max()) + 20, 3), 0.92)


def space_ranger_folder(adata, out):
    """A Space Ranger outs/ folder with the spots of ``adata``, for step 1 of "Your own data"."""
    import json
    import h5py
    import scipy.sparse as sp
    (out / "spatial").mkdir(parents=True, exist_ok=True)
    x = sp.csc_matrix(sp.csr_matrix(adata.X).T.astype(np.int32))           # genes x spots
    n = adata.n_vars
    with h5py.File(out / "filtered_feature_bc_matrix.h5", "w") as f:
        f.attrs.update(library_ids=np.array([b"sample"]), filetype="matrix", version=2)
        for name, v in (("barcodes", adata.obs_names.to_numpy().astype("S")), ("data", x.data),
                        ("indices", x.indices.astype(np.int64)), ("indptr", x.indptr.astype(np.int64)),
                        ("shape", np.array(x.shape, dtype=np.int32))):
            f.create_dataset(f"matrix/{name}", data=v)
        for name, v in (("_all_tag_keys", np.array([b"genome"])), ("feature_type", np.array([b"Gene Expression"] * n)),
                        ("genome", np.array([b"GRCh38"] * n)), ("id", np.array([f"G{i}" for i in range(n)], dtype="S")),
                        ("name", adata.var_names.to_numpy().astype("S"))):
            f.create_dataset(f"matrix/features/{name}", data=v)
    xy = adata.obsm["spatial"]
    pd.DataFrame({"barcode": adata.obs_names, "in_tissue": 1, "array_row": adata.obs["array_row"].astype(int),
                  "array_col": adata.obs["array_col"].astype(int), "pxl_row_in_fullres": xy[:, 1].round().astype(int),
                  "pxl_col_in_fullres": xy[:, 0].round().astype(int)}).to_csv(out / "spatial/tissue_positions.csv",
                                                                               index=False)
    (out / "spatial/scalefactors_json.json").write_text(json.dumps(dict(SCALE, tissue_lowres_scalef=1.0)))
    for name in ("tissue_hires_image.png", "tissue_lowres_image.png"):
        matplotlib.pyplot.imsave(out / "spatial" / name, blank_image(xy))


def run_python(code, ns, label):
    code = code.replace("path/to/sample/outs", "outs")      # the folder space_ranger_folder builds
    if any("path/to/" in line.split("#")[0] for line in code.splitlines()):    # in the code, not in a comment
        note("skipped: template with placeholder paths")
        return True
    buf = io.StringIO()
    with warnings.catch_warnings(record=True) as w, contextlib.redirect_stdout(buf):
        warnings.simplefilter("always")
        try:
            exec(compile(code, label, "exec"), ns)
            ok = True
        except Exception:
            ok = False
            err = traceback.format_exc(limit=3)
    for x in w:
        if issubclass(x.category, UserWarning):
            note(f"warning: {x.message}")
    if buf.getvalue().strip():
        note("stdout: " + buf.getvalue().strip().replace("\n", "\n            ")[:1500])
    if not ok:
        note("FAILED:\n" + err)
    return ok


def last_value(code, ns):
    """Show the value of a block's last bare expression, as a notebook would."""
    lines = [ln for ln in code.strip().splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if not lines:
        return
    expr = lines[-1].split("#")[0].strip()
    if not expr or "=" in expr.replace("==", "") or expr.startswith(("for ", "import ", "from ", "print(")):
        return
    try:
        val = eval(expr, ns)
    except Exception:
        return
    if val is not None and not hasattr(val, "figure") and type(val).__name__ not in ("Figure", "Axes"):
        note("value: " + repr(val).replace("\n", "\n            ")[:1500])


def run_shell(code):
    ok = True
    for line in code.splitlines():
        cmd = line.split("  #")[0].strip()
        if cmd.startswith("$ "):
            cmd = cmd[2:]
        if not cmd or cmd.startswith("#") or not cmd.startswith(("kdomainbench", "python -c")):
            continue
        if SKIP_SHELL.search(cmd):
            note(f"skipped (GPU or all methods): {cmd}")
            continue
        note(f"$ {cmd}")
        t = time.time()
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=SHELL_ENV)
        out = (r.stdout + r.stderr).strip()
        note(f"  exit {r.returncode} in {time.time() - t:.0f} s: " + out[-800:].replace("\n", "\n            "))
        ok &= r.returncode == 0
    return ok


def docstring_examples():
    import inspect
    # every public function and class, but not kdb.metrics: it needs the metric R packages and
    # 3 minutes, and KDB_TEST_METRICS=1 tests it against the paper's values
    funcs = [getattr(kdb, n) for n in kdb.__all__ if callable(getattr(kdb, n)) and n != "metrics"]
    funcs += [getattr(kdb.pl, n) for n in kdb.pl.__all__]
    for f in funcs:
        doc = inspect.getdoc(f) or ""
        code = "\n".join(ln[4:] for ln in doc.splitlines() if ln.startswith(">>> "))
        if code:
            yield f.__name__, code


def main():
    work = ARGS.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    kdb.run = runner.run = stub_run        # kdb.run for the pages, runner.run for run_all
    results = {}
    pages = ARGS.pages or PAGES
    targets = [(p, list(blocks(p))) for p in pages if p != "docstrings"] + ([("docstrings", [("python", c) for _, c in docstring_examples()])]
                                                         if not ARGS.pages or "docstrings" in ARGS.pages else [])
    for page, bl in targets:
        # Installation, Quickstart and the step-by-step tutorials share one folder (kdb_results/ from
        # "Run a method" feeds "Evaluate a run"), as for a reader who follows them in order; the
        # benchmark tutorial and the docstrings start fresh.
        shared = page in ("installation.md", "quickstart.md", "reference/setup.md", *BASICS)
        d = work / ("getstarted" if shared else page.replace("/", "_").replace(".md", ""))
        (d / "data").mkdir(parents=True, exist_ok=True)
        for link in (d / "data" / ARGS.h5ad.name, d / ARGS.h5ad.name):
            if not link.exists():
                link.symlink_to(ARGS.h5ad.resolve())
        os.chdir(d)
        if page in ("how-to/own_data.md", "faq.md") and not Path("my_sample.h5ad").exists():
            import anndata
            adata = anndata.read_h5ad(ARGS.h5ad)
            for name in ("annotation.csv", "my_labels.csv"):
                adata.obs["clusters"].to_csv(name)
            del adata.obs["clusters"]
            # what sc.read_visium adds and the example file lacks: a (blank) tissue image
            adata.uns["spatial"] = {"sample": {"images": {"hires": blank_image(adata.obsm["spatial"])},
                                               "scalefactors": SCALE}}
            adata.write_h5ad("my_sample.h5ad")      # a copy: the tutorial writes to this file
            space_ranger_folder(adata, Path("outs"))     # from which step 1 builds my_sample.h5ad again
        ns = {"__name__": "__docs__"}
        if page in ("docstrings", "reference/methods.md"):   # these assume `import kdomainbench as kdb`
            ns["kdb"] = kdb
        print(f"\n=== {page}: {len(bl)} blocks", flush=True)
        for i, (kind, code) in enumerate(bl, 1):
            label = f"{page}#{i}"
            print(f"  [{label}] {kind}: {code.strip().splitlines()[0][:90] if code.strip() else ''}", flush=True)
            ok = run_python(code, ns, label) if kind == "python" else run_shell(code)
            if ok and kind == "python":
                last_value(code, ns)
            results[label] = ok
            matplotlib.pyplot.close("all")
            note("OK" if ok else "*** FAILED ***")
    failed = [k for k, v in results.items() if not v]
    print(f"\n{len(results) - len(failed)}/{len(results)} blocks OK" + (f"; failed: {failed}" if failed else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--h5ad", type=Path, required=True)
    ap.add_argument("--reuse", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--pages", nargs="*", help="only these pages (e.g. reference/setup.md docstrings)")
    ap.add_argument("--fast", nargs="*", default=sorted(FAST),
                    help=f"methods that really run (default: {' '.join(sorted(FAST))}); the rest reuse --reuse")
    ARGS = ap.parse_args()
    FAST = set(ARGS.fast)
    ARGS.reuse = ARGS.reuse.resolve()
    main()
