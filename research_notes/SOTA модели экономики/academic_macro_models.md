# Academic / central-bank structural macro models: state of the art 2025–2026

Research note scope: which model classes are frontier now, what they explain, their weaknesses, and which have open code or data that an individual could simplify for an educational dashboard on FRED data. Research date: October 2026. About 20 search and fetch calls were made. Several primary PDFs could not be parsed, so some claims rest on abstracts or summaries. Those cases are marked.

## 1. New Keynesian DSGE after the 2021–2023 inflation surprise (Smets-Wouters, NY Fed DSGE, ECB NAWM, FRB/US) and the fixes that followed

### Takeaway
Medium-scale NK DSGE models survive as central-bank tools, but the 2021–23 episode exposed problems. Their flat estimated Phillips curves and strong policy-rule stabilisation meant they could not anticipate the surge. After the fact they explained it mainly as large, persistent cost-push (supply) shocks. Three fixes followed: richer supply and energy blocks, nonlinear or state-dependent Phillips curves, and simple semi-structural decompositions in the style of Bernanke-Blanchard. Bernanke-Blanchard became the de facto common framework across central banks.

### Cited Findings
- An ECB 2025 working paper (WP 3137, "Inflation and monetary policy in medium-sized NK DSGE models") makes four points. First, these models attribute the 2021–22 surge mostly to "repeated and persistent cost-push shocks rather than overheating demand". Second, the flat estimated Phillips curve and strong countercyclical policy act as a stabilising mechanism, which limited the models' ability to predict the surge. Third, the ECB's NAWM was extended with financial frictions, the effective lower bound and energy price shocks. Fourth, the authors call for "richer supply-side structures and nonlinear dynamics". — [ECB WP 3137](https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp3137~e458bce069.en.pdf); [RePEc entry](https://ideas.repec.org/p/ecb/ecbwps/20253137.html)
- The NY Fed DSGE model attributes the recent rise in inflation mostly to "a large cost-push shock that occurred in the second quarter of 2021 and whose inflationary effects persist". — [NY Fed, "Drivers of Inflation: The NY Fed DSGE Model's Perspective"](https://fedinprint.org/item/fednls/93778); see also [Liberty Street Economics 2023 on lagged effects of policy](https://libertystreeteconomics.newyorkfed.org/2023/11/the-new-york-fed-dsge-model-perspective-on-the-lagged-effect-of-monetary-policy/)
- Heterodox critics (INET) argue that the DSGE paradigm rests on "bad modeling" and is not the future of macro. — [INET](https://www.ineteconomics.org/perspectives/blog/why-dsge-models-are-not-the-future-of-macroeconomics)
- **Bernanke and Blanchard (2023), NBER w31417**
  - The model is simple and dynamic, with equations for prices, wages, and short- and long-run inflation expectations. It decomposes the sources of pandemic-era inflation.
  - Price shocks relative to wages drove most of the initial surge: commodity prices and sector-specific spikes, reflecting strong demand plus supply constraints.
  - Labor-market overheating has a smaller but more persistent effect on wage growth and inflation.
  - Replication files are at nber.org/data-appendix/w31417, and a replication package was released via Brookings/PIIE.
  - [NBER w31417 PDF](https://www.nber.org/system/files/working_papers/w31417/w31417.pdf); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4505856)
- **11-economy follow-up (Bernanke-Blanchard with central-bank teams, NBER w32532, 2024)**
  - Relative price shocks and sectoral shortages drove the initial surge. Labor-market tightness became more important as those shocks faded.
  - Some countries showed a weak link between labor-market tightness and wages.
  - The episode differed from the 1970s because expectations were better anchored and wage indexation was lower.
  - Several central banks adopted the framework.
  - [Brookings summary](https://www.brookings.edu/articles/an-analysis-of-pandemic-era-inflation-in-11-economies/); [NBER w32532](https://www.nber.org/system/files/working_papers/w32532/w32532.pdf)
- Replications of Bernanke-Blanchard exist for:
  - France: [Banque de France](https://www.banque-france.fr/en/publications-and-statistics/publications/what-caused-post-pandemic-inflation-replicating-bernanke-and-blanchard-2023-french-data)
  - Germany and the euro area: [Bundesbank technical paper](https://ideas.repec.org/p/zbw/bubtps/290409.html)
  - The euro area: [ECB Occasional Paper 343](https://www.ecb.europa.eu/pub/pdf/scpops/ecb.op343~ab3e870d21.en.pdf)
  - An independent replication paper on Zenodo: [Zenodo](https://zenodo.org/records/20272539)
- **Nonlinear Phillips curve**
  - Benigno and Eggertsson propose an "inverse-L" or "slanted-L" NK Phillips curve. Slack is measured by vacancies per unemployed (v/u). Inflation accelerates sharply when v/u exceeds about 1.
  - They estimate it on US quarterly data for 1960–2024, with the threshold near unity. Above the threshold, both the Phillips-curve slope and supply-shock pass-through rise.
  - [NBER w31197](https://www.nber.org/system/files/working_papers/w31197/w31197.pdf); [CEPR DP18116](https://cepr.org/publications/dp18116); [Slanted-L, NBER w32172](https://www.nber.org/system/files/working_papers/w32172/w32172.pdf)
- The nonlinear Phillips curve is contested. Beaudry, Hou and Portier (NBER w33522, Feb 2025) conclude that "the evidence in support of a nonlinear Phillips curve is very fragile" once inflation expectations are properly controlled for, using both cross-city and aggregate data. This is from the abstract only; the PDF could not be parsed. — [NBER w33522](https://www.nber.org/papers/w33522)
- **Open code**
  - The NY Fed DSGE model is open source in Julia (DSGE.jl, in the General registry, `add DSGE`). — [GitHub FRBNY-DSGE/DSGE.jl](https://github.com/FRBNY-DSGE/DSGE.jl)
  - FRB/US is available as the PyFRB/US Python package, last updated 11 Feb 2026. — [Federal Reserve, FRB/US in Python](https://www.federalreserve.gov/econres/us-models-python.htm)
  - There is also an R port via bimets. — [CRAN bimets vignette](https://cran.r-project.org/web/packages/bimets/vignettes/frb2bimets.pdf)

### Inferences
- The consensus "fix" is less a new model class than (a) adding energy and supply blocks and nonlinearity to DSGEs and (b) relying more on transparent semi-structural decompositions such as Bernanke-Blanchard.
- For a dashboard, Bernanke-Blanchard is the most replicable "frontier" piece. Its inputs are wages (ECI), CPI or PCE, energy and food prices, a shortage index, v/u from JOLTS, and short- and long-run expectations (Cleveland Fed or SPF). Most of these are on FRED. One exception: the shortage index in the paper is Google-trends based. This is from my memory of the paper and was not verified here.
- A v/u-threshold Phillips curve (Benigno-Eggertsson) is easy to compute on FRED with JTSJOL and UNEMPLOY. Because of the Beaudry-Hou-Portier critique, it should be presented as a contested hypothesis.

### Gaps
- I did not verify specific 2024–26 changes to the Smets-Wouters or FRB/US equations, such as a changed expectations block.
- I did not confirm the exact shortage-index variable in Bernanke-Blanchard, or whether the replication code is in EViews or another language. I believe it is EViews, but this is unverified.

## 2. HANK (Heterogeneous Agent New Keynesian) models

### Takeaway
HANK is now presented as the "new core" of usable macro. Key work includes Kaplan-Moll-Violante (2018, background) and the Auclert-Bardóczy-Rognlie-Straub sequence-space Jacobian (SSJ) method (Econometrica 2021). The SSJ made these models fast enough for routine use. Central banks and fiscal institutions now have HANK teams. The main insights are that heterogeneous and intertemporal MPCs drive fiscal multipliers, and that monetary policy works largely through indirect, general-equilibrium income effects.

### Cited Findings
- Auclert's "HANK: A New Core of Usable Macroeconomics" (Jan 2025) says HANK is taught in second-year PhD courses at many universities. It also says that "many central banks and a number of fiscal policy institutions have a HANK development team". — [Auclert 2025](https://web.stanford.edu/~aauclert/hank_as_core.pdf)
- An Annual Review survey by Auclert, Rognlie and Straub, "Fiscal and Monetary Policy with Heterogeneous Agents" (2025), is the standard reference for the fiscal and monetary transmission insights. — [Annual Review draft](https://shade-econ.github.io/annual-review/annual_review_hank.pdf); [alt link](https://straub.scholars.harvard.edu/sites/g/files/omnuum7751/files/2025-04/annual_review_hank.pdf)
- Summary of the main insights. This is a WebFetch model summary of the Auclert PDF, so the specific wording should be treated cautiously.
  - Heterogeneous intertemporal MPCs mean high-MPC (low-liquidity) households spend income gains quickly.
  - Deficit-financed transfers to such households produce larger and more persistent multipliers than in representative-agent (RANK) models.
  - Monetary policy works largely through indirect effects on labor income and redistribution, not through direct intertemporal substitution.
  - Computational complexity remains a challenge.
  - [Auclert 2025](https://web.stanford.edu/~aauclert/hank_as_core.pdf)
- At the Fed Board, a growing number of economists use HA models. The SSJ framework "has facilitated adoption and collaboration", and the method is being extended to life-cycle (OLG) Jacobians. — [NBER SI 2025 slides, Velasquez-Giraldo](https://conference.nber.org/confer/2025/MWs25/Velasquez-Giraldo%20slides.pdf); [Bardóczy, SSJ of life-cycle models](https://www.bencebardoczy.com/files/ssj-lc.pdf); [FEDS 2026-046](https://www.federalreserve.gov/econres/feds/files/2026046pap.pdf)
- Estimating HANK for central-bank use is an active topic. Examples are "Estimating HANK for Central Banks" (NBER SI 2023) and limited-information estimation of HA models (arXiv 2026). — [NBER SI 2023](https://conference.nber.org/confer/2023/MWs23/marco.pdf); [arXiv 2608.13953](https://arxiv.org/pdf/2608.13953)
- Extensions include housing and rental sectors (LSE CFM 2025) and a one-asset vs two-asset comparison of fiscal multipliers (2026). — [LSE CFM DP 2025-29](https://www.lse.ac.uk/CFM/assets/pdf/CFM-Discussion-Papers-2025/CFMDP2025-29-Paper.pdf); [Pretoria WP 2026-10](https://drupalwebprod-files.up.ac.za/Public/2026-04/202610.pdf?VersionId=ZRwXxTE_STzJwu1aud2x7eZvfWpBBp1D)

### Inferences
- SSJ is open-source Python (the `sequence-jacobian` package from the shade-econ group). A toy one-asset HANK can therefore run in Python in seconds, and it is the most feasible "frontier structural model" for an educational demo.
- However, it would be calibrated, not estimated on FRED. Distributional data comes from SCF and CEX, not FRED.
- The mapping to FRED is weak. A dashboard could show impulse responses, such as a transfer shock under different MPC distributions, rather than fit data.

### Gaps
- I found no source naming specific production forecasting models at the Fed or ECB that are HANK. Adoption appears to be for policy analysis and research teams, not the main forecast.
- The package name, license and GitHub URL for SSJ were not verified in this session.

## 3. Agent-based macro models (Poledna et al. 2023; BoE; BeforeIT.jl)

### Takeaway
Poledna, Miess, Hommes and Rabitsch (European Economic Review 2023) is the flagship claim that a data-driven macro ABM can match, and at longer horizons beat, VAR and DSGE benchmarks out of sample (for Austria). Open-source infrastructure (BeforeIT.jl) now exists. Credibility is growing but rests on a small number of applications. The model needs detailed national accounts, input-output, sector and census micro data, not just aggregate FRED series.

### Cited Findings
- Poledna et al. call it "the first agent-based model (ABM) that can compete with and in the long run significantly outperform benchmark VAR and DSGE models in out-of-sample forecasting".
  - The model covers a small open economy (Austria) and includes all ESA 2010 activities with millions of heterogeneous agents.
  - It uses national and sector accounts, input-output tables, government statistics, and census and business-demography data.
  - It was used to forecast the medium-run effects of COVID lockdowns.
  - [EER 151 (2023) 104306 PDF](https://irihs.ihs.ac.at/id/eprint/6453/1/poledna-miess-et-al-2023-economic-forecasting-with-an-agent-based-model.pdf); [EconPapers](https://econpapers.repec.org/RePEc:eee:eecrev:v:151:y:2023:i:c:s0014292122001891)
- An extension to the euro area by Hommes and Poledna analyses and forecasts crises. — [SSRN 4381261](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4381261)
- BeforeIT.jl (2025) is open-source Julia under AGPL-3.0 and implements this base macro ABM.
  - It claims to be "the first open-source, industry-grade software to build macro ABMs of the type of the base model".
  - It is "orders of magnitude faster than a Matlab version".
  - [arXiv 2502.13267](https://arxiv.org/abs/2502.13267)
- The Austrian institute WIFO presented "Economic Forecasting with an Agent-based model" in February 2026, which suggests that forecasting institutions are experimenting with it. — [WIFO slides, Feb 2026](https://www.wifo.ac.at/wp-content/uploads/upload-3765/abm_slides.pdf)

### Inferences
- An ABM in the Poledna style is not realistically calibrated on FRED alone. It needs US input-output tables (BEA), sector accounts and firm demography. A heavily simplified toy ABM could illustrate mechanisms, but it would not be a credible forecaster.
- Evidence of forecast superiority comes from essentially one country study and its extensions. Independent replications are scarce.

### Gaps
- I did not find a reliable 2024–26 source on Bank of England ABM use (housing-market ABM, or ABMs in BoE stress-testing). This was not researched in depth.
- No US calibration of the Poledna ABM was found.

## 4. Machine learning and AI in macro forecasting

### Takeaway
Interpretable ML that nests linear macro, such as Goulet Coulombe's Macroeconomic Random Forest (MRF; Journal of Applied Econometrics 2024), shows documented gains, especially around turning points. LLM forecasts report beating surveys, but they are heavily contaminated by look-ahead bias. Time-series foundation models (TimesFM, Chronos, Moirai) are promising zero-shot but not clearly superior. Real-time, vintage-consistent evaluation is only now emerging.

### Cited Findings
- **Macroeconomic Random Forest (MRF)**
  - MRF uses a random forest to model time-varying parameters of a linear macro equation. These "generalized time-varying parameters" make it interpretable.
  - It gives "clear forecasting gains over numerous alternatives", predicted the 2008 unemployment rise, and does well on inflation.
  - The gains come from forward-looking variables (term spread, housing starts) whose influence nearly doubles before recessions.
  - [arXiv 2006.12724](https://arxiv.org/abs/2006.12724); [JAE 2024](https://onlinelibrary.wiley.com/doi/abs/10.1002/jae.3030)
- **LLM inflation forecasts**
  - Faria-e-Castro and Leibovici (St. Louis Fed) used Google's PaLM to produce conditional inflation forecasts for 2019–23. They found lower MSE than the Survey of Professional Forecasters in most years and at most horizons.
  - These were in-sample relative to training data, which is a caveat the authors acknowledge in framing.
  - [St. Louis Fed Review, Nov 2024](https://www.stlouisfed.org/publications/review/2024/nov/artificial-intelligence-and-inflation-forecasts); [WP 2023-015](https://s3.amazonaws.com/real.stlouisfed.org/wp/2023/2023-015.pdf)
- **Look-ahead bias critique**
  - Gao, Jiang and Yan (2025) propose a "Lookahead Propensity" test. LLM predictive power is amplified on prompts likely seen in training and loses significance on post-cutoff samples. — [RePEc arXiv 2512.23847](https://ideas.repec.org/p/arx/papers/2512.23847.html)
  - Ludwig, Mullainathan et al. document training leakage. In one example, Llama 2 mentioned Covid-19 in more than 25% of risk predictions from 2019 earnings calls. — [arXiv 2412.07031](https://arxiv.org/pdf/2412.07031)
  - "ChatMacro" (2026) notes that LLMs were trained on realized 2021 inflation outcomes. — [ResearchGate](https://www.researchgate.net/publication/400522867_ChatMacro_Evaluating_Inflation_Forecasts_of_Generative_AI)
- AMRO (2025) found that LSTM, GRU and zero-shot LLM models forecast the fed funds rate well, with the LLM slightly ahead. — [AMRO WP/25-10](https://amro-asia.org/wp-content/uploads/2025/09/AMRO_WP_25_10_FedAI_model.pdf)
- **Time-series foundation models**
  - A zero-shot evaluation of TimeGPT, Chronos and Moirai on GDP growth found good point and interval forecasts. They degrade during rapid shocks but "recover forecasting accuracy faster than classical models". — [arXiv 2506.15705](https://arxiv.org/html/2506.15705)
  - "MACROCAST" (arXiv 2026) builds a vintage-consistent TSFM for real-time macro forecasting, which addresses the data-revision and leakage problem. — [arXiv 2606.28670](https://arxiv.org/pdf/2606.28670)
- The BIS uses ML to decompose inflation (BIS WP 1294). — [BIS WP 1294](https://www.bis.org/publ/work1294.pdf)

### Inferences
- The defensible claim is that ML helps modestly, mostly through nonlinearity and time variation near turning points. Claims about LLMs beating the SPF should be treated as unproven because of look-ahead contamination.
- For a dashboard, three components are feasible on FRED: a random-forest or MRF-style forecaster on FRED-MD/QD, a zero-shot Chronos or TimesFM baseline, and a pseudo-out-of-sample comparison against an AR or BVAR benchmark. ALFRED vintages would make the comparison honest. An MRF implementation exists from the author, which I believe is in R and Python, but this is unverified.

### Gaps
- I found no rigorous, peer-reviewed real-time horse race of TSFMs vs BVAR on US data.
- The MRF code location and license were not verified.

## 5. Semi-structural workhorses: FRB/US, BVARs, local projections, r-star (HLW)

### Takeaway
FRB/US (semi-structural, open in Python) and Bayesian VARs remain workhorses. The 2024–25 econometrics consensus (Li-Plagborg-Møller-Wolf; the NBER Macro Annual 2025 primer) is a bias-variance trade-off. Local projections have low bias but high variance, while VARs and BVARs have lower variance. BVARs are recommended when precision matters. HLW r-star (open code and data on the NY Fed site) is the standard r* model. Its estimate is around 0.8% for the US in 2025 and below 1% in 2025Q4, with very wide uncertainty and large disagreement across models.

### Cited Findings
- PyFRB/US contains the full FRB/US equations, simulation code and documentation. It requires Python 3 and was updated 11 Feb 2026. — [Federal Reserve](https://www.federalreserve.gov/econres/us-models-python.htm). FRB/US is also used for dynamic scoring by the Yale Budget Lab. — [Yale Budget Lab](https://budgetlab.yale.edu/research/dynamic-scoring-using-frbus-macroeconomic-model)
- **Local projections vs VARs**
  - Li, Plagborg-Møller and Wolf (Journal of Econometrics 2024) simulate thousands of data-generating processes calibrated to US data. LPs have low bias and high variance; VARs have the opposite.
  - The two are identical on impact. Bias-corrected LP is preferred "if and only if" the researcher overwhelmingly prioritises bias.
  - Otherwise BVARs are preferred at short and long horizons, and least-squares VARs at intermediate and long horizons.
  - [NBER w30207](https://www.nber.org/papers/w30207); [J. Econometrics](https://ideas.repec.org/a/eee/econom/v244y2024i2s030440762400068x.html)
- Montiel Olea, Plagborg-Møller, Qian and Wolf wrote "Local Projections or VARs? A Primer for Macroeconomists" for the NBER Macroeconomics Annual 2025. — [arXiv 2503.17144](https://arxiv.org/html/2503.17144)
- **r-star estimates**
  - The NY Fed updated HLW estimates through 2024Q4 for the US, Canada and the euro area, with charts and replication code. — [NY Fed Research on X](https://x.com/NYFedResearch/status/1896648847922725040)
  - Williams' August 2025 speech, "All the Stars We Cannot See", makes four points:
    - The GDP-weighted r-star across Canada, the euro area, the UK and the US is about "half of a percent" in early 2025, similar to pre-pandemic levels.
    - Real-time estimates rose only "one-quarter to one-half of a percentage point" between 2018Q3 and 2025Q1, and "the era of low r-star appears far from over".
    - The estimates are "very imprecise and … subject to considerable real-time mismeasurement".
    - Market and survey measures "can give a false sense of precision".
    - [NY Fed speech](https://www.newyorkfed.org/newsevents/speeches/2025/wil250825)
  - A search snippet said the US HLW estimate was 0.8 in 2025Q1, up 0.2 percentage points from 2018Q3. The exact source page was not fetched; it is consistent with Williams' range.
- **Cross-model disagreement (St. Louis Fed, May 2026)**
  - A six-model geometric mean put r-star at 1.43% in 2025Q4, near its post-GFC high. The six models are HLW, LW, Lubik-Matthes, D'Amico-Kim-Wei, Zaman and 10Y10Y TIPS.
  - HLW was "a little less than 1%", the lowest, while 10Y10Y TIPS was "a little more than 3%".
  - The FOMC March 2026 SEP longer-run funds rate of 3.1% implies r* ≈ 1.1%.
  - [St. Louis Fed](https://www.stlouisfed.org/on-the-economy/2026/may/comparing-fomc-estimate-r-star-alternative-estimates)
- The NY Fed (Aug 2026) estimates that bond investors' 95% bands on r-star are about ±170 bp. — [Liberty Street Economics 2026](https://libertystreeteconomics.newyorkfed.org/2026/08/a-window-into-bond-investors-uncertainty-about-r-star/). The NY Fed also asked whether financial markets are good predictors of r-star. — [LSE Aug 2025](https://libertystreeteconomics.newyorkfed.org/2025/08/are-financial-markets-good-predictors-of-r-star/)
- The Bank of Finland ran a modified HLW model. — [BoF Bulletin 2024](https://www.bofbulletin.fi/en/2024/articles/recent-insights-into-r-star-an-analysis-using-a-modified-holston-laubach-williams-model/)

### Inferences
- HLW is the single best "frontier but implementable" item for a FRED dashboard. The NY Fed publishes code (R) and estimates. The inputs are GDP, core PCE inflation, the fed funds rate and inflation expectations, all on FRED. The dashboard should display the cross-model range (HLW < 1% vs TIPS > 3%) to teach uncertainty.
- A small BVAR (Minnesota prior) on GDP, PCE inflation, unemployment and fed funds is trivially implementable in Python and is the methodologically recommended default per Li-Plagborg-Møller-Wolf. Local projections (Jordà) are simple OLS and can be shown side by side to illustrate the bias-variance trade-off.

### Gaps
- I did not fetch the NY Fed HLW page directly, so the exact latest 2026 HLW value, the code language and the update date are unverified. The NY Fed historically provides R code.
- Specific Python BVAR packages were not sourced in this session.

## 6. Fiscal theory of the price level (FTPL) and fiscal dominance, 2024–2026

### Takeaway
FTPL (Cochrane's 2023 book; Leeper's active/passive framework) gained traction as an explanation of 2021–22 inflation following large unfunded fiscal transfers. In 2025–26, fiscal dominance moved into mainstream policy debate amid US deficits of about 6% of GDP, net interest of about $1 trillion, and political pressure on the Fed. Yellen said in January 2026 that "the preconditions for fiscal dominance are clearly strengthening", although most economists say it has not arrived.

### Cited Findings
- FTPL says the price level adjusts so that the real value of government liabilities equals the present value of future primary surpluses. Inflation becomes fiscal when fiscal policy is "active" and monetary policy "passive" (Leeper 1991; Woodford 2001; Cochrane 2021/2023). — [Cochrane, FTPL short version](https://static1.squarespace.com/static/5e6033a4ea02d801f37e15bb/t/63cc7978b155d84db08b065c/1674344828516/fiscal_theory_short_website.pdf); [Princeton UP book](https://press.princeton.edu/books/hardcover/9780691242248/the-fiscal-theory-of-the-price-level)
- A 2025 constructive critique of FTPL from the Flossbach von Storch Research Institute calls the theory "particularly timely" given high deficits and high inflation. — [FvS Research Institute 2025](https://www.flossbachvonstorch-researchinstitute.com/en/studies/detail/a-constructive-critique-of-the-fiscal-theory-of-the-price-level)
- At the AEA meetings and Brookings on 4 Jan 2026, Yellen said "the preconditions for fiscal dominance are clearly strengthening". She added that without action on primary deficits, "the temptation to rely on inflation or financial repression to reduce the debt burden will surely grow". — [Brookings, Yellen remarks](https://www.brookings.edu/articles/remarks-by-janet-l-yellen-on-the-future-of-the-fed-central-bank-independence-and-fiscal-dominance/); [Bloomberg](https://www.bloomberg.com/news/articles/2026-01-04/yellen-warns-of-growing-fiscal-dominance-threat-to-us-economy)
- CBO projects a FY2026 deficit of about $1.9 trillion (about 5.8% of GDP), with net interest about $1 trillion. This figure comes from secondary search snippets, not the CBO directly. — [Tax Project Institute explainer](https://taxproject.org/fiscal-dominance/)
- Brookings asked whether the Fed should cut rates to lower federal borrowing costs. — [Brookings](https://www.brookings.edu/articles/should-the-fed-cut-interest-rates-to-make-it-cheaper-for-the-federal-government-to-borrow/)
- An academic revisit of Sargent-Wallace "unpleasant arithmetic" for the modern era is available. — [Webb, LSE](https://www.lse.ac.uk/finance/assets/documents/faculty-papers/WebbFiscal.pdf). Implications of fiscal dominance for bond markets are covered in [Plantin, ARFE](https://www.gplantin.net/ARFE_final.pdf).

### Inferences
- FTPL is not a forecasting model. For a dashboard, it maps to educational indicators on FRED: the debt/GDP and primary-deficit path, the interest-to-revenue ratio, and the real interest rate minus growth (r−g) gap, which drives debt dynamics.
- An "r−g debt dynamics" panel is fully implementable on FRED, for example with GFDEGDQ188S, FYOINT and GDP.

### Gaps
- I did not verify the CBO numbers at the primary source.
- Specific 2025–26 academic estimates of whether the 2021–22 US inflation was fiscal (FTPL-based decompositions) were not found in this session.
