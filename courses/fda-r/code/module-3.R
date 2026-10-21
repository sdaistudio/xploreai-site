# Financial Data Analytics using R — Module 3: Predictive Analytics and Applications for Data Analysis
# https://xploreai.co.in/courses/fda-r/module-3/
# Every data file is read straight from the course site, so this script runs as-is.


# ============================================================================
# Session 3.1 — Introduction to predictive analytics
# ============================================================================

# --- The linear model ---

# --- Which model fits which data? ---

# ============================================================================
# Session 3.2 — Simple and multiple regression in R
# ============================================================================

url <- "https://xploreai.co.in/courses/fda-r/data/"
salary <- read.csv(paste0(url, "salary.csv"))
str(salary)

# --- Simple regression: Salary on Experience ---

model3 <- lm(Salary ~ Experience, data = salary)
summary(model3)

# --- Using the equation to predict ---

coef(model3)
coef(model3)[1] + coef(model3)[2] * 20          # by hand: someone with 20 years
predict(model3, newdata = data.frame(Experience = c(5, 10, 20)))

rust <- "#E2571B"; espresso <- "#4A4238"
plot(salary$Experience, salary$Salary, pch = 19, col = rust, cex = 1.3,
     xlab = "Experience (years)", ylab = "Salary (Rs '000)", main = "Salary vs experience, with the OLS line")
abline(model3, col = espresso, lwd = 2.5)

# --- Multiple regression ---

model4 <- lm(Salary ~ Rating + Experience + Certifications, data = salary)
summary(model4)

# ============================================================================
# Session 3.3 — The assumptions of the classical linear regression model
# ============================================================================

# ============================================================================
# Session 3.4 — Testing the assumptions: cross-sectional data
# ============================================================================

# --- Multicollinearity: correlations and VIF ---

library(psych)
pairs.panels(salary[, -1], hist.col = rust, col = espresso, stars = TRUE)

# install.packages(c("car", "lmtest"))

library(car)
vif(model4)

# --- Zero mean of errors ---

error_model4 <- resid(model4)
mean(error_model4)       # effectively zero

# --- Homoskedasticity: the Breusch–Pagan test ---

plot(error_model4^2, pch = 19, col = rust, ylab = "Squared residual", xlab = "Employee",
     main = "Error variance proxy: no obvious funnel")
library(lmtest)
bptest(model4)

# ============================================================================
# Session 3.5 — Testing the assumptions: time-series data
# ============================================================================

CF_data <- read.csv(paste0(url, "CF_data.csv"))
dim(CF_data)
model_CF <- lm(Firm_Value_TobinsQ ~ ROA + Leverage_Ratio + Debt_Equity_Ratio + Interest_Coverage +
                 Capital_Intensity + Current_Ratio + Policy_Interest_Rate + Sales_Growth, data = CF_data)
round(vif(model_CF), 2)

model_CF2 <- lm(Firm_Value_TobinsQ ~ ROA + Interest_Coverage + Capital_Intensity +
                  Current_Ratio + Policy_Interest_Rate + Sales_Growth, data = CF_data)
round(vif(model_CF2), 2)
summary(model_CF2)

# --- Error mean and heteroskedasticity ---

mean(resid(model_CF2))
bptest(model_CF2)

# --- Box-Cox: what transformation would help? ---

library(MASS)
bc <- boxcox(formula(model_CF2), data = CF_data, lambda = seq(-2, 3, 0.05))
bc$x[which.max(bc$y)]     # best lambda

# --- Autocorrelation: the Durbin–Watson test ---

durbinWatsonTest(model_CF2)

plot(resid(model_CF2), type = "b", pch = 19, cex = .6, col = rust,
     ylab = "Residual", xlab = "Quarter", main = "Residuals over time: runs of positives and negatives")
abline(h = 0, col = espresso, lty = 2)
