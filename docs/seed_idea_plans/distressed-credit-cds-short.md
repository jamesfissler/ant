# Expressing a Distressed-Equity View Through CDS Protection

## 1. Statement of the Idea

Company X appears unable to sustain its current operating model and is likely to be forced
into a restructuring. The equity is the natural short, but the borrow is scarce and
expensive, which makes the equity expression unattractive or unavailable at size. The
proposal is to express the same view further up the capital structure by buying credit
default swap protection on the company's debt, profiting if credit deteriorates or if a
credit event occurs.

The idea as stated contains an important slippage: buying CDS protection is not "shorting
their debt" in the sense of a cash short, and it is not equivalent to a short in the equity.
It is a long position in a specific, contractually defined protection payoff, referencing
specific obligations, subject to a definition of what counts as a credit event, and priced
as a running premium. The entire research question is whether that contract pays off on the
thesis we actually hold.

## 2. Economic Rationale

The thesis is that the market underprices the probability, or the timing, of a
restructuring. Where CDS can be superior to an equity short:

1. **Convexity.** If the restructuring happens, protection on a name trading near par can
   pay several multiples of the premium outlay. The equity short caps at 100% of a small
   notional.
2. **Cost of carry.** An expensive equity borrow is a recurring cost with no upside and no
   defined term. A CDS premium is a known, contractually fixed running cost with a defined
   maturity, which makes the position's carry budgetable.
3. **No recall risk.** A borrow can be recalled at the worst moment, forcing the position
   closed exactly when it is working. A CDS contract cannot be recalled.
4. **Defined trigger.** The payoff is tied to a contractual credit event rather than to the
   market's opinion of the equity, which can remain irrational for a long time.

Where CDS is inferior or dangerous:

1. **Basis risk against the thesis.** Our view is operational. The contract pays on a
   credit event as defined in the documentation. A company can restructure economically —
   dilutive equity raises, asset sales, distressed exchanges structured to avoid triggering
   — without a payout, or with a payout on terms we did not anticipate.
2. **Timing.** Premium accrues continuously; the payoff is discrete and may fall outside
   our contract's maturity. Being right two years late is a total loss on the position.
3. **Liquidity.** Single-name CDS on a stressed mid-cap credit may be thinly traded, with
   wide bid-offer, few dealers, and the possibility of no market at all in a crisis.
4. **Auction and deliverable dynamics.** Recovery is set at auction, and the auction price
   depends on the supply of deliverable obligations relative to net protection outstanding.
   This has been manipulated historically, and the recovery we realise is not the recovery
   we modelled.
5. **Counterparty, documentation and jurisdiction risk.** Which definitions apply, which
   obligations are deliverable, whether a specific restructuring counts as a credit event —
   these are legal determinations made by a committee, not economic ones.

## 3. Hypotheses

- **H1 (thesis validity).** The company's projected cash generation is insufficient to
  service its obligations across a realistic range of scenarios, and the shortfall arrives
  within a definable window.
- **H2 (mispricing).** The market-implied default probability from the CDS curve is lower
  than our fundamentally-derived probability, by a margin that exceeds the uncertainty in
  our own estimate.
- **H3 (instrument fitness).** The credit events that our thesis actually implies are
  covered by the applicable CDS definitions, and the obligations we expect to be
  restructured are deliverable.
- **H4 (tenor selection).** There is a point on the CDS curve where implied timing diverges
  most from our modelled timing, and that point offers a better risk-adjusted expression
  than the standard tenor.
- **H5 (capital structure relative value).** Comparing CDS against alternative expressions
  — cash bond short, equity puts, equity short where available, or a hedged capital
  structure trade — identifies which instrument best expresses the specific thesis after
  costs, and CDS is not automatically the winner.
- **H6 (executability).** Sufficient CDS liquidity exists to establish and, importantly, to
  *exit* the intended size at acceptable cost, including under stressed conditions.
- **H7 (carry survivability).** The position can be carried through the modelled timing
  distribution without the running premium consuming the expected payoff.

## 4. Data and Infrastructure Requirements

- **CDS pricing**: full term structure history for the name, with bid-offer, quoted sizes,
  and dealer counts. Composite marks alone are insufficient — they can suggest liquidity
  where none exists.
- **Applicable CDS documentation**: the governing definitions, the reference entity
  specification, the succession provisions, the deliverable obligation characteristics, and
  the standard coupon and upfront conventions.
- **Full capital structure map**: every outstanding obligation with amount, maturity,
  seniority, security, governing law, covenant package, call schedule, and cross-default
  provisions. This is the single most important input, because it determines both what a
  restructuring would look like and what is deliverable.
- **Cash bond prices and liquidity** across the structure, for the relative value work.
- **Company financials**, historical and with disclosed maturity schedules, liquidity
  sources, revolver capacity and covenant tests.
- **Historical precedent set**: comparable distressed situations, their restructuring
  paths, whether a credit event was determined, and the realised auction recoveries versus
  pre-event market expectations.
- **Equity options surface**, for the alternative-expression comparison.
- **Borrow data for the equity**, to quantify precisely how bad the equity alternative is
  rather than asserting it.
- **Counterparty and clearing arrangements**: which dealers will face us, margin terms, and
  whether the contract clears.

## 5. Analysis and Position Construction

**Fundamental work.** Build a cash flow model with an explicit maturity wall analysis:
when does the company need to refinance, how much, and under what conditions would that
refinancing fail. Produce a scenario set with probabilities — not a point forecast — and
carry the timing distribution explicitly, since timing is the position's dominant risk.

**Restructuring path analysis.** For each scenario, specify the *mechanism*: covenant
breach, missed coupon, distressed exchange, prepackaged filing, out-of-court amendment,
rescue financing. For each mechanism, determine with legal input whether a credit event
would be triggered under the applicable definitions, and which obligations would be
deliverable.

**Implied versus modelled probability.** Convert the CDS curve to implied default
probabilities under a stated recovery assumption, and compare tenor by tenor against our
modelled cumulative default probabilities. Report the comparison as a curve, since the
mispricing may exist at one tenor and not another.

**Recovery analysis.** Estimate recovery from the capital structure and asset base, and
separately estimate the *auction* recovery, accounting for the supply of deliverables
relative to likely net notional outstanding. Treat these as different numbers.

**Expression comparison.** Price each alternative expression on a common basis: expected
payoff under our scenario probabilities, cost to carry over the timing distribution,
maximum loss, liquidity to exit, and margin or capital consumed. CDS is selected only if
it wins this comparison.

**Sizing and carry budget.** Size such that the position can be carried through the full
modelled timing distribution, including its right tail, without breaching a pre-set loss
limit. Explicitly state the date by which the thesis must show progress, and the action if
it does not.

## 6. Experimental Design

This idea is a single-name, fundamentally-driven position rather than a statistical
strategy, so the "experiments" are structured tests of the thesis and of the instrument.

**Stage 0 — Compliance and information-source review.** Confirm that all inputs are public
or properly licensed, that no restricted-list conflict exists, and that the firm holds no
material non-public information on the name through any other engagement. Document. This
gates everything.

**Stage 1 — Capital structure and documentation review.** Map the structure; obtain legal
review of the CDS documentation against the specific restructuring mechanisms in our
scenario set. Deliverable: a table of scenario → credit event determination → deliverable
obligations → estimated recovery. If the most likely scenarios do not trigger, the trade is
dead here and nothing further is needed.

**Stage 2 — Fundamental scenario model.** Cash flow and liquidity model with the maturity
wall, producing a timing distribution rather than a date.

**Stage 3 — Implied versus modelled comparison.** The H2 test, per tenor.

**Stage 4 — Liquidity and execution audit.** Solicit indicative two-way markets in size
across tenors from multiple dealers. Measure realistic bid-offer. Explicitly test the exit:
what is the market for selling protection in this name in a stressed tape? Historical
analogues where possible.

**Stage 5 — Expression bake-off.** The H5 comparison across all instruments on a common
metric.

**Stage 6 — Backtest of the process, not the trade.** Apply the same framework
retrospectively to a set of historical distressed situations with known outcomes, blind to
the outcome where feasible, to calibrate how well this analytical process has performed.
This is the only genuine out-of-sample evidence available for a single-name idea, and it is
the difference between a strategy and an opinion.

**Stage 7 — Position plan.** Sizing, carry budget, entry schedule, stop conditions, and the
pre-committed review dates and thesis-invalidation triggers.

## 7. Evaluation Metrics and Pre-Registered Criteria

Metrics: modelled versus implied cumulative default probability by tenor; expected payoff
per unit of premium; maximum carry cost through the timing distribution's 90th percentile;
round-trip transaction cost as a fraction of expected payoff; estimated exit cost under
stress; and, from Stage 6, the historical hit rate and payoff profile of this analytical
process on comparable situations.

Pre-registered criteria:

- **Go** only if the primary restructuring scenarios trigger a credit event under the
  applicable definitions, confirmed in writing by legal review.
- **Go** requires modelled default probability to exceed implied by a stated margin at the
  chosen tenor, after accounting for the uncertainty in our own estimate.
- **Go** requires demonstrated two-way liquidity at the intended size from at least a
  stated number of dealers, and an estimated stressed exit cost below a stated bound.
- **Go** requires that CDS win the expression bake-off on risk-adjusted expected payoff.
- **No-go** if the carry through the 90th percentile of the timing distribution exceeds the
  position's loss limit.
- **No-go** if Stage 6 shows the analytical process has no demonstrated skill on comparable
  historical situations.

## 8. Deliverables and Timeline

- Week 1: compliance review; capital structure map.
- Weeks 2–3: legal review of documentation against scenarios.
- Weeks 3–5: fundamental scenario model.
- Week 5: implied versus modelled comparison.
- Week 6: liquidity and execution audit.
- Week 7: expression bake-off.
- Weeks 8–10: historical process backtest.
- Week 11: position plan and investment committee memorandum.

---

## Critique of the Plan

### "Obviously going bankrupt" is the premise and it is the weakest link

The seed idea asserts the conclusion. The plan builds machinery around it but never
seriously entertains that the market may be right and we may be wrong. A company visibly in
distress is the most heavily analysed kind of company; its CDS is priced by desks with
restructuring specialists and, frequently, with better information about the debt holders'
intentions than we have. The plan's H2 test compares our modelled probability against
implied, but with no treatment of the base rate: how often, historically, has an "obvious"
distressed thesis been right *on the timeline assumed*? Stage 6 gestures at this but arrives
in week eight. The single most valuable early exercise would be to assemble the population
of names that looked equally obvious three years ago and count how many restructured within
the equivalent window. That is a two-week task and it might end the project.

### Hard-to-borrow equity is a signal, not just an obstacle

The plan treats the expensive borrow as the reason to look elsewhere and proposes measuring
it only to "quantify precisely how bad the equity alternative is". That inverts the
information content. An extreme borrow rate means the short is extremely crowded, which
means the thesis is consensus, which means it is likely reflected in the CDS as well. The
plan should treat borrow cost as a *crowding indicator* feeding directly into H2's
plausibility, not as a mere cost comparison. If the equity is hard to borrow and the CDS
still looks cheap on our model, the most likely explanation is an error in our model, not a
mispricing that everyone else has missed in the more liquid instrument.

### The rescue-financing scenario is missing

The scenario set lists covenant breach, missed coupon, distressed exchange, prepack,
out-of-court amendment and rescue financing — but the plan treats rescue financing as one
path among several rather than as the principal threat to the trade. A distressed company
with any franchise value attracts liability-management transactions specifically structured
to avoid a credit event, and creditors with the incentive and the documentation flexibility
to execute them. These transactions have become the norm rather than the exception in
recent cycles. The position can lose while the thesis is entirely correct: the company can
be economically restructured, the equity can go to nearly nothing, and protection can expire
worthless. The plan's Stage 1 covers the determination question, but the *probability* of a
non-triggering restructuring is never estimated and never enters the go/no-go.

### Timing risk is acknowledged but the sizing rule is circular

The plan sizes so the position survives the 90th percentile of the modelled timing
distribution, and then applies a no-go if carry through that percentile exceeds the loss
limit. But the timing distribution comes from our own model, which is precisely the thing
whose reliability is unknown. If our modelled timing is optimistic — the characteristic
error in distressed analysis, where companies survive far longer than their fundamentals
suggest — then both the sizing and the no-go are calibrated to a distribution that is too
tight. The plan needs an external check: the historical distribution of time-from-obvious-
distress-to-credit-event across comparable situations, which should widen the modelled
distribution rather than being merely compared to it.

### Recovery and auction dynamics are separated but not modelled

The plan correctly distinguishes fundamental recovery from auction recovery. It then
provides no method for estimating the latter. Auction outcomes depend on the deliverable
supply relative to net notional protection outstanding, on which obligations remain
outstanding at the time, and on the behaviour of a small number of participants. Where net
notional data is available it should be tracked explicitly as a required input; it is
absent from the data requirements list. Since the payoff is (1 − recovery) × notional, an
error here scales the entire position's return linearly, and the error is systematically
in the unfavourable direction when protection is crowded.

### The liquidity audit's method may itself be costly

Stage 4 proposes soliciting indicative two-way markets in size from multiple dealers. In a
thinly traded single-name credit, that inquiry is itself information. Asking several
dealers for a size market in protection on a distressed name signals interest and can move
the price against us before we have traded. The plan needs an execution strategy for the
enquiry phase — staged, limited, and with an awareness that the audit and the entry may need
to be a single combined process rather than sequential stages.

### The historical process backtest is the best stage and is the least specified

Stage 6 — applying the framework blind to historical distressed situations — is the only
part of the plan that generates genuine evidence about our skill rather than about the
name. It gets three weeks and one paragraph. How is blindness enforced when the analyst
knows the outcomes of famous restructurings? How many situations constitute a meaningful
sample, given that severe distress events are not numerous? What counts as success — calling
the event, or calling the timing, or the position making money? Without answers, the stage
will produce a comfortable narrative rather than a calibration, and the no-go that depends
on it becomes unenforceable.

### Single-name concentration is never framed as a portfolio decision

The entire plan is about one position. It never asks the portfolio question: what fraction
of risk capital should sit in a single, illiquid, discretely-triggering, hard-to-exit
position whose payoff depends on a committee determination. Nor does it ask whether a
small basket of similar situations would be a better construction than a concentrated
single bet — spreading the timing risk that the plan itself identifies as dominant. The
memorandum in week eleven will present a trade; it should present an allocation.

### Counterparty and margin risk are listed and then dropped

Counterparty, clearing and margin terms appear in the data requirements and never again.
For a position that may run for years and that gains value precisely in market conditions
where dealers are under stress, margin mechanics matter: mark-to-market swings on the
protection leg require posting, and a position that is right but volatile can generate
funding demands at exactly the wrong time. There is no funding or margin stress analysis
anywhere in the design.

### What the plan gets right

Refusing to equate "shorting the debt" with buying protection, and making the contractual
payoff definition the first substantive stage, is exactly correct — the mismatch between an
operational thesis and a contractual trigger is the standard way this trade fails. Making
legal confirmation a hard gate, with the trade dead at Stage 1 if the primary scenarios do
not trigger, is the right level of discipline. The expression bake-off, which forces CDS to
win against alternatives rather than being assumed, protects against instrument
attachment. Separating fundamental from auction recovery shows a grasp of where the payoff
actually comes from. And requiring a timing distribution rather than a date, with the carry
budget built to survive its tail, addresses the risk that most often kills an otherwise
correct distressed thesis.


---

## My Verdict

### Plan

Correctly identified that buying a CDS is not the same as going short the debt. Has it's own criteria for payoff and the buyer pays a premium - this was a key purpose of the question being asked to check if the research plan could highlight this.

The plan also exposes a real risks about the differences between expected vs realised delivery along with timing risks (the idea can be right but too late vs the maturity of the CDS contract purchased) and liquidity concerns.

Legal risks are mentioned early, in particular the possibility of restructuring events that might lead to no payoff from definition of the CDS contract even if we are directionally correct about our viewing being that the company is in trouble. The plan mentions this but then doesn't really flesh it out as a risk factor. It is important because distressed debt situations often involve other lenders who may not act in good faith vs their fellow lenders. This exposes a different risk vector for the trade where actors other than the company need to be modelled to estimate whether they might affect the likelihood of the trade being profitable.

### Critique

The critique of the plan is good and covers a number of relevant areas, including options for faster rejection of the trade idea.