# Trade Impulse as a Predictor of the Next Mid Move — Signal Evaluation Plan

## 1. The claim under test

When a trade executes in security S, the direction and size of that execution carry
information about where the mid-price of S goes next. The immediate impulse of the trade
is a usable short-horizon forecast.

## 2. Scope and non-scope of this evaluation

This study answers one question: after correctly removing the trade's own mechanical
effect on the book, does anything predictive remain, and for how long?

In scope: the shape of the price response to a signed trade, whether that response
contains a *forecastable* component measured from a point after the trade has already
been reflected in the book, and whether the surviving component is large enough and
stable enough to be a feature.

Out of scope: order placement, fill probability, market impact modelling for our own
orders, transaction costs, PnL. Everything below is computed from the trade tape and the
L1/L2 book. No execution simulator is needed and none should be built yet.

The reason to be strict about this is that the idea has an unusually attractive-looking
failure mode. A signed trade is trivially "predictive" of the mid if the measurement
window includes the moment the trade consumed the touch — a buy that lifts the offer moves
the mid by construction. Almost all of the risk in this project is in one methodological
decision, and the plan is organised around getting that decision right first.

## 3. Signal definition

For each trade at time `t` with signed size `ε·V` (`ε = +1` buyer-initiated):

- **S1 — sign only:** `ε`
- **S2 — depth-relative:** `ε · min(1, V / Q_touch(t⁻))`, where `Q_touch(t⁻)` is displayed
  size at the touch being consumed, immediately before the trade
- **S3 — size-relative:** `ε · log(1 + V / V̄)`, where `V̄` is that name's median trade
  size over a trailing window

Three variants, frozen before evaluation begins. S1 isolates direction, S2 asks whether
the fraction of available liquidity consumed matters, S3 asks whether raw size matters
independent of the book state.

**Trade sign must come from the exchange's aggressor flag wherever it is published.**
Where it must be inferred (tick rule, quote rule), classification error is correlated with
the very price move being predicted, which injects the answer into the question. On venues
where both the flag and the inference are available, measure classification accuracy and
report it; where only inference is available, treat those names as a separate stratum and
never pool them into headline numbers.

## 4. Measurement origin — the critical definition

Let `t⁺` be the timestamp at which the book has fully absorbed the trade: the first book
state after all messages causally attributable to that execution have been applied.

- Target: `R(h) = m(t⁺ + h) - m(t⁺)`, in ticks and bps.
- Signal is evaluated as `E[ε · R(h)]` and as the IC of the signed variants against `R(h)`.

`t⁺` is determined empirically, not assumed. Stage 0 measures the average response at
microsecond resolution from the print onward and identifies the knee at which the
mechanical adjustment completes. If that knee is not sharp — if the book keeps adjusting
for tens of milliseconds — then the separation between "impact" and "prediction" is not
clean, and the plan says so rather than picking a convenient cutoff.

Horizons: clock `h ∈ {1ms, 10ms, 100ms, 1s, 10s, 60s}` and event `h ∈ {next 10, 50, 200
book messages}`.

## 5. Sample

- ~24 names spanning tick-size regime (large-tick / small-tick) and liquidity tercile,
  selected on statistics from a window that ends before the development period begins.
- Development: 40 trading days. Sealed holdout: a later disjoint 40 days plus 8 unseen
  names, opened once at stage 8.
- Continuous session only; auctions excluded. Opening and closing five minutes retained as
  a separate stratum.

## 6. Staged evaluation — cheapest kill first

### Stage 0 — Harness validation and the impact/prediction boundary (~1 day)

1. **Response curve at fine resolution.** Plot `E[ε · (m(t + u) - m(t⁻))]` for `u` from
   0 to 100ms on a log grid. Identify where the mechanical jump completes. Set `t⁺` from
   this curve, per tick regime, and freeze it.
2. **Leak positive control.** Deliberately set the origin to `t⁻` instead of `t⁺` and
   confirm the measured effect explodes. If it does not, the pipeline is not measuring
   what it claims to.
3. **Sign-shuffle placebo.** Randomly permute `ε` across trades within each name-day,
   preserving timing and size, and confirm the measured effect collapses to zero.
4. **Pseudo-trade placebo.** Sample random timestamps matched to the trade-time
   distribution, assign random signs, and confirm no effect. This separates "trades
   predict" from "the times at which trades happen are special".

*Gate G0: the knee is identifiable and all three controls behave as designed, or the
project stops until the data or the reconstruction is fixed.*

Stage 0 is placed first because if the impact/prediction boundary is not cleanly
identifiable, every subsequent number is uninterpretable, and that is knowable in a day.

### Stage 1 — Does anything survive past the origin? (~1 day)

- `R(h)` conditional on `ε`, for all horizons, both clock and event time. Report in ticks.
- Rank IC of each signal variant against `R(h)`, aggregated as the mean of per-symbol-day
  ICs with the t-statistic taken from the dispersion of those daily values. Pooling
  individual trades and computing significance from the trade count would be badly wrong:
  trade signs are strongly autocorrelated, so consecutive observations carry a small
  fraction of an independent observation each.
- Decay profile: the shape of `R(h)` beyond `t⁺`. Three shapes are possible and they mean
  different things:
  - **Continuation** (`R` keeps rising): the trade revealed information not yet in the mid.
  - **Reversion** (`R` falls back): the trade pushed the price away from fair value and it
    returns — a liquidity-provision signal, opposite in sign to the stated idea.
  - **Flat**: the trade's information was fully impounded instantly; nothing to forecast.

*Gate G1: mean per-symbol-day rank IC ≥ 0.02 at some horizon beyond `t⁺`, with a
consistent sign in ≥ 70% of symbol-days. If the answer is "flat", stop.*

Note that a clean *reversion* result is a pass of G1 with a sign flip, and should be
reported as such rather than treated as a failure. The stated idea would be wrong and
something usable would still have been found; the plan must not be constructed so that
only one sign counts as success.

### Stage 2 — Is the effect just trade-sign persistence? (~1 day)

Trade signs are autocorrelated over long stretches, largely because parent orders are
sliced. So `ε(t)` predicts `ε(t+)`, and if price follows those trades, `ε(t)` will appear to
predict price without containing any information beyond "more of the same is coming".

- Condition the response on the **inter-trade time** preceding the trade, split into
  terciles. An isolated trade after a quiet interval and a trade in the middle of a burst
  are different objects.
- Condition on the **trailing signed-trade run length** at `t` (how many same-signed
  trades immediately precede it). If the response is monotone increasing in run length,
  the signal is largely a sign-persistence signal.
- Compare the IC of the raw signal against the IC of the signal *after* projecting out a
  trailing exponentially-weighted signed-trade-count over matched lookbacks. Report the
  residual IC.

*Gate G2: the residual IC after removing trailing signed-trade persistence must retain
≥ 40% of the stage-1 IC. If it does not, the finding is "trade signs are
autocorrelated", which is well known, cheap to compute directly, and not what the idea
claimed.*

### Stage 3 — Which trades? (~0.5 day)

Purely descriptive, but it is where the actual usable version of the signal usually lives.
Cut the stage-1 response by:

- Level-clearing vs partial (did the trade consume the entire displayed touch?)
- Trade size bucket relative to touch depth, and relative to the name's median size
- Spread state at `t⁻` (one tick vs wider)
- Time-of-day bucket

The output is a statement of the form "the effect is concentrated in level-clearing trades
in wide-spread states", or the absence of such a statement.

### Stage 4 — Magnitude against frictions (~0.5 day)

- For the strongest conditioning bucket, `|E[R(h)]|` in ticks against the median
  half-spread in ticks for the same name and time bucket. Report
  `ρ = |E[R]| / (half-spread)`.

This is a units check, not a cost model. `ρ > 1` means the effect could matter to a
liquidity-taking decision; `0.2 < ρ ≤ 1` means it is a quote-management or model-feature
signal only; `ρ ≤ 0.2` means it should not be carried alone.

### Stage 5 — Latency (~0.5 day)

Move the *decision point* forward, not the signal backward: signal observed at `t⁺`, return
measured from `t⁺ + δ` to `t⁺ + δ + h`, for `δ ∈ {0, 1ms, 5ms, 25ms, 100ms}`. This removes
both the decayed information and the portion of the move that occurs while we are
reacting.

*Gate G5: at the firm's realistic decision-to-market latency, ≥ 50% of the `δ = 0` effect
survives.*

### Stage 6 — Stability (~1 day)

Cut stage-1 and stage-2 results by symbol, day, time-of-day, tick regime, volatility
tercile, and sign-source (exchange flag vs inferred).

*Gate G6: sign consistent across strata; no single symbol or day contributing more than
25% of the aggregate effect; the inferred-sign stratum not materially stronger than the
exchange-flag stratum — if it is, the extra strength is classification leakage, not alpha.*

### Stage 7 — Incremental content over trivial baselines (~1 day)

Pooled model of `R(h)` on lagged mid returns over matched lookbacks, spread, realized
volatility, and time-of-day; then add the signal. Partial R² and ΔIC out of sample, errors
clustered by (symbol, day).

*Gate G7: ΔR²_oos ≥ 30% of the signal's standalone R².*

### Stage 8 — Sealed holdout (~0.5 day)

Stages 1–7 run once, unchanged, on held-out days and names. No re-tuning afterwards.

## 7. Pre-registered decision rule

| Gate | Test | Threshold | Failure action |
| --- | --- | --- | --- |
| G0 | Knee identifiable; leak, shuffle, pseudo-trade controls | All behave as designed | Stop; fix data/reconstruction |
| G1 | Mean per-symbol-day rank IC past `t⁺` | ≥ 0.02, sign stable in ≥ 70% of symbol-days (either sign) | Stop |
| G2 | Residual IC after removing trade-sign persistence | ≥ 40% of stage-1 IC | Stop; report as a known autocorrelation effect |
| G3 | Conditioning cuts | Descriptive | Narrows the claim |
| G4 | ρ = expected move / half-spread | Reported; classifies use | Informs scope |
| G5 | Effect at realistic latency | ≥ 50% of δ=0 | Stop |
| G6 | Cross-strata stability | Consistent; no >25% concentration; no inferred-sign inflation | Narrow or stop |
| G7 | Partial R² over lagged returns | ΔR²_oos ≥ 30% of standalone | Stop |
| G8 | Holdout | Headline within 50% of development | Stop |

## 8. Deliverables

The fine-resolution response curve, the decay profile beyond `t⁺`, the sign-persistence
residual table, the conditioning cuts, the latency curve, and the holdout table. Six
exhibits. If the suite grows beyond this it has stopped being a screen.

## 9. Effort

Six to seven working days, with the two stages carrying most of the kill probability —
the origin definition and the sign-persistence control — completed in the first two.

---

## Critique of the Plan

### The origin `t⁺` is treated as a data question when it is partly a definitional one

The plan's central methodological move is to locate an empirical knee in the response curve
and call everything after it "prediction". This is cleaner than the alternatives, but it
assumes the mechanical and informational components are separable in time, and there is no
particular reason they should be. A large buy that clears the offer causes an immediate
mechanical jump *and* triggers other participants to cancel and re-quote higher over the
following milliseconds — and those cancellations are a response to the same trade, not new
information. Both are "caused by the trade", both happen after any knee, and only one of
them is something we could have anticipated. The plan will measure the reaction of other
participants and label it prediction. Stage 0's honest caveat ("if the knee is not sharp,
say so") is good, but the plan does not say what it would do in that case beyond
acknowledging it, and the case is likely rather than exceptional.

### G2's threshold is the weakest link in an otherwise strong test

Removing trailing signed-trade persistence is the right control and it is well placed. But
"retain ≥ 40% of stage-1 IC" is arbitrary, and worse, the control itself is
under-specified: "a trailing exponentially-weighted signed-trade-count over matched
lookbacks" leaves the decay parameter unfixed, and the strength of the control varies
enormously with that choice. A weak control makes the signal look independent; a strong one
makes it look redundant. The plan pre-registers the threshold but not the thing the
threshold is applied to, which is the wrong way round. The decay parameter should be
frozen in stage 0, chosen to maximise the control's own explanatory power on a slice of
data not used for the gate.

### The three signal variants are not really three hypotheses

S1, S2 and S3 are heavily collinear — sign dominates all three, and the size scalings are
monotone transforms of a common quantity. Evaluating them as separate variants across six
clock horizons and three event horizons produces 27 headline ICs, and G1 permits selecting
"some horizon". No multiplicity control appears anywhere in the plan. The maximum of 27
correlated statistics has a null distribution well to the right of the null for one, and
the 0.02 threshold is calibrated against neither. Either fix the horizon a priori, or
compare the observed maximum against a permutation null of the maximum — the sign-shuffle
machinery from stage 0 already exists and would make this nearly free.

### The reversion case is allowed but not planned for

Stage 1 correctly says a reversion result is a pass with a sign flip. But every subsequent
stage is written for the continuation case. Stage 2's sign-persistence control, stage 4's
comparison to the half-spread, and stage 5's latency test all mean different things if the
effect is transient impact decay rather than information. In particular, a reversion signal
is a liquidity-provision signal, and for a liquidity provider the half-spread is revenue,
not cost — so `ρ` in stage 4 would be interpreted backwards. The plan permits the outcome
without adapting to it, which in practice means that if reversion is what shows up, the
remaining stages will be improvised.

### "Market data only" hides a real capacity question

The plan is right that PnL modelling is premature. But this particular idea has a capacity
problem that is visible in market data and is not measured: the trades with the largest
apparent predictive content are, by stage 3's own logic, likely to be level-clearing trades
in wide-spread states — which is to say, exactly the moments when there is nothing left to
trade against. A signal whose strongest realisations coincide with an empty book may be
real and unusable, and the plan would report it as a strong pass at G1, G3 and G4. A cheap
addition would be to report, alongside each conditioning bucket, the displayed depth
available at `t⁺` on the side we would want to trade. That is one more column from data
already loaded.

### Sign-source stratification is right but the gate is backwards in practice

G6 requires the inferred-sign stratum not to be materially stronger than the exchange-flag
stratum. That is the correct test. But it will only be informative if both strata are large
and comparable, and the plan selects names by tick regime and liquidity, not by venue
disclosure. It is entirely possible the two strata differ systematically in every other way,
in which case the comparison cannot isolate classification leakage. The cleaner test — on
venues where both are available, recompute everything with inferred signs and compare
against the same names' flag-based results — is mentioned in section 3 as a measurement of
classification accuracy but never fed into a gate.

### Statistical power is asserted rather than calculated

The plan is admirably careful about not counting trades as independent observations, and
then builds six stability strata on top of a 40-day, 24-name sample. As with any design that
reduces its own effective sample size by two or three orders of magnitude for good reasons,
the per-stratum tests in stage 6 will have very little power, and "sign consistent across
strata" will pass mostly because nothing can be rejected. No power calculation appears. The
plan should state what size of instability stage 6 could actually detect, and if the answer
is "only very large instability", say that the stage is descriptive rather than a gate.

### What the plan gets right

It correctly identifies that this idea lives or dies on a single measurement decision and
puts that decision in stage 0 rather than discovering it in week three. The four-part
control set — leak injection, sign shuffle, pseudo-trade timing, and the fine-resolution
response curve — is more rigorous than the idea's apparent simplicity would suggest is
necessary, and the pseudo-trade control in particular catches a confound (that trade times
are themselves informative) that most versions of this study never test. Insisting on
exchange aggressor flags, and treating inferred signs as a separate stratum rather than
silently pooling them, closes off the most common way this measurement is quietly
corrupted. And separating "the trade predicts" from "trade signs are autocorrelated" at stage
2, before any of the expensive stability and incrementality work, is exactly the right
ordering: it is the explanation most likely to be true, and it is cheap to test.


---

## My Verdict

### Plan

Measurement origin should prefer to use feed identifiers where available rather than assuming a need to always calibrate timing estimates. For example, many feeds have ways to know when the exchange has moved on to processing the next 'logical event' which would signify a way of knowing precisely that the information contained in the current trade has been fully represented in the book. If the information is available and we don't use it, we risk mixing follow-on activity from other participants with book adjusting activity from the trade which could confound our signal research results.
Event horizons aren't normalised to symbol data rates.
G1 has indefensible numbers specified. Predictive power needs to scale with the forward horizon being tested. 
G2 chooses an arbitrary value for the gate which doesn't appear to relate to anything. The presence of an exponentially weighted trade count would require a decay parameter which isn't specified.
G5 isn't really a latency check since true latency changes dynamically with market activity levels

### Critique

Capacity problems are mentioned as a reason pnl is a problem to ignore, but this ignores the critique's own point about using the signal in a passive trading context. Talking about the capacity of the signal implies a belief it could only be used for aggressive trading.