# How kDomainBench works

kDomainBench gives ten methods one interface. Every method gets the same input `.h5ad` file and
writes the same output, `cluster_results.csv`, with one domain label per spot. The *estimated k*
is the number of distinct labels in that file.

## One call, three environments

The methods need incompatible software: R 4.4 with Bioconductor, PyTorch with PyG, and
TensorFlow 2.15. So they run in three environments, and `kdb.run` starts each method in the
right one:

1. It looks up the method: its script in `src/kdomainbench/methods/`, its environment
   (your R, `kdb_py` or `kdb_spatialde`) and its arguments.
2. It starts the script with that environment's `Rscript` or `python`, as a separate process
   whose working directory is the run folder.
3. It saves everything the script prints to `run.log`, and measures the run time and the peak
   memory of the process.
4. It reads `cluster_results.csv` back and writes `run_info.json`, with the device, run time,
   memory and estimated k, and `packages.txt`, the package versions of the environment.

Your own Python session needs only `kdb_py`. It never imports R, torch or TensorFlow for a run.

## CPU and GPU

Each method has **one** script for both devices, and the device is a command-line flag.

| | `device="cpu"` | `device="gpu"` |
|---|---|---|
| Visible GPUs | none: `CUDA_VISIBLE_DEVICES=""` | `gpu_id` when given (`CUDA_DEVICE_ORDER=PCI_BUS_ID`), else those already in `CUDA_VISIBLE_DEVICES`, else GPU 0 |
| CellCharter | scVI trains with `accelerator="cpu"` | `accelerator="gpu"` |
| DeepST | `use_gpu=False` | `use_gpu=True` |
| SpatialDE2 | TensorFlow finds no GPU | TensorFlow uses the visible GPU |
| The other seven | CPU | CPU, with a `UserWarning` |

The settings apply to the method's process only. `run_info.json` records both
`device_requested` and `device_used`, the device the method was started with. They differ only
for a CPU-only method asked to use the GPU. kDomainBench does not measure which device the
method ended up on ([GPU or CPU?](tutorials/run.md#gpu-or-cpu)).

## Scores and metrics

Scoring is separate from running. `kdb.evaluate` computes k error, ARI and NMI in Python.
`kdb.metrics` computes the twelve metrics of the paper with the paper's own code: `metrics.R`
for eleven of them, in R, and `scs.py` for SCS, in `kdb_py`. Both files in
`src/kdomainbench/metric_scripts/` are unchanged copies of the scripts that scored the paper's
benchmark ([The twelve metrics of the paper](tutorials/evaluate.md#the-twelve-metrics-of-the-paper)).

## The ten methods

| Method | Model | How k is selected |
|---|---|---|
| [PRECAST](https://feiyoung.github.io/PRECAST/) | Spatial factor model + hidden Markov random field (HMRF) | Fits k = 2 … `kmax`, picks one with a modified BIC (`SelectModel`) |
| [SC.MEB](https://shufeyangyi2015310117.github.io/SC.MEB/) | HMRF on 15 principal components | Fits k = 2 … `kmax`, picks one by BIC (`selectK`) |
| [BayesSpace](https://www.ezstatconsulting.com/BayesSpace/) | Bayesian spatial clustering with a Potts prior | `qTune` gives a log-likelihood for k = 2 … `kmax`. The script takes its elbow, the k with the most negative second difference, which lies in 3 … `kmax` − 1 |
| [BNPSpace](https://github.com/new-zbc/BNPSpace) | Bayesian nonparametric count model with feature selection | Starts from `kmax` domains, adds and empties domains during MCMC, and reports those that hold spots. Its code allows at most 30 |
| [DR.SC](https://feiyoung.github.io/DR.SC/) | Joint dimension reduction + spatial clustering | Fits k = 2 … `kmax`, picks one with a modified BIC |
| [iSC.MEB](https://xiaozhangryy.github.io/iSC.MEB/) | Integrated HMRF on 15 principal components | Fits k = 2 … `kmax`, picks one with a modified BIC (`SelectModel`) |
| [CellCharter](https://cellcharter.readthedocs.io/) | scVI latent space, neighborhood aggregation, GMM | `ClusterAutoK`: the k in 2 … `kmax` whose clustering is most stable over repeated fits (up to 10) |
| [DeepST](https://github.com/JiangBioLab/DeepST) | Graph autoencoder on augmented expression | Leiden resolution 0.1–2.5 with the highest Calinski–Harabasz score (`priori=False`). Ignores `kmax` |
| [SpaGCN](https://github.com/jianhuupenn/SpaGCN) | Graph convolutional network + iterative clustering | Louvain resolution 0.2–1.0 with the highest silhouette score. Ignores `kmax` |
| [SpatialDE2](https://github.com/PMBio/SpatialDE) | Spatially variable genes + Bayesian tissue segmentation | Variational segmentation with up to `kmax` classes. Empty classes are pruned |

An HMRF and a Potts prior are spatial models in which neighboring spots tend to share a domain.
BIC and its modified forms score how well each k fits and penalize the extra parameters. An
elbow is the k after which the fit stops improving quickly.

Each method runs with the settings of its authors' tutorial. The calls are in the
[method scripts](#method-scripts). [Discover methods](tutorials/discover.md#list-the-methods)
lists the environment and GPU support of each method, and [Citation](citation.md#the-methods)
its publication.

## Method scripts

The scripts in `src/kdomainbench/methods/` are copies of the scripts that ran the paper's
benchmark, with only these changes:

* `run_cellcharter.py`, `run_deepst.py`, `run_spatialde.py`: a `--device cpu|gpu` flag sets the
  device. The original CellCharter and DeepST scripts always asked for GPU 0
  (`CUDA_VISIBLE_DEVICES="0"`, `use_gpu=True`), and the original SpatialDE2 script set no
  device.
* `run_spagcn.py`: hides the GPUs (`CUDA_VISIBLE_DEVICES=""`), so SpaGCN always runs on the CPU.
* `bnpspace.R`: finds its helper R and C++ sources through `KDB_METHODS_DIR`, set by
  kDomainBench, so it runs from any working directory.
* `bayesspace.R`: copies `array_row` / `array_col` into `row` / `col`. BayesSpace 1.14 reads
  `row` / `col`, and versions from 1.16 read `array_row` / `array_col`. Both end up with the
  same coordinates.
* `scmeb.R`: runs SC.MEB serially (`parallel = FALSE`), so that it uses `set.seed(114)`. The
  original runs each k in a parallel worker that does not inherit the seed, and two such runs
  on the same data returned k = 7 and k = 9. `SCMEB_PARALLEL=TRUE` (with
  `SCMEB_CORES` workers, default 3) restores the original setting.
* `drsc.R`: no longer copies `obs["clusters"]` into its Seurat object. DR.SC never used the
  column, and the script failed on a file without it. The domains are the same with and without
  the line.
* The Python scripts have a `run_` prefix. Without it, `cellcharter.py` would import itself
  instead of the `cellcharter` package.

No script reads the reference annotation.
