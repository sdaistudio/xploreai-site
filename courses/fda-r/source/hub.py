"""Course hub page: courses/fda-r/index.html"""
import html, os

DATASETS = [
    ("NIFTY50.csv", "NIFTY 50 index, daily OHLC + volume, 2015–2025", "Yahoo Finance (^NSEI)", "5, 6"),
    ("SP500.csv", "S&P 500 index, daily, 2015–2025", "Yahoo Finance (^GSPC)", "6"),
    ("bitcoin.csv", "Bitcoin spot vs CME futures: prices and log returns, Dec 2017–2025", "Yahoo Finance (BTC-USD, BTC=F)", "2, 4"),
    ("portfolio_returns.csv", "Equal-weight portfolio of Reliance, TCS, HDFC Bank, Infosys and ICICI Bank, 2023–2025", "Built from Yahoo Finance prices", "5"),
    ("AirPassengers.csv", "Monthly airline passengers, 1949–1960", "R's built-in dataset", "2, 4"),
    ("sample_financial_data.csv", "31 days of 'ABC Limited' prices with planted errors", "Synthetic, for cleaning practice", "1"),
    ("practice_data.csv", "Five-row starter file", "Synthetic", "1"),
    ("salary.csv", "24 employees: salary, rating, experience, certifications", "Synthetic", "3"),
    ("CF_data.csv", "80 quarters of a firm's financial ratios and Tobin's Q", "Synthetic", "3"),
    ("SENSEX.csv", "BSE Sensex, daily, 2015–2025", "Yahoo Finance (^BSESN)", "Extra"),
    ("RELIANCE.csv", "Reliance Industries, daily, 2015–2025", "Yahoo Finance (RELIANCE.NS)", "Extra"),
    ("USDINR.csv", "US dollar / Indian rupee, daily, 2015–2025", "Yahoo Finance (INR=X)", "Extra"),
]
OTHER = ["TCS", "INFY", "HDFCBANK", "ICICIBANK", "GOLD", "CRUDE", "INDIAVIX"]

SETUP = """install.packages(c("dplyr", "tidyr", "stringr", "ggplot2", "psych", "urca", "tseries",
                   "car", "lmtest", "forecast", "vars", "dLagM", "xts", "quantmod",
                   "rugarch", "FinTS", "TTR", "caret", "rpart", "randomForest",
                   "e1071", "neuralnet"))"""


def render_hub(mods, ncells, nplots, head, foot, inline, slug, site):
    nsess = sum(len(ss) for _, ss in mods)
    cards = []
    for meta, ss in mods:
        m = int(meta["module"])
        li = "".join(f'<li><a href="module-{m}/#{slug(x["num"])}"><span>{x["num"]}</span>{html.escape(x["title"])}</a></li>' for x in ss)
        cards.append(
            f'<article class="mod"><div class="no">{m:02d}<small>MODULE</small></div><div>'
            f'<h3><a href="module-{m}/">{html.escape(meta["title"])}</a></h3><p>{inline(meta.get("lede", ""))}</p>'
            f'<ol>{li}</ol><a class="btn" href="module-{m}/">Start module {m} →</a></div></article>')
    rows = "".join(f'<tr><td><a href="data/{f}" download><code>{f}</code></a></td><td>{d}</td><td>{s}</td><td>{u}</td></tr>'
                   for f, d, s, u in DATASETS)
    others = ", ".join(f'<a href="data/{x}.csv" download>{x}.csv</a>' for x in OTHER)
    page = head("Financial Data Analytics using R — a hands-on course",
                "Learn financial data analytics in R: cleaning, returns, statistics, regression, ARIMA, VAR, VECM, ARDL, "
                "GARCH, VaR, event studies and machine learning, with runnable code and real output.",
                "https://xploreai.co.in/courses/fda-r/")
    page += f"""
<main class="fdar">
<header class="mhero wrap">
  <p class="crumb"><a href="/learn.html">Learn AI</a> / Courses</p>
  <span class="pill">COURSE · R · {len(mods)} MODULES · {nsess} SESSIONS</span>
  <h1>Financial Data Analytics using R<i>.</i></h1>
  <p class="lede">From your first line of R to GARCH volatility forecasts and machine-learning models on NIFTY. Every session shows the <strong>code</strong>, explains what it does, and shows the <strong>exact console output and charts</strong> it produces, so you can check your work as you follow along.</p>
  <div class="dl"><a class="btn" href="module-1/">Start with Module 1 →</a> <a class="btn ghost" href="#data">Download the data</a></div>
  <div class="facts">
    <div class="card"><b>{len(mods)}</b><span>modules</span></div>
    <div class="card"><b>{nsess}</b><span>sessions</span></div>
    <div class="card"><b>{ncells}</b><span>runnable code cells</span></div>
    <div class="card"><b>{nplots}</b><span>charts, rendered from the code</span></div>
  </div>
</header>

<section class="hub-sec wrap" id="setup">
  <span class="eyebrow">Before you start</span>
  <h2 class="big">Set up in ten minutes<i>.</i></h2>
  <p class="lede">Install <a href="https://cran.r-project.org/">R</a> first, then <a href="https://posit.co/download/rstudio-desktop/">RStudio Desktop</a>. Then paste this into the RStudio console once to install every package the course uses:</p>
  <div class="cell"><div class="code"><div class="lab"><span>R</span><button class="copy" type="button">Copy</button></div><pre><code class="language-r">{html.escape(SETUP)}</code></pre></div></div>
  <p>Every script reads its data straight from this site, so there are no file paths to fix. Each module page also has a <strong>Download the R script</strong> button with all of that module's code in one file.</p>
</section>

<section class="hub-sec wrap" id="modules">
  <span class="eyebrow">The course</span>
  <h2 class="big">Six modules, one toolkit<i>.</i></h2>
  <div class="hub-mods">{"".join(cards)}</div>
</section>

<section class="hub-sec wrap" id="data">
  <span class="eyebrow">Datasets</span>
  <h2 class="big">All the data, as plain CSV<i>.</i></h2>
  <p class="lede">Market data comes from Yahoo Finance (daily closes to 31 Dec 2025). The cleaning, salary and corporate-finance files are synthetic: they were built to show the same problems the lessons teach you to find.</p>
  <div class="tbl"><table><thead><tr><th>File</th><th>What's in it</th><th>Source</th><th>Module</th></tr></thead><tbody>{rows}</tbody></table></div>
  <p class="more">Also available in the same format: {others}.</p>
</section>
</main>
"""
    page += foot
    open(os.path.join(site, "index.html"), "w").write(page)
