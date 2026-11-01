import os, sys
# --device cpu|gpu (default cpu). Must be applied before torch/tensorflow are imported:
# cpu hides all GPUs; gpu keeps the caller's CUDA_VISIBLE_DEVICES (kdomainbench sets it to GPU 0).
DEVICE = sys.argv[sys.argv.index("--device") + 1] if "--device" in sys.argv else "cpu"
if DEVICE == "cpu":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
# %%
import SpatialDE
import os
import numpy as np
import scipy
import pandas as pd
import scanpy as sc
import anndata as ad
import argparse

parser = argparse.ArgumentParser(description="Run CellCharter AutoK clustering")
parser.add_argument("--data_path", type=str, required=True,
                    help="Path to input .h5ad file")

parser.add_argument("--out_dir", type=str, required=True,
                    help="Output directory for results")

parser.add_argument("--kmax", type=int, required=True,
                    help="Maximum number of clusters (search range from 2..kmax)")
parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "gpu"],
                    help="cpu or gpu")

args = parser.parse_args()

data = sc.read_h5ad(args.data_path)
# data.obsm['spatial']=data.obs[['array_x','array_y']].to_numpy()
data.var_names_make_unique()
# data.var["mt"] = data.var_names.str.startswith("MT-")
# sc.pp.calculate_qc_metrics(data, qc_vars=["mt"], inplace=True)

# sc.pp.filter_cells(data, min_counts=4000)
# data = data[data.obs["pct_counts_mt"] < 20]
sc.pp.filter_genes(data, min_cells=100)

svg_full, _ = SpatialDE.test(data, omnibus=True)
svg_full["total_counts"] = np.asarray(data.X.sum(axis=0)).squeeze()

vargenes = svg_full[svg_full.padj < 0.001].sort_values("total_counts", ascending=False).gene[:2000]
print(vargenes, "!!!")
segm_default, _ = SpatialDE.tissue_segmentation(data, genes=vargenes, rng=np.random.default_rng(seed=42), params=SpatialDE.TissueSegmentationParameters(nclasses=args.kmax))
# data.obs["segmentation_labels_default"] = data.obs.segmentation_labels
# segm_adj, adata = SpatialDE.tissue_segmentation(data, genes=vargenes, rng=np.random.default_rng(seed=42), params=SpatialDE.TissueSegmentationParameters(smoothness_factor=5))


os.makedirs(args.out_dir, exist_ok=True)
out_file = os.path.join(args.out_dir, "cluster_results.csv")
out = data.obs[['segmentation_labels']].rename(columns={'segmentation_labels': 'cluster'})
out.index.name = 'spot_id'
out.to_csv(out_file, index=True)

