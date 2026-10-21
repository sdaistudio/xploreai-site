# Financial Data Analytics using R — Module 4: Time Series Models and Forecasting in R
# https://xploreai.co.in/courses/fda-r/module-4/
# Every data file is read straight from the course site, so this script runs as-is.


# ============================================================================
# Session 4.1 — Time-series components and ARIMA models
# ============================================================================

# --- ARIMA(p, d, q): forecasting a series from its own past ---

# --- Regression is not causality ---

# --- Choosing the causality framework ---

# ============================================================================
# Session 4.2 — ARIMA in R: forecasting airline passengers
# ============================================================================

url <- "https://xploreai.co.in/courses/fda-r/data/"
rust <- "#E2571B"; espresso <- "#4A4238"
AP <- read.csv(paste0(url, "AirPassengers.csv"))
AP_T <- ts(AP$Passengers, frequency = 12, start = c(1949, 1))

library(urca)
summary(ur.df(AP_T))@teststat                  # level: above -1.95, so non-stationary
summary(ur.df(diff(AP_T)))@teststat            # first difference: stationary

# --- Let auto.arima choose the model ---

# install.packages("forecast")

library(forecast)
model <- auto.arima(AP_T)
model

# --- Forecast four years ahead ---

F <- forecast(model, h = 48)
head(as.data.frame(F), 6)

autoplot(F, fcol = rust) +
  ggplot2::labs(title = "Airline passengers: ARIMA forecast, 1961-64", x = NULL, y = "Passengers ('000)") +
  ggplot2::theme_minimal(base_size = 12)

# --- Is the model any good? Check the residuals ---

checkresiduals(model)

# ============================================================================
# Session 4.3 — Causality with VAR, part 1: stationarity, lags and Granger
# ============================================================================

bitcoin <- read.csv(paste0(url, "bitcoin.csv"))
spot_R_T   <- ts(bitcoin$Spot_Returns,   frequency = 252, start = c(2017, 245))
future_R_T <- ts(bitcoin$Future_Returns, frequency = 252, start = c(2017, 245))

par(mfrow = c(2, 1), mar = c(2.5, 4, 2.5, 1))
plot(spot_R_T,   col = rust,     main = "Bitcoin spot returns",    ylab = "")
plot(future_R_T, col = espresso, main = "Bitcoin futures returns", ylab = "")
par(mfrow = c(1, 1))

# --- Step 1: both must be stationary ---

summary(ur.df(spot_R_T))@teststat
summary(ur.df(future_R_T))@teststat

# --- Step 2: choose the lag length ---

# install.packages(c("vars", "lmtest"))

library(vars)
VARselect(spot_R_T,   lag.max = 10)$selection
VARselect(future_R_T, lag.max = 10)$selection

# --- Step 3: Granger causality in both directions ---

library(lmtest)
lag_spot   <- VARselect(spot_R_T,   lag.max = 10)$selection[["AIC(n)"]]
lag_future <- VARselect(future_R_T, lag.max = 10)$selection[["AIC(n)"]]
grangertest(future_R_T ~ spot_R_T,   order = lag_future)   # does spot lead futures?
grangertest(spot_R_T   ~ future_R_T, order = lag_spot)     # does futures lead spot?

# ============================================================================
# Session 4.4 — Causality with VAR, part 2: estimating and reading the VAR
# ============================================================================

model1 <- VAR(data.frame(future = future_R_T, spot = spot_R_T),
              type = "const", lag.max = 5, ic = "AIC")
model1$p                                         # lag chosen by AIC
round(coef(model1)$future, 4)                    # the futures equation only

model2 <- VAR(data.frame(spot = spot_R_T, future = future_R_T),
              type = "const", lag.max = 5, ic = "AIC")
round(coef(model2)$spot, 4)                       # the spot equation only

# --- A picture of causality: impulse responses ---

ir <- irf(model1, impulse = "spot", response = "future", n.ahead = 8, boot = TRUE, runs = 200)
plot(ir, main = "Futures returns after a shock to spot returns", col = rust)

# ============================================================================
# Session 4.5 — Causality with VECM: when prices share a long-run path
# ============================================================================

BS_T <- ts(bitcoin$Spot_Price,   frequency = 252, start = c(2017, 245))
BF_T <- ts(bitcoin$Future_Price, frequency = 252, start = c(2017, 245))
ts.plot(BS_T, BF_T, col = c(rust, espresso), lwd = c(2, 1), ylab = "USD",
        main = "Bitcoin spot (orange) and futures (dark) prices")

# --- Step 1: both prices are I(1) ---

c(spot_level   = summary(ur.df(BS_T))@teststat,
  spot_diff    = summary(ur.df(diff(BS_T)))@teststat,
  future_level = summary(ur.df(BF_T))@teststat,
  future_diff  = summary(ur.df(diff(BF_T)))@teststat)

# --- Step 2: lag length on the differenced series ---

VARselect(data.frame(diff(BF_T), diff(BS_T)), lag.max = 10, type = "const")$selection

# --- Step 3: the Johansen cointegration test ---

jo <- ca.jo(data.frame(future = BF_T, spot = BS_T), type = "trace", ecdet = "const", K = 5)
summary(jo)

# --- Step 4: estimate the VECM ---

vecm <- cajorls(jo, r = 1)
vecm$beta                                        # the long-run (cointegrating) relationship
summary(vecm$rlm)$`Response future.d`$coefficients[1:6, ]

summary(vecm$rlm)$`Response spot.d`$coefficients[1:6, ]

# ============================================================================
# Session 4.6 — Causality with ARDL: when the orders of integration are mixed
# ============================================================================

# --- The long run: the Pesaran–Shin–Smith bounds test ---

# install.packages("dLagM")

library(dLagM)
btc <- data.frame(Spot_Return = bitcoin$Spot_Returns, Future_Price = bitcoin$Future_Price)
bound1 <- ardlBound(data = btc, formula = Spot_Return ~ Future_Price, case = 3,
                    p = data.frame(Spot_Return = 1, Future_Price = 5))

# --- The short run: the distributed-lag model ---

dlm1 <- ardlDlm(x = btc$Future_Price, y = btc$Spot_Return, p = 5, q = 1)
summary(dlm1)$coefficients
