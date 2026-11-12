# Methods

List the methods and see what each one needs. These calls run nothing.

::: kdomainbench.list_methods

::: kdomainbench.get_method

::: kdomainbench.registry.Method
    options:
      members: false
      merge_init_into_class: false

## All methods

`kdb.METHODS` is a dict from each method's name to its `Method` record, in the order of
`kdb.list_methods()`.

```python
[m.name for m in kdb.METHODS.values() if m.language == "R"]
# ['PRECAST', 'SC.MEB', 'BayesSpace', 'BNPSpace', 'DR.SC', 'iSC.MEB']
```
