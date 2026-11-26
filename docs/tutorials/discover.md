# Discover methods

kDomainBench runs ten methods that estimate the number of spatial domains. This page shows how
to list them, what each one needs, and how each one picks k.

!!! tip "Summary"
    ```python
    import kdomainbench as kdb
    kdb.list_methods()                    # all ten
    kdb.list_methods(gpu_only=True)       # the three that can use a GPU
    m = kdb.get_method("DR.SC")           # one method's settings
    ```

## List the methods

```python
import kdomainbench as kdb
kdb.list_methods()
# ['PRECAST', 'SC.MEB', 'BayesSpace', 'BNPSpace', 'DR.SC', 'iSC.MEB',
#  'CellCharter', 'DeepST', 'SpaGCN', 'SpatialDE2']
```

`kdomainbench methods` prints them as a table:

```text title="kdomainbench methods"
method      language env        GPU  uses kmax
PRECAST     R        r          -    yes
SC.MEB      R        r          -    yes
BayesSpace  R        r          -    yes
BNPSpace    R        r          -    yes
DR.SC       R        r          -    yes
iSC.MEB     R        r          -    yes
CellCharter Python   py         yes  yes
DeepST      Python   py         yes  no (auto)
SpaGCN      Python   py         -    no (auto)
SpatialDE2  Python   spatialde  yes  yes
```

`env` is the environment the method runs in: `r` is your R, `py` is `kdb_py` and `spatialde`
is `kdb_spatialde` ([Installation](../installation.md#step-2-create-the-environments)).

## Filter by what you need

Three methods can use a GPU:

```python
kdb.list_methods(gpu_only=True)
# ['CellCharter', 'DeepST', 'SpatialDE2']
```

Two methods do not take `kmax`:

```python
[m for m in kdb.list_methods() if not kdb.get_method(m).uses_kmax]
# ['DeepST', 'SpaGCN']
```

## Inspect a single method

```python
m = kdb.get_method("cellcharter")      # case-insensitive, and aliases such as "drsc" work too
m.name, m.language, m.env, m.gpu, m.uses_kmax
# ('CellCharter', 'Python', 'py', True, True)
m.reference
# 'https://cellcharter.readthedocs.io/'
m.script
# 'run_cellcharter.py'
```

[`kdb.Method`](../reference/methods.md#kdomainbench.registry.Method) lists every field of the
record.

## How each method picks k

The ten methods choose k in three ways:

* **Fit every k and keep the best.** PRECAST, SC.MEB, BayesSpace, DR.SC, iSC.MEB and CellCharter
  fit k = 2 … `kmax` and keep one by a model-selection score (BIC, clustering stability or a
  likelihood elbow).
* **Start high and drop empty domains.** BNPSpace and SpatialDE2 start from `kmax` domains and
  report those that hold spots at the end. BNPSpace can also add domains, up to 30.
* **Tune a resolution.** DeepST and SpaGCN try a range of clustering resolutions and keep the
  best-scoring one. The number of domains follows from it.

[How kDomainBench works](../overview.md#the-ten-methods) has each method's model and criterion.

Next: [Run a method](run.md).
