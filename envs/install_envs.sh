#!/usr/bin/env bash
# Create the two kdomainbench Python environments from the locked files in this folder.
# The R methods use your own R: install their packages with  Rscript envs/install_r_packages.R
#   bash envs/install_envs.sh            # both
#   bash envs/install_envs.sh py         # one: py | spatialde
#   KDB_ENVS_DIR=/path/to/envs bash envs/install_envs.sh
#                                        # create them as /path/to/envs/kdb_* instead of named envs
#                                        # (kdomainbench finds kdb_spatialde next to kdb_py)
# The same environments work on CPU-only and GPU machines: torch (cu124) and tensorflow[and-cuda]
# bring their own CUDA libraries and fall back to the CPU when no GPU is visible.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CONDA="${CONDA:-$(command -v mamba || command -v conda || true)}"
[ -n "$CONDA" ] || { echo "conda or mamba not found on PATH. Load it (for example 'module load conda'), install Miniforge from https://conda-forge.org/download/ and open a new terminal, or set CONDA=/path/to/conda" >&2; exit 1; }

install_py() {
  "$CONDA" env create $(target kdb_py) -f "$HERE/kdb_py.yml"
  "$(conda_prefix kdb_py)/bin/python" -m pip install --no-deps -e "$HERE/.."   # kdomainbench itself
}

install_spatialde() {
  "$CONDA" env create $(target kdb_spatialde) -f "$HERE/kdb_spatialde.yml"
}

target() { if [ -n "${KDB_ENVS_DIR:-}" ]; then echo "-p $KDB_ENVS_DIR/$1"; else echo "-n $1"; fi; }
conda_prefix() {
  if [ -n "${KDB_ENVS_DIR:-}" ]; then echo "$KDB_ENVS_DIR/$1"; return; fi
  "$CONDA" env list | awk -v n="$1" '$1 == n {print $NF}'
}

targets=("$@"); [ ${#targets[@]} -eq 0 ] && targets=(py spatialde)
for t in "${targets[@]}"; do
  echo "=== installing $t"
  "install_$t"
done
echo "=== done. Check with:  kdomainbench check"
