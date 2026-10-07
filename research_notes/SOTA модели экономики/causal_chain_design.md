# Coherent causal "model of the economy" for monitoring and communication (institutional practice, 2024–2026)

Scope: how central banks / IMF / Fed structure macro→markets monitoring as a causal chain rather than a flat indicator list; for redesigning an educational US-economy Streamlit dashboard (current screens: 18-indicator panel, growth×inflation regimes, rates & bonds, liquidity & debt, valuation CAPE/ERP/Buffett/Gordon, sectors, single stock).

Research date: 2026-10-07. ~16 tool calls; several Fed/NY Fed pages could not be fetched (404 / dynamic content), noted under Gaps.

---

## 1. How central banks describe the monetary transmission mechanism (chain + lags)

### Takeaway
All major central banks present policy as a **chain of stages with feedback through expectations**: policy rate → market rates / asset prices / exchange rate / expectations → demand (domestic + external) → output gap / inflationary pressure → inflation, with "long, variable and uncertain" lags (BoE canonical: ~1 year to peak output effect, ~2 years to peak inflation effect). The 2022–2025 debate concluded lags are uncertain, with evidence both for *shorter* lags (forward guidance moves financial conditions before the policy rate moves) and *long* lags for prices (>3 years for full PCE response).

### Cited Findings
- BoE (MPC, 1999, still the canonical diagram): official rate affects market rates (mortgage, deposit rates), asset prices, expectations/confidence and the exchange rate; these drive domestic demand and net external demand → domestic inflationary pressure + import prices → inflation. "Official interest rate decisions have their fullest effect on output with a lag of around one year, and their fullest effect on inflation with a lag of around two years." — [BoE Quarterly Bulletin 1999 Q2, "The transmission mechanism of monetary policy"](https://www.bankofengland.co.uk/quarterly-bulletin/1999/q2/the-transmission-mechanism-of-monetary-policy); [PDF of MPC paper](https://www.bankofengland.co.uk/-/media/boe/files/quarterly-bulletin/1999/the-transmission-mechanism-of-monetary-policy)
- ECB transmission page: official rates "directly affect money-market interest rates and, indirectly, lending and deposit rates"; channels named: expectations channel ("longer-term interest rates depend in part on market expectations about the future course of short-term rates"; credible CB anchors inflation expectations), asset price channel (stock prices, exchange rate, wealth effects on consumption), credit supply channel, bank risk-taking channel; operates with "long, variable and uncertain time lags"; shocks outside CB control also affect prices. — [ECB, Transmission mechanism of monetary policy](https://www.ecb.europa.eu/mopo/intro/transmission/html/index.en.html)
- Friedman's "long and variable lags" = lag is long, and its length differs unpredictably across episodes. — [St. Louis Fed Regional Economist, May 2023](https://www.stlouisfed.org/publications/regional-economist/2023/may/examining-long-variable-lags-monetary-policy); [St. Louis Fed On the Economy, Oct 2023](https://www.stlouisfed.org/on-the-economy/2023/oct/what-are-long-variable-lags-monetary-policy)
- Powell (Jackson Hole 2023): assessment "further complicated by uncertainty about the duration of the lags with which monetary tightening affects ... especially inflation." — cited in [NBER WP 32623 "The Long and Variable Lags of Monetary Policy: Evidence from Disaggregated Price Indices"](https://www.nber.org/system/files/working_papers/w32623/w32623.pdf)
- That paper (2024; also J. Monetary Economics): after a monetary contraction, aggregate PCE price index response becomes significantly negative only **after more than three years**; long lags for both aggregate and individual categories → 2022–23 tightening may not have been fully reflected in data. — [NBER WP 32623](https://www.nber.org/system/files/working_papers/w32623/w32623.pdf); [ScienceDirect version](https://www.sciencedirect.com/science/article/pii/S0304393224000886)
- Counter-view (shorter lags): Doh & Foerster (KC Fed, 2022) using a proxy funds rate that includes forward guidance and balance sheet policy find a shorter lag since 2009 — peak inflation deceleration ~1 year after tightening (high uncertainty); forward guidance shaved roughly 6 months off the usual 12–24 month lag. — [KC Fed Economic Bulletin, "Have Lags in Monetary Policy Transmission Shortened?"](https://www.kansascityfed.org/research/economic-bulletin/have-lags-in-monetary-policy-transmission-shortened/)
- BIS speech "Big shocks travel fast – why policy lags may be shorter than you think" (July 2023). — [BIS](https://www.bis.org/speeches/20230718-big-shocks-travel-fast-why-policy-lags-may-be-shorter-you-think.pdf)
- SF Fed Economic Letter (Apr 2024) "How Quickly Do Prices Respond to Monetary Policy?" (contribution to the same debate; content not fetched). — [SF Fed](https://www.frbsf.org/research-and-insights/publications/economic-letter/2024/04/how-quickly-do-prices-respond-to-monetary-policy/)
- Policy stance ≠ policy rate: Atlanta Fed (Gospodinov, Aug 2026) builds a Monetary Policy Index = 2/3 policy rate (EFFR) + 1/3 balance-sheet component (inverse share of bank reserves in Fed liabilities); the balance-sheet liquidity measure tracks FCI-G tightening/easing better than EFFR; an MPI tightening shock flattens the curve (−1.62% peak) and tightens FCI-G (+1.34 sd). — [Atlanta Fed Policy Hub/macroblog, 2026-08-18](https://www.atlantafed.org/research-and-data/publications/policy-hub-macroblog/2026/08/18/monetary-policy-stance-and-financial-conditions)

### Inferences
- The dashboard's spine can literally be the BoE/ECB diagram: **Policy (rate + balance sheet) → Market rates & expectations (curve, term premium, breakevens) → Financial conditions (NFCI/FCI-G, spreads, equities, dollar, housing) → Demand (consumption, investment, fiscal impulse) → Output gap / labor market slack → Inflation**, with a "lag" annotation on each arrow (e.g., months to peak).
- Teach "lags are uncertain" explicitly: show both the classic 1y/2y rule and the 2022–25 debate (forward guidance shortens; prices may take 3+ years). Good educational device: a "where is the impulse now" marker along the chain.
- "Liquidity & debt" screen belongs as part of the *policy stance/financial conditions* layer (balance sheet, reserves), not as a separate silo.

### Gaps
- Fed Monetary Policy Report's own description of transmission was not fetched; Fed lacks a single official diagram equivalent to BoE's (not verified).
- Specific 2025–2026 Fed staff estimates of current lag lengths not found. A Waller speech (2026-07-06) on monetary policy appeared in search but was not read — [Fed](https://www.federalreserve.gov/newsevents/speech/waller20260706a.htm).

---

## 2. How institutions organize dashboards / heat maps

### Takeaway
Institutional monitoring frameworks are **structured by causal role, not by data source**: the Fed FSR separates unpredictable *shocks* from monitorable *vulnerabilities* (4 categories that amplify each other); labor dashboards separate *level* vs *momentum* (KC Fed LMCI) or compare *current vs past distributions* (Atlanta Fed spider chart); fiscal policy is reduced to a single *contribution to GDP growth* (Hutchins FIM); financial conditions are reduced to *headwind/tailwind to GDP in pp* (FCI-G).

### Cited Findings
- **Fed Financial Stability Report** (latest May 8, 2026): framework distinguishes shocks ("inherently difficult to predict") from vulnerabilities ("can be monitored as they build up or recede over time"). Four categories: (1) asset valuation pressures (prices high relative to fundamentals/historical norms, "often driven by an increased willingness of investors to take on risk"); (2) borrowing by businesses and households; (3) leverage in the financial sector; (4) funding risks (runnable short-term funding vs long-maturity assets → fire sales). Emphasis on "how those categories might interact to amplify stress". — [Fed FSR May 2026, Purpose and Framework](https://www.federalreserve.gov/publications/2026-may-financial-stability-report-purpose-and-framework.htm); [FSR index](https://www.federalreserve.gov/publications/financial-stability-report.htm)
- FSR May 2026 assessment: asset valuations remained elevated though risk premiums rose amid volatility; broad equity valuations elevated; corporate bond and loan spreads low by historical standards; hedge fund leverage at record highs and concentrated in largest funds. — [FSR May 2026: Asset Valuations](https://www.federalreserve.gov/publications/2026-may-financial-stability-report-asset-valuations.htm); [FSR May 2026: Leverage in the Financial Sector](https://www.federalreserve.gov/publications/2026-may-financial-stability-report-leverage.htm)
- **KC Fed LMCI**: two monthly indicators from 24 labor market variables — *level of activity* and *momentum*; positive = above long-run average. August reading (latest seen): level 0.31 (from 0.20), momentum 0.25 (from 0.39). FRED IDs: FRBKCLMCILA (level), FRBKCLMCIM (momentum); FRED release rid=341. — [KC Fed LMCI](https://www.kansascityfed.org/data-and-trends/lmci/latest-data-for-the-kc-fed-labor-market-conditions-indicators/); [ALFRED FRBKCLMCILA](https://alfred.stlouisfed.org/series?seid=FRBKCLMCILA); [ALFRED FRBKCLMCIM](https://alfred.stlouisfed.org/series?seid=FRBKCLMCIM); [FRED release 341](https://fred.stlouisfed.org/release?rid=341)
- **Atlanta Fed Labor Market Distributions Spider Chart**: monitors broad labor market developments by comparing current conditions to up to two user-selected earlier periods; includes JOLTS openings, hires, layoffs, quits; updated monthly (e.g., Feb 2026 with Dec JOLTS). — [Atlanta Fed, Labor Market Tracking Tools (2025-07)](https://www.atlantafed.org/chcs/feature/2025/07/01/labor-market-distributions-spider-chart-updated-w-jolts-data); [2026-02 update](https://www.atlantafed.org/research-and-data/data/features/chcs/2026/02/03/labor-market-distributions-spider-chart-updated-w-jolts-data)
- **Hutchins Center Fiscal Impact Measure**: translates federal + state/local taxes and spending into contribution to real GDP growth. Q2 2026: fiscal policy subtracted 0.2 pp; federal purchases −0.4 pp, state & local −0.1 pp, other factors (taxes incl. OBBBA tax cuts, transfers, tariffs, supply-side) +0.3 pp. — [Brookings FIM](https://www.brookings.edu/articles/hutchins-center-fiscal-impact-measure/); [Methodology](https://www.brookings.edu/articles/the-hutchins-centers-fiscal-impact-measure/)
- **Fed Board FCI-G (Financial Conditions Impulse on Growth)**: 7 financial variables (fed funds rate, 10y Treasury yield, 30y mortgage rate, BBB corporate yield, Dow Jones total market index, Zillow house prices, nominal broad dollar) weighted by their effect on GDP growth in FRB/US; incorporates past changes (lookback 1y/3y); units = pp of headwind (+) / tailwind (−) to GDP growth over the next year. By May 2026 FCI-G had eased to levels seen at the start of the hiking cycle (March 2022). — [Fed FEDS Note Sep 2024](https://www.federalreserve.gov/econres/notes/feds-notes/financial-conditions-and-risks-to-the-economic-outlook-20240920.html); [data.gov "A New Index to Measure U.S. Financial Conditions"](https://catalog.data.gov/dataset/a-new-index-to-measure-u-s-financial-conditions); recent level per [CEIC summary](https://www.ceicdata.com/en/united-states/financial-conditions-impulse-on-growth/financial-conditions-impulse-on-growth-fcig-index-baseline) (aggregator — treat as secondary)
- **Chicago Fed NFCI**: >100 indicators via dynamic factor model; mean 0, sd 1 since 1971; positive = tighter; weekly; below zero ~70% of the time due to stress outliers; Chicago Fed (2024) finds NFCI leads FCI-G by ~1–2 months and proposes a median-renormalized NFCI. — [Chicago Fed Insights 2024](https://www.chicagofed.org/publications/chicago-fed-insights/2024/nfci-future-economic-growth)
- SF Fed (Mar 2024) "Monetary Policy and Financial Conditions" — link between policy and FCIs (not fetched). — [SF Fed](https://www.frbsf.org/research-and-insights/publications/economic-letter/2024/03/monetary-policy-and-financial-conditions/)

### Inferences
- Design pattern to copy: **each layer gets one "summary gauge" in economically meaningful units** (FCI-G in pp of GDP, FIM in pp of GDP, LMCI level/momentum in sd) plus drill-down components. The 18-indicator panel could be regrouped under these gauges instead of a flat grid.
- Level vs momentum (KC Fed) maps neatly onto the existing growth×inflation regime screen (level = where, momentum = direction).
- The FSR four-category structure is a ready-made template for the "liquidity & debt" + "valuation" screens: valuations (CAPE/ERP/spreads) → household/business debt → financial-sector leverage → funding. Shocks shown separately as scenarios.

### Gaps
- Exact FRED IDs for NFCI subindexes not verified in this session; from prior knowledge: NFCI, ANFCI, NFCIRISK, NFCICREDIT, NFCILEVERAGE, NFCINONFINLEVERAGE (verify before coding).
- FCI-G is published by the Board as a downloadable file, not (as far as found) on FRED.
- Latest LMCI month for the "August" reading not explicitly confirmed (search snippet; likely Aug 2026 but unverified).

---

## 3. Asset pricing decomposition tying macro to markets

### Takeaway
The standard bridge is the present-value identity: price = Σ expected cash flows discounted at (real risk-free rate + inflation compensation + risk premium). Fed research operationalizes it with observables: stock moves = Δreal yield curve + Δequity premium + Δexpected dividends; long-run gains are dominated by cash flows, short-run swings by discount rates/risk premia (2022 = real rates; 2008/2020 = risk premium + earnings). Bond yields similarly = expected short rates + term premium (ACM / Kim-Wright), and breakevens = expected inflation + inflation risk premium (− liquidity premium).

### Cited Findings
- Knox & Vissing-Jorgensen, "A Stock Return Decomposition Using Observables" (FEDS 2022-014, revised Jan 2025): decomposes S&P 500 capital gains into contributions from real yield curve, equity premia, expected dividends using observable PV-formula inputs (no regressions/log-linearization). 2005–2023: expected dividends dominate cumulative gain; real yields and equity premia matter more for short-run fluctuations; 2008 and 2020 declines = higher ERP + lower earnings expectations; **2022 decline primarily driven by rising real rates**. — [Fed FEDS page](https://www.federalreserve.gov/econres/feds/a-stock-return-decomposition-using-observables.htm); [PDF](https://www.federalreserve.gov/econres/feds/files/2022014r1pap.pdf)
- Chicago Fed (Economic Perspectives 2023-5): in the Covid era shifts in risk-free discount rates and expected profits mattered, but most of the early drop and much of the recovery came from the risk-premium component. — [Chicago Fed](https://www.chicagofed.org/publications/economic-perspectives/2023/5)
- NY Fed Staff Report 714 "The Equity Risk Premium: A Review of Models" (Duarte & Rosa) — survey of ~20 ERP models. — [NY Fed SR714](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr714.pdf)
- Fed FEDS Note (Aug 2022) using dividend futures to infer whether stocks price recession risk. — [FEDS Note 2022-08-18](https://www.federalreserve.gov/econres/notes/feds-notes/are-stocks-pricing-in-recession-risks-evidence-from-dividend-futures-20220818.html)
- Bekaert & Engstrom on the "Fed model" (inflation and stock market; why E/P co-moves with nominal yields). — [SF Fed-hosted PDF](https://www.frbsf.org/wp-content/uploads/Bekaert-Engstrom.pdf)
- Term premium: **THREEFYTP10** on FRED = "Term Premium on a 10 Year Zero Coupon Bond" (Kim-Wright, Board); THREEFYTP5 for 5y. — [FRED THREEFYTP10](https://fred.stlouisfed.org/series/THREEFYTP10); [FRED THREEFYTP5](https://fred.stlouisfed.org/series/THREEFYTP5); [FRED term premium tag](https://fred.stlouisfed.org/tags/series?t=term+premium)
- ACM (Adrian-Crump-Moench) term premia: daily from 1961, downloadable from NY Fed Data & Indicators (ACMTermPremium.xls; series name "ACMTP10"); updated monthly. — [Liberty Street Economics, "Treasury Term Premia: 1961-Present"](https://libertystreeteconomics.newyorkfed.org/2014/05/treasury-term-premia-1961-present/); [NY Fed term premia page](https://www.newyorkfed.org/research/data_indicators/term-premia-tabs); a maintained mirror with monthly releases (e.g., 2026-10) exists at [GitHub fernando-duarte/ACM_term_premium](https://github.com/fernando-duarte/ACM_term_premium/releases/tag/acm-term-premium-2026-10). **Conflict:** a search-engine summary claimed ACMTP10 is a FRED series, but https://fred.stlouisfed.org/series/ACMTP10 returned 404 → treat ACM as **not on FRED**; fetch from NY Fed file.
- NY Fed Liberty Street (Aug 2026) "A Window into Bond Investors' Uncertainty About R-Star" and (Aug 2025) "Are Financial Markets Good Predictors of R-Star?" — link market rates to r-star (not fetched). — [LSE 2026/08](https://libertystreeteconomics.newyorkfed.org/2026/08/a-window-into-bond-investors-uncertainty-about-r-star/); [LSE 2025/08](https://libertystreeteconomics.newyorkfed.org/2025/08/are-financial-markets-good-predictors-of-r-star/)

### Inferences
- Valuation screen should be re-framed as a decomposition, not a list of ratios: **Price = EPS × P/E**; **EPS ← nominal GDP growth × margins** (macro layer); **P/E ← real rate (DFII10) + ERP** (rates layer). CAPE, Buffett, Gordon become alternative lenses on the same identity. Gordon: P = D/(r + ERP − g) directly shows the three levers.
- Rates screen: **10y nominal = expected path of short rates (r* + expected inflation + policy) + term premium**; 10y breakeven (T10YIE) = expected inflation + inflation risk premium − TIPS liquidity premium; 10y real (DFII10). (FRED IDs DGS10, DFII10, T10YIE are standard but not re-verified this session.)
- A "what moved the market this year" waterfall (real rates / ERP / earnings expectations) à la Knox–Vissing-Jorgensen would be a strong educational bridge from macro to the sectors/single-stock screens.

### Gaps
- No live 2026 ERP or ACM values gathered.
- Fed MPR/FSR's own ERP measure methodology not fetched.

---

## 4. Supply-side / long-run layer (trend vs cycle)

### Takeaway
Institutions separate **trend** (potential output = labor force × productivity; natural rate r*) from **cycle** (output gap, unemployment gap, policy rate minus r*). CBO projects potential; NY Fed HLW jointly estimates r*, trend growth and output gap — a ready-made "structural layer".

### Cited Findings
- CBO Budget and Economic Outlook 2026–2036 (Feb 2026): real potential GDP grows 2.1%/yr in 2026–2030 and 1.8%/yr in 2031–2036; slowdown because potential labor force productivity grows more slowly later. Real GDP projected +2.2% in 2026 (boosted by 2025 reconciliation act and rebound after late-2025 appropriations lapse), +1.8% in 2027; avg 1.8% 2027–2036. — [CBO publication 62105](https://www.cbo.gov/publication/62105) (figures via search summary of CBO and [CRFB](https://www.crfb.org/papers/cbos-february-2026-budget-and-economic-outlook))
- NY Fed HLW model jointly estimates natural rate of interest (r*), trend growth and output gap for US, Canada, euro area; page updated 27 Aug 2026; replication code (HLW 2023 and COVID-adjusted LW) updated Mar 2026. One secondary source reports HLW US r* peaking ~1.3% in 2021 and trending toward ~1% by 2025 (secondary, unverified). — [NY Fed r-star page](https://www.newyorkfed.org/research/policy/rstar); [NY Fed Research on X](https://x.com/NYFedResearch/status/1896648847922725040); [RSM](https://realeconomy.rsmus.com/r-star-the-role-of-the-natural-rate-of-interest-in-monetary-policy-and-economic-growth/)
- NY Fed Liberty Street (Feb 2026) "The Post-Pandemic Global R*". — [LSE](https://libertystreeteconomics.newyorkfed.org/2026/02/the-post-pandemic-global-r/)
- Atlanta Fed Taylor Rule Utility — interactive tool combining r*, inflation gap and resource gap to compute prescribed policy rate (educational analogue). — [Atlanta Fed](https://www.atlantafed.org/research-and-data/data/taylor-rule)

### Inferences
- Three-layer design: **Structural (slow: potential growth, labor force, productivity, r*, debt/GDP)** → **Cyclical (output gap, labor slack, inflation vs target, policy stance = rate − r*)** → **Market (curve, term premium, breakevens, FCI, valuations, sectors)**. Policy stance should be displayed relative to r* (Taylor-rule style), linking structural and cyclical layers.
- CBO potential (FRED GDPPOT, NROU are standard IDs — not re-verified) allows a computed output gap on the dashboard.

### Gaps
- Exact current HLW numbers not retrieved (dynamic page).
- No institutional source found that explicitly brands a "three-layer structural/cyclical/market" dashboard; this is a synthesis.

---

## 5. Probabilistic framing: Growth-at-Risk, fan charts, educational dashboards

### Takeaway
SOTA risk communication shows **distributions, not points**: Growth-at-Risk (ABG 2019) shows financial conditions mainly move the *lower tail* of future GDP growth; the Fed Board now maps FCI-G into fan charts for GDP, employment and inflation versus a "non-recessionary benchmark". This is directly reproducible in a dashboard with NFCI + quantile regression.

### Cited Findings
- Adrian, Boyarchenko & Giannone, "Vulnerable Growth" (AER 2019): quantile regressions of future GDP growth on current GDP growth/CFNAI and NFCI; lower quantiles vary strongly with financial conditions while upper quantiles are stable; economic conditions forecast the median but not other quantiles; fitted skewed-t gives full conditional distribution. — [NBER conference draft](https://conference.nber.org/confer/2016/EFGf16/Adrian_Boyarchenko_Giannone.pdf); [Yale seminar slides](https://economics.yale.edu/sites/default/files/tobias_adrian_metrics_seminar_102616.pdf)
- IMF adopted GaR in country surveillance (Prasad et al., WP/19/36, "Growth at Risk: Concept and Application in IMF Country Surveillance"). — [IMF WP/19/36](https://www.imf.org/-/media/Files/Publications/WP/2019/WPIEA2019036.ashx)
- Fed Board (Ajello, Favara, Marchal, Szoke, FEDS Note Sep 2024): maps FCI-G into one-year-ahead distributions for GDP growth, employment and inflation using a skewed-t with time-varying location, scale and shape; presented as probability distributions and fan charts vs a non-recessionary benchmark; found financial conditions near the top of the range compatible with expansions; downside employment risks eased from Oct 2023 peak; inflation mode ~2%. — [FEDS Note 2024-09-20](https://www.federalreserve.gov/econres/notes/feds-notes/financial-conditions-and-risks-to-the-economic-outlook-20240920.html)
- Recent extensions: structural GaR, calibrated quantile prediction, Bayesian quantile synthesis ("outlook-at-risk", 2026). — [arXiv 2410.04431](https://arxiv.org/pdf/2410.04431); [arXiv 2411.00520](https://arxiv.org/pdf/2411.00520); [arXiv 2603.11474](https://arxiv.org/pdf/2603.11474)

### Inferences
- Concrete feature: a "GaR" panel — quantile regression of 4-quarter-ahead real GDP growth on NFCI + current growth, showing 5th/50th/95th quantiles and a fan/density chart; highlight that the 5th percentile moves while the 95th barely does (core ABG lesson). Feasible with FRED (GDPC1, NFCI) in statsmodels QuantReg.
- Pair with market-implied probabilities (e.g., prediction markets / fed funds futures) for a "market vs model" comparison.

### Gaps
- Examples of public educational dashboards (Fed dot-plot explainers, FRED dashboards, Bloomberg ECO, Macrobond templates, Kalshi/Polymarket) were **not researched** within the tool budget — no citable findings; writer should not make claims about them from these notes.
- No verified FRED IDs for GaR outputs (none exist officially to my knowledge).
