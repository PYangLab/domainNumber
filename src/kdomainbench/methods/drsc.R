## Mirroring https://feiyoung.github.io/DR.SC/articles/DR.SC.DLPFC.html
args <- commandArgs(trailingOnly = TRUE)
h5ad_path <- args[1]
outdir <- args[2]
kmax <- as.integer(args[3])
platform <- args[4]
set.seed(2024)
library("DR.SC")
library(Matrix)
library(SingleCellExperiment)
library(zellkonverter)
library(Seurat)
sce <- zellkonverter::readH5AD(h5ad_path)
assay_names <- SummarizedExperiment::assayNames(sce)
counts <- SummarizedExperiment::assay(sce, "X")
df <- as.data.frame(colData(sce))
meta_data <- data.frame(
  row        = df$array_row,
  col        = df$array_col,
  annotation = df$clusters,
  row.names  = colnames(counts),
  check.names = FALSE
)
srt <- CreateSeuratObject(counts=counts, meta.data = meta_data)
srt <- NormalizeData(srt, verbose = F)
seu <- FindVariableFeatures(srt, nfeatures = 500, verbose = F)
K_set <- 2:kmax

seu <- DR.SC(seu, K=K_set, platform = platform, verbose=F)
cluster = seu$spatial.drsc.cluster
dir.create(outdir, recursive = TRUE, showWarnings = FALSE)
write.csv(data.frame(spot_id = colnames(seu),
                     cluster  = seu$spatial.drsc.cluster),
          file = file.path(outdir, "cluster_results.csv"),
          row.names = FALSE)
