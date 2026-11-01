## Mirroring https://github.com/new-zbc/BNPSpace/blob/main/Tutorial.html
library(SingleCellExperiment)
library(Matrix)
library(flexclust)
library(scater)
library(scran)
source(file.path(Sys.getenv("KDB_METHODS_DIR", "."), "bnpspace_R", "utils.R"))
source(file.path(Sys.getenv("KDB_METHODS_DIR", "."), "bnpspace_R", "main.R"))

args <- commandArgs(trailingOnly = TRUE)
h5ad_path <- args[1]
outdir <- args[2]
K_init <- as.integer(args[3])

dir.create(outdir, recursive = TRUE, showWarnings = FALSE)

sce <- zellkonverter::readH5AD(h5ad_path)  
assay(sce, "counts") <- assay(sce, "X")
sce <- spatialPreprocess(sce)
reducedDims(sce) <- reducedDims(sce)[
  c("PCA", setdiff(reducedDimNames(sce), "PCA"))
]

# sce = spatialFilter(sce, cutoff_sample = 0, cutoff_max = 5)

colData(sce)$row <- colData(sce)$array_row
colData(sce)$col <- colData(sce)$array_col


Adj = find_neighbors(sce, "Visium", "lattice")
neighbors = find_neighbor_index(Adj, "Visium")

sizeFactors(sce) <- scuttle::librarySizeFactors(sce) 
result1 = NSCFS(sce, neighbors, n_clusters = NULL,d=1 ,K_init=K_init, n_iters = 300, seed = 1) 
pred_spot = result1$pred_label

write.csv(data.frame(spot_id = colnames(sce),
                     cluster  = pred_spot),
          file = file.path(outdir, "cluster_results.csv"),
          row.names = FALSE)
