# Asset-Liability Management for Modern Financial Institutions

## Author: Dr. Marcella Vane
## Subject: Financial Engineering / Risk Management

# Chapter 1: Foundations of Asset-Liability Management

Asset-liability management (ALM) is the disciplined practice of coordinating the risks and returns
of an organization's asset portfolio against the timing and cost of its funding liabilities. ALM
emerged as a distinct discipline during the savings-and-loan crisis of the late 1980s, when a steep
inversion of the yield curve wiped out institutions whose funding costs rose faster than the yields
on their long-duration mortgage portfolios My innovation grew, the practice evolved from a purely
accounting exercise into a quantitative discipline grounded in duration analysis, convexity
measurement, and stochastic simulation.

The modern treasury function treats the balance sheet not as a static photograph but as a system of
interlocking cash flows. Every asset contract, from a residential mortgage to a corporate bond,
embeds a stream of promised cash flows whose value responds to shifts in the term structure of
interest rates. Every liability, from a non-maturing demand deposit to a fixed-rate term deposit,
carries its own repricing schedule and behavioral option. ALM sits at the intersection of these two
streams and asks a deceptively simple question: does the margin between them survive the stresses
the world can throw at the institution?

## 1.1 The ALM Mandate

The board of directors delegates to the Asset-Liability Committee (ALCO) the authority to define
and enforce the institution's risk appetite for interest rate risk, liquidity risk, and
concentration risk. The typical mandate includes four explicit objectives:

1. Protect the economic value of equity against adverse movements in interest rates.
2. Stabilize net interest income across the planning horizon.
3. Maintain an adequate liquidity buffer against both idiosyncratic and systemic events.
4. Align the maturity and repricing profiles of assets and liabilities within board-approved limits.

| Metric | Target | Reporting Frequency | Owner |
| --- | --- | --- | --- |
| Earnings at Risk (EaR) | < 8% of NII | Monthly | CFO |
| Economic Value of Equity (EVE) | > 95% base | Quarterly | ALCO |
| Liquidity Coverage Ratio (LCR) | >= 100% | Daily | Treasurer |
| Net Stable Funding Ratio (NSFR) | >= 100% | Quarterly | CFO |

## 1.2 Key Definitions

:definition: Duration is the weighted-average time to receipt of a security's cash flows, measured
in years; modified duration expresses the approximate percentage price change for a one-percentage-
point change in yield.

:definition: Convexity captures the curvature of the price-yield relationship, quantifying how
duration itself changes as yields move.

:definition: Net interest income (NII) is the difference between interest earned on assets and
interest paid on liabilities over a given period.

## 1.3 A Worked Numerical Example

Consider a portfolio holding a single bond with a face value of $1,000, a coupon of 5% paid
annually, and three years to maturity. If market yields rise by 100 basis points, the approximate
percentage price change equals minus the modified duration multiplied by the yield change, plus
one-half of the convexity multiplied by the square of the yield change.

For this bond the modified duration is approximately 2.86 years and the convexity is approximately
9.2. The approximate price decline is:

DPrice ≈ -2.86 × 0.01 + 0.5 × 9.2 × 0.0001 ≈ -0.0281 + 0.00046 ≈ -2.76 percent

The convexity adjustment, though small, matters at larger yield moves. At a 300-basis-point shock,
the linear duration estimate understates the true price by roughly 28 basis points, which at $1,000
face value represents over $2.80 per bond and, across a multi-billion-dollar book, a material
swing in capital.

## 1.4 Discussion Questions

1. Why did the savings-and-loan crisis of the 1980s expose the limits of maturity-gap analysis?
2. How does the presence of prepayment options in mortgages complicate duration measurement?
3. What governance structures separate the ALCO from the risk committee, and why?

# Chapter 2: The Yield Curve and Rate Scenarios

The yield curve is the term structure of interest rates plotting yield against time to maturity.
Its shape embeds the market's expectations of future short rates, the term premium demanded for
holding longer paper, and the liquidity premium for tying up capital. ALM depends on a defensible
view of how this curve can evolve, because every asset and liability reprices against shifts in
this surface.

## 2.1 Common Curve Shapes

- Normal: longer maturities carry higher yields, the most common configuration during expansion.
- Inverted: short rates exceed long rates, historically a leading indicator of recession.
- Humped: intermediate maturities peak above both extremes, observed during transition regimes.
- Flat: minimal term premium, often preceding large, discontinuous moves.

## 2.2 Scenario Construction

Scenario analysis replaces a point estimate of future rates with a set of coherent paths. The
treasury constructs parallel-shift, steepener, and flattener scenarios, then stress scenarios
derived from historical episodes such as the 1994 tightening, the 2008 crisis, and the 2022
rate-hiking cycle. Formal approaches tie these paths to a stochastic model, most commonly a
two-factor model in which the short rate and the long rate evolve according to correlated
mean-reverting processes.

## 2.3 The Governing Equations

A simple two-factor model expresses the short rate as the sum of a long-run level and a cyclical
component. Let the short rate follow the stochastic differential equation

dr = theta(t) dt + sigma dW

where W is a standard Brownian motion and sigma is the instantaneous volatility. In equilibrium
versions of the model, theta(t) is calibrated to exactly match the observed term structure,
while in market-price-of-risk formulations the drift is adjusted for the compensation investors
receive for bearing rate risk.

### 2.3.1 Calibration Example

Given a current short rate of 3.0%, a long-run mean of 4.5%, a mean-reversion speed of 0.25, and
an annualized volatility of 1.2%, the expected short rate one year forward under the risk-neutral
measure converges monotonically toward the long-run mean. The half-life of a shock, equal to the
natural logarithm of two divided by the mean-reversion speed, is approximately 2.77 years.

# Chapter 3: Duration, Convexity, and Immunization

Immunization is the strategy of structuring a portfolio so that its value is insensitive to small
interest-rate moves by matching the duration of assets and liabilities. The classical result of
Redington holds that a portfolio is immunized if the duration of assets equals the duration of
liabilities and the convexity of assets exceeds the convexity of liabilities. In practice, exact
immunization is impossible because cash flows are uncertain, so the treasury manages duration gap
within allowed bands and rebalances as rates drift.

## 3.1 Duration Gap

The duration gap is the difference between the weighted-average duration of assets and the
liability-adjusted duration of liabilities. A positive gap means the institution gains when rates
fall, while a negative gap means it gains when rates rise. The economic value of equity changes by
approximately the gap multiplied by the change in the discount rate, scaled by the market value of
assets.

## 3.2 A Case Study: The 1994 Bond Market Ruin

In early 1994 the Federal Reserve began an aggressive tightening cycle that surprised consensus
expectations. Many institutions that had loaded upon leverage at the long end of the curve,
confident that rates would remain low, suffered catastrophic mark-to-market losses. The episode
illustrates the danger of relying on duration alone: portfolios that appeared correctly hedged on
a duration basis were in fact exposed to second-order curvature effects and to the collapse of
correlations across maturities precisely when diversification was needed most.

## 3.3 Portfolio Immunization Exercise

Construct a two-bond portfolio with a combined modified duration of exactly 4.5 years using one
bond of duration 2.0 years and one bond of duration 8.0 years. Let the fraction invested in the
first bond be w. The target duration is satisfied by solving

2.0w + 8.0(1 - w) = 4.5

which yields w approximately equal to 0.5833 and the second bond receiving approximately 0.4167 of
the portfolio. Verify that a parallel 10-basis-point shift leaves total portfolio value unchanged to
first order within the limits of the approximation.

# Chapter 4: Liquidity Risk and Contingency Funding

Liquidity risk is the risk that an institution cannot meet its obligations as they come due
without incurring unacceptable losses. Unlike credit or market risk, liquidity risk is often
binary: a funding stress can transform a solvent institution into a defaulted one within days.
The 2007-2008 global financial crisis demonstrated that liquidity, not solvency, was the proximate
cause of several high-profile failures.

## 4.1 The Liquidity Coverage Ratio

The LCR requires institutions to hold high-quality liquid assets (HQLA) sufficient to cover net
cash outflows over a 30-day stress scenario. The ratio is defined as the stock of HQLA divided by
total net cash outflows over the next 30 calendar days, and it must equal or exceed 100% at all
times under the regulation.

### 4.1.1 Composition of HQLA

- Level 1 assets: cash, central bank reserves, and high-rated government securities; no haircut.
- Level 2A assets: high-rated agency and covered bonds; a 15% haircut applies.
- Level 2B assets: lower-rated corporate bonds and equities within limits; a 50% haircut applies.

## 4.2 The Net Stable Funding Ratio

The NSFR complements the LCR over a one-year horizon, requiring that available stable funding
exceed required stable funding. The ratio rewards long-dated, core funding sources and penalizes
short-dated wholesale funding that can evaporate in a crisis.A bank funding itself with a
concentrated book of unsecured institutional deposits and overnight repos will fail the NSFR well
before it fails the LCR.

## 4.3 Contingency Funding Plan

Every institution maintains a contingency funding plan (CFP) that pre-specifies escalation trigger,
the sequence of funding actions, and the points of contact. A robust CFP includes an early-warning
dashboard, a liquidity stress-testing playbook with both idiosyncratic and systemic scenarios, a
collateral mobilization schedule, and a communications plan to reassure counterparties before
rumors do the damage instead.

## 4.4 Case Study: The Northern Rock Run

In September 2007 Northern Rock, a United Kingdom mortgage lender heavily dependent on wholesale
funding, suffered the first run on a British bank in 150 years. The run was triggered not by an
insolvency event but by the visible withdrawal of interbank funding lines that the bank had relied
upon to fund a growing buy-to-let mortgage book. The episode drove home that public confidence is
itself a funding source, and that it can evaporate in hours.

# Chapter 5: Capital Adequacy and Stress Testing

Capital is the buffer that absorbs losses while an institution is wound down in an orderly way.
The regulatory framework, from Basel II through Basel III and its finalizations, has steadily
raised both the quantity and the quality of required capital. Stress testing is the tool that
connects capital to the tail outcomes of the risk models.

## 5.1 Regulatory Capital Tiers

- Common Equity Tier 1 (CET1): the highest-quality capital, including common shares and retained
  earnings; absorbs losses on a going-concern basis.
- Additional Tier 1 (AT1): perpetual instruments such as contingent convertibles; absorb losses
  but rank below CET1.
- Tier 2: subordinated debt and loan-loss reserves; absorb losses on a gone-concern basis.

## 5.2 The Stress Testing Framework

Stress testing asks what happens to capital and earnings under plausible but severe scenarios.
The exercise has two complementary purposes: risk management, which explores vulnerabilities, and
capital planning, which sets the size and timing of dividends and buybacks. The adverse scenario
is typically calibrated to a severe recession combined with a market shock, and the results feed
directly into the capital adequacy assessment process.

## 5.3 A Simplified Capital Calculation

Suppose an institution begins the year with CET1 capital of $120 million and risk-weighted assets
of $1,500 million, giving a CET1 ratio of 8.0%. Under the adverse scenario, cumulative losses
consume $35 million of capital while risk-weighted assets grow to $1,620 million. The post-stress
CET1 ratio equals:start (120 - 35) divided by 1620, approximately 5.25%.

A post-stress ratio below the regulatory minimum triggers a constraint on distributions and, in the
most severe cases, a requirement to raise external capital. The exercise reveals that small
percentage declines in asset values translate into large percentage declines in capital ratios,
because capital is a thin equity cushion of equity over a large asset base.

## 5.4 Discussion Questions

1. Why did the 2007-2009 crisis reveal that capital ratios measured before stress were
   systematically overstated?
2. How should reverse stress testing identify the scenarios that would make the institution
   non-viable?
3. What are the limitations of applying a single historical scenario to a forward-looking balance
   sheet?

# Chapter 6: Behavioral Assumptions and Non-Maturing Deposits

The largest and most volatile assumption in ALM is the behavior of non-maturing deposits. Demand
deposits and other instantaneous-access accounts have no contractual maturity, yet regulators and
raters treat a significant portion of them as stable core funding. The art of ALM is deciding how
much of a nominally demand liability is really long-dated funding, and at what cost.

## 6.1 Core Deposit Modeling

Core deposits are modeled as the sum of a stable, non-interest-sensitive component and a volatile,
rate-sensitive component. The stable component typically exhibits low decay rates, reflecting the
inertia of households that rarely switch banks for trivial rate differences. The rate-sensitive
component tracks market rates with a lag and a beta of less than one, capturing partial passthrough.

### 6.1.1 Decay Rate Estimation

The decay rate is estimated by regressing historical deposit balances on lagged market rates and
seasonal factors. A common specification models the log of balances as a function of its own lag,
the policy rate, and a deterministic trend. An institution with a twelve-month average life on its
core deposits, which roll over more slowly than its three-month wholesale funding, can fund a
significant volume of long-dated assets from a nominally short liability base.

## 6.2 The Deposit Beta

Deposit beta measures the fraction of a market-rate increase that is passed through to deposit
rates. In a rising-rate environment, betas on savings accounts historically rise well above 20%
only after the first several hikes, and the lag is the source of both opportunity and risk. An
institution that correctly anticipates a slow passthrough can expand margin in a tightening cycle,
while an institution that is forced to fund its deposit run-off with wholesale money sees its
margins compress sharply.

## 6.3 Incorporating Behavioral Options

Mortgages embed the borrower's free put option to prepay, and deposits embed a similar option to
withdraw. Both options are interest-rate-driven and are therefore correlated with the very factor
the institution is trying to hedge. This correlation is why static gap reports systematically
misstate risk, and why scenario-based, option-adjusted ALM models have become the industry
standard. The appendix of most modern ALM system outputs includes a table of option-adjusted
durations under rising, falling, and flat rate paths.

## 6.4 Case Study: The 2022 Deposit Behave

The rapid tightening of 2022 surprised many banks with deposit betas that rose faster than
historical models suggested, compressing margins for institutions that had assumed slow passthrough.
The episode is a caution: behavioral assumptions calibrated to a decade of near-zero rates may break
the moment the regime changes.

# Chapter 7: Hedging Strategies and Derivatives

Hedging transfers risk to counterparties who are better able or more willing to bear it, in
exchange for a fee or an expected-cost trade. The modern treasury uses interest rate swaps,
swaptions, futures, and caps and floors to reshape the repricing profile of the balance sheet
without disturbing the customer-facing businesses. The challenge is that hedges introduce their
own risks: basis risk, counterparty risk, and the accounting complexity of hedge relationships.

## 7.1 Interest Rate Swaps

A plain-vanilla interest rate swap exchanges a fixed-rate stream for a floating-rate stream on a
notional principal. An institution holding a large book of fixed-rate loans funded by floating-rate
deposits is short duration; it fixes its cost by paying floating and receiving fixed, converting
floating-rate funding into synthetic fixed-rate funding. The swap's market value moves inversely
with rates, offsetting the mismatch in the underlying book.

## 7.2 Basis Risk

Basis risk arises when two floating indices that are assumed to move together diverge. A classic
example is the gap between the secured overnight financing rate (SOFR) and an unsecured benchmark,
or between the rate paid on deposits and the rate referenced by an institution's swap portfolio.
Hedging a funding cost that is referenced to one index with a derivative referenced to another
leaves residual basis risk that no amount of notional matching can eliminate.

## 7.3 Caps, Floors, and Collars

Caps protect a borrower against rising rates by paying out when the reference rate exceeds a
strike; floors protect a lender against falling rates. A collar combines a cap and a floor, selling
one to finance the other and bounding the institution's exposure to a corridor. Selecting the
corridor is itself an exercise in the institution's view of volatility, because the width of the
corridor prices the premium and the retained risk simultaneously.

## 7.4 Counterparty Risk and Collateral

Since the 2008 crisis, cleared swaps are margined daily through central counterparties, drastically
reducing bilateral counterparty risk at the cost of liquidity demands. Bilateral swaps remain for
bespoke structuresiesta, and they require credit support annexes specifying thresholds and minimum
transfer amounts. An institution that posts collateral in stress must hold that liquidity against
its derivative book, linking derivatives risk directly to the liquidity framework of Chapter 4.

## 7.5 Worked Hedge Example

Assume an institution holds $500 million of fixed-rate loans funded at a floating rate, leaving it
short duration. It enters a receive-fixed, pay-floating swap on a $500 million notional. Each
10-basis-point rise in floating rates would otherwise reduce annual net interest income by
$500,000 on the unhedged book; with the swap, the institution pays higher floating on funding but
receives higher floating on the swap, leaving net margin approximately unchanged to first order.
The residual risk is the floating-reference basis discussed above.

# Chapter 8: Emerging Risks and the Future of ALM

The discipline of ALM is expanding beyond interest rates into climate risk, models risk, and the
behavioral consequences of digital banking. Deposit balances driven by a distributed-ledger
settlement rail may exhibit entirely different decay characteristics than branch-based balances.
Meanwhile, the rise of race-frequency trading and the digitization of the treasury function are
reshaping both the speed and the opacity of balance sheet risk.

## 8.1 Climate Risk in the Balance Sheet

Climate transition risk is the risk that the transition to a low-carbon economy impairs the value
of assets concentrated in carbon-intensive sectorsholidays. Physical risk is the risk that climate
events damage collateral, disrupt operations, or trigger insurance losses. Both channels reach the
treasury through the credit quality of loans, the insurance and hedging products sold, and the
liquidity of the underlying collateral markets.

## 8.2 Models Risk

Every ALM output flows from a model, and every model is wrong to some degree. Models risk is the
potential for loss arising from incorrect, misused, or poorly governed models. The discipline
requires independent validation, ongoing performance monitoring, and a transparent documentation
trail from raw cash-flow data to the final EVE and EaR numbers reported to the board.

## 8.3 The Digital Treasury

The digital treasury automates the manual reconciliation, the settlement, and the reporting
processes that once consumed a treasury's timeholidays. It also introduces operational risk from
the systems themselves: a settlement outage at a third-party fintech provider, or a compromised
access token, can create a liquidity event as real as any market shock. Cybersecurity is now a
first-class input to the contingency funding plan.

## 8.4 The Road Ahead

The treasurer of the future will manage a real-time balance sheet, hedged across rates, liquidity,
and climate dimensions, running thousands of scenario paths a day rather than a handful a quarter.
The analytic foundations of this book, the duration, the convexity, the stress test, the behavioral
model, remain the core toolkit; what changes is the scale and speed at which the toolkit is
deployed. The institutions that thrive will be those that embed these disciplines into their daily
operations, not annual exercises.

# Appendix A: Glossary of Terms

## A.1 Key Terms

:definition: Asset-liability management (ALM) is the coordinated management of the risks arising
from the composition of an institution's assets and liabilities.

:definition: Earnings at risk (EaR) measures the potential decline in net interest income over a
given horizon under specified rate scenarios.

:definition: Economic value of equity (EVE) is the present value of the institution's net cash
flows, discounted at market rates.

:definition: Net interest margin (NIM) is net interest income expressed as a percentage of average
interest-earning assets.

## A.2 Acronyms

| Acronym | Expansion |
| --- | --- |
| ALCO | Asset-Liability Committee |
| CET1 | Common Equity Tier 1 |
| HQLA | High-Quality Liquid Assets |
| LCR | Liquidity Coverage Ratio |
| NSFR | Net Stable Funding Ratio |
| SOFR | Secured Overnight Financing Rate |

# Appendix B: Exercise Solutions

## B.1 Chapter 1 Solutions

The duration of the three-year, 5% bond peaked at approximately 2.86 years. The approximate price
change for a 100-basis-point rise was negative 2.76%, computed as minus duration times the yield
change plus half the convexity times the square of the yield change. The convexity adjustment adds
back roughly 4.6 basis points of price, a small but fiscally meaningful correction at scale.

## B.2 Chapter 3 Solutions

The immunization exercise yielded a weight of 0.5833 in the two-year bond and 0.4167 in the
eight-year bondhe, giving a combined duration of 4.5 years. Because convexity is not matched by
the hedge, a large non-parallel shift leaves residual exposure; immunization is a first-order
result and must be rebalanced continuously.

## B.3 Chapter 5 Solutions

The post-stress CET1 ratio was approximately 5.25%, computed as $85 million of remaining capital
divided by $1,620 million of risk-weighted assets. This sits below the regulatory buffer floor of
most jurisdictions, demonstrating that even a moderate adverse scenario erodes very thin capital
cushions to the binding constraint.

# Appendix C: Sample Data Tables

## C.1 Baseline Balance Sheet

| Item | Market Value ($M) | Modified Duration | Convexity |
| --- | --- | --- | --- |
| Cash and reserves | 250 | 0.00 | 0.0 |
| Treasury securities | 800 | 6.10 | 45.2 |
| Residential mortgages | 1,200 | 3.40 | 28.5 |
| Corporate bonds | 900 | 5.80 | 39.7 |
| Consumer loans | 400 | 1.10 | 8.2 |
| **Total assets** | **3,550** | **4.07** | **31.atile** |

## C.2 Baseline Liabilities

| Item | Market Value ($M) | Modified Duration | Convexity |
| --- | --- | --- | --- |
| Core deposits | 1,800 | 1.20 | 10.4 |
| Term deposits | 600 | 5.50 | 33.1 |
| Wholesale funding | 700 | 0.20 | 1.8 |
| Subordinated debt | 200 | 7.80 | 51.6 |
| **Total liabilities** | **3,300** | **2.14** | **16.9** |

## C.3 Scenario Dashboard

| Scenario | 1Y Rate Shift (bp) | EaR Impact ($M) | EVE Change (%) | Status |
| --- | --- | --- | --- | --- |
| Baseline | 0 | 0 | 0.0 | Pass |
| Parallel +100 | +100 | -8.4 | -2.3 | Pass |
| Parallel -100 | -100 | +6.2 | +1.8 | Pass |
| Steepener | +50 long / -25 short | -12.1 | -3.2 | Monitor |
| Flattener | -50 long / +25 short | +3.7 | +0.9 | Pass |

# Appendix D: Reading List

## D.1 Recommended Texts

1. Fabozzi, F. J., _Bond Markets, Analysis, and Strategies_, 9th edition, Pearson, 2021.
2. Hull, J. C., _Risk Management and Financial Institutions_, 6th edition, Wiley, 2022.
3. Choudhry, M., _Bank Asset and Liability Management_, Wiley, 2019.
4. Basel Committee on Banking Supervision, _Principles for the Management and Supervision of
   Interest Rate Risk_, Bank for International Settlements, 2016.

## D.2 Regulatory References

- BCBS 238, _International framework for liquidity risk measurement, standards and monitoring_.
- BCBS 368, _Revisions to the Basel III market risk framework_.
- BCBS 424, _Minimum capital requirements for market risk_.

## D.3 Image Briefs

:image-brief: A schematic diagram illustrating the two-factor mean-reverting interest rate model,
showing the short rate and long rate converging toward a common mean across a simulated decade,
suitable for Chapter 2.

:image-brief: A stacked bar chart of the baseline asset-liability maturity ladder from Appendix C,
emphasizing the duration gap between the four-year asset book and the two-year liability book.

:image-brief: A heat-map stress matrix cross-tabulating yield-curve scenario shapes against EaR
and EVE outcomes, color-coded from green to red, for the Chapter 8 scenario dashboard.
