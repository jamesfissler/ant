# Buy the Rumour, Sell the News: Trading Anticipation Rather Than Announcement

## 1. Statement of the Idea

Buy a security in advance of an expected favourable announcement, and sell into the
announcement itself. The premise is that the price drifts upward as the market's subjective
probability of the good outcome rises during the anticipation window, and that the
announcement — when it merely confirms what was already expected — delivers no further
gain and often a reversal, as positioning unwinds and the uncertainty premium collapses.

The tradeable object is therefore not the news. It is the *change in expectation* before
the news, and the *positioning unwind* at the news. The research question is whether that
pattern is systematic enough, across a definable population of events, to be traded as a
repeatable strategy rather than as a set of discretionary bets.

## 2. Economic Rationale

Three effects can produce the pattern:

1. **Gradual information revelation.** Between the first credible hint and the formal
   announcement, information leaks through supply-chain data, regulatory filings, expert
   channels and price action itself. Expectations update continuously, and the price drifts
   with them. The announcement then contains little residual surprise.
2. **Uncertainty premium collapse.** Ahead of a binary event, the asset carries an
   elevated risk premium and elevated implied volatility. At the announcement the
   uncertainty resolves and the premium is released, which mechanically pressures the
   price of the underlying if that premium was priced as a discount, and unambiguously
   deflates options.
3. **Positioning and reflexivity.** Anticipatory buyers accumulate before the event. Their
   exit is concentrated at the moment of the announcement, when liquidity is temporarily
   abundant. The selling pressure at that moment is a mechanical consequence of the
   strategy being popular — which means the effect is partly self-generated and its size
   depends on how crowded the trade is.

The critical structural point is that mechanism 3 both creates the effect and limits it.
If enough capital runs the strategy, the anticipation drift is arbitraged forward until it
begins before we can identify the event, and the unwind at the announcement becomes so
sharp that exiting into it is costly. The strategy's viability is therefore a function of
its own crowding, which must be measured rather than assumed.

Two hazards must be stated plainly. First, trading on a "rumour" that constitutes material
non-public information obtained improperly is not a strategy — it is a compliance event.
This project restricts itself strictly to publicly observable anticipation: scheduled event
calendars, public reporting, published expectations, market-implied probabilities, and
price and options data. Any signal source that cannot be sourced to a compliant, auditable,
public channel is excluded from the design, not merely flagged. Second, the strategy is
short a tail: it accumulates small gains while occasionally being long into an
announcement that is far worse than expected.

## 3. Hypotheses

- **H1 (drift).** Across a population of pre-identifiable, scheduled or scheduled-window
  events, there is positive abnormal return in the anticipation window, conditional on a
  publicly observable measure of favourable expectation.
- **H2 (no residual announcement return).** Conditional on that same expectation measure,
  the abnormal return from the announcement onward is not positive, and may be negative,
  making pre-announcement exit weakly dominant.
- **H3 (exit timing).** The optimal exit is at or immediately before the announcement, and
  the return to holding through it is negative net of the increased risk.
- **H4 (expectation measurability).** A publicly constructible expectation proxy — from
  option-implied distributions, from published consensus, from prediction-market or
  market-implied probabilities where they exist — has predictive power for the drift.
- **H5 (event-type heterogeneity).** The effect differs materially by event type, and the
  pooled effect is not the right object; some categories will show it strongly and others
  not at all.
- **H6 (options dominance).** For most event types, the effect is more cleanly and more
  cheaply expressed through the options surface — where the uncertainty premium is
  directly observable and directly tradeable — than through the underlying.
- **H7 (economic significance).** After costs, borrow, gap risk and the capital tied up
  through the anticipation window, the strategy delivers a return per unit of risk that
  justifies the tail it carries.

## 4. Data and Infrastructure Requirements

- **Point-in-time event calendars** with the date each event became publicly scheduled, not
  merely the date it occurred. This distinction is the whole study: a backtest that
  identifies events from a modern calendar is trading on knowledge that the event would
  happen.
- **Categorised event universe**: earnings, scheduled regulatory decisions, product
  approvals with statutory decision dates, index reconstitution effective dates, scheduled
  central bank and macro releases affecting single names, investor days, and lock-up
  expiries. Each category with its own timestamped announcement time.
- **Published consensus expectations with revision history and timestamps**, so the
  expectation proxy is point-in-time.
- **Options data**: full surface with timestamps, open interest, and volume, to construct
  implied distributions and to price the uncertainty premium. Required for H6 and for
  measuring premium collapse.
- **Intraday trade and quote data** around announcement times, at sufficient resolution to
  study exit execution in the minutes surrounding release.
- **Survivorship-free equity universe** with delistings and terminal returns.
- **Borrow availability and cost**, historical.
- **A compliance-reviewed catalogue of permissible signal sources.** Every input must be
  attributable to a public, licensed, auditable source. This is a hard gate on the project,
  and it is reviewed before data acquisition begins, not after results are produced.
- **News and filings archive with precise publication timestamps**, for identifying when
  information genuinely became public.

## 5. Strategy Construction

**Event population.** Restricted to events that are (a) publicly scheduled or have a
publicly known decision window, and (b) identifiable at least `d` days before the event
using only information available at that time. Categories are analysed separately.

**Expectation proxy.** Constructed per category from permissible public sources:

- Published consensus level and the direction of recent revisions.
- Option-implied probability of a favourable outcome, where the surface supports it,
  measured as risk-neutral probability mass above a threshold.
- Market-implied probability from any liquid, public, event-linked instrument.
- The security's own abnormal return and abnormal volume over the anticipation window to
  date — with the caveat that this is partly the thing we are trying to predict, so it
  must be tested separately rather than blended in silently.

**Entry.** At a pre-specified point in the anticipation window, sized inversely to the
security's volatility and to the expected gap risk of the event, and capped as a fraction
of the name's ADV.

**Exit.** The primary specification exits before the announcement. Alternatives — exit at
the announcement, exit shortly after, hold through — are tested as explicit variants, since
H3 is a hypothesis, not an assumption.

**Expression.** Both underlying and options versions are constructed. The options version
targets the uncertainty premium directly: long exposure through the anticipation window,
flat before the premium collapse.

**Hedging.** Market and sector exposure hedged, so the measured return is the event
component and not a directional bet on the market over the anticipation window.

## 6. Experimental Design

**Stage 0 — Compliance gate.** Catalogue every intended data source and obtain sign-off
that each is public, licensed, and permissible. Any source that fails is removed. No
research proceeds on an unapproved source. Document the review.

**Stage 1 — Event universe construction and point-in-time validation.** Build the event
calendar with schedule-announcement timestamps. Validate by sampling: for a random sample
of events, confirm from the filings archive that the event was publicly known at the date
our calendar claims. Report the error rate; a high rate invalidates the study.

**Stage 2 — Unconditional event study.** Abnormal returns around events by category, with
the anticipation window and the announcement window measured separately, market and sector
hedged. This establishes the raw shape and is purely descriptive.

**Stage 3 — Conditional event study.** Repeat conditioning on the expectation proxy. Test
H1, H2, H4. Report per category, with sample sizes, since some categories will have too
few events to support any conclusion.

**Stage 4 — Exit timing study.** Estimate the return path minute by minute around the
announcement, including the execution cost of exiting into it. Test H3 against the
alternatives. The cost of exiting at the moment of peak activity is measured from the
intraday data, not assumed.

**Stage 5 — Options expression.** Measure the implied volatility path through the
anticipation window and its collapse at announcement. Compare the risk-adjusted return of
the options expression against the underlying expression. Test H6.

**Stage 6 — Portfolio simulation.** Full strategy across categories with position sizing,
hedging, borrow constraints, costs, and capital charges for the holding period. Walk-
forward, with all parameter choices made on training data only.

**Stage 7 — Tail and crowding analysis.** Distribution of outcomes with attention to the
left tail. Identification of the worst events in-sample and their common features.
A crowding proxy — anticipatory volume and open interest build — is constructed and tested
as a conditioner: is the effect weaker when the trade is visibly crowded?

**Stage 8 — Holdout.** Single evaluation of the final specification on an untouched final
period against pre-registered criteria.

## 7. Evaluation Metrics and Pre-Registered Success Criteria

Metrics: hedged abnormal return per event by category; hit rate and win/loss size ratio;
return per unit of capital-days deployed; Sharpe after all costs; the distribution of the
worst 5% of outcomes; execution cost of the exit; and the comparison of options versus
underlying expression on risk-adjusted return.

Pre-registered criteria:

- **Go** if net-of-cost hedged return per event is positive with a lower confidence bound
  above zero, in at least two independent event categories, with the effect present in
  both halves of the out-of-sample period.
- **Go** requires that the worst 5% of outcomes not exceed a stated fraction of cumulative
  gains, since the strategy's viability is a tail question.
- **No-go** if the effect exists only in the pooled sample and in no individual category,
  which would indicate the pooling is manufacturing it.
- **No-go** if the effect disappears once the expectation proxy excludes the security's own
  price action, which would make the strategy a momentum strategy under another name.
- **No-go** on any source that fails the compliance gate, irrespective of results.

## 8. Deliverables and Timeline

- Week 1: compliance gate and source catalogue.
- Weeks 2–4: event universe construction and point-in-time validation.
- Week 5: unconditional event study.
- Weeks 6–7: conditional event study and exit timing.
- Week 8: options expression study.
- Weeks 9–11: portfolio simulation.
- Week 12: tail, crowding, holdout, recommendation.

---

## Critique of the Plan

### The idea's colloquial form and the plan's tradeable form are different strategies

The original notion is about rumours — unscheduled, informal, often non-public information
flow ahead of an announcement. The plan, quite properly, refuses that version and
substitutes a strategy about *publicly scheduled* events with *publicly measurable*
expectations. That substitution is the right call, but it should be stated as a
reformulation rather than presented as an implementation, because the two have very
different prospects. The publicly-scheduled version is a well-populated corner of the
market with many participants and thin residual edge; the informal version is where the
colloquial saying comes from and is not available to us. Readers of this plan should not
conclude that a negative result disproves the folk wisdom — it would only show that the
compliant subset of it is not tradeable.

### The event population may be too small for the statistics claimed

The plan analyses by category, which is correct, and then requires effects in at least two
independent categories. But once categories are separated and the sample is restricted to
events identifiable `d` days in advance with a constructible expectation proxy, several
categories will have only tens of usable events per year. Event-study standard errors with
that sample size are wide, and the abnormal returns being sought are small relative to
single-name volatility over a multi-day window. The plan never states an expected sample
size per category or performs a power calculation. It is entirely possible that the study
as designed cannot detect an economically meaningful effect even if one exists, and that
should be established in week one rather than discovered in week eleven.

### The expectation proxy is doing contradictory jobs

H4 requires an expectation proxy that predicts the drift. But if the proxy is
option-implied probability or consensus revisions, those are themselves the market's
updating process — the very drift we are trying to trade. Conditioning on them risks
selecting events where the drift has already occurred, and the measured "predictive power"
is then partly mechanical. The plan half-recognises this by isolating the security's own
price action as a separate component with its own no-go, which is good; but it does not
apply the same scepticism to option-implied and consensus measures, which have the same
problem in a subtler form. Each proxy component needs to be tested for whether it predicts
*future* drift or merely records *past* drift, and the design does not specify that test.

### The uncertainty premium argument is stated backwards for the underlying

Mechanism 2 claims that the collapse of the uncertainty premium at announcement pressures
the underlying's price. For options this is straightforward and well documented. For the
underlying it requires that the event risk was priced as a discount to fair value, which
is a much stronger claim and is not generally true — for many favourable-outcome events the
pre-event price is elevated, not discounted. The plan carries this reasoning into the
underlying expression without testing it. Stage 5 tests the options expression, but nothing
tests whether the premium mechanism operates in the underlying at all, and the strategy's
primary expression rests on it.

### Exit execution cost is measured but the measurement is not representative

Stage 4 measures the cost of exiting into the announcement from historical intraday data.
That measurement describes the market as it was *without our exit in it*. The whole premise
of mechanism 3 is that anticipatory positions unwind simultaneously at the announcement. If
the strategy runs at any size, our exit joins the crowd it is trying to sell into, and the
historical cost estimate is an underestimate by an amount that grows with our size and with
the strategy's popularity. The capacity implication is severe and is not addressed anywhere
— there is no capacity study in the plan at all, which for a strategy defined by a
concentrated exit moment is a significant omission.

### Crowding is measured as a conditioner but not as a trend

Stage 7 builds a crowding proxy and tests whether the effect is weaker when the trade is
crowded. That is useful cross-sectionally. It does not address the time-series question:
has the anticipation drift been arbitraged progressively earlier over the sample, so that
by the end of the period it precedes our identification date entirely? A year-by-year
decomposition of where in the anticipation window the drift occurs would answer this
directly and would be more decision-relevant than the cross-sectional conditioner.

### The hedging specification will absorb much of the effect

The plan hedges market and sector exposure so that the measured return is the event
component. Over a multi-day anticipation window, single-name idiosyncratic returns are
large and the hedge removes only a modest fraction of the variance. The signal-to-noise
ratio on a per-event basis will be poor, and the strategy's Sharpe depends almost entirely
on the number of independent events available for diversification — which returns to the
unaddressed sample size problem. The plan should compute, in advance, how many independent
events per year are required to achieve a target Sharpe given the observed per-event
volatility. That single calculation would do more to determine feasibility than most of the
stages listed.

### Category heterogeneity invites a multiple-comparison problem the criteria do not control

Requiring an effect in "at least two independent event categories" sounds like a
robustness requirement. If there are eight categories, requiring two to show an effect at
conventional significance is close to the expected number under the null. The criterion
needs either an explicit correction for the number of categories tested or a pre-designation
of which two categories carry the hypothesis, chosen on prior reasoning before results.

### The compliance gate is correctly placed but stated too briefly

Making compliance a gate at Stage 0 rather than a review at the end is exactly right. But
the section is a paragraph, and the hard cases are not addressed: expert networks,
alternative data whose provenance is unclear, sell-side commentary distributed to a subset
of clients, and information derived from order flow that is not ours. Each of these is a
realistic candidate for an "anticipation" signal and each raises questions that need an
answer before, not during, the research. The plan should enumerate the specific categories
of source it is ruling out, so that the gate is auditable rather than aspirational.

### What the plan gets right

Refusing to build the strategy on any source that cannot be publicly and auditably sourced,
and making that a gate rather than a caveat, is the correct treatment and the only
defensible one. Separating the anticipation window from the announcement window and
treating the exit as a hypothesis rather than an assumption is the right structure for an
idea whose entire claim is about timing. Requiring category-level results rather than a
pooled effect prevents the most likely form of false positive. The no-go condition on the
expectation proxy reducing to the security's own price action directly targets the risk
that the strategy is momentum in disguise. And identifying the options surface as probably
the cleaner expression, then testing it head-to-head rather than assuming it, is a genuine
insight about where the premium being harvested actually lives.


---

## My Verdict

### Plan

This was an obviously flawed idea with no real substance behind it other than repeating folklore. Claude correctly identified the adage, and the legal risks with potential poor interpretations of it.

### Critique

The critique is good and is particularly correct to highlight the explicit reformulation of the plan under safety constraints. It is further able to identify issues with the reformulated plan.