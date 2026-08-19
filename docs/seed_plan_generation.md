## Prompt for Claude used to generate the research plans

In the `docs` folder you will find `seed_ideas.md` which contains a list of independent research ideas. For each idea in the file you need to produce a plan in a separate markdown file in `docs/seed_idea_plans` where the filename succinctly represents the idea. Having produced the plan you should critique it and write the critique into the same file in a separate section after the plan. Do not cross-reference research ideas with one another in either the plans or the critiques, they should be treated completely independently.

## Using the Claude Code VSCode plugin

The prompt was run with effort set to High, thinking mode is On, and the model chosen was the default model (reported as Opus 5 with 1M context)

## Claude Observation

I had to refine the seed ideas, my `CLAUDE.md` instructions, and the prompt I gave to Claude over the course of a few attempts to get a more useful response. Some early failures including Claude not respecting my statement about independent research ideas and finding that it had cross-referenced different ideas in the different research plans. Additionally I noticed a tendency for it to want to build the full experimental infrastructure from scratch during its plan rather than assuming the existence of a research platform that could be used for the work so I made that explicit to encourage the plans to focus more on the research idea and less on building the environment.

## Claude's output

Nine plans written, one per idea, in docs/seed_idea_plans/:

| File | Idea |
| --- | --- |
| order-book-imbalance.md | Book imbalance as short-horizon predictor |
| trade-impulse-mid-price-signal.md | Trade impulse → next mid move |
| order-flow-imbalance-alpha-extension.md | Extending OFI for incremental alpha |
| sector-mean-reversion.md | Market-neutral within-sector relative value |
| buy-the-rumour-sell-the-news.md | Trading anticipation vs. announcement |
| related-security-momentum.md | Intraday lead/lag from related names |
| distressed-credit-cds-short.md | Distressed thesis expressed via CDS protection |
| merger-arbitrage-deal-spread.md | Post-announcement deal spread capture |
| ai-thematic-basket.md | AI value-chain long exposure |

Each file follows the same shape: idea statement, economic rationale (including the mechanism that would make it fail), numbered hypotheses, data/infrastructure requirements, signal or position construction, staged experimental design, pre-registered go/no-go criteria, timeline — then a ## Critique of the Plan section attacking the plan on its own terms, closing with what it gets right.

Three things worth flagging about the content:

Two ideas were reformulated rather than implemented, and the plans say so explicitly. "Buy the rumour" is rebuilt around publicly scheduled events with a compliance gate at stage 0, because the colloquial version relies on information we cannot lawfully use. The merger idea is restricted to post-announcement entry for the same reason. Both critiques note that a negative result on the reformulated version does not disprove the original folk wisdom.
The AI idea is a conviction, not a proposition. Its plan decomposes it into value creation / capture / pricing / expression and observes that only pricing determines the return. Its critique's sharpest point is that the firm's existing book is probably already long the theme, and the correct action may be to reduce.
The critiques are adversarial, not decorative. Recurring findings include: the decisive economic test being scheduled after weeks of measurement that cannot change the answer; multiple-testing burdens with no FDR control; cost models calibrated on easy executions being extrapolated to hard ones; and success thresholds that are precise but not derived from anything.
Verified no cross-referencing between plans — a keyword sweep confirms each file contains only its own idea's terminology. Project validation (ruff, pyright, pytest) passes; no Python was touched by this work.