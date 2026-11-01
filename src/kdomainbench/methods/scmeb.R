### Mirroring https://shufeyangyi2015310117.github.io/SC.MEB/articles/SC.MEB_CRC.html
library(SC.MEB)
library(scran)
library(scater)
library(Seurat)
library(scuttle)
library(flexclust)
library(fastcluster)
library(philentropy)
library(BiocSingular)
library(zellkonverter)
library(dynamicTreeCut)
library(SingleCellExperiment)
set.seed(114)

get_sc.meb_clusters <- function(h5ad_path, K_set = 5:7, platform = "Visium") { #platform = c("Visium", "ST")
  beta_grid = seq(0,4,0.2)
  parallel = TRUE
  # SC.MEB spawns num_core PSOCK workers over K_set. Total cores =
  # num_core x BLAS threads per worker, so the caller must also pin
  # OMP_NUM_THREADS/OPENBLAS_NUM_THREADS=1 for this to be the real budget.
  num_core = as.integer(Sys.getenv("SCMEB_CORES", unset = "3"))
  PX = TRUE
  maxIter_ICM = 10
  maxIter = 50
  library(glue)

  CRC <- readH5AD(h5ad_path)
  CRC$row <- CRC$array_row
  CRC$col <- CRC$array_col
  counts(CRC) <- CRC@assays@data$X

  CRC <- spatialPreprocess(CRC, platform = platform)
  Adj_sp  <- find_neighbors2(CRC, platform = platform)
  y <- reducedDim(CRC, "PCA")[,1:15]
  fit <- SC.MEB(y, Adj_sp, beta_grid = beta_grid, K_set= K_set, parallel=parallel, num_core = num_core, PX = PX, maxIter_ICM=maxIter_ICM, maxIter=maxIter)
  out <- selectK(fit, K_set = K_set, criterion = "BIC")
  return(data.frame(spot_id = colnames(CRC), cluster = out$best_K_label))
}

args <- commandArgs(trailingOnly = TRUE)
h5ad_path <- args[1]
K <- c(args[2]:args[3])
platform <- args[4] 
save_path <- args[5] 

begin_time <- Sys.time()
predicted_clusters <- get_sc.meb_clusters(h5ad_path, K, platform)
end_time <- Sys.time()
all_time <- difftime(end_time, begin_time, units="secs")

# save the results
if (!dir.exists(save_path)) {
  dir.create(save_path, recursive = TRUE)
  print("path create")
}
write.csv(predicted_clusters, paste0(save_path, "/cluster_results.csv"), row.names = FALSE)


