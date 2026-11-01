# Install the exact R package versions listed in kdb_r.lock.csv (Package, Version, Source).
# Usage: Rscript install_r_packages.R kdb_r.lock.csv [library]
args <- commandArgs(trailingOnly = TRUE)
lock <- read.csv(args[1], stringsAsFactors = FALSE)
lib <- if (length(args) > 1) args[2] else .libPaths()[1]
dir.create(lib, recursive = TRUE, showWarnings = FALSE)
.libPaths(c(lib, .libPaths()))
options(repos = c(CRAN = "https://packagemanager.posit.co/cran/2024-10-01"), Ncpus = 8)
for (p in c("remotes", "BiocManager"))
  if (!requireNamespace(p, quietly = TRUE)) install.packages(p, lib = lib)
options(repos = BiocManager::repositories(version = "3.19"))

have <- function(p, v) {
  ok <- suppressWarnings(tryCatch(as.character(packageVersion(p, lib.loc = lib)) == v, error = function(e) FALSE))
  isTRUE(ok)
}
# Install in lock order (dependencies first); `dependencies = FALSE` keeps every version as locked.
for (i in seq_len(nrow(lock))) {
  p <- lock$Package[i]; v <- lock$Version[i]
  if (have(p, v)) next
  message("installing ", p, " ", v)
  if (lock$Source[i] == "bioc") {        # Bioconductor 3.19 serves exactly one version per package
    BiocManager::install(p, version = "3.19", lib = lib, dependencies = FALSE, update = FALSE, ask = FALSE)
  } else if (lock$Source[i] == "archive") {
    remotes::install_url(sprintf("https://cran.r-project.org/src/contrib/Archive/%s/%s_%s.tar.gz", p, p, v),
                         lib = lib, dependencies = FALSE, upgrade = "never")
  } else {
    remotes::install_version(p, version = v, lib = lib, dependencies = FALSE, upgrade = "never",
                             repos = getOption("repos"))
  }
}
missing <- lock$Package[!mapply(have, lock$Package, lock$Version)]
if (length(missing)) stop("not installed at the locked version: ", paste(missing, collapse = ", "))
cat("all", nrow(lock), "R packages installed at the locked versions\n")
