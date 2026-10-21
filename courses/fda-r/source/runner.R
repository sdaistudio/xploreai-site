# Runs every chunk of one module in a shared environment and records
# console output + plots.  Usage: Rscript runner.R chunks.json outdir datadir
suppressMessages({library(jsonlite); library(evaluate)})
args <- commandArgs(TRUE)
chunks <- fromJSON(args[1], simplifyVector = FALSE)
outdir <- args[2]; datadir <- args[3]
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)
URL <- "https://xploreai.co.in/courses/fda-r/data/"
options(width = 88, digits = 5, scipen = 6, warn = 1)
set.seed(42)
env <- new.env(parent = globalenv())
brand <- function() par(bg = "#FFFDF8", fg = "#4A4238", col.axis = "#4A4238",
  col.lab = "#4A4238", col.main = "#4A4238", col.sub = "#4A4238",
  family = "Helvetica", las = 1, mgp = c(2.4, .7, 0), tcl = -.3, cex.main = 1.05, font.main = 2)
setHook("before.plot.new", function() brand())
res <- list()
for (ch in chunks) {
  code <- ch$code
  run <- gsub(URL, paste0(normalizePath(datadir), "/"), code, fixed = TRUE)
  if (isFALSE(ch$eval)) { res[[ch$id]] <- list(out = "", plots = list()); next }
  w <- if (is.null(ch$w)) 8 else ch$w; h <- if (is.null(ch$h)) 4.6 else ch$h
  pat <- file.path(outdir, paste0(ch$id, "-%d.png"))
  png(pat, width = w, height = h, units = "in", res = 170, bg = "#FFFDF8", type = "quartz")
  brand()
  r <- evaluate(run, envir = env, new_device = FALSE, stop_on_error = 0L,
                output_handler = new_output_handler(graphics = function(x) NULL))
  dev.off()
  out <- character()
  for (x in r) {
    if (is.character(x)) out <- c(out, x)
    else if (inherits(x, "message")) { m <- conditionMessage(x); if (!grepl("Attaching package|The following objects? (is|are) masked", m) && !grepl("^(randomForest [0-9]|Type rfNews|Registered S3|  method|  as\\.zoo|Loading required|Attaching package|The following object|    |\\n)", m)) out <- c(out, m) }
    else if (inherits(x, "warning")) out <- c(out, paste0("Warning message:\n", conditionMessage(x), "\n"))
    else if (inherits(x, "error")) { out <- c(out, paste0("Error: ", conditionMessage(x), "\n")); message("ERROR in ", ch$id, ": ", conditionMessage(x)) }
  }
  files <- list.files(outdir, pattern = paste0("^", ch$id, "-[0-9]+\\.png$"))
  files <- files[order(as.integer(sub(".*-([0-9]+)\\.png$", "\\1", files)))]
  # drop blank pages (cairo can leave an empty first page)
  keep <- files[file.size(file.path(outdir, files)) > 6000]
  file.remove(file.path(outdir, setdiff(files, keep)))
  res[[ch$id]] <- list(out = paste(out, collapse = ""), plots = as.list(keep))
}
writeLines(toJSON(res, auto_unbox = TRUE, pretty = TRUE), file.path(outdir, "results.json"))
