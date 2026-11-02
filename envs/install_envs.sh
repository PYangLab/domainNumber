#!/usr/bin/env bash
# Create the three kdomainbench environments from the locked files in this folder.
#   bash envs/install_envs.sh            # all three
#   bash envs/install_envs.sh py r       # a subset: py | spatialde | r
#   KDB_ENVS_DIR=/path/to/envs bash envs/install_envs.sh
#                                        # create them as /path/to/envs/kdb_* instead of named envs;
#                                        # then point KDB_PY_PYTHON etc. at them
# The same environments work on CPU-only and GPU machines: torch (cu124) and tensorflow[and-cuda]
# bring their own CUDA libraries and fall back to the CPU when no GPU is visible.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CONDA="${CONDA:-$(command -v mamba || command -v conda)}"

install_py() {
  "$CONDA" env create $(target kdb_py) -f "$HERE/kdb_py.yml"
  "$(conda_prefix kdb_py)/bin/python" -m pip install --no-deps -e "$HERE/.."   # kdomainbench itself
}

install_spatialde() {
  "$CONDA" env create $(target kdb_spatialde) -f "$HERE/kdb_spatialde.yml"
}

install_r() {
  # R 4.4.1 + toolchain from conda, then the locked CRAN/Bioconductor 3.19 packages into it.
  "$CONDA" env create $(target kdb_r) -f "$HERE/kdb_r.yml"
  "$(conda_prefix kdb_r)/bin/Rscript" "$HERE/install_r_packages.R" "$HERE/kdb_r.lock.csv"
}

target() { if [ -n "${KDB_ENVS_DIR:-}" ]; then echo "-p $KDB_ENVS_DIR/$1"; else echo "-n $1"; fi; }
conda_prefix() {
  if [ -n "${KDB_ENVS_DIR:-}" ]; then echo "$KDB_ENVS_DIR/$1"; return; fi
  "$CONDA" env list | awk -v n="$1" '$1 == n {print $NF}'
}

targets=("$@"); [ ${#targets[@]} -eq 0 ] && targets=(py spatialde r)
for t in "${targets[@]}"; do
  echo "=== installing $t"
  "install_$t"
done
echo "=== done. Check with:  kdomainbench check"
