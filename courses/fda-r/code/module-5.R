# Financial Data Analytics using R — Module 5: Volatility Modeling and Risk Analytics
# https://xploreai.co.in/courses/fda-r/module-5/
# Every data file is read straight from the course site, so this script runs as-is.


# ============================================================================
# Session 5.1 — Volatility: why the variance itself needs a model
# ============================================================================

# --- ARCH (Engle, 1982) ---

# --- GARCH (Bollerslev, 1986) ---

# ============================================================================
# Session 5.2 — ARCH and GARCH in R: modelling NIFTY 50's volatility
# ============================================================================

# --- Get the data ---

# install.packages(c("quantmod", "rugarch", "FinTS"))
# library(quantmod)
# getSymbols("^NSEI", src = "yahoo", from = "2015-01-01")
# price <- Cl(NSEI)

library(xts)
url <- "https://xploreai.co.in/courses/fda-r/data/"
rust <- "#E2571B"; espresso <- "#4A4238"
nifty <- read.csv(paste0(url, "NIFTY50.csv"))
price <- xts(nifty$Close, order.by = as.Date(nifty$Date))
head(price, 3); tail(price, 3)

plot(price, col = rust, main = "NIFTY 50 close, 2015-2025", grid.col = "#EDE4D3", yaxis.right = FALSE)

# --- Log returns, and a look for clustering ---

returns <- na.omit(diff(log(price)))
plot(returns, col = espresso, main = "NIFTY 50 daily log returns", grid.col = "#EDE4D3", yaxis.right = FALSE)

# --- Step 1: a mean model ---

AR_fit <- arima(returns, order = c(1, 0, 0))
AR_fit
residuals_AR <- residuals(AR_fit)

# --- Step 2: the ARCH LM test ---

library(FinTS)
ArchTest(residuals_AR, lags = 12)

# --- Step 3: fit GARCH(1,1) ---

library(rugarch)
garch11_spec <- ugarchspec(
  variance.model     = list(model = "sGARCH", garchOrder = c(1, 1)),
  mean.model         = list(armaOrder = c(1, 0), include.mean = TRUE),
  distribution.model = "norm")
garch11_fit <- ugarchfit(spec = garch11_spec, data = returns)
round(garch11_fit@fit$matcoef, 6)

sum(coef(garch11_fit)[c("alpha1", "beta1")])      # persistence

# --- Conditional volatility through time ---

cond_vol <- sigma(garch11_fit) * sqrt(252) * 100         # annualised, in %
plot(cond_vol, col = rust, main = "NIFTY 50: GARCH(1,1) annualised volatility (%)",
     grid.col = "#EDE4D3", yaxis.right = FALSE)

# --- Forecast volatility 90 days ahead ---

garch_fc <- ugarchforecast(garch11_fit, n.ahead = 90)
sigma_fc <- as.numeric(sigma(garch_fc))
round(head(sigma_fc), 5)                         # daily sigma for T+1, T+2, ...
sqrt(sum(sigma_fc^2))                            # aggregate 90-day volatility

plot(sigma_fc * 100, type = "l", lwd = 2.5, col = rust, xlab = "Days ahead", ylab = "Daily sigma (%)",
     main = "GARCH forecast: volatility drifts back to its long-run level")
abline(h = sqrt(coef(garch11_fit)["omega"] / (1 - sum(coef(garch11_fit)[c("alpha1", "beta1")]))) * 100,
       col = espresso, lty = 2)

# ============================================================================
# Session 5.3 — Value at Risk and backtesting in R
# ============================================================================

data <- read.csv(paste0(url, "portfolio_returns.csv"))
str(data)
data$Date <- as.Date(data$Date, format = "%d-%m-%Y")
returns <- data$Portfolio_Return
mu <- mean(returns); sigma <- sd(returns)
cat("Mean:", round(mu, 6), "  SD:", round(sigma, 6), "  Days:", length(returns), "\n")
conf_level <- 0.95; alpha <- 1 - conf_level

# --- Three ways to calculate VaR ---

hist_var  <- quantile(returns, probs = alpha)
param_var <- mu + sigma * qnorm(alpha)
set.seed(123)
sim_returns <- rnorm(10000, mean = mu, sd = sigma)
mc_var <- quantile(sim_returns, probs = alpha)

var_results <- data.frame(Method  = c("Historical", "Parametric", "Monte Carlo"),
                          VaR     = round(c(hist_var, param_var, mc_var), 5),
                          LossPct = round(-100 * c(hist_var, param_var, mc_var), 3))
var_results

# --- Backtesting: did reality break the VaR as often as it should? ---

n_obs <- length(returns)
backtest <- data.frame(Method   = var_results$Method,
                       Expected = n_obs * alpha,
                       Actual   = c(sum(returns < hist_var), sum(returns < param_var), sum(returns < mc_var)))
backtest$ViolationRatio <- round(backtest$Actual / backtest$Expected, 3)
backtest

# --- The Kupiec test: is the gap statistically significant? ---

kupiec <- function(x, n, p) {
  phat <- x / n
  lr <- -2 * (log((1 - p)^(n - x) * p^x) - log((1 - phat)^(n - x) * phat^x))
  c(LR = round(lr, 3), p.value = round(1 - pchisq(lr, df = 1), 3))
}
t(sapply(backtest$Actual, kupiec, n = n_obs, p = alpha))

# --- Visualise ---

plot(data$Date, returns * 100, type = "h", col = ifelse(returns < hist_var, rust, "#C9B8A3"),
     xlab = "", ylab = "Daily return (%)", main = "Portfolio returns: days that breached the 95% VaR in orange")
abline(h = var_results$VaR * 100, col = c(rust, espresso, "#2F7D5B"), lty = c(1, 2, 3), lwd = 2)
legend("bottomleft", legend = var_results$Method, col = c(rust, espresso, "#2F7D5B"),
       lty = c(1, 2, 3), lwd = 2, bty = "n", cex = .85)

# --- From percent to rupees ---

portfolio_value <- 1e7                           # Rs 1 crore
data.frame(Method = var_results$Method,
           VaR_Rs = round(portfolio_value * var_results$LossPct / 100))

# ============================================================================
# Session 5.4 — The VaR framework: what it is, and what it misses
# ============================================================================

# --- The four ingredients ---

# --- Where VaR is used ---

# --- Choosing a method ---

# --- Limitations ---

ES_hist <- mean(returns[returns < hist_var])
c(VaR_95 = round(unname(hist_var) * 100, 2), ExpectedShortfall_95 = round(ES_hist * 100, 2))
