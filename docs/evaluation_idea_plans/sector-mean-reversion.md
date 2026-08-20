# Sector Mean Reversion — Signal Evaluation Plan

## 1. The claim under test

Stocks within an industry sector share a common component of return. A stock that has
moved away from its sector over some recent window tends to move back toward it. The
signal is therefore the negative of a stock's recent sector-relative move, and the claim is
that it forecasts that stock's future sector-relative move.

## 2. Scope and non-scope of this evaluation

This is a signal efficacy study. The deliverable is a decision about whether
sector-relative displacement deserves to be a feature in a larger cross-sectional
forecasting model.

The key simplification that makes this cheap: **the market-neutrality requirement in the
idea is handled by the definition of the target, not by building a portfolio.** If the
target is the stock's *residual* return after removing its sector exposure, then any
predictive power we measure is by construction predictive power over sector-neutral
returns. There is no need to construct long/short baskets, size positions, or run a
portfolio optimiser to answer the question the idea actually poses.

Out of scope: portfolio construction, borrow availability, capacity, turnover accounting,
transaction cost modelling, PnL. Everything below is computed from adjusted daily prices,
sector classifications, and quoted spreads.

## 3. Signal definition

At each formation date `t`, for stock `i` in sector `S`:

1. **Residualise the lookback return.** `u_i = r_i(t-L, t) - β_i · r_S(t-L, t)`, where
   `r_S` is the capitalisation-weighted return of sector `S` excluding `i`, and `β_i` is
   estimated on a trailing 120-day window that **ends before the lookback window begins**.
   Excluding `i` from its own sector benchmark, and separating the beta-estimation window
   from the formation window, both matter: the first prevents a large-cap name from being
   benchmarked against itself, and the second prevents the same returns from appearing on
   both sides of the residual.
2. **Cross-sectionally standardise within sector.** `z_i = (u_i - median_S(u)) / MAD_S(u)`,
   using median and median absolute deviation rather than mean and standard deviation so
   that one dislocated name does not define the sector's centre.
3. **Signal:** `x_i = -z_i`.

Two variants only, frozen before evaluation:

- **V1**: `β_i` estimated as above.
- **V2**: `β_i ≡ 1` (simple sector demeaning).

V2 exists as a fragility check. If the result depends on estimated betas, the result partly
depends on a noisy nuisance parameter rather than on the phenomenon.

## 4. Prediction target

The stock's **forward sector-residual return**:

`v_i = r_i(t, t+H) - β_i · r_S(t, t+H)`

with `β_i` from the same pre-formation estimation window (never re-estimated using data
from the holding period).

Grid, pre-registered and deliberately coarse: `L ∈ {1d, 5d, 21d}`, `H ∈ {1d, 5d, 21d}` —
nine cells. Formation dates are sampled **non-overlapping at spacing `H`**, so that
consecutive observations of the IC time series are independent. This costs sample size and
buys the ability to compute a t-statistic that means something without an autocorrelation
correction that would itself need defending.

## 5. Sample

- Universe: the largest ~1000 US-listed names by trailing dollar volume, reconstituted
  monthly from **point-in-time** data. Delisted names retained with their terminal returns.
- Sector: point-in-time GICS (or equivalent) sector membership — the classification as of
  `t`, not as of today.
- Prices: total-return adjusted for splits, dividends and other corporate actions.
- Development: 2010–2019. **Sealed holdout: 2020 onward, opened once at stage 7.**

Survivorship and point-in-time discipline are not optional hygiene here; the idea is about
names that have moved a long way from their peers, which is exactly the population in which
delistings, index deletions and reclassifications concentrate. A backtest run on today's
membership will find reversion because the names that did not revert are missing.

## 6. Staged evaluation — cheapest kill first

### Stage 0 — Data integrity and harness validation (~1 day)

1. Point-in-time checks: sector membership and universe membership as of `t`; delisting
   returns present; corporate actions applied.
2. **Leak positive control**: build a signal that uses one day of forward information and
   confirm the measured IC jumps materially.
3. **Placebo**: shuffle the signal across stocks within each (date, sector) and confirm the
   IC collapses to zero.

*Gate G0: all pass or fix before proceeding.*

### Stage 1 — Raw cross-sectional predictive content (~1 day)

- For each (date, sector) with at least 10 members, the Spearman rank IC between `x_i` and
  `v_i`.
- Aggregate to a per-date IC (average across sectors), giving an IC time series. Report
  mean, standard deviation, t-statistic, and the fraction of dates with positive IC.
- The full 3×3 `L × H` heatmap of mean IC.
- Decile table: `E[v | decile of x]`, checking monotonicity rather than just the extremes.

*Gate G1: at least one cell of the heatmap with mean IC ≥ 0.02 and a positive IC in ≥ 55%
of dates. Additionally — and this is the more informative requirement — the significant
region of the heatmap must be **contiguous**. A single isolated significant cell surrounded
by insignificant neighbours across a smooth parameter grid is what noise looks like; a real
horizon-dependent effect produces a connected region. Failure of contiguity is treated as a
failure even if the individual cell clears the IC bar.*

The contiguity requirement is doing the multiple-testing work here in a way that is more
honest than a formal correction on nine correlated cells would be, and it costs nothing to
check.

### Stage 2 — The microstructure confound (~0.5 day) — the decisive early kill

Measured reversion at short horizons is generated for free by bid-ask bounce and stale
closing prices. A stock whose last trade printed at the bid on day `t` will mechanically
"revert" on day `t+1` with no economic content whatsoever.

Two tests:

- **Skip test.** Form the signal using data through `t`, but measure `v_i` over
  `(t+1, t+1+H)` — leaving a one-day gap. Report the IC with and without the gap.
- **Quote-mid test.** Rebuild everything using closing bid-ask midpoints instead of last
  trade prices, and compare.

*Gate G2: the signal must retain ≥ 60% of its stage-1 IC under the skip test, and the
quote-mid version must not be materially weaker than the trade-price version. If the effect
disappears with a one-day gap, it is bounce, not reversion, and the project stops here.*

This is placed second because it is the cheapest test that can end the project and the
confound it targets is the single most common explanation for a positive result on this
idea.

### Stage 3 — Is the "sector" part real? (~0.5 day)

The idea makes a specific claim: that the *sector* grouping is what matters. That claim is
separable from whether displaced stocks revert at all.

- **Random-sector placebo.** Re-run stage 1 with sector labels randomly permuted across
  stocks (preserving sector sizes), repeated 50 times to give a null distribution.
- **Single-group control.** Re-run with all stocks in one group, i.e. residualising against
  the whole universe rather than the sector.

*Gate G3: the true-sector IC must exceed the 95th percentile of the random-sector null,
**and** exceed the single-group control by a margin. If the sector grouping adds nothing
over universe-wide residualisation, the correct conclusion is that a reversion effect exists
and the sector framing is decoration — a materially different and much cheaper feature.*

### Stage 4 — Contamination by persistent news (~1 day)

Sector-relative displacement is often caused by an event that legitimately repriced the
stock — earnings, guidance, a legal outcome, an acquisition. Those residuals should not
revert, and if the signal's IC is being driven by them it is driven in the wrong direction.

- Recompute stage-1 IC excluding formation windows that overlap a scheduled earnings date
  by ±2 days.
- Recompute excluding names whose formation-window residual exceeded 4 trailing standard
  deviations.
- Report all three versions side by side, and the fraction of the aggregate IC contributed
  by the excluded population.

This stage is diagnostic rather than a hard gate, but it changes the interpretation
completely. A signal that works *only* after excluding event-driven names is a signal that
requires an event filter to be usable, and that requirement should be discovered now rather
than in production.

### Stage 5 — Magnitude against frictions (~0.5 day)

- For the extreme deciles, `|E[v]|` in basis points, against the median round-trip quoted
  spread of the names in that decile, split by liquidity tercile.

A units check, not a cost model. Its purpose is to detect the very common outcome where the
predicted reversion is real, statistically robust, and smaller than the spread of the names
that generate it — which is usually the small-cap tercile.

### Stage 6 — Stability and fragility (~1 day)

- IC by year, by sector, by size tercile, by market-volatility regime.
- Decile monotonicity, and the result after dropping the top 1% of `|z|` observations —
  does the signal live only in the tails?
- V1 versus V2 (estimated beta versus beta of one).

*Gate G6: sign consistent across years and across the large majority of sectors; no single
year or sector contributing more than 30% of the aggregate IC; V1 and V2 broadly agree.
Material disagreement between V1 and V2 means the result is partly an artefact of beta
estimation.*

### Stage 7 — Sealed holdout (~0.5 day)

Stages 1–6 run once, unchanged, on 2020 onward. No re-tuning afterwards.

## 7. Pre-registered decision rule

| Gate | Test | Threshold | Failure action |
| --- | --- | --- | --- |
| G0 | Leak + placebo controls | Behave as designed | Fix harness |
| G1 | Cross-sectional IC, contiguous region | ≥ 1 cell with IC ≥ 0.02, positive on ≥ 55% of dates, region contiguous | Stop |
| G2 | Skip test and quote-mid test | ≥ 60% of IC retained | Stop — effect is bid-ask bounce |
| G3 | Random-sector and single-group controls | Beats 95th pct of null and beats single-group | Reframe as universe-wide reversion; drop the sector claim |
| G4 | Event contamination | Diagnostic | Adds a required event filter to the claim |
| G5 | Predicted move vs spread | Reported by liquidity tercile | Narrows the investable universe |
| G6 | Year/sector stability, V1 vs V2 | Consistent; no >30% concentration; variants agree | Narrow or stop |
| G7 | Holdout | Headline IC within 50% of development | Stop |

## 8. Deliverables

The `L × H` IC heatmap, the skip-test comparison, the random-sector null distribution, the
decile table, the event-contamination panel, the year-by-sector stability grid, and the
holdout table. Seven exhibits.

## 9. Effort

Roughly six working days, with the two stages carrying most of the stop probability — the
bounce confound and the sector-grouping control — complete within the first three.

---

## Critique of the Plan

### The residual-target trick solves one problem and quietly creates another

Defining the target as a beta-adjusted residual return is genuinely the right way to test
this idea without building a portfolio, and it is the plan's best structural decision. But
it makes the measured IC conditional on a hedge that no one has actually executed. The
residual return uses `β_i` estimated before formation and held fixed through the holding
period; a real sector-neutral position would experience beta drift, and the drift is not
random with respect to the signal — a stock that has just moved a long way from its sector
is precisely a stock whose beta is likely to have changed. The plan therefore measures the
predictability of a quantity that is systematically easier to predict than the thing it
stands in for. The fix is cheap and absent: report the IC against a target residualised
with a *contemporaneously estimated* beta as a sensitivity, and report the dispersion
between the two.

### The contiguity requirement is clever but is not a multiple-testing correction

Requiring the significant region of the 3×3 heatmap to be connected is a good instinct and
a real improvement on picking the maximum cell. But it is not equivalent to controlling
error rates, and the plan implies that it is ("doing the multiple-testing work here"). On a
3×3 grid of heavily overlapping parameter choices, adjacent cells are so correlated that
contiguity is close to automatic whenever any cell is significant — the test has almost no
power to reject. The requirement will therefore pass essentially whenever G1's IC bar
passes, which means the multiple-testing problem across nine cells is in practice
unaddressed. Either compare the maximum cell against a permutation null of the maximum —
the stage-0 shuffle machinery already exists and makes this nearly free — or fix `L` and `H`
a priori and report the rest as exploratory.

### Non-overlapping sampling is honest and leaves the study underpowered

Sampling formation dates at spacing `H` to obtain independent IC observations is the
statistically clean choice and the plan is right to prefer it over a Newey–West correction
whose lag choice would need its own defence. The consequence, which the plan does not state,
is severe: at `H = 21d` over a ten-year development window, the IC time series has roughly
120 observations. Detecting a mean IC of 0.02 against typical cross-sectional IC volatility
at that sample size is marginal at best. Stage 6 then subdivides that series by year, by
sector, by size tercile and by volatility regime, at which point the per-stratum tests are
effectively uninformative and G6's "sign consistent across years" will pass by default. The
plan needs an explicit power calculation, and G6 should be demoted to a description unless
the sample can be extended.

### G2's threshold protects against the wrong version of the confound

The skip test is the right test and correctly placed. But requiring 60% retention treats
bounce as an all-or-nothing contaminant, when the realistic case is partial: a genuine
multi-day reversion effect plus a large one-day bounce component. A signal that retains 65%
passes and is then carried forward with an unquantified fraction of its content still
mechanical, because no later stage revisits it. And at `H = 21d` the one-day skip removes
almost nothing, so the test is nearly vacuous in exactly the cells most likely to pass G1.
The skip length should scale with `L`, not be fixed at one day.

### Stage 4 is labelled diagnostic and is actually the crux

The plan says event contamination "changes the interpretation completely" and then declines
to gate on it. That is the wrong way round. For this idea the most likely true state of the
world is that displaced stocks separate into two populations — those displaced by noise,
which revert, and those displaced by information, which do not — and the aggregate IC is a
blend whose sign depends on the mix. Reporting three versions side by side without a
decision rule means the study produces a number and an argument rather than an answer. A
pre-registered rule is needed: for instance, the effect must survive on the
non-event population with at least some stated fraction of its aggregate strength, since
that is the population the idea's economic rationale actually describes.

Relatedly, the ±2-day earnings exclusion is too narrow to do the job. Guidance changes,
analyst-day disclosures, regulatory decisions and sector-wide news are not on the earnings
calendar, and the 4-sigma filter will catch only the most violent of them.

### The friction screen is placed too late and applied too coarsely

Stage 5 compares predicted reversion in basis points against quoted spreads by liquidity
tercile, which is the right cheap check. But it runs fifth, after four stages of work, when
it is one of the most likely reasons to abandon the idea and could be run in an afternoon
immediately after stage 1. It is also applied at the decile level, whereas the relevant
comparison is per name: the extreme decile of `|z|` is disproportionately populated by
small, wide-spread names, so a decile-average spread understates the friction facing exactly
the observations that generate the signal. Reporting the *distribution* of the
predicted-move-to-spread ratio across the names in the decile, rather than the ratio of the
averages, would cost nothing and would say something different.

### Universe and classification choices are under-examined

The universe is the top ~1000 by dollar volume reconstituted monthly, which is defensible,
but the idea's economics are about peer groups, and GICS sectors at the top level are
extremely coarse — a sector containing both a payments processor and a regional bank is not
a set of stocks that should be expected to move together. The plan tests whether the sector
grouping beats a random grouping and whether it beats no grouping, which is good, but it
never tests whether it beats a *finer* grouping. If the effect is really an industry effect,
the sector-level test will understate it and could produce a false negative at G3.

### What the plan gets right

Handling the market-neutrality requirement through the target definition rather than through
portfolio construction is the decision that turns a multi-week backtesting exercise into a
six-day measurement, and it is exactly the right response to a brief that asks for signal
efficacy rather than PnL. The random-sector permutation at stage 3 is the sharpest test in
the plan: it separates "displaced stocks revert" from "sector-displaced stocks revert",
which are routinely conflated, and it specifies in advance what a failure would mean rather
than treating it as a robustness footnote. Insisting on point-in-time membership and
retained delisting returns, with an explicit statement of *why* this idea is unusually
exposed to survivorship, shows the bias was reasoned about rather than defended against by
habit. And the V1/V2 pairing is a well-chosen fragility check — cheap, and aimed at the one
nuisance parameter capable of manufacturing the entire result.


---

## My Verdict

### Plan

Formulating the sector as a cap-weighted one in the signal definition is just one possibility. Other sector constructions might yield interesting results.
G1 has an arbitrary value threshold specified for IC and positive IC date count which might not match reality based on the forward horizon being tested.
G2 also specifies an arbitrary value for IC reduction which isn't backed up. Quote data should be used in the signal from the beginning instead of trades without needing this to be a separate experiment.
The event filter in Stage 4 is material to the design and efficacy of the signal since these times are likely to have a higher probability of repricing the security (e.g. earnings miss) in a manner which causes a semi-permanent dislocation from the rest of the sector as opposed to a temporary dislocation which is expected to revert. The plan should specify more concretely how the signal is expected to behave with/without events and determine a gate threshold. If the signal isn't robust to events it is unlikely to work in practice.

### Critique

The critique is appropriate for this idea