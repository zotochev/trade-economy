# Practitioner macro frameworks linking the economy to asset prices (state of the art, 2025–2026)

Scope note: US focus. About 16 tool calls. Two primary PDFs (AQR stock-bond correlation 2022, Fidelity Business Cycle Approach) could not be text-extracted, so their figures come from search snippets or secondary summaries and are marked as such. "Foundational" items marked [F] are well-known academic references cited by their canonical URLs. They were not re-fetched in this session.

## 1. Growth × inflation regime / quadrant models (Bridgewater, Investment Clock, Man, Two Sigma, academic regime-switching)

### Takeaway
Quadrant models (growth up/down × inflation up/down) are the most common practitioner way to map macro to assets. The core logic has strong theoretical support: growth shocks push stocks and bonds in opposite directions, while inflation shocks push them in the same direction. The 2022 episode confirmed the theory and also broke portfolios built on it: All Weather lost about 22% and the stock-bond correlation turned positive. Published backtests (Investment Clock) are in-sample, vendor-produced and phase-dating-dependent.

### Cited Findings
- **Merrill Lynch Investment Clock** (Trevor Greetham, 2004, "The Investment Clock: Making Money from Macro"): backtested on more than 30 years of US data using the **OECD output gap (growth vs trend) and CPI (inflation direction)** — [Bitget Academy summary](https://www.bitget.com/academy/merrill-lynch-investment-clock); [Huobi Research study](https://medium.com/huobi-research/a-study-on-the-investment-clock-of-merrill-lynch-c8f6e6d59144)
- Four phases: **Reflation** (growth < trend, inflation falling) → bonds best; **Recovery** (growth > trend, inflation falling) → stocks best; **Overheat** (growth > trend, inflation rising) → commodities best; **Stagflation** (growth < trend, inflation rising) → cash best — [Huobi Research](https://medium.com/huobi-research/a-study-on-the-investment-clock-of-merrill-lynch-c8f6e6d59144)
- Original ML backtest figures (real, annualised): bonds in Reflation 9.8% vs long-run average 3.5%; stocks in Recovery 19.9% vs 6.1%; commodities in Overheat 19.7% vs 5.8% — [Huobi Research summary of ML 2004](https://medium.com/huobi-research/a-study-on-the-investment-clock-of-merrill-lynch-c8f6e6d59144) (secondary; these are in-sample, ex-post phase classifications)
- **Bridgewater All Weather / risk parity**: the fund lost about **−22% in 2022**, worse than its −20% in 2008 — [CAIA blog, "Is 2022 All Bad Weather For Risk Parity?"](https://caia.org/blog/2022/12/05/2022-all-bad-weather-risk-parity). Commodities were the only real inflation hedge, and a historic hiking cycle hit both bonds and stocks — [CAIA](https://caia.org/blog/2022/12/05/2022-all-bad-weather-risk-parity). Bridgewater had the highest inflation-hedge exposure among the risk-parity funds analysed, yet it underperformed a 60/40 — [Optimized Portfolio ALLW review](https://www.optimizedportfolio.com/allw/) (secondary)
- Interpretation: 2022 combined "rising inflation" and "falling growth" at once (stagflation-like with rising real rates). Levered bonds sized for a negative stock-bond correlation became a source of loss rather than a hedge — [Optimized Portfolio](https://www.optimizedportfolio.com/allw/); [Markov Processes blog](https://www.markovprocesses.com/blog/risk-parity-not-performing-blame-the-weather/)
- **Stock-bond correlation regime (AQR 2022)**: the key determinant of the correlation's sign is **inflation uncertainty relative to growth uncertainty**. Growth shocks move stocks up and bonds down. Inflation shocks move both down, with bonds usually falling more — [AQR Alternative Thinking 2Q22 (via IPE / AQR Quick Clips)](https://www.aqr.com/Insights/Quick-Takes/2Q22-QC?aqrPDF=1); [IPE Viewpoint](https://www.ipe.com/comment/viewpoint-where-now-for-the-stock/bond-correlation/10060488.article)
- For the roughly two decades before 2022 the correlation was consistently negative. Heightened inflation risk could keep it positive — [AQR PDF](https://savantwealth.com/wp-content/uploads/2022/08/AQR-Alternative-Thinking-The-Stock-Bond-Correlation-2Q-2022.pdf); [Verdad update](https://verdadcap.com/archive/an-update-on-the-stock-bond-correlation). AQR returned to the theme in September 2026 ("Inflation Redux?"), treating persistent inflation risk as live — [Advisor Analyst, Sep 2026](https://advisoranalyst.com/2026/09/16/inflation-redux-aqr-charts-a-course-through-persistent-price-risk.html/)
- **Man Group regime research** ("The Best Strategies for Inflationary Times", Neville, Draaisma, Funnell, Harvey, Van Hemert, 2021, Bernstein Fabozzi/Jacobs Levy award). Inflation regimes are defined as YoY CPI rising through 2%, then 5%, to a peak, giving **8 US episodes** since the 1920s. Over those episodes: **commodities** had the best real returns; **nominal bonds and equities** were weak; **trend-following** was positive in all 8 regimes with about +14% annualised real; **cross-sectional equity momentum** was the best equity factor at about +8% real — [Man Institute](https://man.com/maninstitute/best-strategies-for-inflationary-times); [Duke/Harvey PDF](https://people.duke.edu/~charvey/Research/Published_Papers/P154_The_best_strategies.pdf)
- Man also publishes "regime-based investing" work that classifies the current environment by similarity to historical periods — [Man, "The Road Ahead: Regime-Based Investing"](https://www.man.com/insights/road-ahead-regime-based-investing)
- **Two Sigma Factor Lens**: an 18-factor model. The 4 core macro factors are **Equity, Interest Rates, Credit, Commodities**. Credit and Commodities are residualised against Equity and Rates. The secondary macro factors are **Emerging Markets, Foreign Currency, Local Inflation** (inflation-linked vs nominal bonds) — [Two Sigma Venn FAQ](https://help.venn.twosigma.com/en/articles/1392786-two-sigma-factor-lens-faq); [Revisiting the Two Sigma Factor Lens PDF](https://www.venn.twosigma.com/hubfs/Revisiting%20the%20Two%20Sigma%20Factor%20Lens.pdf)
- Academic research also uses machine-learning regime classification for allocation (explainable ML on regimes) — [WUSTL paper](https://www.cse.wustl.edu/~yixin.chen/public/Allocation.pdf)
- [F] **Hamilton (1989)** Markov-switching model of GNP (Econometrica): the canonical latent-regime model, with expansions and recessions as hidden states — [JSTOR](https://www.jstor.org/stable/1912559). [F] **Ang & Bekaert (2002)** "International Asset Allocation with Regime Shifts" (RFS): bear regimes have higher correlations and volatility, but regime-switching allocation still beats static allocation — [RFS](https://academic.oup.com/rfs/article/15/4/1137/1568620)

### Inferences
- The robust part of quadrant models is the sign pattern: growth matters for equities and inflation surprises hurt nominal bonds. The fragile part is phase dating in real time (output gap and trend estimates get revised) and the large magnitudes in backtests.
- 2022 shows that "balanced across regimes" depends on the correlation assumption. A dashboard should show a **rolling 36-month stock-bond correlation** next to inflation level and volatility.
- The Hamilton/Ang-Bekaert approach (latent regimes estimated from data) gives an honest, probabilistic alternative to hard-coded quadrants. In Python it is available as `statsmodels.tsa.regime_switching.MarkovRegression`.

### Implementation on free data
- Growth axis: INDPRO YoY, CFNAI (FRED: CFNAI or CFNAIMA3), real GDP vs CBO potential (GDPC1, GDPPOT), or the unemployment gap (UNRATE − NROU). Inflation axis: CPIAUCSL or PCEPILFE YoY and its 3- or 6-month change (direction).
- Quadrant = sign(Δ growth) × sign(Δ inflation). Compute average forward 1-, 3- and 12-month returns of SPY, IEF/TLT, GLD/DBC and BIL from Yahoo per quadrant, and show counts so users see the small samples.
- Rolling stock-bond correlation: monthly ^GSPC vs a 10Y bond return proxy (from DGS10 duration approximation or VUSTX/IEF), 36-month window. Overlay CPI YoY.
- Markov switching: 2-state model on monthly S&P returns or INDPRO growth, showing smoothed recession-state probabilities vs USREC shading.

### Gaps
- No independent out-of-sample test of the Investment Clock in the US after 2004 was found. Only Chinese-market and vendor studies came up.
- The AQR 2022 PDF could not be text-extracted, so exact correlation figures by decade are not captured. The CAIA blog also reported a 12–17% "max drawdown" figure that conflicts with the −22% calendar-year loss. Treat −22% as the headline number and note that the definition differs.
- Bridgewater's own "Economic Machine" (productivity + short- and long-term debt cycles) is a conceptual framework with no published quantitative test. It was not fetched in this session.

## 2. Liquidity frameworks (Fed net liquidity, Howell global liquidity, M2)

### Takeaway
"Net liquidity" (WALCL − TGA − RRP) is a 2021-born practitioner heuristic. It tracked the S&P 500 well in the QE/QT era, but it is a level-on-level correlation of two trending series with a short history. No peer-reviewed predictive evidence was found. Howell's global liquidity cycle (about 65 months) is proprietary and narrative-heavy.

### Cited Findings
- Definition: Fed total assets − Treasury General Account − ON RRP balances, as an approximation of cash available to risk markets. It became popular in 2021–22 when S&P moves seemed to track it better than the headline balance sheet — [Market Ontology](https://marketontology.com/indicators/net-liquidity); [Eco3min](https://eco3min.fr/en/qa/net-liquidity-computation/)
- Claimed lead of roughly 2–6 weeks over the S&P 500 in the post-2020 regime — [Market Ontology](https://marketontology.com/indicators/net-liquidity) (practitioner claim, not peer-reviewed)
- Critique: the composition of the change matters. A $500bn drop from RRP exhaustion differs from one caused by a TGA rebuild, and "the correlation is real but limited in predictive power" — [Market Ontology](https://marketontology.com/indicators/net-liquidity); a "Liquidity Illusion" dataset framing appears at [Eco3min](https://eco3min.fr/en/net-liquidity-index-dataset/)
- Current level: about $5.77–5.79tn (Sep–Oct 2026), with the TGA rebuilt to about $945bn — [GuruFocus](https://www.gurufocus.com/economic_indicators/6168/fed-net-liquidity); [Au79 Macro, 5 Oct 2026](https://martyau79.substack.com/p/05oct2026-traditional-markets-and). With RRP near zero, the measure now moves mostly on WALCL and TGA.
- **Michael Howell / CrossBorder Capital ("Capital Wars", 2020)**: defines global liquidity as the balance-sheet capacity of the financial sector, distinct from money in the real economy. He reports a roughly **65-month (about 5.4-year) cycle** — [MarketZeitgeist](https://research.marketzeitgeist.com/p/global-liquidity-the-five-year-cycle); [Pixys profile](https://pixys.info/experts/michael-howell)
- Howell's 2025–26 call: global liquidity (advanced economies ex-China) likely peaked around Q4 2025, with a daily nowcast peaking around August 2025, as "Fed QE" gave way to "Treasury QE". He expects lower stocks by end-2026 and late-cycle leadership in financials and commodities — [Adam Taggart / Thoughtful Money](https://adamtaggart.substack.com/p/alert-the-liquidity-cycle-just-peaked); [Capital Wars Substack](https://capitalwars.substack.com/p/the-liquidity-tide-goes-out) (forecast, not evidence)

### Inferences
- Educational value is high (plumbing: QE/QT, TGA, RRP). Predictive value is unproven, so it should be labelled as a "narrative indicator". Show both the levels chart and a changes-vs-forward-returns scatter: the levels chart looks impressive, while the changes chart usually shows weak links.
- M2 (FRED M2SL) YoY famously spiked in 2020–21 and turned negative in 2023 without a recession. That makes it a useful case study in monetarist signals failing as timing tools. This is an inference, and no specific source was fetched.

### Implementation on free data
- FRED: WALCL (weekly), WTREGEN (TGA, weekly), RRPONTSYD (daily ON RRP). Net liquidity = WALCL − WTREGEN − RRPONTSYD (align units: WALCL and WTREGEN are in $mn, RRPONTSYD in $bn). Compare with ^GSPC from Yahoo, and compute correlations of 4-week changes vs forward 4-week returns.
- M2SL YoY and real M2 (M2SL / CPIAUCSL).

### Gaps
- No academic paper or Fed note was found that tests net liquidity's out-of-sample predictive power for equities. The absence of evidence is itself a finding.
- CrossBorder's index methodology is proprietary and its track record has not been independently verified.

## 3. Credit cycle frameworks (SLOOS, HY spreads, EBP, BIS credit gap, Minsky, private credit)

### Takeaway
Credit indicators have the best-documented recession-forecasting evidence of any macro-financial signal. The Gilchrist-Zakrajšek Excess Bond Premium (EBP), combined with the term spread, performs well out of sample in Fed research. A new blind spot is private credit (about $1.5–2tn), where defaults and PIK are rising and visibility is low.

### Cited Findings
- **EBP**: the component of corporate bond spreads in excess of expected default compensation, a measure of investor risk appetite. It is positively related to near-term recession probability — [FEDS Note, Favara, Gilchrist, Lewis, Zakrajšek, "Recession Risk and the EBP", Apr 2016](https://ideas.repec.org/p/fip/fedgfn/2016-04-08.html); [Updated Oct 2016 note, with monthly updates since](https://www.federalreserve.gov/econres/notes/feds-notes/updating-the-recession-risk-and-the-excess-bond-premium-20161006.html)
- Out of sample: bivariate probits using a term spread plus EBP "perform well on out-of-sample tests across estimation and evaluation subsamples" — [FEDS Note, "Out-of-Sample Performance of Recession Probability Models", Dec 2019](https://www.federalreserve.gov/econres/notes/feds-notes/out-of-sample-performance-of-recession-probability-models-20191213.html)
- Financial factors (credit spreads, EBP) as drivers of fluctuations: [NBER Reporter 2018, Gilchrist & Zakrajšek](https://www.nber.org/reporter/2018number4/role-financial-factors-economic-fluctuations). Yield-curve recession model: [FEDS Note 2018](https://www.federalreserve.gov/econres/notes/feds-notes/predicting-recession-probabilities-using-the-slope-of-the-yield-curve-20180301.html)
- **Private credit (2025–26)**:
  - Size is about $1.5–2tn. Borrowers have lower quality and higher leverage than in public markets — [FSB Report on Vulnerabilities in Private Credit, 6 May 2026](https://www.fsb.org/uploads/P060526.pdf); [FSB press release](https://www.fsb.org/2026/05/fsb-warns-on-private-credit-vulnerabilities/)
  - Default rates depend on the definition: outright defaults are about 1%, and about 5% including selective defaults and distressed exchanges per the FSB; Fitch reported a "record" of about 6% — [Credit Benchmark 2026 update](https://www.creditbenchmark.com/knowledge-base/private-credit-funds-2026-update/) (secondary)
  - PIK is about 12% of the market, roughly double 2022. Leverage is about 5–6x debt/EBITDA vs about 4x for leveraged loans — [Credit Benchmark](https://www.creditbenchmark.com/knowledge-base/private-credit-funds-2026-update/)
  - A BDC stress test (BDCs are about 40% of middle-market direct lending) finds no BDC debt defaults under a severely adverse scenario, but about a 10% cut in credit provision — [Credit Benchmark summary](https://www.creditbenchmark.com/knowledge-base/private-credit-funds-2026-update/). OFR on counterparty exposures: [OFR Brief 26-02](https://www.financialresearch.gov/briefs/files/OFRBrief-26-02-measuring-counterparty-exposures-private-credit.pdf)

### Inferences
- A good hierarchy for a dashboard: SLOOS (lending standards, a 2–4 quarter lead), then HY OAS / EBP (market pricing), then defaults and earnings. The EBP's advantage over a raw HY spread is that it strips expected default, leaving "price of risk".
- Private credit migrates credit-cycle risk away from observable public spreads, so HY OAS may understate tightening. This is an inference from the FSB's opacity point.

### Implementation on free data
- FRED: DRTSCILM (SLOOS, net % of banks tightening C&I standards for large/middle firms, quarterly); BAMLH0A0HYM2 (ICE BofA HY OAS, daily, note the licensing limit of a 3-year history on FRED since 2023 — verify); BAA10Y; T10Y3M; NFCI (Chicago Fed financial conditions).
- EBP: the Fed posts a CSV (`ebp_csv.csv`) with the monthly gz_spread, EBP and recession probability. Fetch from federalreserve.gov (verify URL).
- BIS credit-to-GDP gap: free BIS data portal (series for US private non-financial credit gap). Alternatively compute it on FRED (CRDQUSAPABIS / GDP) with a one-sided HP filter, λ = 400,000.

### Gaps
- The BIS credit-to-GDP gap (Drehmann & Juselius) and Minsky were not researched in this session, so no citations were collected. The report writer should treat them as background only.
- Whether HY OAS history remains fully available on FRED in 2026 is unverified.

## 4. Valuation-based long-horizon models (CAPE, ERP, GMO, AQR, Hussman)

### Takeaway
Valuation explains a meaningful share of 10-year returns, but the fit is regime-dependent: R² is about 0.78 for 1983–2013 and only about 0.11 on the full 1881+ history per Invesco. Since about 1985, out-of-sample CAPE forecasts have been beaten by the historical mean. Valuation-based shops (GMO) were directionally wrong on US large caps through the 2010s, mainly because margins did not mean-revert. Damodaran's implied ERP of 4.23% (Jan 2026) shows that valuations look rich on multiples but not extreme in ERP terms.

### Cited Findings
- **Invesco (Mar 2025)**: CAPE vs 10-year forward returns R² = 0.78 (1983–2013), 0.78 (1953–1983), 0.42 (1953–2013), **0.11 (1881–present)**. One-year forward returns are "practically random". Average CAPE level shifted from 15.6x (1953–83) to 24.2x (1983–2023). At end-2023 (Shiller CAPE about 31–36x) the model implies about 3.5% real price return over 10 years, or about 5.3% total — [Invesco Applied Philosophy](https://www.invesco.com/apac/en/institutional/insights/market-outlook/applied-philosophy-the-shiller-PE-and-SP-500-returns.html); [PDF](https://www.invesco.com/content/dam/invesco/apac/en/pdf/insights/2025/march/invesco-applied-philosophy-the-shiller-PE-and-SP-500-returns-revisited-mar-2025.pdf)
- Vanguard reported R² of 0.43 for 1926–2011 — [Morningstar](https://www.morningstar.com/financial-advisors/better-way-predict-long-term-stock-returns) (secondary)
- Out of sample: since about 1985, 10-year CAPE forecast errors have exceeded those of the trailing historical mean. A "component CAPE" variant has an OOS R² of 57.5% vs 46.7% for aggregate CAPE (1974–2015 rolling) — [Morningstar](https://www.morningstar.com/financial-advisors/better-way-predict-long-term-stock-returns). Shiller/BCA white paper: [Forecasting Equity Returns Using the CAPE Ratio](https://s3.amazonaws.com/bca2.0/ATH20201-Shiller-Forecasting-Equity-Returns-Whitepaper.pdf). Fair-value CAPE adjusting for rates and inflation: [Faber-hosted paper](https://mebfaber.com/wp-content/uploads/2020/02/Improving-U.S.-Stock-Return-Forecasts.pdf)
- Critiques: accounting changes (FAS 142 write-downs, buybacks vs dividends) and the GFC earnings hole distort the 10-year average — [Evidence Investor](https://www.evidenceinvestor.com/post/the-shiller-cape-10-how-to-use-it-not-abuse-it)
- **Damodaran implied ERP**: 4.23% at start of January 2026 (trailing-12-month cash yield basis). This is an IRR-style ERP backed out of prices and expected cash flows. Stocks were rich on PE and dividend yield, but the implied ERP was in line with the realised US premium over 65 years — [Damodaran, Data Update 2 for 2026](https://aswathdamodaran.blogspot.com/2026/01/data-update-2-for-2026-equities-get.html); [historical implied ERP table](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histimpl.html); [ERP monologue, Mar 2026](https://aswathdamodaran.blogspot.com/2026/03/the-price-of-risk-equity-risk-premium.html)
- **GMO 7-year forecasts**:
  - Latest forecasts (late 2025): US large cap about −5.4% real and US small cap about −3.6% real per year; Japan small value is top at about 7.7% real — [Advisor Perspectives, GMO 4Q 2025](https://www.advisorperspectives.com/commentaries/2026/01/21/gmo-7-year-forcast-4q-2025?firm=gmo); [RankiaPro](https://rankiapro.com/en/insights/gmos-forecast-deep-value-small-caps-lead-low-return-world/); [GMO Oct 2025 PDF](https://www.gmo.com/globalassets/articles/gmo-7-year-asset-class-forecast/2025/gmo-7-year-asset-class-forecastoct25.pdf)
  - Track record: a Duke study found forecast-realised correlation of 0.78 for all assets, 0.94 for equities and 0.82 for bonds, but GMO was usually too optimistic in that sample — [Duke paper](https://public.econ.duke.edu/Papers/PDF/GMO_Predictions1.pdf)
  - Failures: the end-2010 forecast for US large cap was 0.4% real vs about 10% realised over 7 years; EM was forecast at 4.1% vs about −2.5% realised. The cause is a built-in mean reversion of US profit margins that did not happen — [White Coat Investor](https://www.whitecoatinvestor.com/gmo-real-return-forecasts/). Rank ordering for 1998–2008 was very accurate — [same](https://www.whitecoatinvestor.com/gmo-real-return-forecasts/)
- GMO's 2025–26 view on AI valuations: [GMO, "Valuing AI: Extreme Bubble, New Golden Era, or Both"](https://www.gmo.com/americas/research-library/valuing-ai-extreme-bubble-new-golden-era-or-both_viewpoints/)

### Inferences
- Valuation models are better seen as "expected return given no regime change in margins and multiples" than as forecasts. Their weakness is structural shifts: margins, the rate regime, and index composition (tech).
- The dashboard should show a CAPE scatter with **two fits** (full sample vs post-1983), which teaches non-stationarity directly. It should also show the excess CAPE yield (1/CAPE − real 10Y), as in Shiller's ECY.

### Implementation on free data
- Shiller's online data (ie_data.xls): monthly S&P price, dividends, earnings, CPI, GS10, CAPE, and Excess CAPE Yield. Compute realised 10-year forward real total return and regress on log(1/CAPE).
- Fed-model ERP proxy: forward earnings yield is not free, so use the trailing earnings yield (Shiller E/P) minus the 10Y TIPS yield (FRED DFII10) or minus 10Y nominal (DGS10).
- Damodaran's histimpl.xls (free annual implied ERP since 1960) can be downloaded and plotted directly.

### Gaps
- AQR's annual Capital Market Assumptions (2025/2026 numbers) and Hussman's MarketCap/GVA measure were not fetched, so they are not covered with citations.
- The Fed's own ERP measures (e.g., the FEDS note on ERP term structure) were not retrieved.

## 5. Factor / cross-asset models, trend-following, sector rotation

### Takeaway
Practitioners decompose portfolios into a few macro factors: equity, rates, credit, commodities, inflation and FX (Two Sigma). Trend-following is the best-documented "regime-agnostic" diversifier, and it was especially strong in inflation episodes (Man) and in 2022. Fidelity's 4-phase business-cycle sector map is the dominant sector-rotation template, but it relies on ex-post phase dating.

### Cited Findings
- Two Sigma Factor Lens structure: see Section 1 — [Two Sigma Venn FAQ](https://help.venn.twosigma.com/en/articles/1392786-two-sigma-factor-lens-faq)
- Trend-following had positive real returns in all 8 US inflation regimes, at about +14% annualised real — [Man Institute](https://man.com/maninstitute/best-strategies-for-inflationary-times). Man also covers trend in inflationary environments — [Man](https://www.man.com/insights/trend-following-in-inflationary-environments?language=en-gb); [Gaining Momentum](https://www.man.com/insights/gaining-momentum-trend)
- [F] Century-long evidence for time-series momentum across asset classes: Hurst, Ooi, Pedersen, "A Century of Evidence on Trend-Following Investing" (AQR) — [AQR](https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing)
- **Fidelity Business Cycle Approach** has four phases: **Early** (sharp recovery, easing credit, low inventories, margin expansion); **Mid** (the longest phase, moderate growth, strong credit growth); **Late** (overheating, restrictive policy, tightening credit, margin squeeze, inventory build); **Recession** — [Fidelity Leadership Series PDF](https://www.fidelity.com/webcontent/ap101883-markets_sectors-content/18.01.0/business_cycle/Business_Cycle_Sector_Approach.pdf); [Fidelity sector rotation page](https://www.fidelity.com/learning-center/trading-investing/markets-sectors/intro-sector-rotation-strats)
- Fidelity's sector pattern: economically sensitive sectors are strongest in the early phase; technology has outperformed in early and mid; staples and utilities in late and recession; defensives (health care, utilities, communication services) in recession — [Fidelity PDF (2020 ed.)](https://www.fidelity.com/webcontent/ap101883-markets_sectors-content/21.01.0/business_cycle/Business_Cycle_Sector_Approach_2020.pdf); [Fidelity Institutional sector investing](https://institutional.fidelity.com/advisors/insights/spotlights/sector-investing)

### Inferences
- Trend is a natural "control" in a dashboard: a rule like price > 10-month SMA on SPY/TLT/GLD needs no macro forecast. Comparing it with quadrant allocation shows whether macro classification adds value.
- Sector rotation works descriptively, but real-time phase identification is the binding constraint.

### Implementation on free data
- Yahoo sector ETFs (XLK, XLF, XLE, XLY, XLP, XLU, XLV, XLI, XLB, XLRE, XLC; history mostly from Dec 1998). Phase proxy: OECD CLI for US (FRED: USALOLITONOSTSAM, check whether discontinued) level vs 100 and direction, giving early/mid/late/recession. Alternatively use ISM, which is not free on FRED, so substitute CFNAI or INDPRO. Compute relative returns vs SPY by phase.
- Factor lens lite: regress a portfolio on SPY, IEF, HYG−IEF (credit), DBC and TIP−IEF (inflation) returns.
- Trend: 10-month SMA or 12-month TSMOM on SPY, TLT, GLD, DBC and UUP.

### Gaps
- Fidelity's quantitative tables (hit rates and average relative performance by phase, data since 1962) could not be extracted from the PDFs. Numbers are missing.
- AQR macro-factor research (e.g., "macro momentum") and trend performance figures for 2022–2026 were not fetched.

## 6. Central-bank reaction function frameworks (Taylor rules, market-implied path)

### Takeaway
The Fed itself publishes a family of simple rules in each Monetary Policy Report. In February 2025, most rules prescribed rates close to the actual 4.25–4.50%, while the first-difference rule prescribed somewhat higher. The main weakness is uncertainty about r* and u*.

### Cited Findings
- Formulas from the Fed MPR, Feb 2025 — [Federal Reserve MPR Part 2](https://www.federalreserve.gov/monetarypolicy/2025-02-mpr-part2.htm):
  - Taylor (1993): R = r_LR + π + 0.5(π − π*) + (u_LR − u)
  - Balanced approach: R = r_LR + π + 0.5(π − π*) + 2(u_LR − u)
  - Balanced approach (shortfalls): R = r_LR + π + 0.5(π − π*) + 2·min{(u_LR − u), 0}
  - Adjusted Taylor (1993): R = max{R_T93 − Z, ELB}, where Z is the cumulative past shortfall at the lower bound
  - First difference: R = R_{t−1} + 0.5(π − π*) + (u_LR − u) − (u_LR,t−4 − u_{t−4})
- In 2024–25 most rules prescribed within the actual 4.25–4.50% range, except the first-difference rule (higher). Caveats: simple rules omit many factors, and r* and u_LR are hard to measure and time-varying — [Fed MPR Feb 2025](https://www.federalreserve.gov/monetarypolicy/2025-02-mpr-part2.htm)
- The Fed's 2025 framework review produced a revised Statement on Longer-Run Goals (2025) — [Fed](https://www.federalreserve.gov/monetarypolicy/monetary-policy-strategy-tools-and-communications-statement-on-longer-run-goals-monetary-policy-strategy-2025.htm); [FEDS Note roadmap, Aug 2025](https://www.federalreserve.gov/econres/notes/feds-notes/a-roadmap-for-the-federal-reserves-2025-review-of-Its-monetary-policy-framework-20250822.html)
- Academic extensions: "Beyond the Taylor Rule" (Nakamura & Riblier, KC Fed Jackson Hole) — [KC Fed PDF](https://www.kansascityfed.org/documents/11203/Taylor_Rule.pdf). "Targeted Taylor Rules" (Hofmann & Manea, AEA 2026) — [AEA](https://www.aeaweb.org/conference/2026/program/paper/iyr8fKa7)

### Inferences
- The rule gap (actual fed funds minus rule) is an intuitive "policy stance" gauge for a dashboard. The 2021 gap (rules far above actual) is the key teaching episode.
- Market-implied path: fed funds futures are not on FRED. Use 2Y Treasury minus fed funds (DGS2 − DFF) as a free proxy for expected near-term moves. Higher-frequency term premia: ACM (NY Fed, free download) or Kim-Wright (FRED THREEFYTP10).

### Implementation on free data
- FRED: FEDFUNDS/DFF, PCEPILFE (core PCE YoY), UNRATE, NROU (CBO natural rate), r* from the NY Fed Laubach-Williams/HLW (free CSV), or a fixed 0.5–1%. Compute all five rules and plot them vs actual.
- Market path proxy: DGS2 − DFF; DGS1MO/DGS3MO/DGS6MO/DGS1 curve.

### Gaps
- No free source for the CME FedWatch-style probability series was identified. Futures data on Yahoo (ZQ=F) is partial and unverified.

## 7. Hierarchical (causal-chain) structure: macro drivers → policy → financial conditions → earnings/discount rates → asset prices

### Takeaway
Most practitioner frameworks are implicitly hierarchical. Real-economy drivers (growth, inflation, productivity and debt) feed the central-bank reaction function. Policy feeds financial conditions (rates, spreads, liquidity, the dollar). These feed both cash flows (earnings) and discount rates (risk-free rate + ERP/credit premium), which together set prices. The frameworks differ in which layer they emphasise.

### Cited Findings
- Stock-bond co-movement is explained as the relative dominance of growth vs inflation shocks (cash-flow vs discount-rate channel) — [AQR via IPE](https://www.ipe.com/comment/viewpoint-where-now-for-the-stock/bond-correlation/10060488.article)
- Fidelity's cycle phases are explicitly described by the chain of credit conditions, monetary policy, profit margins and inventories — [Fidelity PDF](https://www.fidelity.com/webcontent/ap101883-markets_sectors-content/18.01.0/business_cycle/Business_Cycle_Sector_Approach.pdf)
- The Fed's financial-factor literature positions credit-market risk appetite (EBP) as a transmission channel from finance to real activity — [NBER Reporter](https://www.nber.org/reporter/2018number4/role-financial-factors-economic-fluctuations)
- Damodaran's implied ERP isolates the discount-rate layer: price = PV(expected cash flows) at risk-free + ERP — [Damodaran](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histimpl.html)
- Howell places liquidity (financial-sector balance-sheet capacity) above the real economy as a driver of asset prices, which inverts the usual hierarchy — [MarketZeitgeist](https://research.marketzeitgeist.com/p/global-liquidity-the-five-year-cycle)

### Inferences (layer → frameworks → free series)
1. **Macro drivers**: quadrants, Investment Clock, Dalio's machine. INDPRO, PAYEMS, UNRATE, CPI/PCE, GDPC1 vs GDPPOT, CFNAI.
2. **Policy reaction**: Taylor-rule family. DFF vs rule prescriptions; DGS2 − DFF as the market-implied path.
3. **Financial conditions / liquidity / credit**: net liquidity, NFCI, SLOOS, HY OAS, EBP, T10Y3M, DTWEXBGS (dollar).
4. **Fundamentals**: earnings (Shiller E, or corporate profits CP on FRED) and discount rates (DGS10, DFII10, ERP).
5. **Asset prices / allocation**: CAPE→10-year returns, sector rotation, trend, factor exposures (Yahoo prices).
- Frameworks by layer emphasis:
  - Bridgewater and the Investment Clock emphasise layers 1→5 directly, skipping explicit modelling of the middle layers.
  - Liquidity frameworks (Howell, net liquidity) emphasise layer 3.
  - Credit-cycle frameworks emphasise 3→1 (feedback).
  - Valuation models emphasise 4→5 and ignore timing.
  - Trend-following is layer-agnostic and reads layer 5 only.
- A hierarchical dashboard should make feedback loops explicit (credit → growth, asset prices → wealth effects → growth). Strict top-down chains miss these, and Minsky-type dynamics are precisely such feedbacks.

### Gaps
- No single published practitioner document formalising this 5-layer chain was retrieved. The structure above is a synthesis.
- Dynamic factor models (e.g., NY Fed Staff Nowcast, Atlanta Fed GDPNow) were not researched as layer-1 tools.
