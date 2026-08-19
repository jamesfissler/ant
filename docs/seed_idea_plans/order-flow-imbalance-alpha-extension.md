# Extending Order Flow Imbalance to Add Incremental Alpha

## 1. Statement of the Idea

Order flow imbalance (OFI) summarises the recent history of order book actions for a
security S — size added and removed at each price level, on each side — into a signed
quantity that forecasts short-horizon forward returns of S. The baseline construction is
well established. The research question here is explicitly an **extension** question: given
a correctly implemented baseline OFI, can we add structure that improves forecasting power
by an amount that is both statistically credible and economically meaningful after costs?

The project therefore has two halves. The first builds an honest, hard-to-beat baseline.
The second attempts a pre-specified set of extensions and measures each strictly as
*incremental* to that baseline. Any extension that cannot beat the baseline out of sample
is discarded, and the discard is reported.

## 2. Economic Rationale

The baseline works because changes in resting liquidity are the visible footprint of the
inventory and information pressures acting on the book. Additions to the bid and
cancellations from the ask both reflect a shift in the willingness to own the asset, and
in a market where price is set by the interaction of that willingness with aggressive
flow, a persistent asymmetry in book *changes* forecasts a persistent drift in price.

The extensions proposed below each rest on a specific claim about information the baseline
discards:

- The baseline weights all levels equally or by a fixed rule, but liquidity far from the
  touch is less likely to be executed and more likely to be cancelled; its informational
  weight should be lower and should depend on volatility, which sets the probability of
  the price reaching it.
- The baseline treats a cancellation as the negative of an addition. They are not
  symmetric: an addition is a commitment, a cancellation is the withdrawal of one, and
  the participants who do each are systematically different.
- The baseline aggregates over a fixed window in wall-clock time. Information arrives in
  event time, and the mapping between the two varies by orders of magnitude across the
  session.
- The baseline is linear. The relationship between flow imbalance and returns is bounded
  at the extremes because extreme imbalance is disproportionately produced by mechanical
  activity rather than by directional conviction.
- The baseline ignores who is acting. Where order attribution or order-size fingerprints
  allow crude participant segmentation, the flow of persistent, patient participants
  should carry different information from the flow of fleeting ones.

## 3. Hypotheses

- **H0 (baseline, to be established, not tested).** A correctly specified OFI over the
  top levels predicts forward returns over horizons from a few hundred milliseconds to
  a minute. This is the control, and the study is not interested in confirming it.
- **H1 (volatility-scaled depth weighting).** Weighting level contributions by the
  probability that price reaches that level, estimated from short-horizon realised
  volatility, improves incremental R² over fixed-weight OFI.
- **H2 (add/cancel asymmetry).** Decomposing OFI into additions, cancellations, and
  executions as three separate signed streams, and allowing them distinct coefficients,
  improves forecasting power over the netted baseline.
- **H3 (event-time normalisation).** Measuring the OFI window in event time (number of
  book updates or trades) rather than wall-clock time improves stability of the
  coefficient across the session and across volatility regimes.
- **H4 (non-linearity).** A saturating transform of OFI outperforms the linear form, and
  the extreme deciles contribute negatively to the linear fit.
- **H5 (participant segmentation).** Where lifetime and size fingerprints allow separating
  fleeting from persistent liquidity, the flow of persistent liquidity has higher
  predictive power per unit of size.
- **H6 (horizon-specific specification).** The best specification differs systematically
  by horizon, so a single OFI is dominated by a small family of horizon-matched signals.
- **H7 (economic significance).** At least one extension survives costs and delivers a
  net improvement in simulated P&L over the baseline, not merely in R².

## 4. Data and Infrastructure Requirements

- **Market-by-order data.** This is not optional for this project. H2 and H5 both require
  identifying individual orders through their lifecycle: place, modify, partial fill,
  cancel. Market-by-price is sufficient for the baseline only, and would reduce the study
  to its uninteresting half.
- **Correctly ordered, single event stream** of all book actions with matching-engine
  timestamps, plus gateway receipt timestamps for tradability work.
- **History**: 24 months, so that model selection, validation and a genuinely untouched
  holdout can each get meaningful, non-overlapping periods including different regimes.
- **Universe**: 20–30 names chosen to span tick-size regimes and liquidity, held fixed
  from the start and never revised on the basis of results.
- **Reference data**: tick sizes, fee schedules including rebate tiers, auction and halt
  calendars, corporate actions, and venue order-type semantics — in particular iceberg
  refresh behaviour, which will otherwise be misread as a stream of genuine additions.
- **Compute**: out-of-core feature generation over the full event stream; expect the
  feature build, not the model fit, to dominate.

## 5. Signal Construction

**Baseline.** For each book update, the level-wise flow contribution on the bid is the
change in size at that price adjusted for price movement of the level itself, and
symmetrically for the ask. Sum over levels `1..L` and over a window `W` to get `OFI_W`.
Standardise by a trailing measure of flow scale. Fix `L` and `W` up front for the baseline.

**Extensions**, each defined as an additive modification with all else held fixed:

- **E1 — volatility-scaled weights.** Weight level `j` by `exp(−d_j / (σ_t √τ))` where
  `σ_t` is a short-horizon realised volatility estimate and `τ` the forecast horizon. The
  weighting therefore tightens in calm markets and widens in fast ones.
- **E2 — action decomposition.** Three streams: signed additions, signed cancellations,
  signed executions. Estimated with separate coefficients rather than netted.
- **E3 — event-time windows.** `W` defined in book updates or in trades rather than in
  milliseconds, with the mapping calibrated per instrument.
- **E4 — saturation.** Rank-transform or apply a bounded transform to the standardised OFI.
- **E5 — liquidity-type segmentation.** Partition flow by the realised or expected order
  lifetime and by size relative to the instrument's typical order size, and fit separate
  coefficients per bucket.
- **E6 — horizon-matched family.** A small set of signals, each with its own `L`, `W`, and
  weighting, one per target horizon, combined by a simple, low-capacity combiner.

Controls in every specification: spread, depth, realised volatility, event intensity,
time of day, and time since last price change. Extensions are always evaluated against a
model that already contains the baseline and these controls.

## 6. Experimental Design

**Stage 0 — Reconstruction and validation.** Rebuild the book from the event stream,
reconcile against venue snapshots, and quantify the incidence of iceberg refreshes and
hidden executions. Freeze the dataset.

**Stage 1 — Baseline establishment.** Fit and document the baseline per instrument and
horizon. Report it as the control. Critically, spend real effort making the baseline
*good*, since a weak baseline makes every extension look successful.

**Stage 2 — Extension screening.** Each extension is fitted on the training period only,
with hyperparameters selected inside a purged, embargoed cross-validation on that period.
The metric is incremental R² over the baseline plus controls.

**Stage 3 — Validation.** Extensions that pass a pre-set screening threshold are evaluated
once on the validation period. No re-tuning is permitted after seeing validation results;
any that occurs must be logged and the affected extension demoted.

**Stage 4 — Combination.** Surviving extensions are combined under a deliberately
low-capacity combiner (ridge, or simple equal weighting of standardised signals). The
combination is compared against the best single extension; if it does not beat it, the
simpler model wins by default.

**Stage 5 — Cost and tradability.** Simulate a trading policy driven by the combined
signal against one driven by the baseline alone. Include spread cost, fees, and a queue-
aware fill model for any passive component. The comparison of interest is *the difference
in net P&L between extended and baseline*, not the absolute P&L of either.

**Stage 6 — Untouched holdout.** A single evaluation on the final holdout period, of the
final specification only, with all criteria pre-registered. This period is not opened
before this stage under any circumstances.

**Stage 7 — Stability and attribution.** Coefficient stability across time and across
instrument groups; decomposition of the improvement by extension, by regime, and by
instrument; and a decay analysis to estimate how quickly the extension's edge erodes.

## 7. Evaluation Metrics and Pre-Registered Success Criteria

Metrics: incremental R² and information coefficient over baseline; net P&L difference per
unit of risk; turnover change; capacity at fixed participation; and the fraction of the
improvement concentrated in the largest single instrument or single month.

Pre-registered criteria:

- **Screening threshold**: an extension advances only if it improves incremental R² over
  baseline by at least a stated minimum in the training CV, in a majority of instruments,
  with consistent sign.
- **Go** if, on the untouched holdout, the final extended signal improves net-of-cost P&L
  per unit risk over the baseline by at least 15%, with the improvement present in at
  least three of four quarters and not concentrated in a single instrument.
- **No-go** if the improvement in R² does not survive cost simulation — a very likely
  outcome for extensions that raise turnover.
- **No-go** if more than half the improvement comes from one instrument or one month.

## 8. Deliverables and Timeline

- Weeks 1–2: reconstruction, validation, iceberg and hidden-liquidity diagnostics.
- Week 3: baseline established and documented.
- Weeks 4–6: extension screening.
- Week 7: validation pass.
- Week 8: combination.
- Weeks 9–10: cost and tradability simulation.
- Week 11: holdout evaluation.
- Week 12: stability, attribution, written recommendation, production feature library.

---

## Critique of the Plan

### The baseline is the load-bearing element and it is under-specified

Every result in this study is a difference against the baseline, which means the baseline's
quality determines the sign of every conclusion. Stage 1 allocates one week and the
instruction to "spend real effort making it good", with no definition of good and no
adversarial process for strengthening it. There is an obvious incentive problem: the same
researcher builds both the baseline and the extensions and is rewarded for the difference.
A weakly-tuned baseline with fixed `L` and `W` versus extensions with hyperparameters
selected by cross-validation is not a fair comparison — it is a comparison of a tuned model
against an untuned one, and it will show improvement even if every extension is worthless.
The baseline must receive the identical hyperparameter search budget as the extensions,
and that equality should be enforced mechanically rather than by intention.

### The extension set is broad enough to guarantee a winner

Six extensions, each with hyperparameters, evaluated across 20–30 instruments and multiple
horizons, is a search space large enough that something will clear any screening threshold
by chance. The plan uses purged cross-validation, which controls leakage but not multiple
comparisons. There is no false-discovery-rate control, no deflated performance metric, and
no accounting for the number of specifications actually tried — which will exceed the six
named extensions once hyperparameters are counted. The "no-go if the improvement doesn't
survive costs" criterion is a partial backstop, but it operates only at the end, after the
selection damage is done.

### Turnover is the likely killer and is treated too late

Several extensions — event-time windows, horizon-matched families, action decomposition —
will produce a faster, noisier signal. Faster signals almost always show higher R² and
lower net P&L, because the R² improvement is concentrated in short-lived moves that cost
the spread to capture. Cost simulation appears at Stage 5, after screening and validation
have already selected extensions on a cost-blind metric. The selection is therefore
optimising the wrong objective for four of the six stages. A cost-aware metric — even a
crude one, such as R² penalised by realised turnover — should be the *screening* metric,
not a final filter.

### Market-by-order raises problems the plan doesn't address

The plan correctly insists on MBO for H2 and H5, but MBO brings its own hazards that are
not mentioned. Order IDs are not always stable across modifies; some venues implement a
price improvement as a cancel/replace that appears as two events; iceberg refreshes appear
as fresh additions from the same underlying parent. The plan flags iceberg diagnostics in
Stage 0, but the diagnostics are only diagnostic — there is no stated policy for what to do
when a refresh is detected, and the choice materially changes E2 and E5. Worse, H5's
"persistent versus fleeting" segmentation is at risk of circularity: an order's realised
lifetime is only known after it ends, so any feature using realised lifetime is
look-ahead. The plan says "realised or expected", and only the expected version is
legitimate; the ambiguity needs removing before any code is written.

### Volatility-scaled weighting has an estimation problem inside it

E1 requires a short-horizon volatility estimate at every book update. That estimate is
itself a forecast, made from recent returns, and recent returns are correlated with recent
flow. The extension therefore risks improving the fit by smuggling a volatility-timing
signal into a flow signal, and attributing the gain to depth weighting. The design has no
control for this. The fix is straightforward — include the volatility estimate as a
standalone control and as an interaction with the baseline OFI, so E1 must beat both — but
the plan does not do it.

### Twelve weeks is optimistic by a wide margin

Stage 0 alone, on 24 months of MBO data for 30 names with proper reconciliation, is
plausibly a month. The plan gives it two weeks and then schedules six extensions, a
combination stage, a queue-aware fill simulator, and a holdout. The realistic outcome is
that the fill simulator arrives half-built in week 10 and the cost analysis — the part that
determines the answer — is the part that gets compressed. Either the instrument universe
shrinks to a handful, or the extension list is cut to the two or three with the strongest
prior, or the timeline roughly doubles.

### The improvement threshold is not tied to anything

"15% improvement in net P&L per unit risk" is precise but arbitrary. It is not derived
from the cost of running the extended signal in production — additional feature computation
on the critical path, more state to maintain, more ways to fail at 3am — nor from the
capital that would be allocated. An extension that adds 15% to a strategy running at
minimal capacity is worth less than one adding 5% to a large book. The criterion should be
expressed in expected currency terms net of implementation cost, which would also force an
early estimate of capacity — currently listed as a metric but never used in any decision
rule.

### Decay analysis is scheduled after the decision

Stage 7 estimates how quickly the extension's edge erodes, but it runs after the holdout
evaluation and after the recommendation is effectively formed. If the edge has a short
half-life, the correct decision might be different — a rapidly decaying extension may not
justify the production complexity. Decay should be measured before the go/no-go, using the
training and validation periods, so that it can inform the recommendation rather than
decorate it.

### No treatment of the crowding question

The premise is that a widely known baseline exists and we are seeking incremental
structure on top of it. That framing implies the baseline's own edge is compressed by
competition and probably still compressing. Nothing in the design measures the trend in
baseline profitability over the 24-month sample. If the baseline's edge has halved over
the period, the extensions are being fitted to a decaying phenomenon, and a 15%
improvement measured in-sample may be gone before deployment. A simple year-over-year
decomposition of baseline performance should be a Stage 1 deliverable.

### What the plan gets right

Framing the whole project as strictly incremental to a baseline, and reporting discards,
is the correct discipline for extension research and is the thing most such projects get
wrong. The untouched holdout with a single evaluation, opened only at Stage 6, is a real
and enforceable guard. Requiring the combination stage to beat the best single extension —
with the simpler model winning ties by default — is a sensible bias against complexity.
And the criterion rejecting improvements concentrated in one instrument or one month
directly targets the most common way this class of result turns out to be illusory.


---

## My Verdict

### Plan

The proposed hypotheses are generally reasonable but miss one important dimension that an experienced researcher would expect to consider which is time of day seasonality. Forms of normalisation are referenced in the plan but miss a consideration that order book dynamics typically behave differently near the open and close of trading sessions, as well as around scheduled economic news events. An experienced practitioner would expect to test whether time-varying normalisation showed any improvement to the signal construction.

In the Experimental Design section stages 0 and 1 are simultaneously superfluous and under specified. It was reasonable to assume the existence of a platform that can supply tick data and build a book so stage 0 is unnecessary. Establishing the baseline should focus specifically on reproducing the results from a reference paper rather than being described as generically good.

The analysis/evaluation of the experiments could use refinement. Specifically an experienced practitioner would want to see how the markout curve (i.e the predictive power at differing forward horizons) changes with adjustments made to the signal, often with some binning to understand how the signal behaves across its distribution of values.

Having such tooling as part of the evaluation suite would allow more precise comparisons of the change effects seen between experiments, such as allowing a researcher to identify, for example, that experiment A outperforms the baseline because in addition to having a higher expected return at a given forward horizon it slows down the evolution of the signal vs the baseline thus improving the probability that it can be successfully traded under production latency considerations.

During signal construction a relevant metric, in addition to R^2, are statistics describing the conditional expected return of the signal. For example, what is the expected forward return across all occasions the signal values reaches its 90th percentile value or above. Appropriately selected thresholds can provide a quantitative estimate for the magnitude of a signal's forecast strength which can be proxy-compared with trading costs to get a sense of likely profitability before needing to run a full simulation. During development of a signal that is likely to feed into a larger predictive model this type of analysis is frequently more useful at this stage than a P&L estimate of the signal. P&L tends to be a noisy measure that is affected by a larger number of confounding variables which it is preferable to remove than trying to improve signals. This makes Stage 5 unnecessary. Simply put, a better evaluation metric would show the signal improving in forecast R^2 and improving in conditional return statistics which are cleaner metrics than P&L.

The estimated timescale for the plan seems quite long. Generally, with appropriate tooling and a more focused evaluation metric (as I described) I would expect to be able to employ a much faster turnaround on idea testing, partly due to a simplified evaluation metric.

The pre-registered criteria have some magic numbers in them which isn't great.


### Critique

The critique approaches the plan with a generic researcher hat on, not from the lens of an HFT microstructure researcher.

It correctly identifies some domain specific elements, such as speeding up the evolution of the signal but doesn't have the domain knowledge to propose a specific alternative evaluation method.

There are some valid queries raised about data differences between exchange feeds, but these do not invalidate the research project per-se, they simply raise issues that need to be considered if trying to generalise the research across multiple exchanges which is arguably out of scope of this piece of work.

The volatility scaling estimation problem is reasonably highlighted and a sensible control is proposed.