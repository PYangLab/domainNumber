
#### BayesSpace reads coordinates from "array_col", "array_row" directly. https://github.com/edward130603/BayesSpace/blob/devel/R/spatialCluster.R

args <- commandArgs(trailingOnly = TRUE)
data_path <- args[1]
save_path <- args[2]
max_q <- as.integer(args[3])
if (!dir.exists(save_path)) {
  dir.create(save_path, recursive = TRUE)
}


Sys.setenv("OPENBLAS_NUM_THREADS" = "1")
Sys.setenv("OMP_NUM_THREADS" = "1")
suppressPackageStartupMessages({
  library(SingleCellExperiment)
  library(ggplot2)
  library(BayesSpace)
  library(zellkonverter)
  library(rlang)
})


sce <- readH5AD(data_path)
assay(sce, "counts") <- assay(sce, "X")
# BayesSpace >= 1.16 reads array_row/array_col; 1.14 (Bioconductor 3.19) reads row/col. Same coordinates.
colData(sce)$row <- colData(sce)$array_row
colData(sce)$col <- colData(sce)$array_col



##### 
# Why don't we use the preprocess block in https://www.ezstatconsulting.com/BayesSpace/articles/maynard_DLPFC.html?
# Because they assume the RDS data has been log-normalised but our input is raw.
#####


#### n.PCs and n.HVGs are from the DLPFC tutorial, and basically they are the default parameters as well.
set.seed(102)
sce <- spatialPreprocess(sce, platform="Visium",
                        n.PCs=15, n.HVGs=2000, log.normalize=TRUE)



### qTune is from https://www.ezstatconsulting.com/BayesSpace/articles/BayesSpace.html, since we assume the number of domdains is unknown.
sce <- qTune(sce, qs=seq(2, max_q), platform="Visium", d=15)
p <- qPlot(sce)


### Follow the instructions of qTune.R to read the tuning results.
q_tune_results <- attr(sce, "q.logliks")
qs <- q_tune_results$q
log_liks <- q_tune_results$loglik

find_elbow <- function(x, y) {
  x <- as.numeric(x)
  y <- as.numeric(y)
  
  ord <- order(x)
  x <- x[ord]
  y <- y[ord]

  dy <- diff(y) / diff(x)
  d2y <- diff(dy) / diff(x[-1])

  return(x[which.min(d2y) + 1])
}

optimal_q <- find_elbow(qs, log_liks)

q_plot_path <- file.path(save_path, "q_tuning_plot.pdf")
ggsave(q_plot_path, plot = p, width = 20, height = 10)
set.seed(104)

### We follow the DLPFC tutorial to set up gamma, nrep, d=15 matches with the nPCs and is the default hyperparameter.
sce <- spatialCluster(sce, q=optimal_q, platform="Visium", d=15,
                     gamma=3, nrep=50000, save.chain=TRUE)

# p2 <- clusterPlot(sce)
# ggsave("cluster_plot.png",p2)

##### Based on "Get started", we want to read the BayesSpace cluster assignments (spatial.cluster).
cluster_results <- colData(sce)$spatial.cluster
cluster_df <- data.frame(
  spot_id = colnames(sce),
  cluster = cluster_results
)

cluster_results_path <- file.path(save_path, "cluster_results.csv")
write.csv(cluster_df, cluster_results_path, row.names = FALSE)
