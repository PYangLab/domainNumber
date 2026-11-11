#!/usr/bin/env Rscript

# Calculate the R metric set for one Dataset x Method pair.
# Every call uses all observations and physical pixel coordinates.
# SCS is computed separately by metric/scs.py (PASTE's own Python code) and
# added to this output by metric/merge_scs.py.

DEFAULT_METRICS <- c(
  "ARI", "spARI", "NMI", "FM", "AMI", "Purity",
  "HOM", "COM", "PAS", "CHAOS", "LISI"
)

# PAS and CHAOS are computed by fx_PAS() and fx_CHAOS() of the SpatialPCA
# package, the implementation released by the authors who introduced both
# metrics for spatial domains: https://github.com/shangll123/SpatialPCA
# metric/parity/ checks the installed functions against a pinned commit.

collect_metrics <- function(
  truth,
  pred,
  physical_coords
) {
  physical_coords <- as.matrix(physical_coords)
  truth <- droplevels(factor(as.character(truth)))
  pred <- droplevels(factor(as.character(pred)))

  if (nlevels(truth) < 2L) {
    stop(
      "Reference labels must contain at least two domains.",
      call. = FALSE
    )
  }

  report <- clevr::eval_report_clusters(truth, pred)
  nmi <- aricode::NMI(truth, pred, variant = "sum")

  values <- c(
    ARI = unname(report$adj_rand_index),
    spARI = spARI::spARI(
      r_labels = truth,
      c_labels = pred,
      coords = physical_coords
    )[["spARI"]],
    # NMI-arithmetic = 2 * I(truth; pred) / (H(truth) + H(pred)).
    # ## Source: aricode calls the arithmetic-mean normalizer variant = "sum":
    # https://jchiquet.github.io/aricode/reference/NMI.html
    # We call the NMI function directly and retain the conventional NMI output
    # name for benchmark comparability.
    NMI = nmi,
    FM = unname(report$fowlkes_mallows),
    AMI = aricode::AMI(truth, pred),
    Purity = unname(ClusterR::external_validation(
      as.integer(truth),
      as.integer(pred),
      method = "purity"
    )),
    HOM = unname(report$homogeneity),
    COM = unname(report$completeness),
    PAS = SpatialPCA::fx_PAS(as.character(pred), physical_coords),
    CHAOS = SpatialPCA::fx_CHAOS(as.character(pred), physical_coords),
    # LISI on spatial coordinates and predicted labels, as in SpatialPCA's
    # analysis code: compute_lisi(location, labels) with the package defaults
    # (perplexity = 30, exact neighbours). That code keeps one value per spot;
    # the paper reports the median.
    # ## Source: https://github.com/shangll123/SpatialPCA_analysis_codes
    LISI = stats::median(lisi::compute_lisi(
      X = physical_coords,
      meta_data = data.frame(cluster = as.character(pred)),
      label_colnames = "cluster"
    )[["cluster"]])
  )

  data.frame(
    metric = names(values),
    value = unname(values),
    stringsAsFactors = FALSE
  )
}

# ---------------------------------------------------------------------------
# Reading and aligning inputs
# ---------------------------------------------------------------------------
align_prediction_labels <- function(prediction, reference_ids) {
  reference_ids <- as.character(reference_ids)
  prediction_ids <- as.character(prediction[["spot_id"]])

  if (!identical(sort(reference_ids), sort(prediction_ids))) {
    stop("Prediction IDs do not match the dataset.", call. = FALSE)
  }

  as.character(prediction[["cluster"]][match(reference_ids, prediction_ids)])
}

collect_metrics_from_files <- function(
  h5ad_path,
  pred_path,
  out_path = NULL
) {
  sce <- zellkonverter::readH5AD(h5ad_path, use_hdf5 = TRUE, reader = "R")
  col_data <- as.data.frame(SummarizedExperiment::colData(sce))

  required <- c("clusters", "pixel_row", "pixel_col")
  missing_columns <- setdiff(required, names(col_data))
  if (length(missing_columns) > 0L) {
    stop(sprintf("Dataset is missing required column(s): %s",
                 paste(missing_columns, collapse = ", ")), call. = FALSE)
  }

  reference_ids <- rownames(col_data)
  prediction <- utils::read.csv(pred_path, stringsAsFactors = FALSE,
                                check.names = FALSE)
  pred <- align_prediction_labels(prediction, reference_ids)

  physical_coords <- cbind(
    pixel_row = as.numeric(col_data[["pixel_row"]]),
    pixel_col = as.numeric(col_data[["pixel_col"]])
  )

  result <- collect_metrics(
    truth = col_data[["clusters"]],
    pred = pred,
    physical_coords = physical_coords
  )

  if (!is.null(out_path)) {
    dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)
    utils::write.csv(result, file = out_path, row.names = FALSE)
  }
  result
}

main <- function(args = commandArgs(trailingOnly = TRUE)) {
  result <- collect_metrics_from_files(args[[1]], args[[2]], args[[3]])
  cat("Wrote metrics to:", args[[3]], "\n")
  print(result, row.names = FALSE)
  invisible(result)
}

if (sys.nframe() == 0L) {
  main()
}
