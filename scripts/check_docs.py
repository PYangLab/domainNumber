"""Execute the code examples of the documentation and report each one.

Every ```python block of a page runs in order, in one namespace per page, inside a scratch
folder that holds `data/D1_151507_4k.h5ad`. Shell blocks run line by line when they are
`kdomainbench ...` or `python -c ...` commands. Docstring examples of the public API run too.

To keep it to about an hour and off the GPU:
* fast methods (FAST below) really run, once per method; later calls reuse that run;
* slow methods reuse finished runs from --reuse (a folder of <method>/<run>/ run folders);
* device="gpu" never starts a GPU job: GPU methods reuse the CPU run, CPU-only methods only
  issue their warning. Shell commands with --gpu / -d gpu, and `-m all`, are skipped.

    python scripts/check_docs.py --h5ad D1_151507_4k.h5ad --reuse kdb_test/results --work /tmp/check
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
BASICS = ["tutorials/discover.md", "tutorials/run.md", "tutorials/evaluate.md", "tutorials/plot.md"]
PAGES = ["installation.md", "quickstart.md", *BASICS, "tutorials/benchmark.md", "tutorials/cpu_vs_gpu.md", "api.md", "reference/setup.md"]
FAST = {"SpaGCN", "DR.SC", "SC.MEB", "iSC.MEB"}
SKIP_SHELL = re.compile(r"--gpu|-d gpu|-m all|^(git|mamba|conda|bash|Rscript|export|nvidia-smi|wget|"
                        r"python scripts/)")

os.environ["CUDA_VISIBLE_DEVICES"] = ""          # nothing in this process may touch a GPU
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot  # noqa: E402
import kdomainbench as kdb  # noqa: E402
from kdomainbench import runner  # noqa: E402

REAL_RUN = runner.run
_cache = {}          # method -> finished run folder (real or reused)
LOG = []


def note(msg):
    LOG.append(msg)
    print("    " + msg, flush=True)


def stub_run(method, h5ad, kmax=30, device="cpu", out_dir=None, gpu_id=0, verbose=True):
    m = kdb.get_method(method)
    if device == "gpu" and not m.gpu:
        warnings.warn(f"{m.name} has no GPU implementation; running it on the CPU.", stacklevel=2)
    out = Path(out_dir or Path("kdb_results") / m.name / f"{Path(h5ad).stem}_{device}").resolve()
    if m.name not in _cache:
        if m.name in FAST:
            note(f"REAL RUN {m.name} (cpu) -> {out}")
            t = time.time()
            REAL_RUN(m.name, h5ad, kmax=kmax, device="cpu", out_dir=out, verbose=False)
            note(f"  finished in {time.time() - t:.0f} s")
            _cache[m.name] = out
            return kdb.read_clusters(out)
        src = next((p for p in sorted((ARGS.reuse / m.name).glob("*")) if (p / "run_info.json").exists()), None)
        if src is None:
            raise RuntimeError(f"no finished run of {m.name} to reuse under {ARGS.reuse}")
        _cache[m.name] = src
    src = _cache[m.name]
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


def run_python(code, ns, label):
    if "path/to/" in code:
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


def run_shell(code, label):
    ok = True
    for line in code.splitlines():
        cmd = line.split("  #")[0].strip()
        if cmd.startswith("$ "):
            cmd = cmd[2:]
        if not cmd or cmd.startswith("#") or not cmd.startswith(("kdomainbench", "python -c")):
            continue
        if SKIP_SHELL.search(cmd):
            note(f"skipped (GPU / all methods / install): {cmd}")
            continue
        note(f"$ {cmd}")
        t = time.time()
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        out = (r.stdout + r.stderr).strip()
        note(f"  exit {r.returncode} in {time.time() - t:.0f} s: " + out[-800:].replace("\n", "\n            "))
        ok &= r.returncode == 0
    return ok


def docstring_examples():
    import inspect
    funcs = [kdb.list_methods, kdb.get_method, kdb.set_env, kdb.run, kdb.run_all, kdb.read_clusters,
             kdb.ground_truth, kdb.evaluate, kdb.load_results, kdb.k_accuracy, kdb.pl.plot_k_estimates,
             kdb.pl.plot_runtime, kdb.pl.plot_spatial, kdb.pl.plot_spatial_grid]
    for f in funcs:
        doc = inspect.getdoc(f) or ""
        code = "\n".join(ln[4:] for ln in doc.splitlines() if ln.startswith(">>> "))
        if code:
            yield f.__name__, code


def main():
    work = ARGS.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    kdb.run = stub_run                     # run_all looks `run` up in the package namespace
    results = {}
    pages = ARGS.pages or PAGES
    targets = [(p, list(blocks(p))) for p in pages if p != "docstrings"] + ([("docstrings", [("python", c) for _, c in docstring_examples()])]
                                                         if not ARGS.pages or "docstrings" in ARGS.pages else [])
    for page, bl in targets:
        # Get started pages build on each other (out/ from "Run a method" feeds the next pages),
        # as for a reader who follows them in order; tutorials and docstrings start fresh.
        shared = page in ("installation.md", "quickstart.md", "reference/setup.md", *BASICS)
        d = work / ("getstarted" if shared else page.replace("/", "_").replace(".md", ""))
        (d / "data").mkdir(parents=True, exist_ok=True)
        for link in (d / "data" / ARGS.h5ad.name, d / ARGS.h5ad.name):
            if not link.exists():
                link.symlink_to(ARGS.h5ad.resolve())
        os.chdir(d)
        ns = {"__name__": "__docs__"}
        if page == "docstrings":            # docstring examples assume `import kdomainbench as kdb`
            ns["kdb"] = kdb
        print(f"\n=== {page}: {len(bl)} blocks", flush=True)
        for i, (kind, code) in enumerate(bl, 1):
            label = f"{page}#{i}"
            print(f"  [{label}] {kind}: {code.strip().splitlines()[0][:90] if code.strip() else ''}", flush=True)
            ok = run_python(code, ns, label) if kind == "python" else run_shell(code, label)
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
    ARGS = ap.parse_args()
    ARGS.reuse = ARGS.reuse.resolve()
    main()
