# Trade Impulse as a Predictor of the Next Mid-Price Move

## 1. Statement of the Idea

In a system whose job is to forecast the next movement of the mid-price of security S, we
take the occurrence of a trade in S as the predictive event. The signal is the immediate
impulse the trade delivers: its direction (which side was the aggressor), its size, where
it printed relative to the prevailing quotes, and what it did to the book. The claim is
that this impulse forecasts the next mid move in the same security, on a horizon short
enough to be measured in book events rather than seconds.

## 2. Economic Rationale

A trade is the only event in the market that is unambiguously costly to the participant
who caused it. A resting order can be withdrawn for free; an aggressive order pays the
spread and the fee. That asymmetry is the entire economic content of the idea: trades are
the market's most credible signal because they are the only one with skin in it.

Three channels carry the prediction:

1. **Information.** The aggressor may know something. Under sequential trade models,
   market makers rationally revise their beliefs after each trade in the direction of the
   aggressor, and the mid moves permanently by the size of that revision.
2. **Inventory.** A large aggressive buy leaves the liquidity providers who filled it
   short. They will shade quotes upward to attract the offsetting flow, moving the mid
   even absent any information.
3. **Mechanical depletion.** An aggressive order that consumes the entire top level
   forces the best quote to the next price. The mid changes as an arithmetic consequence
   before any belief revision occurs.

Channels 1 and 2 imply predictive content that survives the instant of the trade; channel
3 is partly definitional and, if not carefully excluded, will manufacture an apparently
enormous signal that cannot be traded because the move has already happened by the time we
see the print.

The obvious counter-argument must be confronted at the outset: everybody in the market
sees the same print, at roughly the same time, and the mechanical component of the
response is over in microseconds. Whatever survives has to be either a slower belief-
revision component, or a component only visible to someone who can decompose the trade
better than the naive tape reader.

## 3. Hypotheses

- **H1 (baseline).** Signed trade indicator at event `t` predicts the mid change over the
  next `k` book events, `k ∈ {1, 2, 5, 20, 100}`, with positive coefficient.
- **H2 (size).** The response is concave in trade size — a square-root-like law — rather
  than linear, so a single large print carries less than the sum of its parts.
- **H3 (sweep structure).** A trade that sweeps multiple price levels, or a burst of
  same-direction prints within a short window, carries materially more predictive content
  than an equal volume of isolated prints. Bursts should be aggregated into a single
  "impulse event" before measurement.
- **H4 (depletion conditioning).** The response is stronger when the trade consumes a
  large fraction of the displayed size at the touch, and near zero when it consumes a
  small fraction of a deep level.
- **H5 (decomposition).** Splitting the impulse into a permanent and a transient component
  reveals that the transient component dominates at the shortest horizons and reverts
  within a few hundred milliseconds to a few seconds.
- **H6 (aggressor identification quality).** Predictive power is materially higher when
  the aggressor side is known exactly (from the feed) than when it is inferred by a
  quote-comparison rule. The gap quantifies how much of any published result is an
  artefact of classification error.
- **H7 (tradability).** After latency, fees and the spread, the impulse supports a
  positive-expectancy policy — most plausibly a defensive one (widening or pulling quotes
  after adverse impulses) rather than an offensive one.

## 4. Data and Infrastructure Requirements

- **Trade feed with explicit aggressor flags** where the venue publishes them. Where it
  does not, we need quotes with sufficient timestamp resolution to apply a classification
  rule and, critically, a subset of instruments where both are available so the
  classification error can be measured rather than assumed.
- **Full book updates interleaved with trades in a single, correctly ordered event
  stream.** This is the single most important data requirement. Trade and quote messages
  arriving on separate channels with independent sequencing will produce a signal that is
  entirely an artefact of message ordering.
- **Matching-engine and gateway timestamps.** All tradability work uses gateway time plus
  measured decision latency.
- **Trade condition codes**: to identify and exclude auction prints, off-book crosses,
  late reports, odd lots, and implied trades from spread strategies, all of which have
  different or absent predictive content.
- **History**: 12 months minimum, spanning a volatility regime change.
- **Universe**: a small set of instruments where the mechanism should be cleanest — front-
  month futures with a single venue — plus a fragmented equity subset to test whether the
  signal survives when prints arrive from many venues with heterogeneous latency.

## 5. Signal Construction

Define an **impulse event** by aggregating consecutive trades with the same aggressor side
that occur within a short gap (e.g. 1 ms, tuned per instrument), so that a single parent
order sweeping the book is one observation and not twenty.

Features per impulse event:

- Signed volume, and signed notional.
- Signed volume normalised by the displayed size at the touch prior to the trade
  (the depletion ratio).
- Number of price levels consumed.
- Whether the touch was cleared entirely.
- Whether the print occurred inside the spread (indicating hidden liquidity, which is
  informationally distinct from a visible-book execution).
- Time since the previous impulse event, and the recent intensity of impulses (a Hawkes-
  style self-excitation term).
- Signed volume over trailing windows, to separate the marginal impulse from the run.

Controls: prevailing spread, book depth on both sides, realised volatility, time of day,
and time since the last mid change.

The target is the mid change over the next `k` events, with the mid measured at our
gateway and lagged by the decision latency. A second target using the depth-weighted mid
is run in parallel, because a mid defined at the touch is mechanically sensitive to the
very depletion the trade caused.

## 6. Experimental Design

**Stage 0 — Event stream validation.** Build the interleaved trade/book stream and verify
causal consistency: every trade must be consistent with the book state immediately
preceding it. Report the rate of inconsistencies; a rate above a low threshold invalidates
the whole study and must be fixed before proceeding.

**Stage 1 — Aggressor classification audit.** On the instruments where the venue publishes
the true aggressor, measure the accuracy of the inference rule we would have to use
elsewhere. Report accuracy conditional on spread state, trade size, and event rate.
Carry that error rate forward as a known contaminant in the rest of the analysis.

**Stage 2 — Mechanical exclusion.** Split events by whether the trade cleared the touch.
For cleared-touch events, the next mid move is partly definitional. Report results
separately for cleared and non-cleared events, and treat the non-cleared subset as the
primary evidence for genuine predictability.

**Stage 3 — Response estimation.** Estimate the mid response as a function of signed
impulse features, non-parametrically first (binned by depletion ratio and size decile)
and then in a pooled model. Test H2 by fitting power-law size exponents per instrument.

**Stage 4 — Impulse response and permanence.** Estimate the full response path out to
30 seconds. Decompose into permanent and transient parts. Test whether the transient part
reverts predictably enough to be a signal in its own right.

**Stage 5 — Clustering and self-excitation.** Fit a self-exciting intensity model to
impulse arrivals and test whether conditioning on predicted future impulse intensity adds
to the mid forecast beyond the current impulse.

**Stage 6 — Tradability.**
- *Defensive policy*: a quoting strategy that pulls or widens the far-side quote on an
  adverse impulse. Evaluated by reduction in adverse-selection cost per fill against an
  unconditional quoting baseline, holding fill volume approximately constant.
- *Offensive policy*: cross the spread following a strong impulse. Evaluated on net ticks
  per trade after fees, with the latency-adjusted signal only.
- Both on strictly out-of-sample data after the model selection cutoff.

**Stage 7 — Latency destruction test.** Re-run Stage 6 with additional latency injected at
several levels to locate the point at which the edge vanishes, using the empirical
production latency distribution rather than a constant.

## 7. Evaluation Metrics and Pre-Registered Success Criteria

Metrics: information coefficient by horizon and event class; permanent/transient split;
adverse-selection cost per fill; net ticks per trade; fill-rate impact of the defensive
policy; and the latency at which the edge reaches zero.

Pre-registered criteria:

- **Go (defensive)** if the quoting policy reduces adverse selection cost per fill by at
  least 15% with no more than a 10% reduction in fill volume, out of sample, with the
  effect present in each quarter.
- **Go (offensive)** if net ticks per trade after fees exceed 0.1 in at least one
  instrument at a latency at or above our measured production 90th percentile.
- **No-go** if the entire measured effect resides in cleared-touch events, since that is a
  mechanical artefact rather than a forecast.
- **No-go** if the effect is not present at production latency, regardless of its size at
  zero latency.

## 8. Deliverables and Timeline

- Week 1: interleaved event stream, validation report.
- Week 2: aggressor classification audit.
- Weeks 3–4: response estimation and mechanical decomposition.
- Week 5: impulse response and permanence.
- Week 6: self-excitation model.
- Weeks 7–9: defensive and offensive policy simulation, latency destruction test.
- Week 10: recommendation against pre-registered criteria; production-ready feature
  library with tests.

---

## Critique of the Plan

### The signal is the most crowded object in the market

Every participant with a colocated feed handler sees the same print at the same
microsecond, and the response is the single most optimised reaction in high-frequency
trading. The plan acknowledges latency as a risk but treats it as one stage among nine.
In truth, the study's answer is very likely to be "yes it predicts, no we cannot get
there first", and that answer could be obtained in week one by measuring how fast the mid
actually moves after a print relative to our measured tick-to-trade time. The plan should
be re-ordered so that this cheap, decisive measurement comes before the expensive modelling
rather than after it. As written, there is a real chance of spending nine weeks to reach a
conclusion that was available in three days.

### The mechanical component may be nearly all of it

Stage 2 splits cleared-touch from non-cleared events, which is the right instinct, but the
split is cruder than the problem. Even a non-cleared trade changes the book, and the mid
is a function of the book. If the depletion moves the queue such that the next cancel
clears the level, the "prediction" is largely bookkeeping. A sharper design would define
the target as the mid change *after* the book has fully re-equilibrated following the
trade — for instance, the change relative to a short-window post-trade reference rather
than the instantaneous pre-trade mid. The plan does not define its target precisely enough
to rule out this contamination, and the size of the reported effect will depend heavily on
that definitional choice.

### The defensive policy is the plausible answer but gets the weakest treatment

The plan's own reasoning points to a defensive quoting application as the most likely place
for real value, yet the offensive policy gets the crisper success criterion and the
defensive one is evaluated against an "unconditional quoting baseline" that is never
specified. Holding fill volume "approximately constant" is doing a lot of unexamined work:
a policy that pulls quotes after adverse impulses will systematically lose exactly the
fills that would have been profitable if the impulse was noise, and the trade-off between
fill volume and fill quality has no stated exchange rate. Without a defined objective
function that prices a lost fill against an avoided adverse fill, "15% reduction with 10%
volume loss" is an arbitrary point on an unmapped frontier.

### Aggressor classification error is measured but not propagated

Stage 1 correctly measures classification accuracy on instruments where truth is available.
The plan then "carries that error rate forward as a known contaminant", which is not an
analysis. Misclassification is not random noise: it is concentrated in fast markets,
crossed quotes, and multi-venue prints — precisely the states with the largest moves. That
makes the error correlated with the target, which biases coefficients in a direction that
is not knowable without modelling it. The plan needs either an errors-in-variables
treatment or, more practically, a commitment to restrict conclusions to instruments where
the aggressor is published.

### Impulse aggregation is a free parameter with large consequences

The 1 ms aggregation window that defines an "impulse event" determines the entire event
set. Too short and one parent order becomes many correlated observations, inflating
apparent significance enormously. Too long and genuinely separate decisions are merged,
destroying the signal. The plan says it will be "tuned per instrument" without saying
against what objective — and if it is tuned against predictive power, the whole study is
compromised by selection. This parameter must be fixed on a separate calibration sample
using an objective unrelated to the target, such as the observed inter-arrival time
distribution.

### The unit of independent observation is undefined

With hundreds of millions of trades, every coefficient will be significant. The plan does
not state what an independent observation is. Trades cluster in bursts, bursts cluster in
episodes, and episodes cluster in days. The effective sample size for inference about a
persistent effect is closer to the number of days than the number of trades. No block
bootstrap or clustered inference scheme is specified, and without one the confidence
intervals reported will be misleadingly narrow by orders of magnitude.

### Fragmented equities are included without a plan for fragmentation

The universe includes fragmented equities "to test whether the signal survives", but
nothing in the design handles the specific problems fragmentation creates: prints arriving
from venues with different latencies, a consolidated mid that is stale relative to the
fastest venue, and the question of which venue's book we would actually be quoting on.
The equity leg as specified will produce numbers, but they will not be interpretable.
Either build the multi-venue synchronisation properly, with a stated model of relative
feed latency, or drop the leg.

### Self-excitation modelling is a large detour

Stage 5 fits a self-exciting intensity model. That is a substantial piece of work,
sensitive to specification, and its contribution to the decision is unclear — a simpler
trailing-intensity feature captures most of the practical content. It reads as the most
intellectually interesting stage rather than the most decision-relevant one, and it should
be cut or deferred until after Stage 6 has established whether there is anything worth
refining.

### No treatment of what happens when we act on it

A strategy that systematically reacts to prints becomes a predictable participant. Once
we are known to pull quotes on adverse impulses, a small print becomes a cheap way to move
us, and once we are known to cross on strong impulses, a sweep becomes a cheap way to
sell to us. The plan contains no adversarial analysis and no monitoring plan for detecting
that our reaction function has been discovered. For a signal this visible, that is a
material omission rather than a refinement.

### What the plan gets right

Insisting on a single correctly ordered event stream before any modelling is exactly right;
separate trade and quote channels are the most common source of fictitious results in this
class of work. Auditing aggressor classification against ground truth, rather than assuming
a rule is adequate, is unusually disciplined. Separating permanent from transient response
is the correct organising question, since it determines which family of policies is even
worth simulating. And pre-registering a no-go on effects that vanish at production latency
is the single most valuable line in the document.


---

## My Verdict

### Plan

Good that it correctly identifies the mechanical relationship between the trade happening and the mid moving under full-trade conditions. Also good it splits the potential information channels to retain ways to use the information which are orthogonal to the mechanical elements.

Experiment Stage 3 is under specified and covers many things. Mixing trades from different instruments into a pooled model requires a way of normalising the data so they are comparable across securities which isn't specified. It also talks about testing the power-law scaling hypothesis, which is reasonable but should be a separate experiment to normalisation.

The research spec asked specifically about next-mid prediction and the plan suggests testing out to 30 seconds. I like the inclusion of the response curve, though I think this should be part of the evaluation suite rather than an experiment in its own right. The change seems to be a response to the implicit understanding that using trade information for next-mid is fraught with mechanical issues on one hand, and is extremely latency sensitive even when the modeling can overcome the mechanical challenges. Whilst Claude wasn't asked to overcome this as part of the research idea it has tried to do so anyway, which we could subjectively regard as positive or negative.

Issue about testing signal strength via a hypothetical trading strategy measuring P&L. A stronger evaluation suite would focus on markouts and conditional returns instead of mixing the problem of signal design with trading rule logic. Experimental stage 6 (how to trade it) is a separate problem to that of the signal construction, and stage 7 will be partly shown by the markout profile of the signal.

The pre-registered criteria have some magic numbers in them which isn't great.


### Critique

This is generally a good critique of the plan.

The critique identifies the latency sensitive nature of the trade signal and suggests that highlighting this aspect sooner would benefit the researcher which I agree with, though in my case from the perspective of an improved evaluation suite rather than trying to perform a full P&L simulation.

I like the section in the critique about being open to adjusting the target. It wasn't part of the spec but is the right instinct to overcome the overlapping signal+target issue which exists in the research question as posed.
