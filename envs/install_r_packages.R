# Install the R packages of the kdomainbench R methods into your own R (>= 4.4).
# Only missing packages are installed, from CRAN and Bioconductor as usual.
# Usage: Rscript envs/install_r_packages.R [library]
#   library: optional separate library; then set KDB_R_LIB to it.
# The versions of the benchmark are listed in kdb_r.lock.csv (for reference).
args <- commandArgs(trailingOnly = TRUE)
lib <- if (length(args) > 0) args[1] else .libPaths()[1]
dir.create(lib, recursive = TRUE, showWarnings = FALSE)
.libPaths(c(lib, .libPaths()))
if (is.null(getOption("repos")) || getOption("repos")["CRAN"] %in% c("@CRAN@", NA))
  options(repos = c(CRAN = "https://cloud.r-project.org"))

cran <- c("PRECAST", "DR.SC", "iSC.MEB", "Seurat", "Rcpp", "RcppArmadillo", "flexclust",
          "philentropy", "fastcluster", "dynamicTreeCut", "purrr", "deldir", "glue", "ggplot2",
          "cowplot", "mclust", "remotes", "BiocManager")
bioc <- c("BayesSpace", "zellkonverter", "SingleCellExperiment", "SummarizedExperiment", "scran",
          "scater", "scuttle", "BiocSingular")
missing <- function(p) p[!vapply(p, requireNamespace, logical(1), quietly = TRUE)]

todo <- missing(cran)
if (length(todo)) install.packages(todo, lib = lib)
todo <- missing(bioc)
if (length(todo)) BiocManager::install(todo, lib = lib, update = FALSE, ask = FALSE)
# SC.MEB was archived on CRAN; 1.1 is its last release.
if (length(missing("SC.MEB")))
  remotes::install_url("https://cran.r-project.org/src/contrib/Archive/SC.MEB/SC.MEB_1.1.tar.gz",
                       lib = lib, upgrade = "never")

left <- missing(c(cran, bioc, "SC.MEB"))
if (length(left)) stop("not installed: ", paste(left, collapse = ", "))
cat("all R packages of kdomainbench are installed\n")
