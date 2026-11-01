"""Command line: kdomainbench {methods,check,run,summarize}."""
import argparse
import subprocess
import sys

from . import config
from .registry import METHODS, get_method


def _methods(_):
    print(f"{'method':<12}{'language':<9}{'env':<11}{'GPU':<5}uses kmax")
    for m in METHODS.values():
        print(f"{m.name:<12}{m.language:<9}{m.env:<11}{'yes' if m.gpu else '-':<5}{'yes' if m.uses_kmax else 'no (auto)'}")


_CHECKS = {
    "py": "import torch, cellcharter, deepstkit, SpaGCN; print('torch', torch.__version__, '| CUDA available:', torch.cuda.is_available())",
    "spatialde": "import SpatialDE, tensorflow as tf; print('tensorflow', tf.__version__, '| GPUs:', len(tf.config.list_physical_devices('GPU')))",
    "r": "for (p in c('PRECAST','SC.MEB','BayesSpace','DR.SC','iSC.MEB','zellkonverter','RcppArmadillo')) cat(p, as.character(packageVersion(p)), '\\n')",
}


def _check(args):
    from .runner import _build_env
    ok = True
    for key, code in _CHECKS.items():
        try:
            interp = config.interpreter(key)
        except FileNotFoundError as e:
            print(f"[{key}] MISSING: {e}")
            ok = False
            continue
        m = next(m for m in METHODS.values() if m.env == key)
        env = _build_env(m, "gpu" if args.gpu else "cpu", args.gpu_id)
        flag = ["-e"] if key == "r" else ["-c"]
        r = subprocess.run([interp, *flag, code], env=env, capture_output=True, text=True)
        out = r.stdout.strip() if r.returncode == 0 else r.stderr.strip().splitlines()[-1:]
        print(f"[{key}] {interp}\n    {out if isinstance(out, list) else out.replace(chr(10), chr(10) + '    ')}")
        ok &= r.returncode == 0
    sys.exit(0 if ok else 1)


def _run(args):
    from . import run_all
    from .runner import run
    if args.method == ["all"]:
        run_all(args.input, kmax=args.kmax, device=args.device, out_root=args.out or "kdb_results",
                gpu_id=args.gpu_id)
    else:
        for name in args.method:
            out = f"{args.out}/{get_method(name).name}" if args.out and len(args.method) > 1 else args.out
            run(name, args.input, kmax=args.kmax, device=args.device, out_dir=out, gpu_id=args.gpu_id)


def _summarize(args):
    from .results import k_accuracy, load_results
    df = load_results(args.root)
    print(df.to_string(index=False))
    if args.csv:
        df.to_csv(args.csv, index=False)
    if args.plot:
        import matplotlib
        matplotlib.use("Agg")
        from .plotting import plot_k_estimates
        ax = plot_k_estimates(df)
        ax.figure.tight_layout()
        ax.figure.savefig(args.plot, dpi=150)
    if df["success"].any():
        print("\n", k_accuracy(df).to_string())


def main(argv=None):
    p = argparse.ArgumentParser(prog="kdomainbench", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("methods", help="list methods").set_defaults(fn=_methods)
    c = sub.add_parser("check", help="check that the three environments import")
    c.add_argument("--gpu", action="store_true", help="check with the GPU visible")
    c.add_argument("--gpu-id", type=int, default=0)
    c.set_defaults(fn=_check)
    r = sub.add_parser("run", help="run method(s) on an h5ad")
    r.add_argument("-m", "--method", nargs="+", required=True, help="method name(s) or 'all'")
    r.add_argument("-i", "--input", required=True, help="input .h5ad")
    r.add_argument("-k", "--kmax", type=int, default=30)
    r.add_argument("-d", "--device", choices=["cpu", "gpu"], default="cpu")
    r.add_argument("--gpu-id", type=int, default=0)
    r.add_argument("-o", "--out", help="output directory")
    r.set_defaults(fn=_run)
    s = sub.add_parser("summarize", help="collect run_info.json files into a table")
    s.add_argument("root", nargs="?", default="kdb_results")
    s.add_argument("--csv")
    s.add_argument("--plot", help="save k-estimate figure (png/pdf)")
    s.set_defaults(fn=_summarize)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
