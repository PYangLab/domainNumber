import os, sys
# --device cpu|gpu (default cpu). Must be applied before torch/tensorflow are imported:
# cpu hides all GPUs; gpu keeps the caller's CUDA_VISIBLE_DEVICES (kdomainbench sets it to gpu_id).
DEVICE = sys.argv[sys.argv.index("--device") + 1] if "--device" in sys.argv else "cpu"
if DEVICE == "cpu":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
### Mirroring the set up from https://cellcharter.readthedocs.io/en/latest/notebooks/cosmx_human_nsclc.html
import os
import argparse
import scanpy as sc
import squidpy as sq
import cellcharter as cc
import scvi
import numpy as np
from lightning.pytorch import seed_everything

parser = argparse.ArgumentParser(description="Run CellCharter AutoK clustering")
parser.add_argument("--data_path", type=str, required=True,
                    help="Path to input .h5ad file")
parser.add_argument("--kmax", type=int, required=True,
                    help="Maximum number of clusters (search range from 2..kmax)")
parser.add_argument("--out_dir", type=str, required=True,
                    help="Output directory for results")
parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "gpu"],
                    help="cpu or gpu")

args = parser.parse_args()

seed_everything(12345)
scvi.settings.seed = 12345
os.makedirs(args.out_dir, exist_ok=True)
adata = sc.read_h5ad(args.data_path)
sc.pp.filter_genes(adata, min_counts=3)
adata.layers["counts"] = adata.X.copy()
sc.pp.normalize_total(adata, target_sum=1e6)
sc.pp.log1p(adata)


#### from L47 of https://github.com/CSOgroup/cellcharter_analyses/blob/main/src/benchmarking/CellCharter/individual.py
sc.pp.highly_variable_genes(
    adata,
    n_top_genes=5000,
    subset=True,
    layer="counts",
    flavor="seurat_v3",
)

scvi.model.SCVI.setup_anndata(adata, layer="counts")

### latent=5, from line61 of https://github.com/CSOgroup/cellcharter_analyses/blob/main/src/benchmarking/CellCharter/individual.py, 
### but, after installing the packages with the instructions in github, scvi does not support latent parameter anymore.
model = scvi.model.SCVI(adata)


### from line 62 of https://github.com/CSOgroup/cellcharter_analyses/blob/main/src/benchmarking/CellCharter/individual.py
model.train(accelerator='gpu' if DEVICE == 'gpu' else 'cpu', early_stopping=True, plan_kwargs=dict(optimizer='AdamW', reduce_lr_on_plateau=True))

adata.obsm['X_scVI'] = model.get_latent_representation(adata).astype(np.float32)

# sq.gr.spatial_neighbors(adata, coord_type='generic', delaunay=True,
#                         spatial_key='spatial', percentile=99)


### In the original paper they mentioned for Visium data, they assigned the six and four closest surrounding spots, rather than using Delaunay triangulation.
### Follow how https://github.com/CSOgroup/cellcharter_analyses/blob/main/ATAC-RNA_mouse_brain.ipynb assign neighbors:
sq.gr.spatial_neighbors(adata, coord_type='grid', n_neighs=6)

### n_layers should be changed from 3 to 4 based on line65 of https://github.com/CSOgroup/cellcharter_analyses/blob/main/src/benchmarking/CellCharter/individual.py,
cc.gr.aggregate_neighbors(adata, n_layers=4, use_rep='X_scVI',
                            out_key='X_cellcharter')

autok = cc.tl.ClusterAutoK(
    n_clusters=(2, args.kmax),
    max_runs=10,
    convergence_tol=0.001
)
autok.fit(adata, use_rep='X_cellcharter')
cc.pl.autok_stability(autok)
adata.obs['cluster_cellcharter'] = autok.predict(adata, use_rep='X_cellcharter')
out_file = os.path.join(args.out_dir, "cluster_results.csv")
out = adata.obs[['cluster_cellcharter']].rename(
    columns={'cluster_cellcharter': 'cluster'}
)
out.index.name = 'spot_id'
out.to_csv(out_file, index=True)


