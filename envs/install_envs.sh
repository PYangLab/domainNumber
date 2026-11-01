#!/usr/bin/env bash
# Create the three kdomainbench environments from the locked files in this folder.
#   bash envs/install_envs.sh            # all three
#   bash envs/install_envs.sh py r       # a subset: py | spatialde | r
# The same environments work on CPU-only and GPU machines: torch (cu124) and tensorflow[and-cuda]
# bring their own CUDA libraries and fall back to the CPU when no GPU is visible.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CONDA="${CONDA:-$(command -v mamba || command -v conda)}"

install_py() {
  "$CONDA" env create -y -n kdb_py -f "$HERE/kdb_py.yml"
  "$(conda_prefix kdb_py)/bin/python" -m pip install --no-deps -e "$HERE/.."   # kdomainbench itself
}

install_spatialde() {
  "$CONDA" env create -y -n kdb_spatialde -f "$HERE/kdb_spatialde.yml"
}

install_r() {
  # R 4.4.1 + toolchain from conda, then the locked CRAN/Bioconductor 3.19 packages into it.
  "$CONDA" env create -y -n kdb_r -f "$HERE/kdb_r.yml"
  "$(conda_prefix kdb_r)/bin/Rscript" "$HERE/install_r_packages.R" "$HERE/kdb_r.lock.csv"
}

conda_prefix() { "$CONDA" env list | awk -v n="$1" '$1 == n {print $NF}'; }

targets=("$@"); [ ${#targets[@]} -eq 0 ] && targets=(py spatialde r)
for t in "${targets[@]}"; do
  echo "=== installing $t"
  "install_$t"
done
echo "=== done. Check with:  kdomainbench check"
