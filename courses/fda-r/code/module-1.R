# Financial Data Analytics using R — Module 1: Introduction to Financial Data Analytics and R-Studio
# https://xploreai.co.in/courses/fda-r/module-1/
# Every data file is read straight from the course site, so this script runs as-is.


# ============================================================================
# Session 1.1 — What financial data analytics is
# ============================================================================

# --- The four levels of analytics ---

# --- Levels of measurement ---

# --- Three shapes of data ---

# ============================================================================
# Session 1.2 — R, RStudio and your first commands
# ============================================================================

# license()      # what licence R is released under
# demo()         # list of built-in demonstrations
# help.start()   # opens the HTML manuals in your browser
# help(sum)      # help page for one function
# ?mean          # shortcut for the same thing

2 + 2
5 * 5
100 - 20
100 / 20

# ============================================================================
# Session 1.3 — The RStudio interface: scripts, console and objects
# ============================================================================

# --- Objects and assignment ---

x <- 100
Y <- 150
x + Y
200 + x

x + y

y <- 300
x + y
(x + y) * y    # anything after # is a comment and is ignored

# --- Text needs quotes ---

today <- "today we are learning the basics of RStudio"
now   <- 'it is a sunny day here'   # single quotes work too
today
now

# ============================================================================
# Session 1.4 — R programming basics: vectors, sequences and matrices
# ============================================================================

# --- Functions ---

sum(2, 3, 5)
sqrt(25)
rep(1, times = 3)

# --- Vectors: the basic unit of data in R ---

q <- c(1, 2, 5)
p <- c("India", "China", "USA", "Japan")
q
p

# --- Sequences ---

1:10
c(1, 100, 0.5)          # NOT a sequence, just three numbers
h <- seq(1, 100, 0.5)   # 1, 1.5, 2, ... 100
head(h, 12)
length(h)

# --- Picking elements with [ ] ---

h[1]
h[10]
p[3]

# --- Matrices ---

A <- matrix(0, nrow = 3, ncol = 4)
A
B <- matrix(1:12, nrow = 3, ncol = 4)
B
B[2, 3]      # row 2, column 3

# ============================================================================
# Session 1.5 — Importing your own data
# ============================================================================

url <- "https://xploreai.co.in/courses/fda-r/data/"
practice_data <- read.csv(paste0(url, "practice_data.csv"))
practice_data

# View(practice_data)          # opens a spreadsheet-style viewer in RStudio
# # reading from your own computer instead:
# practice_data <- read.csv("C:/Users/you/Desktop/practice_data.csv")

str(practice_data)               # structure: rows, columns, types
practice_data$Characteristics.1  # $ pulls out one column
practice_data[2, ]               # row 2, all columns
practice_data[, "Country"]       # all rows, one column

# ============================================================================
# Session 1.6 — Data cleaning I: inspecting a messy price file
# ============================================================================

# install.packages(c("dplyr", "tidyr", "stringr", "ggplot2"))   # once per computer

library(dplyr); library(tidyr); library(stringr); library(ggplot2)   # every session
df <- read.csv(paste0(url, "sample_financial_data.csv"))
head(df)

str(df)
summary(df)

# --- Missing values and duplicates ---

colSums(is.na(df))     # missing values per column
sum(duplicated(df))    # how many rows are exact copies
df[duplicated(df), ]   # which row

# --- Inconsistent text ---

unique(df$Company)
unique(df$Sector)

# ============================================================================
# Session 1.7 — Data cleaning II: fixing problems, returns and a first chart
# ============================================================================

# --- Standardise the text ---

df <- df %>%
  mutate(Company = str_to_title(Company),
         Sector  = str_to_title(Sector))
unique(df$Company)
unique(df$Sector)

# --- Remove duplicates, then fill gaps ---

df <- df %>%
  distinct() %>%
  mutate(Date = as.Date(Date, format = "%d-%m-%Y")) %>%
  arrange(Date) %>%
  fill(Closing_Price, Volume, .direction = "down")
nrow(df)
colSums(is.na(df))

# --- Find the outlier with the IQR rule ---

rust <- "#E2571B"; espresso <- "#4A4238"
boxplot(df$Closing_Price, horizontal = TRUE, col = "#FBE9DF", border = espresso,
        main = "ABC Limited closing price: one value is not like the others")

Q1 <- quantile(df$Closing_Price, 0.25)
Q3 <- quantile(df$Closing_Price, 0.75)
IQR_value <- Q3 - Q1
lower_bound <- Q1 - 1.5 * IQR_value
upper_bound <- Q3 + 1.5 * IQR_value
c(lower = lower_bound, upper = upper_bound)
df %>% filter(Closing_Price < lower_bound | Closing_Price > upper_bound)
df <- df %>% filter(Closing_Price >= lower_bound, Closing_Price <= upper_bound)
summary(df$Closing_Price)

# --- Calculate returns ---

df <- df %>%
  arrange(Date) %>%
  mutate(Simple_Return = Closing_Price / lag(Closing_Price) - 1,
         Log_Return    = log(Closing_Price / lag(Closing_Price)))
head(df[, c("Date", "Closing_Price", "Simple_Return", "Log_Return")])

# --- Summarise and plot ---

df %>% summarise(Mean_Price  = mean(Closing_Price),
                 SD_Price    = sd(Closing_Price),
                 Mean_Return = mean(Simple_Return, na.rm = TRUE),
                 SD_Return   = sd(Simple_Return, na.rm = TRUE),
                 Mean_Volume = mean(Volume))

ggplot(df, aes(Date, Closing_Price)) +
  geom_line(colour = rust, linewidth = 1) +
  geom_point(colour = rust, size = 1.8) +
  labs(title = "ABC Limited: clean closing price", x = NULL, y = "Price (Rs)") +
  theme_minimal(base_size = 12)
