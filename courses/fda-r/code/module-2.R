# Financial Data Analytics using R — Module 2: Statistical Foundations for Financial Time Series
# https://xploreai.co.in/courses/fda-r/module-2/
# Every data file is read straight from the course site, so this script runs as-is.


# ============================================================================
# Session 2.1 — Descriptive statistics I: centre and spread
# ============================================================================

# --- Central tendency ---

x <- c(10, 11, 12, 8, 9)
mean(x)
median(x)          # sorted: 8 9 10 11 12, so the middle value is 10

y <- c(20, 30, 25, 30, 40, 30, 35)
mode_stat <- function(v) { t <- table(v); as.numeric(names(t)[which.max(t)]) }
mode_stat(y)

# --- Dispersion ---

z <- c(4, 9, 2, 6, 1, 12, 3, 8, 9)
range(z)
diff(range(z))                    # 12 - 1 = 11
quantile(z, c(0.25, 0.5, 0.75))
IQR(z)
IQR(z) / 2                        # quartile deviation

# ============================================================================
# Session 2.2 — Descriptive statistics II: risk, skewness and kurtosis
# ============================================================================

# --- Variance and standard deviation ---

r <- c(0.04, -0.01, 0.06, 0.02, -0.03, 0.05, 0.01)   # seven monthly returns
sum(r - mean(r))                  # always (almost) exactly zero
mean(abs(r - mean(r)))            # mean absolute deviation
var(r)
sd(r)

# --- The empirical rule ---

# --- Coefficient of variation: risk per unit of return ---

stocks <- data.frame(stock = c("A", "B"), mean_ret = c(10, 12), sd_ret = c(6, 7))
stocks$CV <- round(stocks$sd_ret / stocks$mean_ret, 3)
stocks

# --- Skewness and kurtosis ---

# ============================================================================
# Session 2.3 — Descriptive statistics in R: Bitcoin spot vs futures
# ============================================================================

url <- "https://xploreai.co.in/courses/fda-r/data/"
bitcoin <- read.csv(paste0(url, "bitcoin.csv"))
str(bitcoin)

mean(bitcoin$Spot_Returns)
sd(bitcoin$Spot_Returns)
range(bitcoin$Spot_Returns)
summary(bitcoin[, -1])     # -1 drops the Date column

# install.packages("psych")

library(psych)
describe(bitcoin[, -1])

# ============================================================================
# Session 2.4 — Graphical analysis: histograms, box plots and scatter plots
# ============================================================================

# --- Histogram: the shape of the distribution ---

rust <- "#E2571B"; espresso <- "#4A4238"; peach <- "#F3C7B0"
hist(bitcoin$Spot_Returns, breaks = 80, col = rust, border = "white",
     xlab = "Daily log return", ylab = "Number of days",
     main = "Bitcoin spot returns: tall peak, long tails")

# --- Four charts at once with par(mfrow) ---

par(mfrow = c(2, 2))
hist(bitcoin$Spot_Returns,   breaks = 60, col = rust,     border = "white", main = "Spot returns",   xlab = "")
hist(bitcoin$Future_Returns, breaks = 60, col = espresso, border = "white", main = "Futures returns", xlab = "")
hist(bitcoin$Spot_Price,     breaks = 40, col = peach,    border = "white", main = "Spot price",     xlab = "")
hist(bitcoin$Future_Price,   breaks = 40, col = "#C9B8A3", border = "white", main = "Futures price",  xlab = "")
par(mfrow = c(1, 1))   # always reset afterwards

# --- Box plots: outliers at a glance ---

par(mfrow = c(1, 2))
boxplot(bitcoin$Spot_Returns,   main = "Spot returns",    col = peach, border = espresso, outcol = rust)
boxplot(bitcoin$Future_Returns, main = "Futures returns", col = peach, border = espresso, outcol = rust)
par(mfrow = c(1, 1))

# --- Scatter plot: do spot and futures move together? ---

plot(bitcoin$Spot_Returns, bitcoin$Future_Returns, pch = 16, cex = .5,
     col = adjustcolor(rust, .45), xlab = "Spot return", ylab = "Futures return",
     main = "Spot vs futures daily returns")
abline(lm(Future_Returns ~ Spot_Returns, data = bitcoin), col = espresso, lwd = 2)

# --- Everything in one picture: pairs.panels() ---

pairs.panels(bitcoin[, -1], hist.col = rust, col = espresso, lm = TRUE, stars = TRUE)

# ============================================================================
# Session 2.5 — Time-series components and stationarity
# ============================================================================

# ============================================================================
# Session 2.6 — Testing stationarity in R
# ============================================================================

# --- Step 1: declare it as a time series ---

AP <- read.csv(paste0(url, "AirPassengers.csv"))
str(AP)
AP_T <- ts(AP$Passengers, frequency = 12, start = c(1949, 1))
str(AP_T)

plot(AP_T, col = rust, lwd = 2, ylab = "Passengers ('000)", xlab = "",
     main = "Airline passengers: trend + seasonality")

# --- Step 2: the ADF test with urca ---

# install.packages("urca")

library(urca)
model1 <- ur.df(AP_T, type = "none", lags = 1)
summary(model1)

# --- Step 3: difference and test again ---

AP_T_D <- diff(AP_T, differences = 1)
head(AP_T_D)             # 118-112 = 6, 132-118 = 14, ...
plot(AP_T_D, col = rust, lwd = 1.6, ylab = "Change", xlab = "",
     main = "First difference: the trend is gone")
abline(h = 0, col = espresso, lty = 2)
model2 <- ur.df(AP_T_D, type = "none", lags = 1)
summary(model2)@teststat
model2@cval

# --- Getting a p-value instead ---

library(tseries)
adf.test(AP_T_D)
kpss.test(AP_T_D)
