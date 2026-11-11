"""Turn `conda env export --no-builds` output into the shareable lock files kdb_py.yml / kdb_spatialde.yml."""
import re
import sys

PIP_OPTS = {
    "kdb_py": ["--extra-index-url https://download.pytorch.org/whl/cu124",
               "--find-links https://data.pyg.org/whl/torch-2.5.0+cu124.html"],
    "kdb_spatialde": [],
}
REPLACE = {
    "torch==2.5.1": "torch==2.5.1+cu124",
    "spatialde==2.0.0": "SpatialDE @ git+https://github.com/PMBio/SpatialDE.git@6dbdb559a566d639da0f6fd3acc9e17104c0674f",
}
DROP = re.compile(r"^\s*- (kdomainbench)==")
HEADER = {
    "kdb_py": "# kdomainbench: CellCharter, DeepST, SpaGCN (+ kdomainbench). torch 2.5.1+cu124 works on CPU and GPU.\n",
    "kdb_spatialde": "# kdomainbench: SpatialDE2. tensorflow[and-cuda] 2.15.1 works on CPU and GPU.\n"
                     "# SpatialDE is pinned to upstream commit 6dbdb55. The original env was installed from a local copy of that commit\n"
                     "# with two edits that do not affect kdomainbench: `Literal` imported from typing_extensions, and the default\n"
                     "# TissueSegmentationParameters(nclasses=2) (run_spatialde.py always passes nclasses=kmax explicitly).\n",
}

src, dst, name = sys.argv[1:4]
out, in_channels = [HEADER[name]], False
for line in open(src):
    if line.startswith("channels:"):
        out += ["channels:\n", "  - conda-forge\n", "  - nodefaults\n"]
        in_channels = True
        continue
    if in_channels:
        if line.startswith("  - "):
            continue
        in_channels = False
    if line.startswith("name:"):
        line = f"name: {name}\n"
    if DROP.match(line):
        continue
    stripped = line.strip()[2:] if line.strip().startswith("- ") else None
    if stripped in REPLACE:
        line = line.replace(stripped, REPLACE[stripped])
    out.append(line)
    if line.strip() == "- pip:":
        out += [f"      - {o}\n" for o in PIP_OPTS[name]]
open(dst, "w").writelines(out)
print("wrote", dst)
