# Real-time macro monitoring (US, 2025–2026): nowcasting, recession-probability models, financial conditions indices, leading & inflation indicators

Notes compiled 2026-10-07. "Verified on FRED" = the series ID was downloaded today via `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<ID>` (no API key needed) and the last observation is quoted as returned. NY Fed probit and Fed EBP figures were computed from the official data files downloaded today (URLs given).

---

## 1. Nowcasting: GDPNow, NY Fed Staff Nowcast, St. Louis; methodology, accuracy, and DIY DFM in Python

### Takeaway
GDPNow (bottom-up "bridge equation + factor model + BVAR" tracking of the 13 GDP subcomponents) and the NY Fed Staff Nowcast (relaunched 8 Sep 2023 as a *component-based* dynamic factor model with density intervals) are the two operational US nowcasts. Neither beats professional forecasters on point accuracy (GDPNow RMSE ≈1.17 pp), and both can be thrown off badly by idiosyncratic shocks (Q1 2025 gold imports/front-running of tariffs). A simplified Banbura–Modugno-type DFM is fully reproducible on FRED/ALFRED data with `statsmodels` `DynamicFactorMQ`.

### Cited Findings
**Atlanta Fed GDPNow**
- GDPNow RMSE of initial estimates = 1.17 pp over 2011:Q3–2025:Q2; average absolute error of final nowcasts since 2011 = 0.77 pp; the Atlanta Fed itself says these stats "do not give compelling evidence that the model is more accurate than professional forecasters", though it fares well vs other conventional statistical models — [Atlanta Fed GDPNow](https://www.atlantafed.org/research-and-data/data/gdpnow)
- FRED carries the final GDPNow nowcast as a quarterly series `GDPNOW`; latest observation 2026-07-01 (i.e., 2026:Q3) = 3.68% SAAR (verified on FRED) — [FRED GDPNOW](https://fred.stlouisfed.org/series/GDPNOW). FRED also carries component nowcasts, e.g. `IMPORTSNOW`, `IMPORTSGOODSNOW` — [FRED IMPORTSNOW](https://fred.stlouisfed.org/series/IMPORTSNOW)
- Q1 2025 episode (tariff front-running + gold imports): GDPNow was −2.8% on 3 Apr 2025, −2.4% on 9 Apr; Atlanta Fed launched an alternative "gold-adjusted" model that strips international gold trade from net exports (−0.3% on that date) — [CEIC](https://info.ceicdata.com/global-gold-shipments-distort-us-trade-and-gdp-nowcast-again); [Atlanta Fed on X, 26 Mar 2025: standard −1.8% vs gold-adjusted 0.2%](https://x.com/AtlantaFed/status/1904928834656309575); [Bloomberg: Atlanta Fed to update GDPNow with gold-adjusted model](https://www.bloomberg.com/news/articles/2025-04-23/atlanta-fed-to-update-gdpnow-with-model-that-adjusts-for-gold)
- Final Q1 2025 nowcasts: standard −2.7%, gold-adjusted −1.5%; BEA advance −0.3%. Main miss was private inventories: BEA had inventories adding 2.25 pp vs 0.30 pp in both GDPNow models; real goods imports surged 50.9% annualized and net exports subtracted 4.83 pp — [Atlanta Fed Macroblog, 14 May 2025](https://www.atlantafed.org/research-and-data/publications/policy-hub-macroblog/2025/05/14/challenges-in-forecasting-gdp-growth-last-quarter-and-this-quarter)

**NY Fed Staff Nowcast**
- Original Staff Nowcast launched April 2016 as a DFM producing weekly current-quarter GDP estimates; suspended Sept 2021 because of COVID-era uncertainty; reintroduced 8 Sep 2023 — [Fed in Print: Reintroducing the New York Fed Staff Nowcast](https://www.fedinprint.org/item/fednls/96733); [NY Fed press release](https://www.newyorkfed.org/newsevents/news/research/2023/20230908)
- New model = "component-based dynamic factor model": combines bottom-up national accounts identity with a DFM, models all GDP components jointly, produces nowcast densities and impact (news) decompositions for each component — [NY Fed Staff Report 1152](https://www.newyorkfed.org/research/staff_reports/sr1152); [technical paper](https://newyorkfed.org/medialibrary/media/research/blog/2023/NYFed-Staff-Nowcast_technical-paper)
- Published by AMEC, updated ~11:45 ET each Friday, with 50% and 68% probability bands (e.g. 2024:Q4 nowcast 1.9%, 50% band [0.8, 2.9], 68% band [0.2, 3.3]) — [NY Fed on X](https://x.com/NewYorkFed/status/1875223557765992506)
- An April 2025 NY Fed staff report finds point-nowcast RMSE of a standard DFM can be improved ~15% and density log-score ~20% over a long historical sample (by the extensions studied) — reported via [search summary of NY Fed staff work; primary: SR 1152 / related](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr1152.pdf?sc_lang=en) (verify exact paper before quoting)
- Academic evaluation of the original NY Fed nowcast: in expansions the model is at best as good as a historical-mean benchmark, but in recessions MSFE falls ~90% vs benchmark — [Econometrics 9(1):11, "New York FED Staff Nowcasts and Reality"](https://doi.org/10.3390/econometrics9010011)

**DFM in Python**
- `statsmodels.tsa.statespace.DynamicFactorMQ`: mixed monthly/quarterly data (Mariano–Murasawa 2011 aggregation), EM estimation scalable to hundreds of series, arbitrary missing-data patterns (ragged edge), multiple factor blocks (global/real/nominal/labor), AR(1) or white-noise idiosyncratic terms, and built-in "news" decomposition à la Bok et al. (2017) — exactly the NY Fed 2016 architecture — [statsmodels docs](https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.dynamic_factor_mq.DynamicFactorMQ.html)
- Chad Fulton (statsmodels author, Fed Board) has a worked tutorial replicating a large DFM nowcast on FRED-MD data — [chadfulton.com](http://www.chadfulton.com/topics/statespace_large_dynamic_factor_models.html)
- Recent research alternatives: neural CDE + DFM hybrids — [arXiv 2409.08732](https://arxiv.org/pdf/2409.08732); LLM nowcasts evaluated in real time — [arXiv 2608.30110](https://arxiv.org/pdf/2608.30110)

### Inferences
- A DIY nowcaster using FRED monthly series (PAYEMS, INDPRO, RSAFS, HOUST, ICSA aggregated monthly, PCE real, durable goods, ISM proxies, trade) + quarterly GDPC1 in `DynamicFactorMQ(factors=1–3, factor_orders=1–2, idiosyncratic_ar1=True)` is realistic; for honest backtests use ALFRED vintages (or FRED-MD/QD vintage files) because revisions matter.
- The Q1 2025 episode shows the bottom-up (GDPNow) approach is vulnerable to accounting oddities (gold, inventory book values); a DFM with soft data would have been less extreme but also less "exact". Practical lesson: watch final sales to private domestic purchasers rather than headline GDP nowcasts during trade shocks.
- Note: project venv currently lacks `statsmodels` and `pandas` is only in `.venv` — adding statsmodels to pyproject is needed for a DFM.

### Gaps
- St. Louis Fed "Economic News Index" nowcast: I did not find a current source confirming it is still published in 2025–2026 (it was historically on FRED as a nowcast); treat as unverified/possibly discontinued.
- No published head-to-head 2023–2025 RMSE comparison of GDPNow vs NY Fed Staff Nowcast found.
- GDPNow methodological detail (BVAR for unknowns, bridge equations for 13 subcomponents, Higgins 2014 working paper) not re-confirmed from a fetched page this session (page content truncated).

---

## 2. Recession probability models and the 2022–2025 "recession that never came"

### Takeaway
Every classic recession signal fired in 2022–2024 (10y–3m inversion, NY Fed probit >70%, Conference Board LEI, Sahm rule Aug 2024) and no NBER recession followed (USREC = 0 through Sep 2026). Models built on near-term forward spread and on credit-market prices (EBP) were much less alarmed and were vindicated. As of autumn 2026 all models read low: NY Fed probit ~14–15%, Chauvet–Piger 0.62%, EBP-model ~9%, Sahm 0.00.

### Cited Findings
**NY Fed 10y–3m probit**
- Model: probit on the 10-year minus 3-month Treasury spread (3m on bond-equivalent basis, monthly averages) predicting recession 12 months ahead — [NY Fed yield curve FAQ](https://www.newyorkfed.org/research/capital_markets/ycfaq); data file [allmonth.xls](https://www.newyorkfed.org/medialibrary/media/research/capital_markets/allmonth.xls) columns: 10Y, 3M, 3M bond-equivalent, Spread, Rec_prob, NBER_Rec
- From allmonth.xls (downloaded 2026-10-07): peak probability since 2020 = 70.85% for target month May 2024 (i.e., computed from May 2023 spread); latest = 13.9% for Aug 2027 (Aug 2026 spread +0.87 pp); Jul 2026 spread +0.78 — [NY Fed data](https://www.newyorkfed.org/medialibrary/media/research/capital_markets/allmonth.xls)
- Secondary tracking: 14.98% (May 2026 data) vs 17.63% prior month — [Economic Greenfield, June 2026](https://www.economicgreenfield.com/2026/06/06/recession-probability-models-june-2026/)
- FRED spreads: `T10Y3M` = 1.06 (2026-10-06), `T10Y2Y` = 0.48 (verified on FRED) — [FRED T10Y3M](https://fred.stlouisfed.org/series/T10Y3M); [FRED T10Y2Y](https://fred.stlouisfed.org/series/T10Y2Y). Underlying: `DGS10` 5.31% (2026-10-05), `DTB3` 4.05% — [FRED DGS10](https://fred.stlouisfed.org/series/DGS10)
- 10y–2y first inverted 5 Jul 2022, inversion ended ~Oct 2024 (>28 months); GDP grew 2.9% in 2023 and >3% annualized in Q2–Q3 2024 — [eco3min (secondary)](https://eco3min.fr/en/yield-curve-inversion-history-2s10s-spread/)

**Near-term forward spread (Engstrom–Sharpe)**
- NTFS = 6-quarter-ahead forward 3m T-bill rate minus current 3m rate; dominates long-term spreads as predictor (Engstrom & Sharpe 2019) — [FEDS Notes, 12 Jul 2022](https://www.federalreserve.gov/econres/notes/feds-notes/monetary-policy-inflation-outlook-and-recession-probabilities-20220712.html)
- 2022 decomposition: NTFS = current policy gap (real rate − r*) + expected policy gap + expected inflation slope + term premium; its predictive power comes from current policy gap and inflation slope. As of mid-2022: "near-zero" 4-quarter recession probability; baseline tightening scenario → ~35% by end-2023, more restrictive → ~60%. Unusual 2022 combination (accommodative policy + falling expected inflation) not seen before past recessions — same FEDS Note; also [Chicago Fed Economic Perspectives 2022-4](https://www.chicagofed.org/publications/economic-perspectives/2022/4)
- Chicago Fed letter on sources of short-yield fluctuations vs recession odds — [Chicago Fed Letter 469](https://www.chicagofed.org/publications/chicago-fed-letter/2022/469); SF Fed 2022 letter on yield-curve recession risk — [FRBSF EL 2022-05](https://www.frbsf.org/research-and-insights/publications/economic-letter/2022/05/current-recession-risk-according-to-yield-curve/)

**Why the inverted curve failed (explanations)**
- Inversion reflected expected disinflation (falling inflation slope) rather than expected policy-induced slump — implied by the NTFS decomposition — [FEDS Notes 2022](https://www.federalreserve.gov/econres/notes/feds-notes/monetary-policy-inflation-outlook-and-recession-probabilities-20220712.html)
- Transmission channels impaired: credit did not contract enough; economy supported by pandemic savings, tight labor market, fiscal stimulus — [eco3min (secondary)](https://eco3min.fr/en/yield-curve-inversion-history-2s10s-spread/); BIS analysis of inversion and recession risk — [BIS](https://www.bis.org/publications/yield-curve-inversion-and-recession-risk)

**Sahm rule**
- Triggered with the July 2024 jobs report (released 2 Aug 2024), reaching 0.57; first trigger since 2020; Claudia Sahm herself flagged likely false positive because immigration-driven labor supply raised unemployment without demand collapse — [Fortune](https://fortune.com/2024/08/02/recession-indicator-claudia-sahm-rule-trigger-unemployment-rate-jobs-report); [Reason](https://reason.com/2024/08/02/whats-the-sahm-rule-alarming-jobs-report-raises-recession-risk/); [KBC on labour supply shocks](https://www.kbc.com/en/economics/publications/sahm-rule-and-labour-supply-shocks.html)
- First false signal of the real-time rule since 1970 — [eco3min (secondary)](https://eco3min.fr/en/sahm-rule-false-signals-history/)
- FRED: `SAHMREALTIME` (real-time vintages) and `SAHMCURRENT` (current vintage), both 0.00 for Sep 2026 (verified on FRED) — [FRED SAHMREALTIME](https://fred.stlouisfed.org/series/SAHMREALTIME)

**Chauvet–Piger smoothed recession probabilities**
- FRED `RECPROUSM156N` (Markov-switching DFM on payrolls, IP, real income ex-transfers, real manufacturing & trade sales; published with ~2-month lag) = 0.62% for Aug 2026 (verified on FRED); 0.44% for Apr 2026 per Greenfield — [FRED RECPROUSM156N](https://fred.stlouisfed.org/series/RECPROUSM156N); [Economic Greenfield](https://www.economicgreenfield.com/2026/06/06/recession-probability-models-june-2026/)
- Related: Hamilton GDP-based recession index `JHGDPBRINDX` = 7.0 for 2026:Q1 (verified on FRED) — [FRED JHGDPBRINDX](https://fred.stlouisfed.org/series/JHGDPBRINDX)
- NBER indicator `USREC` = 0 through Sep 2026 (verified on FRED) — [FRED USREC](https://fred.stlouisfed.org/series/USREC)

**Excess Bond Premium (Gilchrist–Zakrajšek)**
- EBP = part of corporate credit spreads not explained by expected default risk; strong predictor of unemployment, IP and recessions; Fed publishes monthly EBP and model-implied 12-month recession probability (Favara, Gilchrist, Lewis, Zakrajšek 2016 FEDS Note, updated) — [Fed in Print: Updating the Recession Risk and the EBP](https://www.fedinprint.org/item/fedgfn/10701); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3750973); [arXiv: Understanding the EBP](https://arxiv.org/html/2412.04063v1)
- From the Fed's [ebp_csv.csv](https://www.federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv) (columns: date, gz_spread, ebp, est_prob), downloaded 2026-10-07: max probability since 2022 = 30.1% (Oct 2023, EBP +0.26); Sep 2026 = 9.1% (EBP −0.39, GZ spread 0.93) — i.e., credit markets never priced a 2022–24 recession.

**Estrella–Mishkin** — classic 1996/1998 probit showing 10y–3m spread outperforms other financial predictors at 2–6 quarter horizons; basis of the NY Fed model — no primary source fetched this session (see Gaps).

### Inferences
- Ranking by 2022–2025 performance: EBP model (max 30%) and NTFS (low) > Chauvet–Piger (coincident, correctly near 0) >> 10y–3m probit (70%), LEI, Sahm (false). Lesson for a dashboard: combine a term-spread signal with credit-spread/EBP and NTFS; treat Sahm as coincident and sensitive to labor-supply shocks.
- Re-steepening ("un-inversion") historically precedes recession onset, but in 2024–2026 it happened with no recession; as of Oct 2026 the steep curve is partly driven by high long yields (10y 5.31%), i.e., term premium, not easing expectations.
- NTFS is reproducible from FRED Treasury yields (approximate forward 6q-ahead from DGS1/DGS2 or use Fed Board's Gürkaynak–Sack–Wright yield curve file).

### Gaps
- Estrella–Mishkin primary paper not fetched; coefficients of NY Fed probit not extracted (the FAQ page fetch returned navigation only).
- No official Fed published NTFS series found for 2025–2026 values.

---

## 3. Financial conditions indices

### Takeaway
The Chicago Fed NFCI/ANFCI, St. Louis STLFSI4 and Kansas City KCFSI are on FRED and all read "loose" in autumn 2026 (negative = looser than average). The Fed Board's FCI-G (2023) differs conceptually: it measures the *impulse to next-year GDP growth* from changes in 7 asset prices, weighted by FRB/US multipliers; it is downloadable from the Fed site but not on FRED.

### Cited Findings
- FCI-G (Ajello et al., FEDS Notes 30 Jun 2023): aggregates changes in fed funds rate, 10y Treasury, 30y mortgage rate, BBB corporate yield, Dow Jones total market index, Zillow house prices, nominal broad dollar; weights = FRB/US-based dynamic multipliers of permanent shocks on real GDP growth over the next year; +1 = financial conditions subtract 1 pp from GDP growth over next year; measures impulse, not level of restrictiveness — [FEDS Notes 2023](https://www.federalreserve.gov/econres/notes/feds-notes/a-new-index-to-measure-us-financial-conditions-20230630.html)
- Fed follow-up on FCI and risks to outlook (Sep 2024) — [FEDS Notes 20 Sep 2024](https://www.federalreserve.gov/econres/notes/feds-notes/financial-conditions-and-risks-to-the-economic-outlook-20240920.html); Brookings on Fed policy's effect on FCI-G — [Brookings](https://www.brookings.edu/articles/the-impact-of-federal-reserve-policy-on-the-feds-financial-conditions-index/)
- SF Fed 2024 on monetary policy and financial conditions (easing of FCIs in late 2023 despite high rates) — [FRBSF EL 2024-03](https://www.frbsf.org/research-and-insights/publications/economic-letter/2024/03/monetary-policy-and-financial-conditions/); Chicago Fed comparison of 2022–24 financial conditions with past tightenings — [Chicago Fed Letter 498](https://www.chicagofed.org/publications/chicago-fed-letter/2024/498)
- Caballero–Caravello–Simsek "FCI-star": an FCI target consistent with output gap closing — [MIT paper (2026 version)](https://economics.mit.edu/sites/default/files/2026-01/FCIstarPublic.pdf)
- FRED IDs and latest values (verified on FRED, 2026-10-07):
  - `NFCI` −0.548 (week of 2026-09-25); `ANFCI` (adjusted for macro conditions) −0.574; `NFCICREDIT` −0.061 — [FRED NFCI](https://fred.stlouisfed.org/series/NFCI), [ANFCI](https://fred.stlouisfed.org/series/ANFCI)
  - `STLFSI4` −0.807 (2026-09-25) — [FRED STLFSI4](https://fred.stlouisfed.org/series/STLFSI4)
  - `KCFSI` −0.986 (Sep 2026, monthly) — [FRED KCFSI](https://fred.stlouisfed.org/series/KCFSI)
  - Credit spreads: `BAMLH0A0HYM2` (HY OAS) 3.12 (2026-10-05); `BAMLC0A4CBBB` (BBB OAS) 1.04 — [FRED BAMLH0A0HYM2](https://fred.stlouisfed.org/series/BAMLH0A0HYM2)
- PIMCO practitioner view of policy through financial conditions — [PIMCO](https://www.pimco.com/gbl/en/insights/monetary-policy-through-the-lens-of-financial-conditions)

### Inferences
- Mapping to growth: FCI-G is directly in GDP-pp units; NFCI/STLFSI are z-scores (0 = average) and are best used as inputs to a growth-at-risk quantile regression (Adrian–Boesch–Giannone style) or as a factor in the DFM.
- Goldman Sachs FCI is proprietary (not free); FCI-G is the closest free analogue and can be approximately rebuilt from FRED series (FEDFUNDS, DGS10, MORTGAGE30US, BAMLC0A4CBBBEY, Wilshire/S&P proxy, house prices, DTWEXBGS) — but published weights must be taken from the Fed's data file.
- The 2023–2024 easing of NFCI while policy rates were high is one reason the yield-curve recession call failed.

### Gaps
- Current (2026) FCI-G reading not retrieved (Fed CSV URL not fetched).
- Goldman FCI methodology/levels: no free primary source checked.

---

## 4. Leading indicators

### Takeaway
The Conference Board LEI gave its longest-ever non-recession decline in 2022–2024 (and re-triggered its "3Ds" rule in 2025) — a major false signal. High-frequency real-activity gauges (initial claims, NY Fed/Dallas Fed WEI, Philly Fed ADS) stayed consistent with expansion. Free-data reproducibility: claims, WEI, OECD CLI, coincident indexes are on FRED; LEI levels are licensed; Philly Fed's state "leading index" `USSLIND` is discontinued.

### Cited Findings
- LEI "3Ds rule": recession signal when 6-month diffusion ≤50 AND 6-month annualized LEI growth below −4.3% — [Conference Board release Dec 2025 (PDF)](https://www.conference-board.org/pdf_free/press/US%20LEI%20PRESS%20RELEASE-Dec%202025.pdf); latest release [Sep 2026 PDF](https://www.conference-board.org/pdf_free/press/US%20LEI%20PRESS%20RELEASE-Sep%202026.pdf)
- LEI fell for an extended run in 2022–2024, deeply negative 6-month change in 2024, signal not followed by recession — [whatisarecession.com (secondary)](https://whatisarecession.com/leading-economic-index); [Marketplace Nov 2024](https://www.marketplace.org/story/2024/11/21/leading-economic-index-the-conference-board-indicator-jobless-claims); [Advisor Perspectives](https://www.advisorperspectives.com/dshort/updates/2024/12/19/cb-leading-economic-index-small-rise-in-november)
- In mid-2025 the recession signal was triggered for a third consecutive month, yet Conference Board explicitly did not forecast a recession — [RVBusiness reprint of TCB release](https://rvbusiness.com/leading-economic-index-for-u-s-declined-by-0-3-in-june/); [Marketplace Mar 2025](https://www.marketplace.org/story/2025/03/21/one-index-of-economic-indicators-the-conference-board-lei-signal-data)
- FRED (verified 2026-10-07):
  - `ICSA` initial claims 197,000 (week of 2026-09-26); `CCSA` continuing 1.701 m — [FRED ICSA](https://fred.stlouisfed.org/series/ICSA)
  - `WEI` Weekly Economic Index (Lewis–Mertens–Stock, scaled to 4-quarter GDP growth) 2.93 (2026-09-26) — [FRED WEI](https://fred.stlouisfed.org/series/WEI)
  - `USPHCI` Philly Fed US coincident index 149.85 (Aug 2026) — [FRED USPHCI](https://fred.stlouisfed.org/series/USPHCI)
  - `USSLIND` Philly Fed leading index: last observation Feb 2020 → discontinued — [FRED USSLIND](https://fred.stlouisfed.org/series/USSLIND)
  - OECD CLI: `USALOLITOAASTSAM` (amplitude-adjusted) 100.96 (Aug 2026) is live; older `USALOLITONOSTSAM` stops at Jan 2024 — [FRED USALOLITOAASTSAM](https://fred.stlouisfed.org/series/USALOLITOAASTSAM)
- Philadelphia Fed ADS (Aruoba–Diebold–Scotti) business conditions index: daily, published by the Philly Fed (not on FRED) — from background knowledge; not fetched this session.

### Inferences
- LEI's failure likely reflects its heavy weight on manufacturing/ISM, consumer expectations and the yield curve — all of which were depressed in a services-led, fiscally supported expansion.
- ISM new orders: licensed data, not on FRED (ISM removed series from FRED in 2016); regional Fed manufacturing surveys (Philly, NY Empire, Richmond, KC, Dallas) are free substitutes.

### Gaps
- No 2025–2026 primary source on ADS index track record or on WEI 2024–2026 performance was fetched.
- Exact Conference Board LEI readings for 2026 not extracted.

---

## 5. Inflation monitoring tools

### Takeaway
The Fed system runs a family of "underlying inflation" gauges, most of which are on FRED: Atlanta Fed sticky/flexible CPI, Dallas Fed trimmed-mean PCE, NY Fed Multivariate Core Trend (Fed site only), Cleveland Fed expected inflation model, TIPS breakevens and 5y5y, and the NY Fed GSCPI. As of Aug–Sep 2026: trimmed-mean PCE 2.19% y/y, core sticky CPI 2.70%, Cleveland 1y expectations 2.64%, 5y breakeven 2.37%, 5y5y 2.35%, Michigan 1y 4.0%.

### Cited Findings
- NY Fed MCT: regular publication since July 2023; measures persistence in 17 core PCE sectors (DFM with common + sector-specific trends); MCT hit 3.0% y/y for March 2025 (highest since Feb 2024), driven by non-housing services — [Liberty Street: Layers of Inflation Persistence](https://libertystreeteconomics.newyorkfed.org/2023/01/the-layers-of-inflation-persistence/); [Wolf Street (secondary)](https://wolfstreet.com/2025/05/05/ny-feds-multivariate-core-trend-inflation-measure-hits-3-0-worst-in-over-a-year-predicts-acceleration-of-pce-price-index/)
- Global MCT extension (Feb 2025) — [Liberty Street: Global Trends in U.S. Inflation Dynamics](https://libertystreeteconomics.newyorkfed.org/2025/02/global-trends-in-u-s-inflation-dynamics/)
- GSCPI spikes tend to coincide with spikes in the goods trend inflation component — [Liberty Street inflation archive](https://libertystreeteconomics.newyorkfed.org/inflation/) (GSCPI itself published as Excel on newyorkfed.org; not on FRED — background knowledge)
- FRED IDs (verified 2026-10-07):
  - `CORESTICKM159SFRBATL` core sticky CPI y/y 2.70 (Aug 2026); `STICKCPIM157SFRBATL` sticky CPI (monthly annualized) 0.25; `FLEXCPIM679SFRBATL` flexible CPI −5.82 (Aug 2026) — [FRED CORESTICKM159SFRBATL](https://fred.stlouisfed.org/series/CORESTICKM159SFRBATL)
  - `PCETRIM12M159SFRBDAL` Dallas trimmed-mean PCE 12-month 2.19 (Aug 2026) — [FRED PCETRIM12M159SFRBDAL](https://fred.stlouisfed.org/series/PCETRIM12M159SFRBDAL)
  - `EXPINF1YR` Cleveland Fed 1y expected inflation 2.64; `EXPINF10YR` 2.57 (Sep 2026) — [FRED EXPINF1YR](https://fred.stlouisfed.org/series/EXPINF1YR)
  - `T5YIE` 2.37, `T10YIE` 2.36, `T5YIFR` (5y5y forward) 2.35 (2026-10-06) — [FRED T5YIFR](https://fred.stlouisfed.org/series/T5YIFR)
  - `MICH` UMich 1y expectations 4.0 (Aug 2026) — [FRED MICH](https://fred.stlouisfed.org/series/MICH)

### Inferences
- Divergence in 2026: market/model expectations ~2.3–2.6% vs household (Michigan) 4.0% — survey expectations remain elevated after the 2025 tariff episode, a typical pattern.
- All except MCT and GSCPI are one-line FRED pulls; MCT is reproducible in principle (Almuzara–Sbordone model) but complex.

### Gaps
- Latest MCT and GSCPI values for 2026 not retrieved.
- Cleveland Fed model methodology (Haubrich–Pennacchi–Ritchken: Treasury yields + inflation swaps + surveys) not fetched this session.

---

### Summary table (all sections): free-data reproducibility (FRED IDs verified 2026-10-07; sources as cited above)

| Tool | Free? | FRED ID / source | Latest |
|---|---|---|---|
| GDPNow | Yes | `GDPNOW` (quarterly final) + Atlanta Fed site | 2026Q3: 3.68% |
| NY Fed Staff Nowcast | Site only | newyorkfed.org | – |
| NY Fed 10y–3m probit | Yes | allmonth.xls; `T10Y3M` | 13.9% (Aug 2027 target) |
| Chauvet–Piger | Yes | `RECPROUSM156N` | 0.62% (Aug 2026) |
| Sahm rule | Yes | `SAHMREALTIME`, `SAHMCURRENT` | 0.00 (Sep 2026) |
| EBP + prob | Yes | Fed ebp_csv.csv | 9.1% (Sep 2026) |
| NFCI / ANFCI | Yes | `NFCI`, `ANFCI` | −0.55 / −0.57 |
| STLFSI | Yes | `STLFSI4` | −0.81 |
| KC FSI | Yes | `KCFSI` | −0.99 |
| FCI-G | Fed site | federalreserve.gov | – |
| Goldman FCI | No | proprietary | – |
| Conference Board LEI | No (licensed) | – | – |
| OECD CLI | Yes | `USALOLITOAASTSAM` | 100.96 |
| WEI | Yes | `WEI` | 2.93 |
| Claims | Yes | `ICSA`, `CCSA` | 197k / 1.70m |
| Sticky/flex CPI | Yes | `CORESTICKM159SFRBATL`, `FLEXCPIM679SFRBATL` | 2.70 / −5.8 |
| Trimmed-mean PCE | Yes | `PCETRIM12M159SFRBDAL` | 2.19 |
| Cleveland expectations | Yes | `EXPINF1YR`, `EXPINF10YR` | 2.64 / 2.57 |
| Breakevens, 5y5y | Yes | `T5YIE`, `T10YIE`, `T5YIFR` | 2.37 / 2.36 / 2.35 |
| MCT, GSCPI | NY Fed site | newyorkfed.org | – |
