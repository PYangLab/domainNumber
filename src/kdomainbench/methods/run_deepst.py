import os, sys
# --device cpu|gpu (default cpu). Must be applied before torch/tensorflow are imported:
# cpu hides all GPUs; gpu keeps the caller's CUDA_VISIBLE_DEVICES (kdomainbench sets it to GPU 0).
DEVICE = sys.argv[sys.argv.index("--device") + 1] if "--device" in sys.argv else "cpu"
if DEVICE == "cpu":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
# %%
import os
import matplotlib.pyplot as plt
import scanpy as sc
import deepstkit as dt
import anndata
import argparse
import scipy
# %%
parser = argparse.ArgumentParser()
parser.add_argument("--data_path", type=str, required=True, help="Input h5ad file path")
parser.add_argument("--save_path", type=str, required=True, help="Output h5ad file path")
parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "gpu"],
                    help="cpu or gpu")
args = parser.parse_args()

# ========== Configuration ==========
SEED = 0                     # Random seed for reproducibility
RESULTS_DIR = args.save_path   # Directory to save outputs
dt.utils_func.seed_torch(seed=SEED)
deepst = dt.main.run(
    save_path=RESULTS_DIR,
    task="Identify_Domain",  # Spatial domain identification
    pre_epochs=500,          # Pretraining iterations
    epochs=500,              # Main training iterations
    use_gpu=(DEVICE == "gpu")  # set by --device
)

adata = anndata.read_h5ad(args.data_path)
# adata.obsm['spatial']=adata.obs[['pixel_row','pixel_col']].to_numpy()
if isinstance(adata.X, scipy.sparse.spmatrix):
    adata.X = adata.X.toarray()
print("loaded data")
    
adata = deepst._get_augment(
    adata,
    spatial_type="BallTree",
    use_morphological = False  # Set True if using H&E features
)
print("augment done")

graph_dict = deepst._get_graph(
    adata.obsm["spatial"],
    distType="KDTree"        # Spatial relationship modeling
)
print("graph done")

# Dimensionality reduction ### slightly different from the original tutorial for making sure the model could work when the number of features is lower than 200.
n_obs, n_feat = adata.obsm["augment_gene_data"].shape
pca_comps = min(200, n_obs - 1, n_feat - 1)     
data = deepst._data_process(
    adata,
    pca_n_comps=pca_comps
)

deepst_embed = deepst._fit(
    data=data,
    graph_dict=graph_dict
)
adata.obsm["DeepST_embed"] = deepst_embed
print("training done")


adata = deepst._get_cluster_data(
    adata,
    n_domains=0,
    priori=False              # Use prior knowledge if available
)
print("clustering done")



# %%
output_dir = args.save_path
if not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)
# adata.obs['DeepST_domain'].to_csv(os.path.join(output_dir, 'deepst_D1.csv'), header=True)
# adata.obs['DeepST_refine_domain'].to_csv(os.path.join(output_dir, 'deepst_refine_D1.csv'), header=True)
# adata.write_h5ad(os.path.join(output_dir, 'deepst_result_D1.h5ad'))

out = adata.obs[['DeepST_domain']].rename(columns={'DeepST_domain': 'cluster'})
out.index.name = 'spot_id'
out.to_csv(os.path.join(output_dir, 'cluster_results.csv'), index=True) 

