# Merger Arbitrage: Capturing the Deal Spread After Announcement

## 1. Statement of the Idea

Companies A and B will announce a merger. On the announcement, buy stock in the target and
hold to close, capturing the difference between the market price immediately after
announcement and the consideration payable at completion. In a stock-for-stock deal, the
position is paired with a short in the acquirer at the exchange ratio. The return is the
deal spread, earned over the time to completion, conditional on the deal actually closing.

The premise contains an assumption that must be made explicit before any work begins: the
plan is a plan for trading *announced* deals. Positioning ahead of an announcement on the
basis of knowledge that a merger is forthcoming is not a research programme; where such
knowledge is material and non-public it is unlawful. This project therefore begins at the
public announcement and treats the announcement timestamp as the earliest permissible
entry.

## 2. Economic Rationale

The spread that persists after announcement is compensation for four things, and a serious
strategy is a strategy for pricing each of them:

1. **Deal break risk.** The probability the transaction fails — financing withdrawn,
   regulators block it, shareholders vote it down, a material adverse change is invoked,
   the acquirer walks. On a break, the target typically falls sharply toward, and often
   below, its pre-announcement level. The payoff is therefore explicitly asymmetric: a
   small, capped gain against a large, uncapped loss.
2. **Time value.** Capital is committed for a period whose length is itself uncertain.
   Regulatory review can extend a three-month deal into an eighteen-month one, and the
   annualised return collapses even when the deal ultimately closes.
3. **Terms risk.** Consideration may be revised, a competing bid may emerge (favourably),
   or the acquirer's stock may move in a stock deal such that the realised consideration
   differs from the announced one.
4. **Liquidity and crowding.** The trade is well known and heavily populated. When the
   sector's positioning unwinds, spreads widen across all live deals simultaneously,
   independent of any individual deal's merits.

The strategy is therefore closer to underwriting insurance than to forecasting prices. Its
expected return is a premium; its risk is a correlated tail. The research question is
whether we can price break probability better than the market's implied estimate, or
whether we can construct the portfolio such that the premium is harvested with tolerable
tail exposure.

## 3. Hypotheses

- **H1 (unconditional premium).** A portfolio of announced deals, entered after
  announcement and held to resolution, earns a positive return in excess of the risk-free
  rate over a long sample.
- **H2 (implied probability quality).** The market-implied break probability, backed out
  from the spread and an estimate of the downside on break, is a biased estimate of the
  realised break frequency — and the direction and magnitude of the bias is the source of
  edge, if any.
- **H3 (predictability of breaks).** Break probability is predictable from observable deal
  characteristics at announcement: consideration type, financing condition, regulatory
  overlap and jurisdiction count, premium offered, target and acquirer size ratio, hostile
  versus agreed status, presence of a go-shop, break fee size, and the acquirer's history.
- **H4 (timing structure).** Spread returns are not earned uniformly over the deal's life;
  they are concentrated around resolution of specific milestones (regulatory clearance,
  shareholder vote, financing confirmation), and entering after a milestone is materially
  different from entering at announcement.
- **H5 (entry timing).** Entering immediately at announcement versus after the initial
  price discovery period produces materially different risk-adjusted returns, and the
  execution cost of the immediate entry is significant.
- **H6 (correlated tail).** Deal spreads across live transactions co-move, particularly in
  risk-off environments and following high-profile regulatory interventions, so a
  many-deal portfolio is far less diversified than a naive count of positions suggests.
- **H7 (economic significance).** After costs, borrow on the acquirer leg, financing, and
  the realised tail, the strategy delivers a return per unit of risk that justifies the
  capital and the tail exposure.

## 4. Data and Infrastructure Requirements

- **Complete, survivorship-free deal database**, covering both completed and failed
  transactions, with point-in-time fields: announcement timestamp, initial terms,
  every subsequent amendment with its date, consideration structure, conditions precedent,
  break fee, financing arrangements, regulatory filings required, and final outcome with
  its date. Missing failed deals would invert the entire conclusion, so this is the
  study's single most important data dependency.
- **Point-in-time regulatory milestone data**: filing dates, second requests or equivalent,
  clearance dates, litigation events, and jurisdictional approvals.
- **Daily and intraday prices for target and acquirer**, adjusted, from before announcement
  through resolution, including the break-day price path.
- **Borrow availability and cost** for acquirer shorts, historical. In stock deals the
  short leg is essential and its cost is a direct deduction from the spread.
- **Options data** on target and acquirer where available, for market-implied probability
  cross-checks and for potential hedged expressions.
- **Corporate action and index membership data**, point-in-time, since targets are removed
  from indices at completion with attendant flows.
- **Financing rates** for the holding period, to compute return on committed capital
  correctly.
- **A compliance-approved definition of the permissible entry time**, tied to public
  announcement, with an auditable rule and a documented review.

## 5. Strategy Construction

**Universe.** All announced transactions meeting minimum size, target liquidity, and
listing criteria, in specified jurisdictions. Filters are defined ex ante and never
adjusted on the basis of returns.

**Position.**
- Cash deals: long the target, sized by the spread and by an estimate of downside on break.
- Stock deals: long the target, short the acquirer at the exchange ratio, with the ratio
  updated per the terms including any collar mechanics.
- Mixed and contingent consideration: modelled explicitly; deals whose structure cannot be
  modelled are excluded, and the exclusions are reported.

**Break probability model.** A model estimating the probability of completion from
announcement-date characteristics (H3), updated at observable milestones (H4). Estimated
on a training period only, with strict point-in-time features.

**Expected return per deal.** Spread, adjusted for the modelled probability of break, the
modelled downside on break, the expected time to completion, and all costs. The strategy
takes positions where this expected return exceeds a threshold, rather than taking every
deal.

**Sizing.** Inverse to modelled break risk and to estimated downside, capped per deal, per
sector, per acquirer, and per regulatory jurisdiction — the last because a single agency's
posture can impair many deals at once.

**Portfolio-level constraints.** Limits on aggregate exposure to any one regulatory
regime, on total gross exposure, and on the concentration of expected loss in a stress
scenario where an assumed fraction of live deals break simultaneously.

## 6. Experimental Design

**Stage 0 — Deal database validation.** Reconcile the deal universe against an independent
source for a sample of periods. Specifically measure the completeness of *failed* deals,
by checking a list of known break events against the database. Report coverage. If failed
deals are under-represented, everything downstream is invalid and the study stops here.

**Stage 1 — Unconditional characterisation.** Distribution of spreads at announcement,
realised time to completion, realised break frequency by year, and the price path on
break. Descriptive, but it establishes the two parameters — break rate and downside on
break — that dominate every subsequent calculation.

**Stage 2 — Implied versus realised break probability.** Back out implied break probability
from announcement spreads using the empirical downside distribution. Compare to realised
frequency, overall and by deal characteristic. This tests H2 and is the cleanest single
test of whether an edge exists at all.

**Stage 3 — Break prediction model.** Fit and validate the model of H3 on training data,
with purged, embargoed validation. Evaluate on discrimination and calibration; calibration
matters more, because the strategy uses the probability as a price rather than as a rank.

**Stage 4 — Milestone dynamics.** Estimate the spread's evolution around regulatory and
shareholder milestones. Test H4 and evaluate whether a milestone-conditional entry policy
dominates announcement entry.

**Stage 5 — Entry execution study.** From intraday data, measure the achievable entry price
in the hours after announcement, at realistic participation rates, and its dependence on
target liquidity. Test H5. This determines how much of the theoretical spread survives
contact with the market.

**Stage 6 — Portfolio backtest.** Full simulation with the model, sizing, constraints,
borrow costs, financing and execution costs. Walk-forward. All model fitting strictly
point-in-time.

**Stage 7 — Tail and correlation analysis.** Measure realised co-movement of live deal
spreads. Construct stress scenarios: a simultaneous break of the largest positions; a
regulatory regime shift impairing a jurisdiction's deals; a risk-off episode widening all
spreads. Report portfolio loss under each.

**Stage 8 — Holdout.** Single evaluation on an untouched final period against
pre-registered criteria.

## 7. Evaluation Metrics and Pre-Registered Success Criteria

Metrics: annualised return on committed capital net of all costs; realised break rate
versus modelled; model calibration curve; Sharpe and Sortino; maximum drawdown; loss in
each stress scenario; capital efficiency (return per capital-day); borrow cost as a share
of gross spread; and the fraction of return attributable to the largest few deals.

Pre-registered criteria:

- **Go** if net annualised return on committed capital exceeds the risk-free rate by a
  stated margin over the out-of-sample period, with the break prediction model
  demonstrating calibration error below a stated bound.
- **Go** requires that the loss under the pre-specified simultaneous-break stress scenario
  remain within a stated fraction of annual expected return.
- **No-go** if the strategy's return is entirely explained by the unconditional premium —
  that is, if the break model adds nothing over taking every deal — since in that case we
  are being paid for bearing a tail we have no special ability to assess, and the position
  is better sized as a passive allocation than run as a research-driven strategy.
- **No-go** if realised co-movement of deal spreads implies the portfolio's effective
  number of independent bets is below a stated minimum.

## 8. Deliverables and Timeline

- Weeks 1–3: deal database assembly and validation, with particular attention to failed
  deal coverage.
- Week 4: unconditional characterisation.
- Week 5: implied versus realised break probability.
- Weeks 6–8: break prediction model.
- Week 9: milestone dynamics.
- Week 10: entry execution study.
- Weeks 11–13: portfolio backtest.
- Week 14: tail, stress, holdout, recommendation.

---

## Critique of the Plan

### The idea as stated is not what the plan tests, and the gap matters

The seed idea describes buying the target "as soon as the announcement hits" to capture
"the delta between the current market price and the deal premium on closing". That phrasing
treats the spread as a delta to be collected rather than as compensation for risk. The plan
corrects this — it reframes the spread as an insurance premium — but the correction should
be foregrounded more sharply, because the naive framing leads directly to the strategy's
characteristic disaster: sizing positions by expected return without regard to the loss
given break. Any presentation of results should lead with the loss distribution, not with
the annualised spread.

### The break-probability model faces a severe sample-size problem

Break events are rare. Depending on the universe filters, a long sample may contain only
one to two hundred outright failures, spread across decades of shifting regulatory regimes.
The plan proposes fitting a model on announcement characteristics with a substantial feature
list — consideration type, jurisdictions, premium, size ratio, hostility, go-shop, break
fee, acquirer history — and validating it with purged cross-validation. With that many
features and that few positive cases, the model will be badly overfit and its calibration,
which the success criterion depends on, will be unreliable out of sample. The plan needs a
hard constraint on model complexity relative to event count, and it should say up front
what the expected number of break events in the training set actually is. If the answer is
under a hundred, the honest design is a small number of pre-specified risk buckets rather
than a fitted model.

### Regulatory regime is a non-stationarity the design does not handle

Break probability is not a stable function of deal characteristics; it is a function of the
prevailing antitrust and national-security posture, which changes discontinuously with
administrations and with agency leadership. A model fitted across a long history will
average over regimes that no longer exist. Walk-forward validation does not solve this — it
merely ensures the model is fitted to the *previous* regime, which is exactly wrong at the
moment a regime changes, which is exactly when losses cluster. The plan needs either a
regime variable that is observable in real time, or an explicit acknowledgement that the
model's calibration will be worst precisely when it matters most, with sizing that reflects
that.

### Downside on break is treated as a modelled parameter but it is highly variable

Both the implied-probability calculation in Stage 2 and the sizing rule depend on an
estimate of the price on break. In practice this varies enormously: some targets fall to
below their pre-announcement price because the bid revealed that no other buyer exists;
others fall very little because a competing bidder is expected; occasionally a break is
followed by a higher offer. Using a single empirical distribution flattens this, and it
flattens it in the direction that makes the strategy look safer, because the worst cases
are the rarest. Stage 2's implied probabilities inherit the error directly. The plan should
model downside conditionally on deal characteristics, or at minimum report all headline
results under both a median and a pessimistic downside assumption.

### The correlated-tail criterion is the right idea with an unworkable metric

"No-go if the effective number of independent bets is below a stated minimum" correctly
identifies the central portfolio risk. But effective independence for a portfolio of
insurance-like exposures is not well captured by the correlation of spread changes in
normal times, which is what Stage 7 measures. Spreads can co-move mildly day to day and
still break together. What matters is tail dependence, which requires either a structural
model of shared break drivers (same agency, same sector, same financing market) or an
event-based measure counting historical episodes of clustered breaks. The plan's measure
will produce a comfortingly high effective-bet count and understate the real exposure.

### Entry execution is studied but the adverse selection in it is not

Stage 5 measures achievable entry prices in the hours after announcement. It does not
address who is selling to us in those hours. Immediately post-announcement, the sellers
include holders with genuine information about the deal's prospects and event-driven desks
with better regulatory analysis than a systematic model. The measured execution cost
therefore understates the true cost, because part of it is not slippage but adverse
selection that only shows up later in the break rate of the deals we happened to fill in.
A useful diagnostic — absent from the plan — is whether deals where we could fill easily at
a wide spread break more often than deals where the spread closed quickly.

### The no-go on "the model adds nothing" is well-conceived but incomplete

Requiring that the break model beat taking every deal is exactly the right test of whether
research is adding value. But the conclusion drawn — that a passive allocation would be
better — deserves more scrutiny than it gets. A passive merger-arbitrage allocation is
available cheaply in fund form, and if that is the recommendation the project should say so
explicitly and compare against the fee and the capacity of that alternative. Otherwise the
no-go quietly becomes an argument for running the strategy anyway with less justification.

### Fourteen weeks is plausible only if the deal database already exists

Three weeks to assemble a point-in-time, survivorship-free deal database with amendment
history, conditions precedent, regulatory milestones and outcome dates is optimistic unless
this is a licensed vendor product already in the firm's warehouse. If it must be built or
substantially cleaned, that alone is a quarter's work, and the validation step — checking
failed-deal coverage against an independent source — is precisely the kind of task that
uncovers weeks of remediation.

### Capacity is never addressed

There is no capacity analysis anywhere in the plan. Merger arbitrage has a hard capacity
limit set by the float of the target and by the crowd already in the trade, and returns
degrade sharply with size in exactly the deals with the widest spreads, which are the small
and difficult ones. Without a capacity estimate, a positive result cannot be converted into
an allocation decision, and the entire study stops short of the question the firm actually
needs answered.

### What the plan gets right

Refusing pre-announcement positioning and defining announcement as the earliest permissible
entry, with an auditable rule, is the correct and necessary framing. Making failed-deal
coverage the gating check in Stage 0 targets the one data flaw that would invert every
conclusion, and it is the right place to be uncompromising. Reframing the spread as
insurance premium rather than as a delta to be collected changes the sizing logic in a way
that is essential to survival. Backing out implied break probability and comparing it to
realised frequency is the cleanest possible test of whether an edge exists, and placing it
early — before the expensive modelling — is good sequencing. And the no-go on the model
failing to beat the naive all-deals portfolio is an unusually honest criterion to
pre-register.


---

## My Verdict

### Plan

Good refinement to being specific about trading after the announcement of the deal to avoid legal risks, this is an important clarification to ensure a safe research and trading plan.

No capacity analysis is performed for deals which needs resolving before the strategy could be deemed investable given the operational overheads. As it stands, reporting annualised return on committed capital is only part of the equation. Earning 10% on committed capital USD1bn is meaningfully different than a maximum committed capital of USD10mm.

### Critique

The critique accurately highlights a number of areas the plan needs improving.