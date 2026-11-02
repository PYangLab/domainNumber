# Write kdb_r.lock.csv: every non-base package in an R library, dependencies first.
# Usage: Rscript export_r_lock.R <library> <out.csv>
args <- commandArgs(trailingOnly = TRUE)
ip <- installed.packages(lib.loc = args[1], fields = c("Repository", "biocViews"))
pk <- rownames(ip)
deps <- tools::package_dependencies(pk, db = ip, which = c("Depends", "Imports", "LinkingTo"))
deps <- lapply(deps, intersect, pk)
ord <- character(0)
while (length(ord) < length(pk)) {
  ready <- setdiff(pk[vapply(deps, function(d) all(d %in% ord), TRUE)], ord)
  if (!length(ready)) stop("dependency cycle")
  ord <- c(ord, sort(ready))
}
src <- ifelse(!is.na(ip[ord, "biocViews"]) | grepl("Bioconductor", ip[ord, "Repository"]), "bioc", "cran")
src[ord == "SC.MEB"] <- "archive"     # removed from CRAN; installed from the CRAN archive
write.csv(data.frame(Package = ord, Version = ip[ord, "Version"], Source = src), args[2], row.names = FALSE)
cat(length(ord), "packages:", table(src), "\n")
