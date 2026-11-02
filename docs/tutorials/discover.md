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

## The ten methods

```python
import kdomainbench as kdb
kdb.list_methods()
# ['PRECAST', 'SC.MEB', 'BayesSpace', 'BNPSpace', 'DR.SC', 'iSC.MEB',
#  'CellCharter', 'DeepST', 'SpaGCN', 'SpatialDE2']
```

The same table from the command line:

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

**A GPU.** Three methods can use one:

```python
kdb.list_methods(gpu_only=True)
# ['CellCharter', 'DeepST', 'SpatialDE2']
```

**A cap on k.** Eight methods use `kmax` as the largest k they consider. DeepST and SpaGCN choose k by themselves
and ignore `kmax`:

```python
[m for m in kdb.list_methods() if not kdb.get_method(m).uses_kmax]
# ['DeepST', 'SpaGCN']
```

## Inspect a single method

```python
m = kdb.get_method("cellcharter")      # case-insensitive; aliases such as "drsc" work too
m.name, m.language, m.env, m.gpu, m.uses_kmax
# ('CellCharter', 'Python', 'py', True, True)
m.reference
# 'https://cellcharter.readthedocs.io/'
m.script
# 'run_cellcharter.py'
```

??? note "All fields"
    | Field | Meaning |
    |---|---|
    | `name` | canonical name |
    | `language` | `"R"` or `"Python"` |
    | `env` | environment key: `"r"`, `"py"` or `"spatialde"` |
    | `script` | the method's script in `src/kdomainbench/methods/` |
    | `gpu` | `True` if `device="gpu"` really runs on a GPU |
    | `uses_kmax` | `False` if the method chooses k by itself |
    | `big_stack` | `True` if the method needs `ulimit -s unlimited` (PRECAST, iSC.MEB) |
    | `reference` | the method's documentation or repository |
    | `aliases` | other accepted names |

## How each method picks k

Six methods fit K = 2 … `kmax` and keep the best by a model-selection score (BIC, stability,
likelihood elbow); BNPSpace and SpatialDE2 start from `kmax` and drop empty clusters; DeepST and
SpaGCN tune a clustering resolution instead. [How kDomainBench works](../methods.md#the-ten-methods)
has each method's model, criterion and settings.

## Before running

* Run times differ a lot. On the 4k sample on a CPU, PRECAST, BayesSpace, BNPSpace, DeepST and
  SpatialDE2 took 40–75 minutes each, CellCharter and SC.MEB 15–18, and DR.SC, SpaGCN and
  iSC.MEB under 10. [Benchmark the ten methods](benchmark.md) lists every run time and peak memory.
* Next: [run a method](run.md).
Next: [run a method](run.md).
