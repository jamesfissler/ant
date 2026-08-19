# Related-Security Intraday Momentum as a Lead Signal

## 1. Statement of the Idea

For a target stock T, identify a set of related securities R — names sharing an industry
sector, or simply exhibiting a reasonable historical correlation with T. Measure intraday
price momentum in R. The hypothesis is that momentum in R is reflected, with a lag, in T:
when the related security is moving up, be long T; when it is moving down, be short T.
The lag is the alpha, and the research question is whether that lag is long enough to
capture and large enough to pay for the round trip.

## 2. Economic Rationale

The claim is a claim about the speed of information diffusion across related names. Its
plausible mechanisms:

1. **Attention and coverage asymmetry.** A sector's most liquid name is watched
   continuously; the third and fourth names are watched intermittently. News that is
   priced instantly in the leader is priced with a delay in the followers.
2. **Index and ETF mechanics.** Flow into a sector product is executed across constituents
   with heterogeneous urgency and liquidity, so the same underlying demand reaches
   different names at different times.
3. **Liquidity constraints.** A market maker in the follower widens on seeing a move in
   the leader before any trade occurs in the follower; price adjusts, but only when
   someone trades.

The counter-argument is strong and must be stated: this is the most mechanically obvious
cross-sectional relationship in equities, and it is the explicit target of a large
population of statistical arbitrage and market-making systems. Any lag long enough to be
tradeable by a system with ordinary latency has survived intense competition, which by
itself is evidence that it is small, concentrated in illiquid names, or both. The
realistic hope is not to discover the effect but to find the specific corners — small
names, particular times of day, particular event types — where the lag remains economic.

There is also a serious identification hazard. Correlation between T and R does not
establish direction. If both respond to a common factor at slightly different speeds, then
"R leads T" and "T leads R" are both partially true, and a naive fit will select whichever
direction happened to dominate in-sample. The design must treat lead/lag direction as a
quantity to be estimated with proper uncertainty, not assumed.

## 3. Hypotheses

- **H1 (lead/lag existence).** The intraday return of a related basket over the trailing
  window `w` predicts the return of T over the next horizon `h`, with `h` in the range of
  seconds to tens of minutes.
- **H2 (direction of leadership).** Leadership is systematic and predictable from
  observable characteristics — liquidity, market capitalisation, index membership,
  analyst coverage — rather than being an artefact of in-sample fitting.
- **H3 (basket construction).** A basket built from estimated factor exposure or from
  residual correlation outperforms one built from raw return correlation, because raw
  correlation is dominated by common market exposure that carries no cross-sectional
  information.
- **H4 (market decomposition).** The predictive content resides in the *residual* movement
  of R after removing the market and sector, not in R's total return. If it does not, the
  strategy is a market-timing strategy in disguise.
- **H5 (conditioning).** The lag is longer and the signal stronger following identifiable
  events in R — earnings, guidance, large prints — than in quiet conditions.
- **H6 (decay).** Predictive power has decayed materially over the sample period as
  competition has increased, and the trend is measurable.
- **H7 (economic significance).** After spread, fees, impact and borrow, the strategy is
  profitable at a stated capital level — most plausibly in less liquid targets, where the
  lag is longest but the costs are highest.

## 4. Data and Infrastructure Requirements

- **Intraday trade and quote data** for the full universe, at a resolution well below the
  shortest horizon under test, with consistent, synchronised timestamps across names. For
  a lead/lag study, cross-sectional timestamp integrity is not a detail — it is the
  measurement instrument. Any systematic timestamp offset between two names will manifest
  as a lead/lag relationship that does not exist.
- **Consolidated quotes with venue-level detail**, so that we know whether an apparent lead
  is a real economic lag or a feed-latency artefact.
- **Survivorship-free universe** with delistings and terminal returns.
- **Point-in-time sector classifications and index membership.**
- **Corporate event calendar**, point-in-time: earnings, guidance, M&A, index changes,
  offerings.
- **Borrow availability and cost**, historical, by name and date.
- **ETF holdings and creation/redemption data** for the relevant sector products, to test
  the second mechanism directly.
- **History**: at least 24 months, and enough to test H6's decay claim, which argues for
  longer — four or five years if available.
- **Cost model** calibrated to our own executions, with explicit treatment of the less
  liquid names this strategy will concentrate in.

## 5. Signal Construction

**Related set definitions**, all pre-specified:

- Same-industry peers by point-in-time classification.
- Top `k` names by trailing residual return correlation, re-estimated on a rolling window
  with a strict gap between estimation and use.
- Factor-exposure neighbours: names with the closest estimated loadings on the risk model.
- The relevant sector ETF, as a single-instrument related "basket".

**Signal.** At time `t` for target T:

- Compute the related basket's return over trailing window `w`, weighted by inverse
  volatility or by estimated beta of T to each constituent.
- Residualise: remove the market return and the broad sector return over the same window,
  so the signal is the basket's *idiosyncratic* move.
- Scale by T's own volatility, so the signal is expressed in units of T's expected move.
- Subtract T's own contemporaneous residual move over the same window — this is the crucial
  step, since the trade is only attractive to the extent T has *not yet* followed.

The resulting signal is therefore a lag measure: how far T has fallen behind its related
set, in T's own volatility units.

Windows `w` and horizons `h` are drawn from a small pre-specified grid — `w` in
{30s, 2m, 5m, 15m}, `h` in {30s, 2m, 5m, 15m, 60m} — and the grid is fixed before any
fitting.

Controls: T's own recent momentum, T's spread and depth, T's event proximity, time of day,
and the market's own return over the same window.

## 6. Experimental Design

**Stage 0 — Timestamp and synchronisation audit.** Measure cross-name timestamp
consistency using a synthetic test: pairs of names that should have no economic lead/lag
relationship should show none. Any measured lead/lag between unrelated names is an
instrumentation error, and its magnitude sets the noise floor for the entire study. This
must be quantified before anything else. If the noise floor exceeds the effect size we
hope to find, the study cannot proceed on this data.

**Stage 1 — Lead/lag estimation.** Cross-correlation of residual returns at a grid of
leads and lags, per pair and per basket, over the training period only. Report the full
profile, not just the peak, and report the peak's confidence interval. The shape matters:
a genuine diffusion effect has a smooth, decaying profile; an artefact typically has a
spike at one lag.

**Stage 2 — Leadership characterisation.** Regress estimated leadership on observable
characteristics to test H2. If leadership is not predictable out of sample from
characteristics, then it must be re-estimated continuously, and the strategy's complexity
and overfitting risk rise sharply — a result that changes the design.

**Stage 3 — Basket comparison.** Compare the four related-set definitions on a common
metric, on the training period only. Test H3 and H4, the latter by comparing residualised
against raw-return baskets. If raw beats residual, the strategy is market timing and should
be re-labelled and re-evaluated as such.

**Stage 4 — Conditioning.** Test H5 by splitting on events in the related set and on
liquidity states. Report per-bucket sample sizes prominently.

**Stage 5 — Decay analysis.** Estimate the effect year by year across the full history to
test H6. This is run early, because a strongly decaying effect changes the value of all
subsequent work.

**Stage 6 — Realistic backtest.** Portfolio-level simulation across many targets, with
position limits, market and sector neutrality, borrow constraints, a calibrated impact
model, and execution at realistic latencies. Walk-forward with purged and embargoed
parameter selection.

**Stage 7 — Capacity and cost sensitivity.** Re-run at multiple capital levels; report the
impact model parameter at which the edge reaches zero.

**Stage 8 — Holdout.** Single evaluation of the final specification on an untouched final
period against pre-registered criteria.

## 7. Evaluation Metrics and Pre-Registered Success Criteria

Metrics: information coefficient by (window, horizon) pair; the lead/lag profile shape and
its noise floor; net Sharpe after costs; turnover; per-trade net edge in basis points;
borrow cost share; capacity; year-by-year effect size; and the fraction of return coming
from the least liquid tercile.

Pre-registered criteria:

- **Go** if net-of-cost Sharpe exceeds 1.0 out of sample, with positive net return in at
  least three of four quarters, and with the measured effect at least three times the
  Stage 0 instrumentation noise floor.
- **Go** requires that the effect not be confined to the least liquid tercile, or, if it
  is, that capacity there exceeds a stated minimum after impact.
- **No-go** if the year-by-year decay implies the effect will be below cost within the
  next two years by simple extrapolation.
- **No-go** if residualised baskets do not beat raw-return baskets, since that indicates
  the signal is market beta timing rather than cross-sectional diffusion.

## 8. Deliverables and Timeline

- Weeks 1–2: data assembly, timestamp and synchronisation audit.
- Week 3: lead/lag estimation.
- Week 4: leadership characterisation and basket comparison.
- Week 5: conditioning and decay analysis.
- Weeks 6–9: portfolio backtest with costs.
- Week 10: capacity and sensitivity.
- Week 11: holdout evaluation and recommendation.

---

## Critique of the Plan

### The most likely outcome is a real effect that is too small to trade, and the plan finds out late

Stages 1 through 5 are all measurement; the cost-aware portfolio simulation does not begin
until week 6. For a strategy whose entire viability question is "is the lag longer than our
round-trip cost", that ordering is backwards. A single early calculation — comparing the
estimated half-life of the lag against the spread plus impact in the target names — would
tell us the answer's order of magnitude in the first fortnight. As written, five weeks are
committed before the decisive constraint is examined.

### The Stage 0 noise floor is the best idea in the plan and it is under-powered

Using economically unrelated pairs to establish an instrumentation noise floor is the
correct instinct, and the criterion requiring an effect three times that floor is
enforceable. But "unrelated" names in the same market are not truly unrelated — they share
market beta, they share flow, they are held in the same index products. The synthetic
control will therefore show a genuine lead/lag and overstate the noise floor, making the
criterion too strict; or, if the control pairs are chosen to minimise shared exposure, they
will differ systematically in liquidity from the real universe and understate it. Neither
error is addressed. The control construction needs to be specified far more carefully than
one paragraph allows, because a criterion is only as good as its calibration.

### Subtracting the target's own move creates a mechanical short-term reversion signal

The signal explicitly subtracts T's own contemporaneous residual move. That construction is
economically motivated, but it means the signal is large exactly when T has just moved
*against* the basket — which is to say the signal is substantially a short-horizon reversion
signal on T with a basket-shaped filter. Bid-ask bounce, a single large print in T, or a
stale quote in T will all produce a large signal with no cross-sectional content whatsoever.
The plan includes T's own recent momentum as a control, which is not sufficient, because
the control is in the regression while the mechanical contamination is in the signal
construction itself. A necessary diagnostic — absent from the plan — is to test the signal
built from T's own move alone, with no basket at all, and confirm that the basket adds
something beyond it.

### Lead/lag direction is treated as estimable but the sample may not support it

Stage 2 asks whether leadership is predictable from characteristics. This is the right
question, but the plan does not consider the likely answer: that leadership is unstable,
partially bidirectional, and dominated by whichever name happened to receive news first.
If so, the strategy requires continuous re-estimation of a quantity with a low
signal-to-noise ratio, across many pairs, which is a recipe for fitting noise. The plan
notes that this "changes the design" without saying how. It needs a pre-specified fallback:
either restrict to pairs where leadership is stable by an explicit statistical test, or
abandon directionality and trade the relationship symmetrically as a convergence strategy —
a different strategy that should be evaluated on its own terms rather than as a fallback
smuggled in mid-project.

### Costs will concentrate exactly where the alpha is

The plan anticipates that the effect is strongest in less liquid names, and its own success
criterion allows for the effect being confined there. But the strategy in those names
demands frequent trading at horizons of minutes, in stocks with wide spreads and thin
books, on both the long and the short side. The gross edge would need to be several times
larger than in liquid names merely to break even, and the impact model calibrated on our
existing executions is least reliable precisely there. The capacity study inherits this,
and its output will be optimistic in a way that no sensitivity band around a single impact
model will reveal.

### The decay criterion is a linear extrapolation of a noisy series

"No-go if simple extrapolation implies the effect falls below cost within two years" sounds
rigorous, but year-by-year effect estimates over a four- or five-year sample give four or
five noisy points. A trend fitted to those points has enormous uncertainty, and the
criterion will fire or not fire essentially at random depending on which years happened to
be volatile. Either the decay test needs a longer sample and a proper uncertainty
treatment, or it should be replaced by a weaker, more honest statement: report the
year-by-year path and require the most recent year to independently pass the economic
criteria.

### The universe scale is unstated and it drives everything

The plan describes portfolio simulation "across many targets" without ever specifying how
many, or how the target universe is chosen. This matters more than any modelling choice:
the number of independent bets determines whether a small per-trade edge can be diversified
into a viable Sharpe, and it determines the multiple-testing burden across pair-level
estimation. A strategy with 50 targets and 4 windows and 5 horizons is running a thousand
implicit tests. There is no multiple-comparison control anywhere in the design.

### Sector ETFs are listed as a data requirement and then barely used

ETF holdings and creation/redemption data are required in Stage 0's data list, and the
second economic mechanism rests on them, but no stage tests that mechanism. Either the ETF
flow channel should get an explicit test — do lead/lag effects intensify around large
creation/redemption events? — or the data requirement should be dropped. As it stands the
plan asks for expensive data it has no experiment for.

### What the plan gets right

Establishing an instrumentation noise floor before measuring the effect, and gating the
success criterion on it, is the single most important control for lead/lag research and it
is often omitted entirely. Requiring residualised baskets to beat raw-return baskets, with
an explicit no-go if they do not, is a sharp test that prevents a market-timing strategy
from being reported as a cross-sectional one. Running the decay analysis early rather than
late correctly treats the trend in the effect as decision-relevant rather than descriptive.
And insisting on the shape of the full lead/lag profile, not just its peak, is the right
way to distinguish genuine diffusion from measurement artefact.


---

## My Verdict

### Plan

The noise test needs refining. The definition of 'no economic lead/lag relationship' is imprecise, since many profitable trading strategies have been produced by finding relationships where a human didn't expect there to be one. This definition needs refinement to be practically useful.

The signal as described is unstable if the lead-lag direction is not constant. A more sophisticated signal design would address this fact in the calculation methodology. For example, moves in the anticipated lead instrument might add credits to a buffer which the lagging instrument(s) need to use up with their confirmatory move(s) after which the signal is zero instead of allowing lagging instruments to generate non-zero signal values in cases where they move first.

Inappropriate magic numbers in the final evaluation criteria. 


### Critique

The effect being too small to trade on its own doesn't negate the signal idea as part of a larger model. Similarly if the effects are getting smaller through time it might still be useful as a signal.

The critique was successful in identifying the issue posed by the implementation symmetry regarding lead/lag offering the potential for a short-term reversion signal. The failure mode was identified well but a practical alternative wasn't provided.