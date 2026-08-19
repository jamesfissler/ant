# Sector Mean Reversion: Market-Neutral Relative Value Within Industry Groups

## 1. Statement of the Idea

Group stocks by industry sector. Take as the null that, on average, stocks within a sector
move together — they share exposure to the same demand conditions, input costs, regulation
and investor flows. Deviations from that common movement are then, at least in part, noise
that will reverse. The strategy is to short the stocks that have outperformed their sector
basket and buy those that have underperformed, sized so that the resulting portfolio is
neutral to the market and, ideally, to the sector itself.

## 2. Economic Rationale

The reverting component is supposed to come from three sources:

1. **Liquidity provision.** A large uninformed order in one name pushes it away from its
   peers. Whoever takes the other side is compensated by the reversion when the pressure
   ends. Under this account, the strategy is a paid service, and its return is a
   liquidity premium rather than a forecasting edge.
2. **Slow information diffusion.** Sector-wide news is impounded into different names at
   different speeds; the laggards catch up. This produces a co-movement effect that looks
   like reversion of the leaders relative to the basket.
3. **Over-reaction to idiosyncratic news.** Attention-driven flows push a name too far on
   its own news, and it partially retraces.

The opposing force is the one that determines whether the strategy is viable at all: some
divergences are *correct*. A stock that underperforms its sector because its margins are
genuinely deteriorating should keep underperforming. The strategy is therefore short a
distribution with a long left tail — it wins small and often, and loses large and rarely,
which is the classic risk profile of systematic mean reversion. Everything that follows is
really about separating the reverting divergences from the informative ones, and about
surviving the times when we cannot.

## 3. Hypotheses

- **H1 (existence).** Residual returns relative to a sector basket exhibit negative
  autocorrelation over horizons from one day to two weeks.
- **H2 (attribution).** The effect is stronger following high-volume, low-news divergences
  than following divergences accompanied by company-specific news, consistent with the
  liquidity-provision account.
- **H3 (definition sensitivity).** The result is materially sensitive to how the peer group
  is defined; a statistical peer group (returns-based) outperforms a classification-based
  one (GICS or similar) because official classifications are coarse and slow to update.
- **H4 (residualisation).** Reversion measured on returns residual to estimated common
  factors is stronger and more stable than reversion measured on raw relative returns,
  because the latter conflates reversion with unintended factor bets.
- **H5 (asymmetry).** The short leg behaves differently from the long leg — shorting a
  strong outperformer is a different trade from buying a weak underperformer — and the
  two legs' returns, borrow costs and tail risks must be reported separately.
- **H6 (capacity and costs).** Net of transaction costs, borrow costs and financing, the
  strategy retains a meaningful Sharpe ratio at a stated capital level.
- **H7 (regime).** The strategy's returns are conditionally negative in periods of sharp
  dispersion increase, and this exposure is measurable and hedgeable at least in part.

## 4. Data and Infrastructure Requirements

- **Prices and returns**: daily, and intraday closing auction prices, fully adjusted for
  splits, dividends and other corporate actions.
- **Survivorship-free universe**: including delistings, mergers, bankruptcies, and their
  terminal returns. This is a hard requirement; without it, the short leg is systematically
  flattered because the worst outcomes are missing.
- **Point-in-time sector classifications**: with historical revision dates. Using today's
  classification for a stock that was reclassified two years ago is a subtle and
  meaningful look-ahead.
- **Point-in-time index membership**, for benchmark and for index-rebalance flow controls.
- **Borrow data**: historical availability and fee, by name and by date. Without it the
  short leg is fiction, since the names that diverge most are frequently the names that
  are hardest and most expensive to borrow.
- **Corporate event calendar**: earnings dates, guidance, M&A announcements, index changes,
  secondary offerings — all point-in-time.
- **Fundamental data with point-in-time snapshots**, for the news/no-news conditioning in
  H2 and for the risk model.
- **Risk model**: either a vendor factor model or an internally estimated one; if internal,
  it must be estimated only on data available at the time.
- **Cost model**: historical spreads, ADV, and a market impact model calibrated to our own
  execution history.

## 5. Strategy Construction

**Peer group definitions** (all tested, one pre-selected as primary before results are
seen):

- Official classification at the industry level.
- Statistical peers: for each name, the `k` names with highest trailing correlation of
  residual returns, re-estimated monthly on a rolling window.
- Hybrid: statistical peers constrained to the same broad sector.

**Signal.** For stock `i` in group `g` at time `t`:

- Compute the residual return `e_{i,t}` over a lookback `L` after removing exposure to the
  market and to estimated common factors, and to the group return itself.
- The raw signal is `−z(e_{i,t})`, cross-sectionally standardised within the group.
- Lookbacks tested: 1, 3, 5, 10, 20 trading days. Both overlapping and non-overlapping.
- Conditioners applied as multiplicative modifiers or as exclusions:
  - Exclude names with a company-specific news event within the lookback (the H2 test).
  - Down-weight names whose divergence is accompanied by unusually low volume, which is
    more likely to be information than liquidity demand.
  - Down-weight names near earnings dates.
  - Exclude names subject to pending M&A, where the price is anchored to a deal rather
    than to a sector.

**Portfolio construction.** Optimise to maximise expected signal exposure subject to:
market beta neutrality; sector neutrality; factor exposure limits against the risk model;
per-name position limits as a fraction of ADV; a turnover penalty; and a borrow-
availability constraint on the short leg. The optimiser, not the raw signal, is the
strategy — a fact the evaluation must respect by never reporting raw-signal returns as if
they were achievable.

## 6. Experimental Design

**Stage 0 — Data integrity.** Verify survivorship-free coverage by reconciling universe
counts against historical index constituent files. Verify point-in-time integrity of
classifications by sampling known reclassifications. Produce a data quality report; this
gates everything else.

**Stage 1 — Residual reversion measurement.** Panel autocorrelation of residual returns by
horizon, by peer-group definition, and by market-cap tercile. This tests H1 and H3
directly and cheaply, before any portfolio machinery exists.

**Stage 2 — Conditioning study.** Split residual divergences by news/no-news, by volume,
and by proximity to earnings. Test H2. Report the reversion strength per bucket with
sample sizes, since the interesting buckets are the small ones.

**Stage 3 — Naive backtest.** Simple decile long/short within sector, equal weighted,
daily rebalance, no costs. This exists only as a reference point and its results are
explicitly labelled as unachievable.

**Stage 4 — Realistic backtest.** Full optimiser, with all constraints, with costs from
the calibrated impact model, borrow costs from historical data, financing, and execution
at the closing auction or via a VWAP schedule with realistic slippage. Walk-forward with
purged, embargoed parameter selection.

**Stage 5 — Risk decomposition.** Decompose realised P&L into: reversion alpha, residual
factor exposures, sector drift, and cost drag. If a large fraction of returns is
attributable to unintended factor exposure, the strategy is a factor bet wearing a
reversion costume and must be re-specified.

**Stage 6 — Stress and tail analysis.** Performance in pre-identified stress windows;
drawdown distribution; worst-name contribution analysis; the behaviour of the strategy
around the largest single-name events in the sample. Explicitly examine crowding-driven
unwinds, in which relative value strategies lose simultaneously across the industry.

**Stage 7 — Capacity.** Re-run Stage 4 at multiple capital levels to locate the point at
which impact costs consume the edge.

## 7. Evaluation Metrics and Pre-Registered Success Criteria

Metrics: net Sharpe after all costs; annualised net return per unit of gross exposure;
turnover; maximum drawdown and time to recover; return attribution by source; hit rate and
win/loss size ratio; borrow cost as a fraction of gross return; capacity at a defined
impact tolerance; and correlation to existing book.

Pre-registered criteria:

- **Go** if net Sharpe after all costs exceeds 1.0 over the full out-of-sample period,
  with positive net returns in at least 60% of quarters, and with at most 30% of the gross
  return attributable to identifiable factor exposures rather than residual reversion.
- **Go** requires capacity above a stated minimum at an impact tolerance of no more than
  25% of the gross edge.
- **No-go** if the strategy's returns are indistinguishable from a short-volatility profile
  once dispersion regimes are controlled for.
- **No-go** if borrow costs consume more than half the gross edge in the median year.

## 8. Deliverables and Timeline

- Weeks 1–3: data assembly and integrity report.
- Week 4: residual reversion measurement.
- Week 5: conditioning study.
- Week 6: naive backtest reference.
- Weeks 7–10: realistic backtest with optimiser and cost model.
- Week 11: risk decomposition and stress analysis.
- Week 12: capacity study and written recommendation.

---

## Critique of the Plan

### The premise contains an unexamined assumption about the return generating process

The idea assumes that a stock's divergence from its sector is predominantly noise. For a
large fraction of divergences that is simply false, and the plan's conditioning stage —
excluding names with company-specific news — is a much weaker filter than it appears.
Company-specific information arrives continuously and mostly without a datable news event:
a competitor's disclosure, a channel check, a broker's revision, a slow institutional
reallocation. The news-event filter will remove press releases and earnings, and leave
untouched the majority of informed divergence. The plan should be honest that it cannot
separate noise from information reliably, and should shift emphasis from filtering toward
position sizing and tail control, which are the only defences that work when the filter
fails.

### The strategy is short a tail and the plan's metrics under-report this

Net Sharpe as the primary criterion is the wrong headline statistic for a payoff that is
frequent-small-wins, rare-large-losses. Sharpe over a sample without a full-scale
relative-value unwind will look excellent and will be misleading. The plan does include
stress windows and drawdown analysis, but as Stage 6 diagnostics rather than as gating
criteria. At minimum, the go/no-go should include a maximum-drawdown criterion and a
statistic sensitive to the left tail. The one genuinely good criterion here — "no-go if
returns are indistinguishable from a short-volatility profile" — is stated without any
specification of how that test would be conducted, which makes it unenforceable as written.

### Sector neutrality and the signal may be in direct conflict

The portfolio construction imposes sector neutrality, but the signal is defined *within*
sector. Imposing neutrality against a risk model whose sector definitions differ from the
peer-group definitions used to build the signal will systematically cancel part of the
signal, and the plan never reconciles the two taxonomies. If the primary peer group is
statistical rather than classification-based — as H3 anticipates — then the risk model's
sector constraints are neutralising exposures the signal never intended to take, and
possibly neutralising the signal itself. This needs resolving in the design: either the
risk model's groupings must align with the signal's, or the constraints must be expressed
in terms of the statistical groups.

### Borrow is treated as a cost when it is really a selection effect

The plan sources historical borrow fees and constrains the short leg by availability, which
is better than most. But it treats borrow as a drag applied to an otherwise-determined
portfolio. In reality, hard-to-borrow status is informative: the names that are expensive
to short are frequently the names with the largest expected reversion, and the fee is the
market's price for exactly the trade we want. Constraining them out removes the best trades
and biases the backtest upward relative to a strategy that could actually trade them; not
constraining them out biases it upward for a different reason. Neither is addressed. A
clean approach reports the strategy twice — with and without the hard-to-borrow universe —
and treats the difference as a measure of how much of the edge is unreachable.

### Crowding is named once and not modelled

Sector-relative reversion is among the most widely run systematic strategies. Its
distinguishing failure mode is that everybody exits at once, and that the losses arrive
precisely when the signal looks strongest. The plan mentions crowding-driven unwinds inside
Stage 6, but has no measurement of crowding as a state variable, no leading indicator, and
no policy response. A serious version would include a crowding proxy — dispersion of
residual returns, short interest concentration, or the co-movement of relative-value
proxies — and pre-specify a de-gearing rule. Without that, the backtest will show the
unwinds as unlucky months rather than as the structural cost of running the strategy.

### The peer group is selected by search but the plan pre-commits to one

Stage 1 tests three peer-group definitions and H3 predicts a winner, yet the plan also
requires selecting a primary definition "before results are seen". These two instructions
are in tension. If the primary is genuinely pre-selected, Stage 1's comparison is not used
for selection and its purpose is unclear; if the comparison drives selection, the
pre-commitment is nominal. The design needs to be explicit: run the comparison on a
dedicated early sample, select there, and never revisit — otherwise the peer-group choice
becomes one more degree of freedom in a study that already has many.

### Cost modelling for a mid-cap short-horizon strategy is the whole answer

Reversion at 1–10 day horizons in names small enough to diverge meaningfully implies high
turnover in less liquid stocks. The edge per trade will be small relative to spread plus
impact. The plan calibrates an impact model to our execution history, which is right, but
our history is presumably drawn from the trades we chose to do — usually the easier ones.
Extrapolating that model to the harder names and the higher participation rates this
strategy would demand is exactly where impact models fail, and they fail optimistically.
The capacity study in Stage 7 inherits this bias in full. A sensitivity analysis over
impact model parameters, reporting the parameter value at which the strategy breaks even,
would be more informative than a single capacity number.

### Twelve weeks understates the data work

Survivorship-free universes with point-in-time classifications, point-in-time index
membership, historical borrow, and a point-in-time event calendar constitute a serious data
engineering project on their own. Three weeks is optimistic unless this infrastructure
already exists in a validated state. If it does, the plan should say so; if it does not,
the schedule is not credible and the compression will land on the cost and risk work at
the end, which is where the answer lives.

### Return attribution threshold is arbitrary and probably too generous

Allowing up to 30% of gross return to come from identifiable factor exposures is a large
allowance. A strategy deriving 30% of its return from unintended factor bets is
substantially a factor product, and would be better replaced by the factor exposure itself,
which is cheaper to run. The threshold should be tightened, and the residual should be
tested against a matched portfolio of the identified factors rather than merely decomposed.

### What the plan gets right

Requiring the survivorship-free universe and point-in-time classifications, and gating all
subsequent work on a data integrity report, addresses the two errors that most often
produce spurious results in this class of strategy. Distinguishing explicitly between the
naive decile backtest and the achievable optimiser-based one, and labelling the former as
unachievable, prevents the most common form of self-deception. Treating the optimiser as
part of the strategy rather than as post-processing is the correct framing. And separating
long-leg from short-leg performance, borrow costs and tails is exactly the decomposition
that determines whether the strategy is fundable.


---

## My Verdict

### Plan

Got the economic rationale right. H3 is particularly on-point, the construction of the baskets can materially change the realised performance of a signal like this. The plan could be more explicit about methodologies here when discussing peer group definitions. It can be valid to run multiple versions of the signal with competing peer group definitions rather than fixating on a single generative rule.

Requirements for point-in-time data are particularly important, as is the survivorship concern through the data. This is a reference data heavy signal and the requirements are capturing this. There is a weakness which is that the length of the data history is not explicitly specified. For daily data we require many years worth of data since we only have approximately 250 sample points per year. Given that the lookbacks being tested range up to 20 business days that reduces the number of independent periods to ~12~ per year which is a very small number to be trying to fit a model to, hence the requirement for a large number of years of data history.

The plan identifies that the optimiser is key to this being a good signal but it doesn't talk about how to parameterise it. A number of constraints are specified in the Portfolio Construction section but they are never explored, instead simply used as though there is a golden value for each of them in Experiment Stage 4.

The magic numbers in the pre-registered criteria are a problem.

### Critique

I disagree with the first critique that the plan is always conditioning on excluding names with company specific news. I see a hypothesis to be tested (H2) about whether excluding news is an improvement or not but did not interpret the plan that this is always done, rather it would be tested in Experiment Stage 2 to determine whether that conditioner is warranted. To me this is a comprehension failure of the critique.

The statements about whether the reporting metrics are reasonable and about the interaction between sector selection and risk management are both valid.

I do not fully agree with the 'borrow is a cost when it is really a selection effect' statement. A counter argument to the one made by Claude in its critique is that a stock might be hard to borrow because it is going to zero and therefore fully expected to further deviate from the sector it belongs to rather than return to the mean after having a period of being over-valued.

The cost-modelling step is conflating a valid concern about execution cost modeling with the existence of the signal itself but to me these are orthogonal concerns. It is quite reasonable to separate the identification of "I have an opportunity" from "How efficiently can I execute this opportunity?". Whilst both are important for full monetisation of a trading strategy trying to solve all problems within a single piece of research is likely to lead to slow and poor progress. For me this was another example of poor comprehension/hallucination because the work plan states an assumption to use a pre-specified cost model (execution stage 4) rather than calibrating it as part of the work.