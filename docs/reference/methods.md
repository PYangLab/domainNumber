# Methods

List the methods and see what each one needs. These calls run nothing.

| Name | Summary |
|---|---|
| [`kdb.list_methods`](#kdomainbench.list_methods) | Return the names of the methods. |
| [`kdb.get_method`](#kdomainbench.get_method) | Return one method's settings. |
| [`kdb.Method`](#kdomainbench.registry.Method) | One method: its script, its environment and how it is called. |
| [`kdb.METHODS`](#all-methods) | Every method's record, by name. |

::: kdomainbench.list_methods

::: kdomainbench.get_method

::: kdomainbench.registry.Method
    options:
      members: false

## All methods

`kdb.METHODS` is a dict from each method's name to its `Method` record, in the order of
`kdb.list_methods()`.

```python
[m.name for m in kdb.METHODS.values() if m.language == "R"]
# ['PRECAST', 'SC.MEB', 'BayesSpace', 'BNPSpace', 'DR.SC', 'iSC.MEB']
```
