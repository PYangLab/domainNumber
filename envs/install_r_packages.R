# Install the R packages kdomainbench needs into your own R.
# Only missing packages are installed, from CRAN and Bioconductor as usual.
# Usage: Rscript envs/install_r_packages.R [--metrics] [library]
#   (default)  the packages of the six R methods (R >= 4.4)
#   --metrics  the packages of the metric code instead (R >= 4.5 with Bioconductor >= 3.22,
#              the first release with spARI)
#   library    optional separate library. Then set KDB_R_LIB to it.
# The versions of the benchmark are listed in kdb_r.lock.csv (for reference).
args <- commandArgs(trailingOnly = TRUE)
metrics <- "--metrics" %in% args
args <- setdiff(args, "--metrics")
if (length(args) > 0) {
  # A separate library is all the R methods see with KDB_R_LIB (plus base R), so a package
  # that is only in your user or site library counts as missing here.
  lib <- args[1]
  dir.create(lib, recursive = TRUE, showWarnings = FALSE)
  .libPaths(lib, include.site = FALSE)
} else {
  lib <- .libPaths()[1]
  if (file.access(lib, 2) != 0) {
    # e.g. an R from a module, whose first library is the read-only system one
    lib <- Sys.getenv("R_LIBS_USER")
    dir.create(lib, recursive = TRUE, showWarnings = FALSE)
    .libPaths(c(lib, .libPaths()))
  }
}
cat("installing missing packages into", lib, "\n")
if (is.null(getOption("repos")) || getOption("repos")["CRAN"] %in% c("@CRAN@", NA))
  options(repos = c(CRAN = "https://cloud.r-project.org"))

if (metrics) {
  # what src/kdomainbench/metric_scripts/metrics.R calls. HDF5Array and rhdf5 are behind
  # zellkonverter's reader = "R". The GitHub packages are pinned to the commits of the paper.
  cran <- c("clevr", "aricode", "ClusterR", "remotes", "BiocManager")
  bioc <- c("spARI", "zellkonverter", "SummarizedExperiment", "HDF5Array", "rhdf5")
  github <- c(lisi = "immunogenomics/lisi@a917556310d8d2c66833dcc35aa3d0f4d1b6e0f4",
              SPARK = "xzhoulab/SPARK@a8b4bf27b804604dfda53da42992f100b8e4e727",
              SpatialPCA = "shangll123/SpatialPCA@1d4dbb1fe6f23b77bb7ed805ce2de8bbc017ef66")
  archive <- character()
} else {
  # what the method scripts load, and mclust, which SC.MEB 1.1 depends on
  cran <- c("PRECAST", "DR.SC", "iSC.MEB", "Seurat", "Rcpp", "RcppArmadillo", "flexclust",
            "philentropy", "fastcluster", "dynamicTreeCut", "purrr", "deldir", "glue", "ggplot2",
            "mclust", "remotes", "BiocManager")
  bioc <- c("BayesSpace", "zellkonverter", "SingleCellExperiment", "SummarizedExperiment", "scran",
            "scater", "scuttle", "BiocSingular")
  github <- character()
  # SC.MEB was archived on CRAN. 1.1 is its last release.
  archive <- c(SC.MEB = "https://cran.r-project.org/src/contrib/Archive/SC.MEB/SC.MEB_1.1.tar.gz")
}
missing <- function(p) p[!vapply(p, requireNamespace, logical(1), quietly = TRUE)]

todo <- missing(cran)
if (length(todo)) install.packages(todo, lib = lib)
todo <- missing(bioc)
if (length(todo)) BiocManager::install(todo, lib = lib, update = FALSE, ask = FALSE)
# From here on, dependencies come from this R's Bioconductor release, never a newer one.
options(repos = BiocManager::repositories())
if (length(github)) {
  # lisi and SPARK ask for C++11, which RcppArmadillo >= 15.4 no longer compiles under:
  # build them as C++14. R_MAKEVARS_USER replaces ~/.R/Makevars, so its lines are kept.
  user <- Sys.getenv("R_MAKEVARS_USER", "~/.R/Makevars")
  makevars <- tempfile("Makevars")
  writeLines(c(if (file.exists(user)) readLines(user), "CXX11STD = -std=gnu++14"), makevars)
  Sys.setenv(R_MAKEVARS_USER = makevars)
}
for (p in missing(names(github))) remotes::install_github(github[[p]], lib = lib, upgrade = "never")
for (p in missing(names(archive))) remotes::install_url(archive[[p]], lib = lib, upgrade = "never")

left <- missing(c(cran, bioc, names(github), names(archive)))
if ("spARI" %in% left)
  message("spARI is in Bioconductor from release 3.22 (R 4.5). This R uses release ", BiocManager::version())
if (length(left)) stop("not installed: ", paste(left, collapse = ", "))
cat("all R packages of the kdomainbench", if (metrics) "metrics" else "methods", "are installed\n")
