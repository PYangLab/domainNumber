#  Mirroring https://xiaozhangryy.github.io/iSC.MEB/articles/iSC.MEB.DLPFC.html
library(iSC.MEB)
library(Seurat)
library(zellkonverter)
library(SingleCellExperiment)

platform = "Visium" 


get_iSCME_clusters <- function(h5ad_path="./../../data/test/151507.h5ad", K = 7:8, platform = "Visium") {
  sce <- readH5AD(h5ad_path)
  seu <- as.Seurat(sce, counts = "X", data = "X")
  seu[["RNA"]] <- seu[["originalexp"]]
  DefaultAssay(seu) <- "RNA"
  cm <- GetAssayData(seu, layer = "counts", assay = "RNA")
  seu$nCount_RNA   <- Matrix::colSums(cm)
  seu$nFeature_RNA <- Matrix::colSums(cm > 0)
  seu[["originalexp"]] <- NULL
  seu$row <- as.integer(seu$array_row)
  seu$col <- as.integer(seu$array_col)
  seuList <- list(seu)
  print(seu) 
  
  iSCMEBObj <- CreateiSCMEBObject(seuList = seuList, verbose = FALSE, postmin.features=-1,  premin.features = -1) 
  iSCMEBObj <- CreateNeighbors(iSCMEBObj, platform = "Visium") #platform = c("Other", "ST", "Visium"),

  iSCMEBObj <- runPCA(iSCMEBObj, npcs = 15, pca.method = "APCA")
  iSCMEBObj <- SetModelParameters(iSCMEBObj, verbose = TRUE, coreNum = 10)
  iSCMEBObj <- iSCMEB(iSCMEBObj, K = K)
  iSCMEBObj <- SelectModel(iSCMEBObj)
  print(length(idents(iSCMEBObj)[[1]]))
  labels <- idents(iSCMEBObj)[[1]]
  return(data.frame(cell_id = colnames(seu), cluster = labels))
}

args <- commandArgs(trailingOnly = TRUE)
h5ad_path <- args[1]
K <- c(args[2]:args[3])
save_path <- args[4] 

print(h5ad_path)
print(K)
print(platform)


begin_time <- Sys.time()
predicted_clusters <- get_iSCME_clusters(h5ad_path, K, platform)
end_time <- Sys.time()
all_time <- difftime(end_time, begin_time, units="secs")

# save the results
if (!dir.exists(save_path)) {
  dir.create(save_path, recursive = TRUE)
  print("path create")
}
write.csv(predicted_clusters, paste0(save_path, "/cluster_results.csv"), row.names = FALSE)




