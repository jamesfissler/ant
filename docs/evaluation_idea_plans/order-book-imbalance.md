# Order Book Imbalance — Signal Evaluation Plan

## 1. The claim under test

The instantaneous state of the limit order book — specifically the asymmetry between
resting bid size and resting ask size — contains information about the direction of the
next move in the mid-price.

## 2. Scope and non-scope of this evaluation

This is a **signal efficacy study**, not a strategy study. The deliverable is a decision
about whether book imbalance earns a place as a feature in a larger short-horizon
forecasting model.

In scope:

- Does the statistic correlate with forward mid-price movement, and over what horizon?
- Is that correlation something other than a restatement of the book we can already see?
- Is it stable enough across names, days and market states to be worth engineering?
- Is its magnitude in the right order of units to matter?

Explicitly out of scope: position sizing, queue-position modelling, fill simulation,
transaction-cost accounting, portfolio construction, PnL. Every number in this plan is
computed from L2 book data and the trade tape. No execution simulator is required, and
none should be built at this stage — the whole point is to find out cheaply whether there
is anything here before anyone pays for that infrastructure.

## 3. Signal definition

Deliberately minimal. Two variants only, frozen before any evaluation runs:

- **Top-of-book imbalance**

  `I1(t) = (Qb(t) - Qa(t)) / (Qb(t) + Qa(t))`

  where `Qb`, `Qa` are displayed sizes at the best bid and best ask. Bounded in [-1, 1].

- **Depth-weighted imbalance over five levels**

  `I5(t) = (Σ_k w_k Qb_k - Σ_k w_k Qa_k) / (Σ_k w_k Qb_k + Σ_k w_k Qa_k)`, with `w_k = 1/k`.

Two variants is the entire budget for stage 1. The question at this stage is whether the
*family* carries information, not which member of it is best; searching over weighting
schemes, level counts and decay parameters before establishing that the family works is
how a null result gets converted into a false positive.

Reference quantity used later:

- **Microprice** `pm(t) = (Qb·Pa + Qa·Pb) / (Qb + Qa)`, which satisfies the identity
  `pm(t) = m(t) + (s(t)/2)·I1(t)` where `m` is the mid and `s` the spread. This identity
  is the reason stage 2 exists.

## 4. Prediction targets

Forward mid-price change `Δm(t,h) = m(t+h) - m(t)`, expressed in **ticks** (for
interpretation against frictions) and in **bps** (for cross-name pooling).

Horizons, both flavours:

- Clock time: 100ms, 1s, 10s, 60s
- Event time: next 20 and next 100 book-modifying messages

Both are needed because clock horizons pool busy and quiet periods, and a signal that only
works when the book is churning will look weak in clock time and strong in event time.
The disagreement between the two is itself a finding.

A second target, used only in stage 2:

- `Δ'(t,h) = m(t+h) - pm(t)` — the forward move measured **relative to the current
  microprice** rather than the current mid.

## 5. Sample

- Universe: ~24 names chosen to span two tick-size regimes (large-tick, where the spread
  is almost always one tick and queues are long; small-tick, where the spread floats) and
  three liquidity terciles within each. Chosen by liquidity/tick statistics only, before
  any signal is computed.
- Development sample: 40 trading days.
- Sealed holdout: a later, disjoint 40 days **plus 8 names never seen in development**.
  Opened once, at stage 7, with no tuning permitted afterwards.
- Continuous session only. Opening and closing auctions excluded; the first and last five
  minutes of continuous trading are retained but reported as a separate stratum.

## 6. Staged evaluation — cheapest kill first

The stages are ordered so that the tests most likely to end the project run earliest and
cost least. Each gate is pre-registered (section 7) and is a genuine stop, not a
checkpoint to be renegotiated.

### Stage 0 — Data integrity and harness validation (~0.5 day)

- Book reconstruction checks: no crossed or locked books outside known conditions, no
  sequence gaps, monotone timestamps, staleness distribution reported per name.
- **Point-in-time discipline test.** Deliberately inject a one-event look-ahead into the
  signal and confirm the measured IC jumps materially. A harness that cannot detect
  planted leakage cannot be trusted to report its absence.
- **Placebo.** Shuffle the signal series across timestamps within each day and confirm the
  measured IC collapses to zero within sampling error.

*Gate G0: all three pass, or fix the harness before anything else runs.*

### Stage 1 — Raw predictive content (~1 day)

- For each (symbol, day), Spearman rank IC between the signal and `Δm(t,h)`, at every
  horizon, sampled on a fixed grid to avoid over-weighting busy periods.
- Aggregate as the **mean of per-symbol-day ICs**, with the t-statistic computed from the
  dispersion of those daily values. Pooling raw tick observations and computing a t-stat
  from the pooled count is the single easiest way to manufacture a significant result here:
  consecutive book states are almost perfectly autocorrelated, and the effective sample
  size is closer to the number of symbol-days than to the number of observations.
- Signal decay curve: IC as a function of h.
- Decile table: `E[Δm | decile of I]`, with monotonicity across deciles as the qualitative
  check. A signal that only works in its extreme deciles is a different, narrower claim.
- Directional accuracy conditional on `Δm ≠ 0`, against the 50% base rate.

*Gate G1: mean rank IC at the best horizon ≥ 0.02, with the sign consistent in ≥ 70% of
symbol-days. Otherwise stop.*

### Stage 2 — The microprice confound (~1 day) — the decisive test

Because `pm = m + (s/2)·I1`, a positive stage-1 result is consistent with a completely
uninteresting explanation: the mid drifts toward the size-weighted price as the thinner
side of the touch depletes. That is not a forecast of anything. It is an arithmetic
restatement of the book that every participant quoting on weighted depth already has, and
the portion of the move it describes is precisely the portion that occurs while the queue
we would want to join is disappearing.

- Recompute stage-1 statistics with target `Δ'(t,h) = m(t+h) - pm(t)`, i.e. asking whether
  the signal predicts movement *beyond* the current microprice.
- Separately, test whether the signal predicts the forward **microprice** change
  `pm(t+h) - pm(t)`.
- Report the ratio `IC(Δ') / IC(Δm)` per horizon and per tick regime.

*Gate G2: the signal must retain ≥ 50% of its stage-1 IC when the target is measured
relative to the current microprice. If it does not, the honest conclusion is that book
imbalance is a spread-positioning and passive-fill diagnostic rather than a directional
forecast, and the alpha line stops here.*

Running this before the stability and incrementality work is deliberate: it is the test
most likely to end the project, and it costs a day.

### Stage 3 — Magnitude against frictions (~0.5 day)

Not a cost model — a units check.

- For the extreme deciles, `|E[Δm]|` in ticks, against the median half-spread in ticks for
  the same name and time-of-day bucket. Report `ρ = |E[Δm | extreme decile]| / (s/2)`.

The value of `ρ` determines what class of thing this is, and therefore what further work
would even be relevant:

- `ρ > 1` — potentially relevant to liquidity-taking decisions.
- `0.2 < ρ ≤ 1` — a quote-skewing or model-feature signal; taking is off the table.
- `ρ ≤ 0.2` — not worth carrying as a standalone feature.

### Stage 4 — Latency and staleness sensitivity (~0.5 day)

- Recompute stage-1 IC using `I(t - δ)` for `δ ∈ {0, 1ms, 5ms, 25ms, 100ms}`.
- Report the IC half-life in δ.

*Gate G4: at the firm's realistic decision-to-market latency, ≥ 50% of the δ=0 IC
survives. A signal whose content evaporates inside our own reaction time is not a signal
we have.*

### Stage 5 — Stability (~1 day)

Cut the stage-1 IC by: symbol; day; time-of-day bucket (open / midday / close); tick
regime; realized-volatility tercile; spread state (one-tick vs wider).

*Gate G5: sign consistent across all strata, and no single symbol or single day
contributing more than 25% of the aggregate IC.*

### Stage 6 — Incremental content over trivial baselines (~1 day)

A pooled linear model of forward return on: lagged mid returns over lookbacks matched to
each horizon, time-of-day dummies, spread, and realized volatility. Then add the signal.

- Report partial R² and ΔIC out-of-sample, with errors clustered by (symbol, day).

*Gate G6: adding the signal raises out-of-sample R² by at least 30% of the signal's own
standalone R². If the content is already in lagged returns, the signal is a slower way of
computing something we have.*

### Stage 7 — Sealed holdout (~0.5 day)

Run stages 1–6 once, unchanged, on the held-out days and held-out names. Report the full
table. No re-tuning after this point; if the holdout disagrees with development, that is
the result.

## 7. Pre-registered decision rule

| Gate | Test | Threshold | Failure action |
| --- | --- | --- | --- |
| G0 | Leak detection + placebo | Both behave as designed | Fix harness |
| G1 | Mean per-symbol-day rank IC | ≥ 0.02, sign stable in ≥ 70% of symbol-days | Stop |
| G2 | IC vs microprice-relative target | ≥ 50% of stage-1 IC retained | Downgrade to passive/queue diagnostic; stop alpha line |
| G3 | ρ = expected move / half-spread | Reported, classifies use | Informs scope, not a stop |
| G4 | IC at realistic latency | ≥ 50% of δ=0 IC | Stop |
| G5 | Cross-strata sign stability | Consistent; no >25% concentration | Narrow the claim to the surviving stratum or stop |
| G6 | Partial R² over lagged returns | ΔR²_oos ≥ 30% of standalone R² | Stop |
| G7 | Holdout | Headline IC within 50% of development | Stop |

Thresholds are written down before the first run. Any post-hoc movement of a threshold is
recorded in the report alongside the original.

## 8. Deliverables

One report, and it should be small: an IC decay table, a decile table, the microprice
comparison table, the latency curve, a stability panel, and the holdout table. Roughly
five charts. If the evaluation suite grows past this, the suite has become the project.

## 9. Effort

Approximately five to six working days end to end, front-loaded so that roughly 60% of the
probability of stopping is discharged in the first two and a half.

## 10. What a "no" would and would not mean

A failure at G2 says the statistic is arithmetic, not information. A failure at G4 says the
information exists but not for us. A failure at G5 that is confined to one tick regime is
not a failure of the idea but a narrowing of it: "imbalance predicts in large-tick names,
where the queue is the scarce resource" is a legitimate positive result and should be
written up as one rather than buried in an aggregate that averages it away.

---

## Critique of the Plan

### The decisive test may be too decisive, and it is asymmetric

Gate G2 is the strongest part of the plan and also its biggest risk. The microprice
identity is real, but the plan treats "the signal only predicts convergence to the
microprice" as equivalent to "the signal is worthless", and those are not the same
statement. Convergence to the microprice is uninteresting to a taker and highly
interesting to a passive quoter deciding whether to stay in a queue — a decision that has
real economic value even though it never appears in a directional forecast. The plan
gestures at this in its failure action ("downgrade to passive/queue diagnostic") but then
stops the work. If the firm's actual use for this feature is quote management rather than
direction, G2 is set up to kill the version of the idea that would have been useful. The
gate should be conditioned on the intended consumer of the feature, and that consumer
should be named before stage 0, not after stage 2.

The 50% retention threshold is also unmotivated. It is a round number, not a quantity
derived from how much residual predictive content a downstream model would need. Nothing
in the plan explains why 50% rather than 30% or 70%, and with the sampling error implied
by 24 names over 40 days the confidence interval around the retention ratio is likely wide
enough to straddle any of those values. The gate as written can be decided by noise.

### The IC threshold at G1 is doing more work than it can bear

A rank IC of 0.02 is stated with no reference to what magnitude of IC a short-horizon
microstructure feature would need to be worth carrying. In tick-level data with enormous
sample sizes, ICs of 0.02 are routinely both statistically overwhelming and economically
irrelevant; ICs of 0.10 are not unusual for book-derived features at 100ms horizons. So
0.02 risks being too *low* a bar at short horizons and simultaneously too high at 60s,
where almost nothing survives. A single threshold across a horizon grid spanning three
orders of magnitude is not coherent. The gate should be horizon-specific, and should be
expressed against a reference — for instance, the IC of the naive "mid moves toward
microprice" predictor on the same sample.

### The multiple-comparison problem is acknowledged and then not handled

The plan is careful about autocorrelation inflating t-statistics, which is the right
instinct, but it evaluates two signal variants across six horizons in two time flavours,
then cuts results by six stability dimensions. That is a large number of implicit
comparisons, and stage 5's "sign consistent across all strata" is the only discipline
applied. No family-wise or false-discovery correction is specified anywhere, and the
"best horizon" language in G1 explicitly invites selection of the maximum over a grid
without penalty. Either the horizon should be fixed a priori, or the gate should be
applied to the mean across horizons, or the maximum should be compared against a
permutation null of the maximum — not against the null of a single comparison.

### "No PnL" removes a discipline as well as a cost

Refusing to build a fill simulator is the right call for a first pass, and stage 3's
`ρ` ratio is a sensible cheap substitute. But `ρ` compares an expected move to a
half-spread as though the two were commensurable, and they are not: the conditional
expectation `E[Δm | extreme decile]` is computed over all occurrences of that decile,
whereas any real use of the signal would be selecting a subset of those occurrences, at
times when the spread and queue state are themselves conditioned on. The most likely
failure mode is that a signal passes stage 3 with `ρ ≈ 0.5`, gets carried forward as a
promising quote-skew feature, and turns out to be unrealisable because the states in which
the signal is most extreme are exactly the states in which the queue we want is longest.
The plan cannot see this, and should say so explicitly rather than implying that `ρ`
classifies the signal's usefulness.

### The latency gate is the right idea implemented at the wrong point

Stage 4 shifts the signal backwards in time, which measures how quickly the signal's
information decays. That is not the same as measuring whether we can act on it, because it
holds the *target* fixed. A more faithful test shifts the decision point forward — signal
at `t`, return measured from `t + δ` — which additionally removes the portion of the move
that happens during our latency and is therefore unavailable to us. The plan's version
will systematically overstate surviving content, and the overstatement is largest exactly
where it matters most, at the shortest horizons.

### Sample construction has an unexamined dependency

Twenty-four names over forty days sounds substantial but the effective sample for the
stability tests is forty daily IC observations per stratum, and the plan's own statistical
argument — that the effective n is closer to symbol-days than to ticks — implies that the
per-stratum tests in stage 5 have very little power. G5 will therefore mostly fail to
reject sign instability even when it exists, and will read as a pass. Stage 5 needs either
a longer sample or an honest power calculation stating what magnitude of instability it
could actually detect.

Relatedly, the universe is selected on liquidity and tick statistics measured over some
window that the plan does not specify. If that window overlaps the evaluation period, the
selection is mildly forward-looking — names are chosen partly because of how they behaved
during the test.

### What the plan gets right

The ordering is genuinely good: the confound test that is most likely to kill the idea runs
second, not last, which is the opposite of the common failure where the decisive economic
question is scheduled after three weeks of measurement that cannot change the answer. The
leak-injection positive control in stage 0 is a better piece of engineering discipline than
most evaluation suites contain — it tests the instrument, not just the sample. Freezing
the variant list at two, and saying explicitly why, correctly identifies parameter search
as the mechanism by which a null result becomes a publication. And section 10's insistence
that a regime-confined positive is a result rather than a failure is the right posture: the
most likely true outcome for this idea is not "works" or "does not work" but "works where
the queue is the binding constraint", and a plan that could not report that would be worse
than one that could.


---

## My Verdict

### Plan

The choice of clock and event time forward horizons are quite arbitrary. For HFT purposes the clock times are reasonable but the event time choices of 20 & 100 book-modifying messages might well be inappropriate. A stronger choice of threshold would be to estimate the number of book modifying messages seen between trades, or every 1 second, for each instrument and use that as the forward horizon to provide a control across symbols. Without this, 20 messages on symbol A might have a very different meaning to 20 messages on symbol B in terms of the expected change in asset price during the given period.
Holding out the first and last 5 minutes of the trading day to report separately is a good direction given that start & end of day dynamics can vary meaningfully but these time windows should be measured empirically for the venue in question and linked to any known market dynamics rather than assuming a generic 5 minute window.
The suggested placebo needs to be tested with care. Over short time horizons there can be significant auto-correlation in signal values and returns so a simple shuffle may not cause the IC to go to zero in all cases.
Gate G1 needs refinement of the numbers because they appear arbitrary with no apparent link to expected properties of high frequency microstructure signals at different forecast horizons.
Gate G2 and Stage 3 need further refinement of the numbers. For a signal which might be expected to combine with a larger model we should be careful to be too prescriptive about how much individual alpha the signal needs to show. As an example, taking units from the plan, a signal with predictive power of 0.2 half spreads that is orthogonal to the existing model might well be preferable to one offering 0.5 half spreads with 95% correlation to the existing model.
Stage 4 has a good intuition but the latency analysis proposed is flawed because choosing a fixed number here will almost always understate things during the most active periods and overstate them during quieter ones, a better model would be to evaluate the latency adjustment dynamically with market activity levels. Similarly it should shift the evaluation time forward rather than back to approximate actual evaluation latency.


### Critique

Generally a strong critique. Misses some domain specific knowledge, particularly around choices of forward horizons.