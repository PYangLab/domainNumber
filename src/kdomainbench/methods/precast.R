### Mirroring https://feiyoung.github.io/PRECAST/articles/PRECAST.DLPFC.html

#```{r}
library(Seurat)
library(PRECAST)
library(zellkonverter)
library(SingleCellExperiment)
set.seed(2022)


#h5ad_path <- './../../data/dataset_downsampled/D14_downsampled.h5ad'
#platform = "Other_SRT"
#K=2:30


get_precast_clusters <- function(h5ad_path, K = 2:20, platform = "Visium") {
  sce <- readH5AD(h5ad_path)
  seu <- as.Seurat(sce, counts = "X", data = NULL)
  seu@meta.data$row <- as.integer(seu$array_row)
  seu@meta.data$col <- as.integer(seu$array_col)
  

  preobj <- CreatePRECASTObject(list(seu), selectGenesMethod = "HVGs", gene.number = 2000, premin.features=-1, postmin.features=-1)
  PRECASTObj <- AddAdjList(preobj, platform = platform) #"Visium", "ST" and "Other_SRT" #, radius.upper=100
  # Fork workers across the K grid. Override with PRECAST_CORES to cap CPU use;
  # total cores = coreNum x BLAS threads per worker, so pin the latter to 1.
  core_num <- as.integer(Sys.getenv("PRECAST_CORES", unset = "4"))
  if (is.na(core_num) || core_num < 1L) core_num <- 4L
  PRECASTObj <- AddParSetting(PRECASTObj, Sigma_equal = FALSE, coreNum = core_num, maxIter = 30, verbose = TRUE) # Other options for multi-K in the tutorial.
  PRECASTObj <- PRECAST(PRECASTObj, K = K)
  PRECASTObj <- SelectModel(PRECASTObj)

  cl  <- PRECASTObj@resList$cluster[[1]]          
  ids <- colnames(PRECASTObj@seulist[[1]])        
  cat("n spots =", length(ids), " | n labels =", length(cl), "\n")   
  stopifnot(length(ids) == length(cl)) 
  
  return(data.frame(spot_id = ids, cluster = cl))
}

args <- commandArgs(trailingOnly = TRUE)
path <- args[1]
K <- c(args[2]:args[3])
platform <- args[4] 
save_path <- args[5] 

begin_time <- Sys.time()
predicted_clusters <- get_precast_clusters(path, K = K,platform)
end_time <- Sys.time()
all_time <- difftime(end_time, begin_time, units="secs")

# save the results
if (!dir.exists(save_path)) {
  dir.create(save_path, recursive = TRUE)
  print("path create")
}

write.csv(predicted_clusters,
          file.path(save_path, "cluster_results.csv"),
          row.names = FALSE)

# ```

# ####################### visualisation ###################
#seuInt <- PRECASTObj@seulist[[1]]
#seuInt@meta.data$cluster <- factor(unlist(PRECASTObj@resList$cluster))
#seuInt@meta.data$batch <- 1
#seuInt <- Add_embed(PRECASTObj@resList$hZ[[1]], seuInt, embed_name = "PRECAST")
#posList <- lapply(PRECASTObj@seulist, function(x) cbind(x$row, x$col))
#seuInt <- Add_embed(posList[[1]], seuInt, embed_name = "position")
#Idents(seuInt) <- factor(seuInt@meta.data$cluster)

#p_sp1 <- SpaPlot(seuInt, item = "cluster", point_size = 3, combine = F)[[1]] + cowplot::theme_cowplot()




#Rscript main.Rmd  './../../data/dataset_downsampled/D15_downsampled.h5ad' 2 30  ‘ST’ './../../result_downsampled//D15/PRECAST/'
