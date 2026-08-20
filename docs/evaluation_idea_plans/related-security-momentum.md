# Related Security Momentum — Signal Evaluation Plan

## 1. The claim under test

Intraday price movement in securities related to a target security — related by industry
membership or by realised correlation — is subsequently reflected in the target. Observing
a positive move in the related names predicts a positive move in the target over the
following minutes.

## 2. Scope and non-scope of this evaluation

This is a signal efficacy study. The deliverable is a decision on whether a peer-return
term deserves to be a feature in a larger intraday forecasting model.

The idea contains a hidden assumption that dominates the entire study: it assumes the
relationship is **directional in time**. Two securities that are simply correlated will show
apparent "prediction" in both directions when observed asynchronously, and the naive
version of this measurement will report a strong result on data containing no exploitable
lead at all. Most of the design below exists to separate a genuine information lead from
contemporaneous correlation observed through stale prices.

Out of scope: hedging, position sizing, portfolio construction, transaction costs, PnL.
Everything is computed from intraday quotes and trades.

One simplification keeps the study cheap: the hedging implied by the idea is handled by the
**target definition** rather than by constructing positions. Both the peer signal and the
target return are measured net of the common market factor, so any predictive power we
measure is already predictive power over market-neutral returns, and no portfolio needs to
exist for the question to be answered.

## 3. Signal definition

Bars: 1-minute, built from **quote midpoints sampled at the bar boundary** (the last valid
NBBO mid at or before the boundary), not from last trade prices. Trade prints are
asynchronous and stale, and using them is the single easiest way to manufacture a spurious
lead. The **age** of the mid used for each bar is recorded and carried through the study.

For target `j` at time `t`:

1. **Market residualisation.** For every security, `r̃(t) = r(t) - β_M · r_M(t)`, where
   `r_M` is the return of a broad market ETF over the same bar and `β_M` is estimated on a
   trailing 20-day window ending before the evaluation day. Without this step the study
   measures index-level co-movement and calls it a lead-lag relationship.
2. **Peer set.** `P_j` = the 5 securities with the highest correlation of 1-minute residual
   returns to `j`, estimated over a trailing 20-day **formation window that never overlaps
   the evaluation period**. Peer sets are re-formed monthly and held fixed within a month.
3. **Signal.** `s_j(t) = Σ_{i ∈ P_j} w_ij · r̃_i(t-L, t)`, with `w_ij ∝ corr_ij` from the
   formation window, normalised to sum to one.

Two variants only, frozen before evaluation:

- **V1**: correlation-selected peers as above.
- **V2**: sector-membership peers — the 5 largest names in the target's sector by dollar
  volume, equally weighted.

V2 exists because "related" is ambiguous in the idea and the two readings can give different
answers; if only one works, that is the finding.

## 4. Prediction target

The target's **forward market-residual return** `r̃_j(t, t+H)`, in basis points, standardised
by the target's trailing intraday volatility so that names pool.

Grid, pre-registered and coarse: `L ∈ {1, 5, 15} minutes`, `H ∈ {1, 5, 15} minutes`.
Observations sampled non-overlapping at spacing `H`.

## 5. Sample

- ~200 US equities spanning liquidity terciles, drawn from a point-in-time universe with
  monthly reconstitution and delistings retained.
- Development: 12 months. **Sealed holdout: a later disjoint 6 months plus 50 unseen
  targets**, opened once at stage 8.
- Continuous session only; opening and closing auctions excluded. First and last 15 minutes
  retained but reported as a separate stratum, since the effect — if real — is expected to
  concentrate near the open.

## 6. Staged evaluation — cheapest kill first

### Stage 0 — Data integrity and harness validation (~1 day)

1. Clock alignment across venues; NBBO reconstruction sanity; distribution of quote age at
   bar boundaries, per name and per time-of-day bucket.
2. **Leak positive control**: build a signal using one bar of forward peer information and
   confirm the measured IC jumps materially.
3. **Placebo**: shuffle the signal across timestamps within each name-day and confirm the IC
   collapses to zero.

*Gate G0: all pass, or fix before proceeding.*

### Stage 1 — The lead–lag asymmetry test (~1 day) — the decisive early kill

This runs before any signal construction is evaluated, because it can end the project in a
day and it tests the idea's load-bearing assumption directly.

For each (peer, target) pair, compute the cross-correlation of residual bar returns at leads
and lags:

`ρ_ij(k) = corr( r̃_i(t), r̃_j(t+k) )` for `k ∈ {-5, ..., +5}` minutes.

Define the **asymmetry** `A_ij = ρ_ij(+1) - ρ_ij(-1)`. A tradable lead requires `A_ij > 0`:
the peer must predict the target by more than the target predicts the peer. If `ρ_ij(+1) ≈
ρ_ij(-1) > 0`, the two names are simply correlated and both series are being observed with
noise and delay — there is no direction to trade, and any IC measured later will be an
artefact of how the bars were sampled.

- Report the distribution of `A_ij` across pairs, its median, and the fraction of pairs with
  `A_ij > 0`.
- Report the full `ρ(k)` profile averaged across pairs — a genuine lead produces a visibly
  skewed profile, not a symmetric peak at `k = 0`.

*Gate G1: median `A_ij` significantly greater than zero, with `A_ij > 0` for at least 60% of
pairs. If the cross-correlation profile is symmetric, stop. Nothing later in the plan can
rescue this.*

### Stage 2 — The staleness confound (~0.5 day)

The most common source of a spurious positive at stage 1 is that the *target's* quotes
update less often than the peers'. The target's price appears to "follow" only because it
had not yet caught up — and the price we would have traded at was never the stale one.

- Repeat stage 1 restricted to bars where **both** names have a quote update within the
  previous 5 seconds.
- Repeat stage 1 with the roles of peer and target reversed for the same pairs, and confirm
  the asymmetry reverses sign as it should.

*Gate G2: the asymmetry must retain ≥ 60% of its stage-1 magnitude on the fresh-quote
subsample. If it disappears, the lead was an observation artefact and the project stops.*

### Stage 3 — Liquidity ordering (~0.5 day)

If the effect is genuine information flow, it should run from the more liquid name to the
less liquid one, and its strength should increase with the liquidity gap.

- Sort pairs by the ratio of dollar volume (peer / target) into quintiles and report the
  median `A_ij` in each.

*Gate G3: `A_ij` monotone, or close to it, in the liquidity gap. A symmetric or reversed
relationship indicates the measurement is picking up a mechanical artefact rather than
information transmission, and the burden of proof shifts back to stage 2.*

### Stage 4 — Signal-level predictive content (~1 day)

Only reached if the pairwise structure survives.

- Rank IC of `s_j(t)` against `r̃_j(t, t+H)`, aggregated as the mean of per-target-day ICs
  with the t-statistic from the dispersion of those daily values. Pooling bar-level
  observations and computing significance from the bar count would be wrong: intraday
  returns and peer signals are both autocorrelated and cross-sectionally dependent through
  the residual market factor.
- The full 3×3 `L × H` IC surface, with the same connectedness expectation as any smooth
  parameter grid: an isolated significant cell among insignificant neighbours is noise.
- Decay of IC in `H`. A real intraday transmission effect should decay within minutes; an
  effect that is flat across `H` out to 15 minutes is more likely a slow common factor that
  market residualisation failed to remove.
- Decile table and monotonicity.
- **Random-peer placebo**: for each target, draw 5 random peers matched on volatility and
  dollar volume, repeat 50 times, and report where the true-peer IC falls in that null
  distribution. This is the test that separates "peers predict" from "any basket of
  volatile names predicts".

*Gate G4: mean per-target-day rank IC ≥ 0.02 in a connected region of the grid, exceeding
the 95th percentile of the random-peer null.*

### Stage 5 — Incremental content over trivial baselines (~1 day)

The two explanations that must be excluded before claiming a peer effect:

- The target's **own lagged residual return** over matched lookbacks (own autocorrelation).
- The **sector or index return** over the same window, which the peer signal partially
  proxies even after market residualisation.

Fit forward residual return on those baselines, then add `s_j`. Report partial R² and ΔIC
out of sample, with errors clustered by (target, day).

*Gate G5: ΔR²_oos ≥ 30% of the signal's standalone R². If the peer term adds nothing over
the target's own lagged return and the sector return, the finding is that a cheaper feature
already contains it.*

### Stage 6 — Latency and magnitude screens (~0.5 day)

- **Latency**: move the decision point forward — signal at `t`, return measured from `t + δ`
  — for `δ ∈ {0, 1s, 5s, 30s}`. *Gate G6: at realistic latency, ≥ 50% of the `δ = 0` IC
  survives.* This gate matters more here than for most signals: the peers' move is public,
  and if the transmission takes less time than our reaction, the content is real and
  unavailable.
- **Magnitude**: for the extreme deciles, `|E[r̃_j]|` in basis points against the target's
  median half-spread, reported by liquidity tercile. A units check, not a cost model — and
  one that is likely to bite, since stage 3 predicts the effect is strongest in the *less*
  liquid targets, which are exactly the ones with the widest spreads.

### Stage 7 — Stability (~1 day)

IC by target, by month, by time-of-day bucket, by market-volatility regime, and V1 versus
V2.

*Gate G7: sign consistent across strata; no single target or month contributing more than
25% of the aggregate IC.*

### Stage 8 — Sealed holdout (~0.5 day)

Stages 1–7 run once, unchanged, on held-out months and unseen targets. No re-tuning
afterwards.

## 7. Pre-registered decision rule

| Gate | Test | Threshold | Failure action |
| --- | --- | --- | --- |
| G0 | Leak + placebo controls | Behave as designed | Fix harness |
| G1 | Cross-correlation asymmetry | Median `A > 0`, positive for ≥ 60% of pairs | Stop — correlation, not lead |
| G2 | Fresh-quote subsample | ≥ 60% of asymmetry retained | Stop — staleness artefact |
| G3 | Monotonicity in liquidity gap | Monotone or near-monotone | Reopen stage 2 |
| G4 | Signal IC vs random-peer null | IC ≥ 0.02 in a connected region, above 95th pct of null | Stop |
| G5 | Partial R² over own lag and index | ΔR²_oos ≥ 30% of standalone | Stop |
| G6 | Latency | ≥ 50% of IC survives realistic δ | Stop |
| G7 | Stability | Consistent; no >25% concentration | Narrow or stop |
| G8 | Holdout | Headline IC within 50% of development | Stop |

## 8. Deliverables

The averaged cross-correlation profile, the asymmetry distribution before and after the
fresh-quote filter, the liquidity-gap quintile table, the `L × H` IC surface with the
random-peer null, the incrementality table, the latency curve, and the holdout table. Seven
exhibits.

## 9. Effort

Roughly six to seven working days, with the two stages carrying nearly all of the stop
probability — the asymmetry test and the staleness control — complete within the first two.

---

## Critique of the Plan

### The asymmetry test is the right idea and the statistic is too crude to carry the gate

Placing the cross-correlation asymmetry first is the plan's best decision, but `A_ij =
ρ(+1) - ρ(-1)` is a single-lag difference computed on noisy 1-minute residual returns, and
its sampling error across a single pair over twelve months is large. G1 requires the median
across pairs to be positive and 60% of pairs to be positive — but under a true null of pure
contemporaneous correlation, `A_ij` is symmetric around zero, so roughly 50% of pairs will
be positive by construction, and 60% is not far outside what sampling noise plus a small
number of genuinely-leading pairs would produce. The gate is much weaker than it appears.
A permutation null on `A` — shuffling day labels between the two series and recomputing —
would give the correct reference distribution and is cheap, since the machinery already
exists for stage 0.

The single-lag choice is also arbitrary: a real transmission effect at a 30-second scale
would show up mostly at `k = 0` on 1-minute bars and barely at `k = ±1`, and the plan's own
`L` grid starts at 1 minute. The bar size and the lead measured are the same quantity, which
means the test can only see leads longer than a bar.

### Market residualisation with a 20-day trailing beta is not enough to kill the common factor

Stage 4's decay check ("an effect flat across `H` is more likely a slow common factor") is a
good instinct and an admission that the residualisation may leak. It probably will. A single
market beta estimated over 20 days of 1-minute bars is a weak control against intraday
sector and style co-movement, which is exactly the co-movement peers share. Stage 5 adds the
sector return as a baseline, which helps, but it arrives four stages after the asymmetry
gate that the leaked common factor could have passed on its own. The residualisation should
be at least two-factor (market plus sector) from the start, and the plan should state what
fraction of peer-target residual correlation survives it — a single number that would
calibrate how much to believe everything downstream.

### The staleness control tests the confound but not the version that matters

Requiring both names to have a quote update within 5 seconds is the right shape of test. But
quote *updates* are not the same as tradable freshness: a quote can update without the price
moving, and a name can have a fresh quote that is nonetheless the same stale price it has
shown for a minute. More importantly, the filter conditions on a variable — recent quote
activity — that is itself correlated with recent price movement, which is the signal. The
fresh-quote subsample is therefore not a random subsample, and comparing asymmetry across it
mixes the confound being tested with a selection effect. A cleaner complement, absent here,
is to repeat the asymmetry test on bars sampled in *event time* for the target rather than
clock time.

### Stage 3's gate has no failure action worth the name

G3 says a non-monotone result means "the burden of proof shifts back to stage 2". That is
not a decision rule; it is a description of a conversation. The liquidity-ordering test is
genuinely informative — it is one of the few checks that distinguishes information
transmission from measurement artefact on economic grounds rather than statistical ones —
and the plan should commit to what it does when the ordering comes out flat. The likely
truth is messier than the gate anticipates: liquidity and volatility are strongly related,
and the quintile sort will partly be a volatility sort, so a monotone result is not
unambiguous evidence either.

### Peer-set construction is out-of-sample in form but not in effect

Peers are selected on a trailing 20-day formation window and re-formed monthly, which is the
correct discipline. But peers selected on realised correlation are, mechanically, the names
most likely to share whatever factor structure was live in that window, and factor structure
is persistent. The random-peer placebo at stage 4 is the intended defence, and it is a good
one — but it matches on volatility and dollar volume, not on factor exposure, so the null
basket is systematically less factor-aligned with the target than the true basket. The
placebo will therefore make the true peers look better than they are, by an amount the plan
cannot quantify. Matching the random peers on sector as well would cost nothing and would
make the null much harder to beat.

### The friction screen is placed last and is likely to be the actual answer

Stage 6 notes, correctly and to the plan's credit, that the effect is expected to be
strongest in less liquid targets, which are the ones with the widest spreads. That
observation is close to fatal for the idea in its stated form, and it is scheduled after
five stages of work. If the transmission effect is real but lives in names whose half-spread
exceeds the predicted move, the study's conclusion is known in advance and could be
approximated on day one from the liquidity distribution of the universe and typical
lead-lag magnitudes reported in the literature. Running a rough version of the magnitude
screen immediately after stage 1 would cost an afternoon and could stop the project.

### Non-overlapping sampling is right and the stability stage does not survive it

Sampling at spacing `H` is the honest choice. At `H = 15` minutes over 12 months, each
target contributes roughly 6,000 observations, which sounds ample — but the plan correctly
aggregates to per-target-day ICs, giving roughly 250 daily observations per target, and then
stage 7 subdivides by month, time-of-day bucket, volatility regime and variant. No power
calculation appears anywhere. G7's "sign consistent across strata" will pass because the
strata cannot reject anything, and the 25% concentration limit is a reasonable idea applied
without knowing whether 25% is inside or outside normal sampling variation for this design.

### V1 and V2 are two hypotheses treated as one robustness check

Correlation-selected peers and sector peers encode genuinely different economic claims —
statistical co-movement versus fundamental relatedness — and the plan runs both through
every gate and then compares them at stage 7. If they disagree, which is likely, the study
has two results and one decision rule, and the pre-registration does not say which wins. It
also doubles the effective search without any multiplicity accounting.

### What the plan gets right

It correctly identifies that this idea's central risk is not statistical but structural —
that correlation observed asynchronously imitates prediction — and it builds the first two
stages entirely around that risk rather than treating it as a robustness appendix. Testing
the pairwise cross-correlation profile *before* constructing any signal is the right order:
the signal construction adds parameters and cannot fix a symmetric profile, so spending a
day to find out is a genuine saving. Handling the hedging requirement through the target
definition, so that no portfolio needs to exist for the question to be answered, keeps the
study to a week. The liquidity-ordering test brings an economic prediction to bear on a
statistical measurement, which is a stronger form of evidence than more statistics would be.
And the plan is candid, in stage 6, about the friction problem that most versions of this
research quietly discover only at the end — even if it schedules the discovery too late.


---

## My Verdict

### Plan

The signal design is symmetric so stage 1 confirms an asymmetry in the training data to validate a hypothesis, though this may still fail in held-out data or live trading. An alternative, potentially more robust, mechanism would be to construct the signal in a way which lets the information content in the signal trend to zero when the expected lead-lag relationship doesn't manifest.

The specified bar length will be too coarse to reliably detect the shortest lags proposed - the bar length needs to be at a finer granularity than the shortest lag.

### Critique

Comments about quote staleness are less relevant when discussing securities traded on limit order books, since the best bid/offer seen on the feed are firm executable orders.

A signal having a predictive magnitude which isn't enough to trade on its own isn't necessarily a failure since it may still add value to a larger model. This reduces the justification of the criticism about wide spreads in less liquid targets.