# Order Book Imbalance as a Short-Horizon Predictive Signal

## 1. Statement of the Idea

The visible limit order book at any instant is a census of resting supply and demand at
a set of discrete prices. The hypothesis is that when that census is materially
asymmetric — more size resting on the bid than the ask, or vice versa — the next
increments of the price are more likely to move toward the thin side than the thick side.
We want to know whether this asymmetry, measured in real time from data we can actually
receive, carries exploitable information about the mid-price over horizons of
milliseconds to a few seconds.

## 2. Economic Rationale

Two distinct mechanisms are usually offered, and they matter because they imply different
decay profiles and different optimal trading policies.

**Mechanical / queueing.** Price moves when one side of the book is exhausted. If the ask
holds 200 lots and the bid holds 2,000, then a symmetric arrival process of aggressive
orders exhausts the ask first in expectation. Under this mechanism the signal is a
statement about the *conditional hazard of the next price change*, it decays as the book
refills, and it has no informational content beyond the visible state.

**Informational.** Resting size is placed by participants with views. A thick bid is a
revealed preference to own the asset at that price. Under this mechanism the imbalance
proxies the direction of latent demand, and the price move it predicts should be at least
partially permanent.

The two mechanisms are separable empirically: the mechanical one predicts that the move
substantially reverts once the book replenishes; the informational one predicts a
permanent component. Distinguishing them is a core objective, not an aside, because a
purely mechanical signal is much harder to monetise — it tends to predict exactly the
moves in which we are the one being run over.

The confounding third possibility must be stated up front: displayed size is cheap to
post and cheap to cancel. A book that looks thick may be thick with orders that will
vanish the moment they are threatened. Any positive result must survive the question
"is this signal just measuring spoofable, non-committal liquidity?"

## 3. Hypotheses

- **H1 (existence).** Signed imbalance measured at event time `t` has non-zero predictive
  correlation with the mid-return over horizons `h`, for `h` in both wall-clock
  ({1, 10, 50, 250, 1000, 5000} ms) and event clock (next {1, 5, 20, 100} book updates).
- **H2 (sign and shape).** The relationship is positive (imbalance toward the bid
  predicts upward moves) and concave in the magnitude of the imbalance, saturating before
  the extremes.
- **H3 (regime dependence).** Predictive power is strongest in large-tick, queue-
  constrained instruments where the spread is pinned at one tick, and materially weaker
  in small-tick instruments where price discovery happens through spread movement rather
  than queue exhaustion.
- **H4 (depth structure).** Beyond the shortest horizons, an imbalance measure that uses
  multiple levels with distance-decaying weights outperforms a top-of-book-only measure.
  At the very shortest horizons the ordering reverses.
- **H5 (transience).** A significant fraction of the predicted move reverts within a few
  seconds, and the permanent fraction is the part that determines whether an aggressive
  policy can be profitable.
- **H6 (economic significance).** After realistic fill modelling, fees, and adverse
  selection, the signal supports a positive-expectancy trading policy in at least one
  instrument class. This is the hypothesis the project actually stands or falls on.

## 4. Data and Infrastructure Requirements

Assuming access to the firm's tick store and research cluster, the specific requirements
are:

- **Book granularity.** Market-by-price to at least 10 levels is the minimum. Market-by-
  order is strongly preferred and is a hard requirement for the tradability work, because
  queue position cannot be reconstructed without individual order identity and
  add/cancel/modify sequencing.
- **Timestamps.** Both matching-engine timestamps and our own gateway receipt timestamps.
  The former defines the true event ordering; the latter defines what we could actually
  have observed. Every signal used in the tradability tests must be computed from the
  latter, lagged by a measured, instrument-specific decision latency.
- **History.** A minimum of 12 months of continuous data, deliberately spanning at least
  one volatility regime change and one tick-size or fee-schedule change if available.
- **Universe.** Three deliberately different groups, sized about 8–12 instruments each:
  large-tick futures (single venue, no fragmentation); liquid small-tick cash equities
  (fragmented, the hardest case); and mid-cap equities where the book is thin enough that
  the signal should be strong but capacity is small.
- **Reference data.** Tick size regimes, auction and halt schedules, corporate actions,
  fee and rebate schedules by tier, and the venue's order type semantics (hidden orders,
  iceberg refresh behaviour, self-match prevention).
- **Compute.** Event-level regressions over roughly 10^9–10^10 book updates. Budget for a
  columnar event store and out-of-core fitting; this is not a laptop study.

## 5. Signal Construction

At each book update `t`, with bid and ask sizes `Q^b_j`, `Q^a_j` at levels `j = 1..L` and
distance `d_j` from the mid:

- `I_1 = (Q^b_1 - Q^a_1) / (Q^b_1 + Q^a_1)` — the canonical top-of-book form.
- `I_L(w) = (Σ_j w_j Q^b_j − Σ_j w_j Q^a_j) / (Σ_j w_j Q^b_j + Σ_j w_j Q^a_j)` for weight
  families `w_j ∈ {1, 1/j, exp(−d_j/κ)}`, with `κ` fitted per instrument.
- Notional-weighted variants using `Q × price`, for cross-instrument comparability.
- Session-normalised variants: divide by a trailing EWMA of `|I|` to strip out the
  intraday U-shape in book shape, which otherwise leaks time-of-day into the signal.
- A **commitment-weighted** variant that down-weights size which has rested for less than
  some age threshold, computed from MBO. This is the direct test of the spoofing concern.

Controls that must enter the same model, or the study will simply rediscover them under a
new label:

- Spread in ticks, and an indicator for the one-tick-spread state.
- Recent signed trade flow over several lookbacks.
- Recent realised volatility and event intensity.
- Time of day, and time since the last price change.
- The microprice, `(Q^a_1 P^b_1 + Q^b_1 P^a_1) / (Q^b_1 + Q^a_1)`, which is an algebraic
  function of top-of-book imbalance. Its inclusion is what tests whether multi-level
  imbalance adds anything beyond the standard depth-weighted mid.

## 6. Experimental Design

**Stage 0 — Data validation.** Reconstruct the book from the raw feed and reconcile
against venue-published snapshots. Report crossed-book incidence, sequence gaps, and
timestamp monotonicity violations. Freeze the cleaned dataset. No modelling begins until
this passes; a book reconstruction bug produces a spectacular and entirely false signal.

**Stage 1 — Unconditional predictability.** For each instrument and horizon, estimate
`r_{t→t+h} = α + β I_t + γ' X_t + ε`. Report `β`, its standard error under a
Newey–West-style correction with bandwidth well beyond `h`, and the incremental R² over
controls alone. Present the results as a heatmap over (instrument class × horizon), not
as a single pooled number.

**Stage 2 — Shape and conditioning.** Non-parametric estimation of `E[r | I]` by decile
and by spread state to test H2 and H3. Test H4 by comparing weight families under a
common evaluation.

**Stage 3 — Permanence decomposition.** Estimate the impulse response of the mid to an
imbalance shock out to 30 seconds. Decompose into transient and permanent components.
This directly tests H5 and tells us which trading policy family is even viable.

**Stage 4 — Commitment test.** Repeat Stage 1 with the age-weighted variant and with size
partitioned by order age. If the signal is carried entirely by young orders, we are
measuring flicker, and capacity assumptions must be revised downward sharply.

**Stage 5 — Tradability.**
- *Passive policy.* Simulate posting at the top of book conditional on imbalance,
  with an explicit queue position model driven by MBO: our order joins at the back,
  advances on cancels ahead of us and on trades, and fills when the queue in front is
  consumed. Score fills against the mid at fill time plus a horizon, so adverse selection
  is measured rather than assumed away.
- *Aggressive policy.* Simulate crossing the spread when imbalance exceeds a threshold,
  paying the full spread and taker fee. This is where the transient/permanent split from
  Stage 3 becomes decisive.
- Both policies are evaluated only on data after the model-selection cutoff.

**Stage 6 — Robustness.** Purged, embargoed walk-forward across the full sample; parameter
stability plots across periods; sensitivity of conclusions to assumed latency (sweep from
optimistic to pessimistic); and a deliberate degradation test in which we add 1, 5 and 20
ms of extra latency to find the point at which the edge disappears.

## 7. Evaluation Metrics and Pre-Registered Success Criteria

Metrics: incremental R², information coefficient by horizon, impulse-response
decomposition, simulated P&L per trade in ticks and in basis points net of fees, fill
rate, adverse selection cost per fill, turnover, and estimated capacity at a fixed
participation cap.

Pre-registered thresholds, fixed before Stage 5 is run:

- **Go** if the aggressive policy nets at least 0.15 ticks per trade after fees in at
  least one instrument class over a full out-of-sample year, with the sign stable across
  every quarter, **or** the passive policy improves net-of-adverse-selection edge per
  fill by at least 20% over an unconditional quoting baseline.
- **No-go** if the edge is positive only under latency assumptions faster than our
  measured production round trip, or if it exists only in instruments whose capacity is
  below a stated floor.
- The permanent component must be a non-trivial fraction of the total predicted move for
  an aggressive policy to be recommended.

## 8. Deliverables and Timeline

- Weeks 1–2: data validation report and frozen dataset.
- Weeks 3–4: Stage 1–2 predictability results.
- Week 5: permanence decomposition and commitment test.
- Weeks 6–8: fill simulator with queue model, and both trading policies.
- Week 9: robustness, latency sensitivity, capacity.
- Week 10: written recommendation with a go/no-go against the pre-registered criteria,
  and a reusable signal library with tests.

---

## Critique of the Plan

### The research question is not actually open

The plan's own framing concedes that the effect is heavily documented, and then spends
five stages establishing that it exists. Stages 1 and 2 will almost certainly succeed and
will teach us nothing we can trade. The real question — H6 — is deferred to Stage 5,
by which time most of the calendar and most of the goodwill are spent. A better-shaped
project would run a crude version of the fill simulator in week 1 against a naive signal,
establish the order of magnitude of the answer, and only then decide whether the careful
version is worth building. As written, the plan risks producing a beautiful confirmation
of a known fact and an under-resourced answer to the question that matters.

### The microprice makes part of the design circular

Including the microprice as a control while testing top-of-book imbalance is close to
including the signal as its own control: the microprice is a deterministic function of
`I_1` and the spread. The plan states this but does not resolve it. The consequence is
that Stage 1's "incremental R² over controls" will be near zero for `I_1` by construction,
and the plan does not say what conclusion that would license. The design needs an explicit
statement of what the null model is: predicting mid returns is a different exercise from
predicting microprice returns, and a signal that merely reproduces the microprice is not
worthless — it is the baseline against which everything else must be measured. This must
be decided before running, not after seeing the numbers.

### The fill model is the result, not an input

Stage 5 carries the entire economic conclusion, and its queue model is described in one
paragraph. Everything hard lives in that paragraph: how iceberg refreshes are inferred,
how hidden liquidity is handled when we cannot see it, whether cancels ahead of us in the
queue are assumed to be random or adversarially correlated with the signal, and — most
importantly — whether our own order changes the behaviour of others. That last item is
not simulatable from historical data at all. A passive strategy conditioned on imbalance
is systematically joining queues that other participants are also joining for the same
reason; the historical queue we model is not the queue we would have faced. The plan
should say plainly that simulated passive results are an upper bound, and should
pre-commit to a haircut, or to a small live pilot as the only real test.

### Adverse selection is named but not modelled

The plan measures adverse selection after the fact by marking fills against a later mid.
It does not model the mechanism: we get filled on the bid precisely when someone is
willing to sell to us, and imbalance-conditioned quoting concentrates our fills in the
states where informed sellers are most active. The measured statistic will capture this,
but only after the simulator has already made assumptions about *whether we would have
been filled at all*. If the fill model is optimistic about queue position, the adverse
selection number is optimistic too, and the two errors compound in the same direction.
There is no independent check on this in the design.

### Latency treatment is a sweep, not a model

Sweeping added latency from 1 to 20 ms is useful but treats latency as a scalar constant.
In production it is a distribution with a fat tail, and the tail events are correlated
with exactly the high-message-rate moments when the signal is strongest. A plan that
concludes "profitable at our median latency" can be wrong because the profitable trades
cluster in the moments when we are slowest. The sweep should be replaced by, or at least
supplemented with, a replay using the empirical latency distribution measured from
production, including queueing effects under message bursts.

### The universe is too wide for the resources

Three instrument classes with 8–12 names each, at MBO granularity, over 12 months, with
a full queue simulator, in ten weeks, is not a credible schedule. The likely failure mode
is that the equity work is done badly rather than dropped. It would be more honest to
commit to one class end-to-end — large-tick futures, where the mechanism is cleanest and
the data are simplest — and treat the others as explicitly out of scope for this phase.

### Statistical inference is under-specified

Newey–West is named, but with 10^9 overlapping observations, standard errors are not the
binding constraint; everything will be significant. The real risks are (a) the effective
sample size being far smaller than the observation count because observations cluster
within episodes, and (b) multiple comparisons across instruments × horizons × weight
families × conditioning states, which is easily several hundred tests. The plan has no
multiple-testing control and no statement of the unit of independent observation. Without
those, the heatmaps in Stage 1 will contain attractive patterns that are noise.

### Spoofing test is good but incomplete

The commitment-weighted variant is one of the stronger parts of the design. But order age
is only a proxy for commitment, and a sophisticated participant can make a non-committal
order look old. More importantly, the plan doesn't consider the reflexive case: if the
signal works and we trade it at size, we become a predictable responder, and the cheapest
way to extract money from us is to display size we will react to. The plan needs an
explicit section on how the strategy degrades when others know it is running, and a
monitoring plan for detecting that degradation early.

### The success criterion has a soft edge

"0.15 ticks per trade after fees" is admirably concrete. "Improves edge per fill by 20%
over an unconditional quoting baseline" is not, because the baseline is unspecified and a
weak baseline makes the criterion trivially attainable. The passive criterion needs the
baseline pinned down — in particular whether the baseline quotes the same volume at the
same times — before any results are seen.

### What the plan gets right

The separation of transient from permanent price impact is the correct central question
and is placed early enough to steer the trading policy work. Requiring book reconstruction
validation before any modelling is the right discipline and catches the single most common
source of spurious microstructure results. Using both matching-engine and gateway
timestamps, and computing tradable signals only from the latter, is the correct handling
of the observability problem. Pre-registering thresholds before Stage 5 is a genuine
guard against the ex-post rationalisation that dooms most signal research.


---

## My Verdict

### Plan

The plan gets confused between testing what is a very simple and well-known microstructure effect with building a exchange simulation suite, a trading strategy, and then trying to enhance the signal.
A better response would have been simpler, with signal effects constrained to markout analysis rather than trying to simulate P&L through an under specified trading strategy.
The core issue with such a simple signal is that it is extremely well known so to someone proposing it they need quick diagnostics which help them to see it will be unlikely to manifest useful alpha over an executable forward horizon (unless they are specifically targeting an ultra low latency hardware solution).
The pre-registered criteria have some magic numbers in them which isn't great.

### Critique

The critique correctly highlights that the plan is confused, though it gets things wrong that simulated P&L is the correct way to evaluate the signal.