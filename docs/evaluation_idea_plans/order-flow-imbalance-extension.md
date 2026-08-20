# Extending Order Flow Imbalance for Incremental Alpha — Signal Evaluation Plan

## 1. The claim under test

A running summary of recent order book *actions* in security S — quantity added,
cancelled and executed at each price level — forecasts short-horizon forward returns of S.
The research question is not whether the base construction works, which is well
established, but whether enrichments of it add forecasting power beyond the base.

That framing determines the entire design: **every number in this study is an increment,
not a level.** A candidate enrichment that produces a strong standalone information
coefficient and adds nothing to the base has failed.

## 2. Scope and non-scope of this evaluation

In scope: whether a frozen list of candidate enrichments collectively, and then
individually, raise out-of-sample forecasting power over a fixed base specification;
whether any gains are concentrated, stable, and larger than what a multiple-testing
correction would erase.

Out of scope: order placement, fills, costs, sizing, PnL. All measurement is from L2 book
message data. No execution simulator.

## 3. Base specification (fixed first, then never touched)

For consecutive top-of-book states `n-1, n`:

```
e_n =  1{Pb_n >= Pb_{n-1}}·Qb_n  -  1{Pb_n <= Pb_{n-1}}·Qb_{n-1}
     - 1{Pa_n <= Pa_{n-1}}·Qa_n  +  1{Pa_n >= Pa_{n-1}}·Qa_{n-1}
```

The base signal is the sum of `e_n` over a trailing window `W`, standardised by a trailing
estimate of its own scale:

```
OFI_W(t) = Σ_{n in (t-W, t]} e_n  /  σ_W(t)
```

`W` is chosen once, by a coarse pre-registered sweep over `{100ms, 1s, 10s}` on the
development sample only, selecting the value with the highest mean per-symbol-day IC. That
sweep is the only tuning the base receives. After it, the base is frozen and becomes the
fixed reference against which every candidate is measured.

## 4. Prediction target

Forward mid-price change `Δm(t,h) = m(t+h) - m(t)`, standardised by the name's trailing
realized volatility over a matched interval so that names pool. Horizons `h ∈ {1s, 10s,
60s}`, and additionally the event-time horizon "next 100 book messages". The horizon for
the *headline* increment tests is fixed a priori to the base's best horizon from the W
sweep; the others are reported but do not drive gates.

## 5. Frozen candidate list

Eight candidates, written down before any evaluation runs. Nothing may be added later; a
ninth idea that occurs mid-study goes into the write-up as a follow-up, not into this
study's results.

| # | Candidate | Hypothesis it encodes |
| --- | --- | --- |
| C1 | Multi-level OFI, levels 2–5 entered separately | Depth beyond the touch carries independent information |
| C2 | Decomposition into additions / cancellations / executions | The three action types have different information content and the base averages them away |
| C3 | Exponentially time-decayed OFI, two decay rates | Recent flow matters more than the flat window implies |
| C4 | Event-time window (last N messages) alongside the clock window | Information arrives in event time, not clock time |
| C5 | Alternative normalisation: by trailing average displayed depth rather than by σ | Scale should be liquidity, not volatility |
| C6 | Interaction with spread state (one-tick vs wider) | The mapping from flow to price differs by regime |
| C7 | Cross-level shape: slope of per-level OFI across levels 1–5 | The *profile* of flow, not its sum, is the informative object |
| C8 | Concave transform: signed square root, and winsorisation at the 99th percentile | The response to flow saturates |

## 6. Sample and splits

- ~24 names across two tick-size regimes and three liquidity terciles, selected on
  statistics from a window ending before the development period.
- **Development**: 40 days, used for the W sweep, the ceiling test, and all candidate
  screening. Within it, an inner time-split (first 25 days fit, last 15 days evaluate) is
  used for every out-of-sample increment number.
- **Sealed holdout**: a later disjoint 40 days plus 8 unseen names. Opened once, at
  stage 5. Whatever it says is the result.

## 7. Staged evaluation — cheapest kill first

### Stage 0 — Harness validation and base viability (~1 day)

1. Book reconstruction integrity: sequence continuity, no unexplained crossed states,
   staleness distribution per name.
2. **Leak positive control**: inject a one-message look-ahead into the base signal and
   confirm the measured IC jumps. A harness that cannot see planted leakage cannot certify
   its absence.
3. **Placebo**: shuffle the base signal across timestamps within name-days; IC must
   collapse to zero.
4. **Base viability**: the W sweep, then the base's mean per-symbol-day rank IC, with the
   t-statistic computed from the dispersion of daily ICs — never from pooled message counts,
   which are so autocorrelated that the effective sample size is nearer the number of
   symbol-days than the number of observations.

*Gate G0: controls behave as designed and the base achieves a mean per-symbol-day rank IC
of at least 0.02 with a consistent sign in ≥ 70% of symbol-days. If the base does not
work on our data, there is nothing to extend and the project stops. This is a real
possibility — the construction is sensitive to feed quality, message-level reconstruction
and venue fragmentation, and a base that fails here usually indicates a data problem worth
knowing about regardless.*

### Stage 1 — The ceiling test (~1 day) — the decisive early stop

Before evaluating any candidate individually, ask whether the entire enrichment programme
could possibly be worth the engineering.

- Fit a single model containing the base plus **all eight candidates**, on the inner fit
  window; evaluate on the inner evaluation window.
- Report `ΔR²_oos = R²_oos(base + all) - R²_oos(base)` and `ΔIC_oos`, both in absolute
  terms and as a fraction of the base's own `R²_oos`.
- Also fit an unregularised in-sample version to establish the optimistic upper bound, and
  report the gap between in-sample and out-of-sample increments as a measure of how much
  of the apparent gain is fitting noise.

*Gate G1: the kitchen-sink model must improve out-of-sample R² by at least 20% relative to
the base. If eight candidates jointly cannot manage that, no individual candidate will, and
the project stops after two days rather than after three weeks of attribution work on an
effect that does not exist.*

This ordering is the most important structural decision in the plan. The natural instinct
is to evaluate candidates one at a time and accumulate; that spends the entire budget
before learning whether the ceiling is above the floor.

### Stage 2 — Candidate attribution (~2 days)

Only reached if the ceiling is high enough to be worth dividing up.

- For each candidate `Ci` independently: fit `base + Ci`, report `ΔR²_oos`, `ΔIC_oos`, and
  a t-statistic on the candidate's coefficient with errors clustered by (symbol, day).
- **Multiplicity control**: Benjamini–Hochberg across the eight candidates at `q = 0.10`.
  The candidate list was frozen precisely so this correction is legitimate.
- **Redundancy map**: the correlation matrix of the eight candidate series, and a
  hierarchical clustering of it. Candidates that cluster tightly are one effect wearing
  eight costumes, and must be reported as one finding, not eight.
- **Joint vs marginal**: fit forward stepwise from the base, adding candidates in order of
  marginal contribution, and report the increment curve. The gap between "sum of individual
  increments" and "increment of the joint model" is the redundancy, quantified.

*Gate G2: at least one candidate survives BH correction with `ΔR²_oos` ≥ 5% of the base's
`R²_oos`. If the ceiling was real but no individual candidate can be identified as
carrying it, the honest report is that the gain is diffuse and not attributable — which is
a weak basis for engineering work, and should be treated as a soft stop.*

### Stage 3 — Stability of the survivors (~1 day)

For each surviving candidate only:

- Sign and magnitude of the increment by symbol, by day, by tick regime, by
  time-of-day bucket, by volatility tercile.
- Fraction of symbols on which the increment is positive.

*Gate G3: the increment must be positive on ≥ 60% of symbols and in both halves of the
development period. An increment concentrated in a handful of names is a property of those
names, and should be reported that way.*

### Stage 4 — Latency and magnitude screens (~0.5 day)

- **Latency**: move the decision point forward — signal at `t`, return measured from
  `t + δ` — for `δ ∈ {0, 1ms, 5ms, 25ms, 100ms}`. Report the surviving increment.
  *Gate G4: at realistic latency, ≥ 50% of the `δ = 0` increment survives.*
- **Magnitude**: for the top and bottom deciles of the enriched forecast, `|E[Δm]|` in ticks
  against the median half-spread. This is a units check that classifies what the improved
  forecast could be used for, not a cost model.

### Stage 5 — Sealed holdout (~0.5 day)

Base, plus the surviving candidates only, run once on held-out days and names. Report the
increment. No re-tuning afterwards.

## 8. Pre-registered decision rule

| Gate | Test | Threshold | Failure action |
| --- | --- | --- | --- |
| G0 | Controls + base viability | Controls pass; base IC ≥ 0.02, sign stable ≥ 70% of symbol-days | Stop; investigate data |
| G1 | Kitchen-sink ceiling | `ΔR²_oos` ≥ 20% of base `R²_oos` | Stop |
| G2 | Individual candidates after BH at q=0.10 | ≥ 1 survivor with `ΔR²_oos` ≥ 5% of base | Soft stop; report diffuse gain |
| G3 | Stability of survivors | Positive on ≥ 60% of symbols and both sample halves | Narrow claim to surviving stratum |
| G4 | Latency | ≥ 50% of increment survives realistic δ | Stop |
| G5 | Holdout | Increment within 50% of development | Stop |

## 9. Deliverables

The base viability table, the ceiling table (in-sample vs out-of-sample increment), the
candidate attribution table with BH-adjusted p-values, the redundancy clustering, the
stability panel for survivors, and the holdout table. Six exhibits.

## 10. Effort

Roughly six working days, with the ceiling test — carrying most of the stop probability —
complete by day two.

---

## Critique of the Plan

### The ceiling test is the best idea here and the threshold attached to it is unjustified

Running the kitchen-sink model before attribution is the correct ordering and saves the
majority of the budget in the likely case. But "20% relative improvement in out-of-sample
R²" is a number with no derivation. It is not tied to how much forecast improvement a
downstream model would need to justify the engineering and data cost of computing eight
enriched features in production, and it is not tied to the sampling error of the estimate.
With a 15-day inner evaluation window across 24 names, the standard error on a relative
R² increment of this kind is plausibly comparable to 20% itself, which means G1 is close to
a coin flip in the region where it matters most. The plan needs either a bootstrap
confidence interval on the ceiling increment, with the gate applied to the lower bound, or
a threshold derived from a stated cost of implementation.

### The kitchen-sink model's specification is left open, and it decides the answer

Stage 1 says "fit a single model containing the base plus all eight candidates" without
saying what kind of model. With C1 contributing four regressors, C2 three, C3 two, C6 an
interaction and C7 a derived slope, the joint model has on the order of fifteen correlated
predictors. Ordinary least squares on that set will overfit visibly; ridge or lasso will
produce an increment that depends heavily on the penalty, which is itself a tuning
parameter the plan does not pre-register. A conservative choice makes the ceiling look low
and stops a real programme; a liberal one makes it look high and buys three more days of
attribution work on noise. The plan explicitly notes the in-sample/out-of-sample gap as a
diagnostic, which helps, but a diagnostic is not a specification.

### Freezing the candidate list makes BH legitimate but does not make it sufficient

The eight candidates are frozen, which is genuinely the right discipline and is what
licenses the Benjamini–Hochberg correction at stage 2. But BH assumes a degree of
independence (or positive dependence) among the tests, and the plan's own redundancy map
exists precisely because the candidates are expected to be heavily correlated. More
importantly, the correction is applied to eight tests while the study as a whole involves a
window sweep, four horizons, an inner split, and five stability strata. The correction
covers the part of the search that was pre-registered and ignores the part that was not.
The redundancy clustering is the right instrument for this and should feed the correction
— for instance by applying BH at the cluster level, on the cluster's best member — rather
than being reported alongside it as a separate exhibit.

### G2's soft stop is where the plan will actually break down

The plan anticipates the outcome "the ceiling is real but no individual candidate is
attributable" and calls it a soft stop. This is the most likely non-null outcome for a set
of correlated microstructure enrichments, and "soft stop" is not a decision rule — it is a
placeholder for an argument that will happen in a meeting. In practice a diffuse but real
gain has a perfectly reasonable disposition: ship the joint enriched feature as a single
feature and stop trying to attribute it. The plan should say that, or say why not. As
written, the most probable result of the study has no specified action.

### The base's frozen window is a single point of failure

`W` is swept once over three values and then fixed, and every candidate increment is
measured against that one base. If the sweep lands on a window that is slightly wrong, some
candidates — C3 and C4 in particular, which are both re-parameterisations of the window —
will appear to add information that is really just a correction to the base's
misspecification. This is not a fatal flaw, and freezing the base is the right call for a
clean increment study, but the plan should include the cheap defence: re-run the stage-2
increments for C3 and C4 against the two *unselected* window values as well, and report
whether their increments persist. If they collapse, they were window repair, not new
information.

### "No PnL" is right, but the increment framing hides a real economic question

Because everything is measured as an increment in R², the study can report a clear success
— say, a 30% relative improvement — that corresponds to a change in expected move far
inside the tick. Stage 4's magnitude screen partially addresses this, but it is applied to
the *enriched forecast's* deciles rather than to the increment itself. The more useful
number, and it is nearly free from the same fit, is how much the expected move at the
extreme decile changes between the base and the enriched model, in ticks. If that number is
a small fraction of a tick, the increment is statistically real and operationally invisible,
and the study should be able to say so before anyone builds it.

### Stability thresholds are set where nothing can be detected

G3 requires the increment to be positive on ≥ 60% of symbols. With 24 names, that is
roughly 15 of 24, and under a true null of no effect the probability of reaching 15 by
chance is not small. The gate is therefore weak against false positives and, because
per-symbol increments over 15 evaluation days are extremely noisy, also weak against true
positives that happen to be concentrated. It is a gate in name that will mostly pass. If
per-symbol stability matters, the sample needs more days, not a percentage rule.

### What the plan gets right

Framing the entire study as increments rather than levels is the single decision that makes
this idea researchable rather than restateable, and the plan holds that line consistently —
including in G2, where a candidate with strong standalone power and no marginal
contribution correctly fails. Testing base viability before extending it is obvious in
hindsight and is routinely skipped; the plan not only tests it but notes that a base failure
is itself a useful finding about the data. The ceiling-before-attribution ordering is the
right way to spend a research budget on an open-ended enrichment question, and the explicit
in-sample versus out-of-sample gap gives the ceiling test an internal honesty check rather
than a single number to be argued about. Freezing the candidate list in a table, with the
hypothesis each candidate encodes written next to it, converts what is usually an
open-ended fishing expedition into eight falsifiable statements — and makes it obvious to a
later reader exactly what was and was not searched.


---

## My Verdict

### Plan

Fails to normalise the event-time horizon across symbols for better normalisation.
Concern about the placebo shuffle expecting the IC to collapse to zero being too strict given the highly autocorrelated nature of high frequency data
G0 applies an arbitrary value for IC threshold which should be related to the choice of forecast horizon otherwise it is likely inappropriate
G1 is a reasonable check in theory but the arbitrary value of a 20% improvement in OOS R^2 hasn't been related to the actual delta one might hope to see from a related piece of work. 20% might be overly optimistic and throw out an otherwise good change which could have a meaningful impact on the downstream model. This number needs to be derived from something concrete. Relatedly, no specification is given for constructing the kitchen-sink model. If we throw a collection of highly correlated regressors into a simple OLS the difference in improvement between INS and OOS will be larger than if we use a regularised technique, but that would throw additional tuning parameters into the mix which would need to be specified, with a risk of suboptimal specification.
G2 might not be the right conclusion. It's possible that a combination of the effects tested are providing genuine improvement but that the right conclusion is to combine them all together. This would motivate a follow-on research project for the optimal combination method rather than stopping the work.


### Critique

The critique makes some good points but misses some subtlety about the quantitative research process. It prefers the plan to have a gate which would reject an improvement in return forecast magnitude of a fraction of a tick. Whilst it would be nice if every improvement could produce large forecast results the reality of the industry is that most research produces incremental benefits of small fractions of ticks, which when combined into a large model become something monetisable.
