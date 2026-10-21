# Financial Data Analytics using R — Module 6: Applications of Financial Data Analytics in the Real World
# https://xploreai.co.in/courses/fda-r/module-6/
# Every data file is read straight from the course site, so this script runs as-is.


# ============================================================================
# Session 6.1 — Event study: the COVID-19 lockdown and NIFTY 50
# ============================================================================

# --- The timeline ---

# --- The formulas ---

library(xts)
url <- "https://xploreai.co.in/courses/fda-r/data/"
rust <- "#E2571B"; espresso <- "#4A4238"
nifty <- read.csv(paste0(url, "NIFTY50.csv"))
nifty$Date <- as.Date(nifty$Date)
nifty <- subset(nifty, Date >= as.Date("2019-09-01") & Date <= as.Date("2020-05-31"))

returns_df <- data.frame(Date = nifty$Date[-1], Return = diff(log(nifty$Close)))
event_date <- as.Date("2020-03-25")
event_index <- which(returns_df$Date == event_date)
est_window <- 120; event_window <- 10

est_data <- returns_df[(event_index - event_window - est_window):(event_index - event_window - 1), ]
evt_data <- returns_df[(event_index - event_window):(event_index + event_window), ]
range(est_data$Date); range(evt_data$Date)

# --- Abnormal and cumulative abnormal returns ---

exp_ret <- mean(est_data$Return)
sd_est  <- sd(est_data$Return)

evt_data$EventTime <- -event_window:event_window
evt_data$AR  <- evt_data$Return - exp_ret
evt_data$CAR <- cumsum(evt_data$AR)
evt_data$t_AR <- evt_data$AR / sd_est
print(transform(evt_data, Return = round(Return * 100, 2), AR = round(AR * 100, 2),
                CAR = round(CAR * 100, 2), t_AR = round(t_AR, 2)), row.names = FALSE)

CAR_full <- sum(evt_data$AR)
t_CAR <- CAR_full / (sd_est * sqrt(nrow(evt_data)))
cat("Event-day AR:", round(evt_data$AR[evt_data$EventTime == 0] * 100, 2), "%  t =",
    round(evt_data$t_AR[evt_data$EventTime == 0], 2), "\n")
cat("CAR(-10,+10):", round(CAR_full * 100, 2), "%  t =", round(t_CAR, 2), "\n")

# --- Visualise ---

par(mfrow = c(2, 1), mar = c(3, 4.2, 2.6, 1))
barplot(evt_data$AR * 100, names.arg = evt_data$EventTime, col = ifelse(evt_data$AR < 0, rust, "#C9B8A3"),
        border = NA, ylab = "AR (%)", main = "Abnormal returns, t = -10 to +10")
abline(h = 0, col = espresso)
plot(evt_data$EventTime, evt_data$CAR * 100, type = "b", pch = 19, col = rust, lwd = 2,
     xlab = "", ylab = "CAR (%)", main = "Cumulative abnormal return")
abline(v = 0, h = 0, col = espresso, lty = 2)
par(mfrow = c(1, 1))

# write.csv(evt_data, "event_study_results.csv", row.names = FALSE)   # saved to getwd()

# ============================================================================
# Session 6.2 — Does the US lead India? Causality between NIFTY and the S&P 500
# ============================================================================

sp <- read.csv(paste0(url, "SP500.csv"))
nf <- read.csv(paste0(url, "NIFTY50.csv"))
price_data <- na.omit(merge(data.frame(Date = nf$Date, nifty_close = nf$Close),
                            data.frame(Date = sp$Date, sp500_close = sp$Close), by = "Date"))
price_data$Date <- as.Date(price_data$Date)
dim(price_data)

par(mar = c(3, 4.5, 3, 4.5))
plot(price_data$Date, price_data$nifty_close, type = "l", col = rust, lwd = 1.6, xlab = "", ylab = "NIFTY 50",
     main = "NIFTY 50 (orange, left) and S&P 500 (dark, right)")
par(new = TRUE)
plot(price_data$Date, price_data$sp500_close, type = "l", col = espresso, lwd = 1.2, axes = FALSE, xlab = "", ylab = "")
axis(4); par(mar = c(5, 4, 4, 2) + .1)

# --- Step 1: orders of integration ---

library(urca)
nifty_d <- diff(price_data$nifty_close); sp_d <- diff(price_data$sp500_close)
c(nifty_level = summary(ur.df(price_data$nifty_close))@teststat,
  nifty_diff  = summary(ur.df(nifty_d))@teststat,
  sp_level    = summary(ur.df(price_data$sp500_close))@teststat,
  sp_diff     = summary(ur.df(sp_d))@teststat)

# --- Step 2: lags and cointegration ---

library(vars)
VARselect(data.frame(nifty_d, sp_d), lag.max = 10, type = "const")$selection
jo <- ca.jo(data.frame(nifty = price_data$nifty_close, sp500 = price_data$sp500_close),
            type = "trace", ecdet = "const", K = 2)
cbind(test = round(jo@teststat, 2), jo@cval)

# --- Step 3: the VAR on daily changes ---

diff_data <- data.frame(nifty = nifty_d, sp500 = sp_d)
var1 <- VAR(diff_data, lag.max = 5, ic = "AIC", type = "const")
round(coef(var1)$nifty[1:4, ], 4)        # NIFTY equation: does the S&P lead?
round(coef(var1)$sp500[1:4, ], 4)        # S&P equation: does NIFTY lead?

# --- Step 4: Granger causality in both directions ---

library(lmtest)
k <- var1$p
grangertest(nifty ~ sp500, order = k, data = diff_data)
grangertest(sp500 ~ nifty, order = k, data = diff_data)

# ============================================================================
# Session 6.3 — The machine learning framework for finance
# ============================================================================

# --- Two families ---

# --- The models in Session 6.4 ---

# ============================================================================
# Session 6.4 — Machine learning in R: predicting NIFTY's direction
# ============================================================================

# install.packages(c("TTR", "caret", "rpart", "randomForest", "e1071", "neuralnet"))

library(TTR)
nf <- read.csv(paste0(url, "NIFTY50.csv")); sp <- read.csv(paste0(url, "SP500.csv"))
d <- na.omit(merge(data.frame(Date = nf$Date, close = nf$Close, volume = nf$Volume),
                   data.frame(Date = sp$Date, sp_close = sp$Close), by = "Date"))
d <- subset(d, Date >= "2018-01-01" & volume > 0)

d$ret     <- c(NA, diff(log(d$close))) * 100
d$sp_ret  <- c(NA, diff(log(d$sp_close))) * 100
d$lag1    <- d$ret; d$lag2 <- c(NA, head(d$ret, -1)); d$lag3 <- c(NA, NA, head(d$ret, -2))
d$ma5_gap  <- (d$close / SMA(d$close, 5) - 1) * 100
d$ma20_gap <- (d$close / SMA(d$close, 20) - 1) * 100
d$rsi14    <- RSI(d$close, 14)
d$vol10    <- runSD(d$ret, 10)
d$vol_chg  <- c(NA, diff(log(d$volume)))

# the target is TOMORROW's return: every feature is known today
d$next_ret  <- c(d$ret[-1], NA)
d$Direction <- factor(ifelse(d$next_ret > 0, "Up", "Down"))
ml_df <- na.omit(d)
nrow(ml_df); table(ml_df$Direction)

# --- Split by time, not at random ---

predictors <- c("lag1", "lag2", "lag3", "sp_ret", "ma5_gap", "ma20_gap", "rsi14", "vol10", "vol_chg")
cut   <- floor(0.8 * nrow(ml_df))
train <- ml_df[1:cut, ];  test <- ml_df[(cut + 1):nrow(ml_df), ]
range(train$Date); range(test$Date)
fml_reg <- as.formula(paste("next_ret ~", paste(predictors, collapse = " + ")))
fml_cls <- as.formula(paste("Direction ~", paste(predictors, collapse = " + ")))

# --- 1. Linear regression (the baseline) ---

library(caret)
lm_model <- lm(fml_reg, data = train)
round(summary(lm_model)$coefficients, 4)
lm_pred <- predict(lm_model, test)
c(adj_R2 = round(summary(lm_model)$adj.r.squared, 4),
  RMSE = round(RMSE(lm_pred, test$next_ret), 3), MAE = round(MAE(lm_pred, test$next_ret), 3),
  RMSE_naive = round(RMSE(rep(mean(train$next_ret), nrow(test)), test$next_ret), 3))

# --- 2. Decision tree ---

library(rpart)
tree_model <- rpart(fml_cls, data = train, method = "class", control = rpart.control(cp = 0.004, maxdepth = 4))
tree_pred  <- predict(tree_model, test, type = "class")
par(xpd = NA, mar = c(1, 1, 2, 1))
plot(tree_model, uniform = TRUE, branch = .6, margin = .06, col = espresso, main = "Decision tree: Up or Down tomorrow?")
text(tree_model, use.n = TRUE, cex = .72, col = rust)

confusionMatrix(tree_pred, test$Direction, positive = "Up")

# --- 3. Random forest ---

library(randomForest)
set.seed(123)
rf_model <- randomForest(fml_cls, data = train, ntree = 500)
rf_pred  <- predict(rf_model, test)
confusionMatrix(rf_pred, test$Direction, positive = "Up")$overall[c("Accuracy", "AccuracyNull", "AccuracyPValue")]

varImpPlot(rf_model, main = "Random forest: which features matter?", pch = 19, col = rust)

# --- 4. Support vector machine ---

library(e1071)
svm_model <- svm(fml_cls, data = train, kernel = "radial")
svm_pred  <- predict(svm_model, test)
confusionMatrix(svm_pred, test$Direction, positive = "Up")$overall[c("Accuracy", "AccuracyNull", "AccuracyPValue")]

# --- 5. Neural network ---

library(neuralnet)
mins <- sapply(train[predictors], min); maxs <- sapply(train[predictors], max)
sc <- function(df) as.data.frame(scale(df[predictors], center = mins, scale = maxs - mins))
nn_train <- sc(train); nn_train$Up <- as.numeric(train$Direction == "Up")
set.seed(123)
nn_model <- neuralnet(as.formula(paste("Up ~", paste(predictors, collapse = " + "))),
                      data = nn_train, hidden = 3, linear.output = FALSE, stepmax = 1e6)
nn_prob <- compute(nn_model, sc(test))$net.result
nn_pred <- factor(ifelse(nn_prob > 0.5, "Up", "Down"), levels = c("Down", "Up"))
confusionMatrix(nn_pred, test$Direction, positive = "Up")$overall[c("Accuracy", "AccuracyNull", "AccuracyPValue")]

plot(nn_model, rep = "best", col.entry = espresso, col.hidden = rust, col.out = espresso,
     col.intercept = "#C9B8A3", show.weights = FALSE, information = FALSE, fontsize = 10)

# --- Compare all four ---

acc <- data.frame(Model = c("Decision tree", "Random forest", "SVM", "Neural net"),
                  Accuracy = 100 * c(mean(tree_pred == test$Direction), mean(rf_pred == test$Direction),
                                     mean(svm_pred == test$Direction), mean(nn_pred == test$Direction)))
nir <- 100 * max(prop.table(table(test$Direction)))
acc$Accuracy <- round(acc$Accuracy, 1); acc
bp <- barplot(acc$Accuracy, names.arg = acc$Model, col = rust, border = NA, ylim = c(0, 75),
              ylab = "Out-of-sample accuracy (%)", main = "Next-day direction: models vs 'always say Up'")
abline(h = nir, col = espresso, lty = 2, lwd = 2)
text(bp, acc$Accuracy + 3, paste0(acc$Accuracy, "%"), col = espresso, font = 2)
