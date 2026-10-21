# Builds the teaching datasets that mirror the ones used in the lectures
suppressMessages(library(jsonlite))
# Run from this folder: Rscript gen_data.R   (market CSVs come from dl.py)
d <- "../data"; set.seed(2026)

# Module 1: practice_data.csv (typed in Excel in class)
write.csv(data.frame(Country = c("India", "China", "Japan", "USA", "Russia"),
                     Characteristics.1 = c(20, 25, 30, 35, 40),
                     Characteristics.2 = c(10, 20, 30, 40, 50)),
          file.path(d, "practice_data.csv"), row.names = FALSE)

# Module 1: sample_financial_data.csv: ABC Limited with planted data-quality problems
dates <- seq(as.Date("2025-01-01"), by = "day", length.out = 50)
dates <- dates[!weekdays(dates) %in% c("Saturday", "Sunday")][1:30]
px <- round(104 + cumsum(rnorm(30, 0.25, 1.4)), 1)
vol <- round(runif(30, 120000, 210000), -2)
ret <- round(c(NA, diff(px) / head(px, -1)), 4); ret[1] <- 0.004
abc <- data.frame(Date = format(dates, "%d-%m-%Y"), Company = "ABC Limited", Sector = "Banking",
                  Closing_Price = px, Volume = vol, Market_Return = ret)
abc$Company[c(4, 19, 23)] <- c("ABC LimiTed", "abc limited", "ABC LIMITED")
abc$Sector[c(7, 19, 26)] <- c("banking", "BANKING", "banking")
abc$Closing_Price[8] <- NA
abc$Volume[21] <- NA
abc$Closing_Price[25] <- 999
abc <- rbind(abc[1:15, ], abc[10, ], abc[16:30, ])   # duplicate of row 10 appears as row 16
write.csv(abc, file.path(d, "sample_financial_data.csv"), row.names = FALSE)

# Module 2: bitcoin.csv: real BTC-USD spot vs CME futures (BTC=F) closes from Yahoo Finance
if (file.exists("btc_raw.json")) {
b <- fromJSON("btc_raw.json")
bt <- data.frame(Date = b$dates, Spot_Price = round(b$spot, 2), Future_Price = round(b$fut, 2))
bt$Spot_Returns <- c(NA, diff(log(bt$Spot_Price)))
bt$Future_Returns <- c(NA, diff(log(bt$Future_Price)))
bt <- bt[-1, c("Date", "Spot_Returns", "Future_Returns", "Spot_Price", "Future_Price")]
bt$Spot_Returns <- round(bt$Spot_Returns, 6); bt$Future_Returns <- round(bt$Future_Returns, 6)
write.csv(bt, file.path(d, "bitcoin.csv"), row.names = FALSE)
}

# Module 2: AirPassengers.csv (same numbers as R's built-in dataset)
write.csv(data.frame(Month = format(seq(as.Date("1949-01-01"), by = "month", length.out = 144), "%Y-%m"),
                     Passengers = as.integer(AirPassengers)),
          file.path(d, "AirPassengers.csv"), row.names = FALSE)

# Module 3: salary.csv: 24 employees (salary in Rs '000s per month)
n <- 24
Experience <- round(runif(n, 1, 25))
Rating <- round(pmin(10, pmax(3, 4 + 0.12 * Experience + rnorm(n, 0, 1.2))), 1)
Certifications <- pmin(6, pmax(0, round(0.06 * Experience + rnorm(n, 1.6, 1.1))))
Salary <- round(35 + 1.05 * Rating + 0.33 * Experience + 1.3 * Certifications + rnorm(n, 0, 1.1), 1)
write.csv(data.frame(Employee_ID = sprintf("E%02d", 1:n), Salary, Rating, Experience, Certifications),
          file.path(d, "salary.csv"), row.names = FALSE)

# Module 3: CF_data.csv: 80 quarters of a firm's ratios, built with collinearity and autocorrelated errors
q <- 80
Quarter <- paste0(rep(2006:2025, each = 4), "-Q", 1:4)
Total_Assets <- round(5000 * exp(cumsum(rnorm(q, 0.02, 0.03))))
Revenue <- round(Total_Assets * runif(q, 0.22, 0.28))
EBITDA_Margin <- round(pmax(0.08, 0.2 + arima.sim(list(ar = .7), q, sd = .02)), 3)
EBIT <- round(Revenue * (EBITDA_Margin - 0.04))
Leverage_Ratio <- round(0.45 + arima.sim(list(ar = .9), q, sd = .025), 3)
Debt_Equity_Ratio <- round(Leverage_Ratio / (1 - Leverage_Ratio) + rnorm(q, 0, .01), 3)
Policy_Interest_Rate <- round(6 + 1.5 * sin((1:q) / 9) + rnorm(q, 0, .15), 2)
Interest_Expenses <- round(Total_Assets * Leverage_Ratio * (Policy_Interest_Rate + 2) / 400)
Interest_Coverage <- round(EBIT / Interest_Expenses, 2)
Net_Income <- round((EBIT - Interest_Expenses) * 0.75)
ROA <- round(Net_Income / Total_Assets, 4)
Net_Profit_Margin <- round(Net_Income / Revenue, 4)
Capital_Intensity <- round(Total_Assets / Revenue, 3)
Current_Ratio <- round(1.4 + arima.sim(list(ar = .6), q, sd = .08), 2)
Sales_Growth <- round(c(NA, diff(log(Revenue))), 4); Sales_Growth[1] <- 0.02
u <- arima.sim(list(ar = .6), q, sd = .07)
Firm_Value_TobinsQ <- round(0.6 + 9 * ROA + 0.04 * Interest_Coverage - 0.35 * Leverage_Ratio -
  0.05 * Policy_Interest_Rate + 0.25 * Current_Ratio + 0.8 * Sales_Growth + u, 3)
write.csv(data.frame(Quarter, Revenue, EBITDA_Margin, EBIT, Net_Income, Total_Assets, Leverage_Ratio,
                     Debt_Equity_Ratio, Interest_Expenses, Interest_Coverage, ROA, Net_Profit_Margin,
                     Capital_Intensity, Current_Ratio, Sales_Growth, Policy_Interest_Rate, Firm_Value_TobinsQ),
          file.path(d, "CF_data.csv"), row.names = FALSE)
cat("done\n")

# Module 5: portfolio_returns.csv: equal-weight portfolio of five NIFTY heavyweights, 2023-2025 (real prices)
stk <- c("RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK")
pr <- Reduce(function(a, b) merge(a, b, by = "Date"),
             lapply(stk, function(s) { x <- read.csv(file.path(d, paste0(s, ".csv")))[, c("Date", "Adjusted")]; names(x)[2] <- s; x }))
pr <- pr[pr$Date >= "2022-12-30", ]
rets <- sapply(stk, function(s) diff(log(pr[[s]])))
pf <- data.frame(Date = format(as.Date(pr$Date[-1]), "%d-%m-%Y"), Portfolio_Return = round(rowMeans(rets), 6))
write.csv(pf, file.path(d, "portfolio_returns.csv"), row.names = FALSE)
cat(nrow(pf), "portfolio days\n")
