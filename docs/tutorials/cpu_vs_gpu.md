# CPU versus GPU

CellCharter, DeepST and SpatialDE2 can run on a GPU. This tutorial runs each of them on the CPU
and on GPU 0, then compares the run time and the domains.

!!! tip "Summary"
    ```python
    import kdomainbench as kdb
    h5ad = "data/D1_151507_4k.h5ad"
    for m in kdb.list_methods(gpu_only=True):
        kdb.run(m, h5ad, kmax=30, device="cpu", out_dir=f"devices/{m}/cpu")
        kdb.run(m, h5ad, kmax=30, device="gpu", gpu_id=0, out_dir=f"devices/{m}/gpu")
    kdb.pl.plot_runtime(kdb.load_results("devices/"))
    ```

## 1. Check the GPU

```bash title="terminal"
nvidia-smi                          # pick a free GPU; its index is gpu_id
kdomainbench check --gpu --gpu-id 0 # torch: CUDA available: True, tensorflow: GPUs: 1
```

!!! warning "Shared machines"
    Always pass `gpu_id` on a machine with several GPUs, so the run does not land on a GPU
    someone else is using.

## 2. Run each method on both devices

```python
import kdomainbench as kdb

h5ad = "data/D1_151507_4k.h5ad"
runs = {}
for m in kdb.list_methods(gpu_only=True):
    runs[m, "cpu"] = kdb.run(m, h5ad, kmax=30, device="cpu", out_dir=f"devices/{m}/cpu")
    runs[m, "gpu"] = kdb.run(m, h5ad, kmax=30, device="gpu", gpu_id=0, out_dir=f"devices/{m}/gpu")
```

## 3. Compare run time and memory

```python
summary = kdb.load_results("devices/")
summary[["method", "device_used", "k_estimated", "ARI", "wall_time_s", "peak_rss_mb"]]

kdb.pl.plot_runtime(summary)                          # CPU and GPU bars side by side
kdb.pl.plot_runtime(summary, metric="peak_rss_mb")
```

`peak_rss_mb` is host memory. GPU memory is not recorded; watch it with `nvidia-smi` while the
run is going.

## 4. Do the domains change?

GPU kernels are not bit-identical to CPU kernels, so the trained embeddings, and sometimes the
chosen resolution or k, can differ a little between devices even with the same seed. Compare
the two runs of each method with ARI:

```python
from sklearn.metrics import adjusted_rand_score

for m in kdb.list_methods(gpu_only=True):
    cpu, gpu = runs[m, "cpu"], runs[m, "gpu"]
    print(m, adjusted_rand_score(cpu.loc[gpu.index, "cluster"], gpu["cluster"]))
```

An ARI of 1 means the same domains on both devices.

!!! info "Results pending"
    The GPU runs of this benchmark have not been run yet. Their times and ARIs will be added here.
