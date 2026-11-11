# Citation

Cite the kDomainBench paper, the publication of each method you run, the metrics you report, and
the dataset.

## The benchmark

The kDomainBench paper is in preparation. This page will give its reference once it is
available. Until then, name the repository, <https://github.com/liuchunlei0430/kDomainBench>,
the package version (`kdb.__version__`) and the commit you used (`git rev-parse --short HEAD`
in the cloned folder).

## The methods

| Method | Publication |
|---|---|
| PRECAST | Liu W. et al. Probabilistic embedding, clustering, and alignment for integrating spatial transcriptomics data with PRECAST. *Nature Communications* 14, 296 (2023). [doi:10.1038/s41467-023-35947-w](https://doi.org/10.1038/s41467-023-35947-w) |
| SC.MEB | Yang Y. et al. SC-MEB: spatial clustering with hidden Markov random field using empirical Bayes. *Briefings in Bioinformatics* 23, bbab466 (2022). [doi:10.1093/bib/bbab466](https://doi.org/10.1093/bib/bbab466) |
| BayesSpace | Zhao E. et al. Spatial transcriptomics at subspot resolution with BayesSpace. *Nature Biotechnology* 39, 1375–1384 (2021). [doi:10.1038/s41587-021-00935-2](https://doi.org/10.1038/s41587-021-00935-2) |
| BNPSpace | Zhu B. et al. Bayesian nonparametric clustering with feature selection for spatially resolved transcriptomics data. *The Annals of Applied Statistics* 19, 1028–1047 (2025). [doi:10.1214/25-AOAS2014](https://doi.org/10.1214/25-AOAS2014) |
| DR.SC | Liu W. et al. Joint dimension reduction and clustering analysis of single-cell RNA-seq and spatial transcriptomics data. *Nucleic Acids Research* 50, e72 (2022). [doi:10.1093/nar/gkac219](https://doi.org/10.1093/nar/gkac219) |
| iSC.MEB | Zhang X. et al. iSC.MEB: an R package for multi-sample spatial clustering analysis of spatial transcriptomics data. *Bioinformatics Advances* 3, vbad019 (2023). [doi:10.1093/bioadv/vbad019](https://doi.org/10.1093/bioadv/vbad019) |
| CellCharter | Varrone M. et al. CellCharter reveals spatial cell niches associated with tissue remodeling and cell plasticity. *Nature Genetics* 56, 74–84 (2024). [doi:10.1038/s41588-023-01588-4](https://doi.org/10.1038/s41588-023-01588-4) |
| DeepST | Xu C. et al. DeepST: identifying spatial domains in spatial transcriptomics by deep learning. *Nucleic Acids Research* 50, e131 (2022). [doi:10.1093/nar/gkac901](https://doi.org/10.1093/nar/gkac901) |
| SpaGCN | Hu J. et al. SpaGCN: Integrating gene expression, spatial location and histology to identify spatial domains and spatially variable genes by graph convolutional network. *Nature Methods* 18, 1342–1351 (2021). [doi:10.1038/s41592-021-01255-8](https://doi.org/10.1038/s41592-021-01255-8) |
| SpatialDE2 | Kats I., Vento-Tormo R. & Stegle O. SpatialDE2: Fast and localized variance component analysis of spatial transcriptomics. Preprint at *bioRxiv* (2021). [doi:10.1101/2021.10.27.466045](https://doi.org/10.1101/2021.10.27.466045) |

## The metrics

`kdb.metrics` uses the code of these publications for five of its twelve metrics.

| Metric | Publication |
|---|---|
| spARI | Yan Y., Feng X. & Luo X. Spatially aware adjusted Rand index for evaluating spatial transcriptomics clustering. *Biometrics* 81, ujaf127 (2025). [doi:10.1093/biomtc/ujaf127](https://doi.org/10.1093/biomtc/ujaf127) |
| PAS, CHAOS | Shang L. & Zhou X. Spatially aware dimension reduction for spatial transcriptomics. *Nature Communications* 13, 7203 (2022). [doi:10.1038/s41467-022-34879-1](https://doi.org/10.1038/s41467-022-34879-1) |
| LISI | Korsunsky I. et al. Fast, sensitive and accurate integration of single-cell data with Harmony. *Nature Methods* 16, 1289–1296 (2019). [doi:10.1038/s41592-019-0619-0](https://doi.org/10.1038/s41592-019-0619-0) |
| SCS | Zeira R. et al. Alignment and integration of spatial transcriptomics data. *Nature Methods* 19, 567–575 (2022). [doi:10.1038/s41592-022-01459-6](https://doi.org/10.1038/s41592-022-01459-6) |

## The data

Sample 151509 is from Maynard K. R. et al. Transcriptome-scale spatial gene
expression in the human dorsolateral prefrontal cortex. *Nature Neuroscience* 24, 425–436
(2021). [doi:10.1038/s41593-020-00787-0](https://doi.org/10.1038/s41593-020-00787-0)

## Reporting a run

To make a result reproducible, report the package version and commit, `kmax` and the device.
The run folder records the rest: `run_info.json` holds the exact call of the method script
(`command`) and the settings that change a method (`env`), and `packages.txt` the package
versions of its environment. These matter most for the R methods, since your R is not pinned
([Installation](installation.md#r)).
