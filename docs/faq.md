# FAQ

Error messages and their fixes are under [Troubleshooting](how-to/troubleshooting.md).

## Do I need a GPU?

No. All ten methods run on a CPU. CellCharter, DeepST and SpatialDE2 can use a GPU, and a GPU
run can give a different result ([GPU or CPU?](tutorials/run.md#gpu-or-cpu)).

## How much memory does a run need?

It depends on the method and on the number of spots.
[Run on a cluster](how-to/cluster.md#memory) lists the peak memory of each method on a sample of
4,220 spots.

## My sample has no annotation. Can I still use kDomainBench?

Yes. Every method still returns its domains and its estimated k. Only the scores need an
annotation. [Your own data](how-to/own_data.md) walks through it.

## The methods give different k. Which one is right?

No single run tells you. On sample 151509 the ten methods disagree widely
([Benchmark the ten methods](tutorials/benchmark.md#3-estimated-k-and-accuracy)).
[The methods will disagree](how-to/own_data.md#the-methods-will-disagree) says how to read
their estimates.

## Does it work for mouse, or for another tissue?

Yes. No method takes the species or the tissue as a setting. Each reads only the count matrix
and the spot coordinates of a 10x Visium sample. One step depends on gene names: SpaGCN drops
the genes whose names start with `MT-` or `ERCC`, which catches human mitochondrial genes but
not mouse ones (`mt-`). The results on this site are from one human brain sample.

## Can I use Jupyter?

Yes, with `kdb_py` as the kernel. `kdb_py` has the kernel package but no Jupyter server, so
use the Jupyter you already have on the Linux machine where the methods run, for example
JupyterLab, or a JupyterHub or Open OnDemand service of your cluster. Register `kdb_py` with it once, then pick the kernel
`kdb_py` in Jupyter:

```bash title="terminal"
conda run -n kdb_py python -m ipykernel install --user --name kdb_py
```

When Jupyter does not see the R on your `PATH`, name it at the top of the notebook with
`kdb.set_env("r", "/path/to/Rscript")`.

## Will I get the same result twice?

On the same machine, mostly. The scripts fix a random seed for every method except iSC.MEB
([Method scripts](overview.md#method-scripts)). Results can still change with the device and,
for the R methods, with the package versions in your R.

## Can I score labels from another tool?

Yes. `kdb.evaluate` takes any labels indexed by spot barcode:

```python
import pandas as pd
import kdomainbench as kdb

labels = pd.read_csv("my_labels.csv", index_col=0).iloc[:, 0]      # barcode, label
kdb.evaluate(labels, "data/D3_151509_5k.h5ad")
```

## Can I add a method?

Yes, as a script and one entry in the package. [Contributing](contributing.md#add-a-method)
says what the script receives and must write.

## How do I run on a cluster?

[Run on a cluster](how-to/cluster.md) installs the environments in a project folder and submits
one job per method.
