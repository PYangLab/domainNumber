# Run on a cluster

This guide installs kDomainBench on a shared Linux cluster and runs each method as its own
batch job. The examples use Slurm.

## 1. Install where there is internet

Create the environments in a project folder, which usually has more space than your home
folder:

```bash title="terminal"
KDB_ENVS_DIR=/project/envs bash envs/install_envs.sh
/project/envs/kdb_py/bin/kdomainbench check
```

conda and pip keep download caches in your home folder, which `CONDA_PKGS_DIRS` and
`PIP_CACHE_DIR` move. `kdomainbench check` also downloads the reader the R methods need, so run
it once on a node with internet ([Troubleshooting](troubleshooting.md#the-first-r-run-is-slow-or-fails-without-internet)).

## 2. Submit one job per method

Called by its full path, `kdomainbench` needs no `conda activate` and finds `kdb_spatialde`
next to `kdb_py`. Each run writes its own folder, and the command exits with an error code when
the method did not finish, so the scheduler marks the job as failed.

```bash title="run_method.sh"
#!/bin/bash
#SBATCH --cpus-per-task=10
#SBATCH --mem=16G
#SBATCH --time=02:00:00
module load R                # only for the six R methods
/project/envs/kdb_py/bin/kdomainbench run -m "$1" -i data/D3_151509_5k.h5ad -o results/
```

```bash title="terminal"
for m in PRECAST SC.MEB BayesSpace BNPSpace DR.SC iSC.MEB \
         CellCharter DeepST SpaGCN SpatialDE2; do
  sbatch run_method.sh "$m"
done
```

This memory fits a sample of about 4,000 spots for most methods ([Memory](#memory) lists what
each needed). The memory reported there is that of a method's largest process, so give more to
iSC.MEB, which starts 10 workers, and to PRECAST, which starts 4 (`PRECAST_CORES`). A job that reaches its time limit is stopped together with the method, and
its `run_info.json` records `"success": false`.

## 3. Use a GPU

With `-d gpu`, the method uses the GPU your scheduler assigned through `CUDA_VISIBLE_DEVICES`.
`--gpu-id` overrides it. Only CellCharter, DeepST and SpatialDE2 use the GPU.

```bash title="run_gpu.sh"
#!/bin/bash
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --time=02:00:00
/project/envs/kdb_py/bin/kdomainbench run -m CellCharter DeepST SpatialDE2 -i data/D3_151509_5k.h5ad -d gpu -o results/
```

## 4. Collect the results

When the jobs are done:

```bash title="terminal"
/project/envs/kdb_py/bin/kdomainbench summarize results/ --csv summary.csv --plot k.png
```

## Memory

The peak memory of one CPU run of each method with `kmax = 30` on sample 151507 of the same
study as the example data (4,220 spots, 9,948 genes):

| Method | Peak memory (GB) |
|---|---:|
| SpaGCN | 1.4 |
| CellCharter | 2.0 |
| DR.SC | 2.3 |
| SC.MEB | 2.6 |
| SpatialDE2 | 2.8 |
| DeepST | 2.9 |
| iSC.MEB | 2.9 |
| PRECAST | 3.4 |
| BNPSpace | 5.2 |
| BayesSpace | 11.7 |

This is the peak memory of the method's largest process.
