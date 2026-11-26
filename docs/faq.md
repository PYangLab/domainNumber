# FAQ

Error messages and their fixes are under [Troubleshooting](how-to/troubleshooting.md).

## Do I need a GPU?

No. All ten methods run on a CPU. CellCharter, DeepST and SpatialDE2 can also use a GPU
([GPU or CPU?](tutorials/run.md#gpu-or-cpu)).

## My sample has no annotation. Can I still use kDomainBench?

Yes. Every method still returns its domains and its estimated k. Only the scores need an
annotation. [Your own data](how-to/own_data.md) walks through it.

## The methods give different k. Which one is right?

No single run tells you.
[The methods will disagree](how-to/own_data.md#the-methods-will-disagree) says how to read
their estimates.

## Does it work for mouse, or for another tissue?

Yes. No method takes the species or the tissue as a setting. Each reads only the count matrix
and the spot coordinates of a 10x Visium sample. The results on this site are from human brain
samples of one study.

## Can I use Jupyter?

Yes, with `kdb_py` as the kernel. `kdb_py` has no Jupyter server, so use the Jupyter of the
Linux machine where the methods run (JupyterLab, JupyterHub or Open OnDemand). Register `kdb_py`
with it once, then pick it as the kernel:

```bash title="terminal"
conda run -n kdb_py python -m ipykernel install --user --name kdb_py
```

For environments made with `KDB_ENVS_DIR`, name `kdb_py` by its path:
`conda run -p /project/envs/kdb_py ...`.

When Jupyter does not see the R on your `PATH`, name it at the top of the notebook with
`kdb.set_env("r", "/path/to/Rscript")`.

## Can I score labels from another tool?

Yes. `kdb.evaluate` takes any labels indexed by spot barcode:

```python
import pandas as pd
import kdomainbench as kdb

labels = pd.read_csv("my_labels.csv", index_col=0).iloc[:, 0]      # barcode, label
kdb.evaluate(labels, "data/D3_151509_5k.h5ad")
```

`n_spots_scored` in the result must equal your number of spots. A smaller number means that
some barcodes did not match.

## Can I add a method?

Yes, as a script and one entry in the package. [Contributing](contributing.md#add-a-method)
says what the script receives and must write.

## How do I run on a cluster?

[Run on a cluster](how-to/cluster.md) installs the environments in a project folder and submits
one job per method.
