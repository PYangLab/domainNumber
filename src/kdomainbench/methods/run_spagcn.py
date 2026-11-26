import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # CPU-only benchmark: hide GPUs before torch/tensorflow load
# mirroring https://github.com/jianhuupenn/SpaGCN/blob/master/tutorial/tutorial.md
import argparse
import random
import numpy as np
import scanpy as sc
import SpaGCN as spg
import scipy.sparse as sp
import torch
from sklearn.metrics import silhouette_score
import os

parser = argparse.ArgumentParser()
parser.add_argument("--data_path", type=str, required=True, help="Input h5ad file path")
parser.add_argument("--save_path", type=str, required=True, help="Output h5ad file path")
args = parser.parse_args()

# Load data
adata = sc.read(args.data_path)

# Set coordinates
# x_array = adata.obs["array_row"].tolist()
# y_array = adata.obs["array_col"].tolist()
x_pixel = adata.obs["pixel_row"].tolist()
y_pixel = adata.obs["pixel_col"].tolist()
adj = spg.calculate_adj_matrix(x=x_pixel, y=y_pixel, histology=False)

# Preprocessing
adata.var_names_make_unique()
spg.prefilter_genes(adata, min_cells=3)
spg.prefilter_specialgenes(adata)

# Normalize and take log for UMI
sc.pp.normalize_per_cell(adata)
sc.pp.log1p(adata)

# Search l
p = 0.5
l = spg.search_l(p, adj, start=0.01, end=1000, tol=0.01, max_run=100)

adata.obs['x_pixel'] = x_pixel
adata.obs['y_pixel'] = y_pixel
if sp.issparse(adata.X):
    adata.X = adata.X.toarray()

resolutions = np.arange(0.2, 1.1, 0.1)
best_silhouette = -1
best_res = None
best_pred = None
best_prob = None


#From the original paper "Otherwise, we vary the resolution parameter from 0.2 to 1.0 and select the resolution that gives the highest Silhouette score"
for res in resolutions:
    clf = spg.SpaGCN()
    clf.set_l(l)
    r_seed = t_seed = n_seed = 100
    random.seed(r_seed)
    torch.manual_seed(t_seed)
    np.random.seed(n_seed)
    print(f"Testing resolution: {res:.1f}")
    clf.train(adata, adj, init_spa=True, init="louvain", res=res,
              tol=5e-3, lr=0.05, max_epochs=200)
    y_pred, prob = clf.predict()
    silhouette = silhouette_score(adata.X, y_pred)
    print(f"Resolution {res:.1f}: Silhouette score = {silhouette:.4f}")
    if silhouette > best_silhouette:
        best_silhouette = silhouette
        best_res = res
        best_pred = y_pred
        best_prob = prob

print(f"\nBest resolution: {best_res} with Silhouette score: {best_silhouette:.4f}")

adata.obs["pred"] = best_pred
adata.obs["pred"] = adata.obs["pred"].astype('category')

# Save results
output_dir = os.path.dirname(args.save_path)
if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)
out = adata.obs[['pred']].rename(columns={'pred': 'cluster'})
out.index.name = 'spot_id'
out.to_csv(args.save_path, index=True)   # columns: spot_id, cluster
