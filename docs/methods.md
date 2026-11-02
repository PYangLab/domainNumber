# How kDomainBench works

kDomainBench gives ten methods one interface. Every method gets the same input `.h5ad` file and
writes the same output, `cluster_results.csv`, with one domain label per spot. The *estimated k*
is the number of distinct labels in that file.

## One call, three environments

The methods need incompatible software: R 4.4 with Bioconductor, PyTorch with PyG, and
TensorFlow 2.15. So each runs in its own environment, and `kdb.run` bridges them:

1. It looks up the method: its script in `src/kdomainbench/methods/`, its environment
   (`kdb_r`, `kdb_py` or `kdb_spatialde`) and its arguments.
2. It starts the script with that environment's `Rscript` or `python`, as a separate process
   whose working directory is the run folder.
3. It saves everything the script prints to `run.log`, and measures the wall time and the peak
   memory of the process.
4. It reads `cluster_results.csv` back and writes `run_info.json`, with the device, time,
   memory and estimated k.

Your own Python session needs only `kdb_py`. It never imports R, torch or TensorFlow for a run.

## CPU and GPU

Each method has **one** script for both devices; the device is a command-line flag.

| | `device="cpu"` | `device="gpu"` |
|---|---|---|
| Visible GPUs | none: `CUDA_VISIBLE_DEVICES=""` | only `gpu_id`: `CUDA_DEVICE_ORDER=PCI_BUS_ID`, `CUDA_VISIBLE_DEVICES=<gpu_id>` |
| CellCharter | scVI trains with `accelerator="cpu"` | `accelerator="gpu"` |
| DeepST | `use_gpu=False` | `use_gpu=True` |
| SpatialDE2 | TensorFlow finds no GPU | TensorFlow uses the visible GPU |
| The other seven | CPU | CPU, with a `UserWarning` |

The settings apply to the method's process only. `run_info.json` records both
`device_requested` and `device_used`; they differ only for a CPU-only method asked to use the GPU.
The same environments serve both kinds of machine: the CUDA builds of torch and TensorFlow fall
back to the CPU when no GPU is visible.

## The ten methods

| Method | Env | GPU | Model | How k is selected | Key settings |
|---|---|:---:|---|---|---|
| [PRECAST](https://feiyoung.github.io/PRECAST/) | `kdb_r` | – | Spatial factor model + hidden Markov random field (HMRF) | Fits K = 2 … kmax, picks one with a modified BIC (`SelectModel`) | 2000 HVGs, Visium neighbours, `maxIter=30` |
| [SC.MEB](https://shufeyangyi2015310117.github.io/SC.MEB/) | `kdb_r` | – | HMRF on 15 principal components | Fits K = 2 … kmax, picks one by BIC (`selectK`) | β grid 0–4 (step 0.2), serial |
| [BayesSpace](https://www.ezstatconsulting.com/BayesSpace/) | `kdb_r` | – | Bayesian spatial clustering with a Potts prior | `qTune` log-likelihood for q = 2 … kmax; the elbow (minimum second difference) is q | 15 PCs, 2000 HVGs, γ = 3, 50 000 MCMC iterations |
| [BNPSpace](https://github.com/new-zbc/BNPSpace) | `kdb_r` | – | Bayesian nonparametric count model with feature selection | Clusters left non-empty after MCMC, starting from K = kmax | 300 MCMC iterations, lattice neighbours |
| [DR.SC](https://feiyoung.github.io/DR.SC/) | `kdb_r` | – | Joint dimension reduction + spatial clustering | Fits K = 2 … kmax, picks one with a modified BIC | 500 HVGs |
| [iSC.MEB](https://xiaozhangryy.github.io/iSC.MEB/) | `kdb_r` | – | Integrated HMRF on APCA embeddings | Fits K = 2 … kmax, picks one with a modified BIC | 15 PCs (APCA), `coreNum=10` |
| [CellCharter](https://cellcharter.readthedocs.io/) | `kdb_py` | ✓ | scVI latent space, neighbourhood aggregation, GMM | `ClusterAutoK`: clustering stability over K = 2 … kmax (10 runs) | 5000 HVGs, 6 grid neighbours, 4 layers |
| [DeepST](https://github.com/JiangBioLab/DeepST) | `kdb_py` | ✓ | Graph autoencoder on augmented expression | Leiden resolution 0.1–2.5 chosen by the Calinski–Harabasz score (`n_domains=0`); ignores kmax | 500 + 500 epochs, PCA ≤ 200 |
| [SpaGCN](https://github.com/jianhuupenn/SpaGCN) | `kdb_py` | – | Graph convolutional network + iterative clustering | Louvain resolution 0.2–1.0 with the highest silhouette score; ignores kmax | p = 0.5, 200 epochs |
| [SpatialDE2](https://github.com/PMBio/SpatialDE) | `kdb_spatialde` | ✓ | Spatially variable genes + Bayesian tissue segmentation | Variational segmentation with up to kmax classes; empty classes are pruned | 2000 SVGs (padj < 0.001), seed 42 |

SpaGCN is written in PyTorch but always runs on the CPU, as in the original benchmark scripts.
PRECAST forks workers over the K grid; `PRECAST_CORES` (default 4) caps them.

## Method scripts

The scripts in `src/kdomainbench/methods/` are copies of the original benchmark scripts, with
only these changes:

* `run_cellcharter.py`, `run_deepst.py`, `run_spatialde.py`: a `--device cpu|gpu` flag replaces
  the hard-coded CPU settings (`CUDA_VISIBLE_DEVICES=""`, `accelerator='cpu'`, `use_gpu=False`).
* `bnpspace.R`: finds its helper `R/` sources through `KDB_METHODS_DIR`, set by kDomainBench, so
  it runs from any working directory.
* `bayesspace.R`: copies `array_row` / `array_col` into `row` / `col`. BayesSpace 1.14
  (Bioconductor 3.19, the version in `kdb_r`) reads `row` / `col`; ≥ 1.16 reads
  `array_row` / `array_col`. Both end up with the same coordinates.
* `scmeb.R`: runs SC.MEB serially (`parallel = FALSE`). The original runs each K in a parallel
  worker, and the workers do not inherit `set.seed(114)`, so two runs on the same data gave
  different k (7 and 9). Serial runs give the same result every time, at the cost of time.
  `SCMEB_PARALLEL=TRUE` (with `SCMEB_CORES` workers, default 3) restores the original setting.
* The Python scripts have a `run_` prefix. Without it, `cellcharter.py` would import itself
  instead of the `cellcharter` package.

PRECAST and iSC.MEB need `ulimit -s unlimited`; kDomainBench sets it for them.
