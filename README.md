# fin-discrim

## Intro

This project looks at financial research plan discrimination. Each
under-specified research idea is written up twice, as two independent plans, and
a Claude model is asked which of the two it would fund. Scoring those choices
against held-back gold preferences measures how well a model tells a sound
research plan from a weaker one.

## Pipeline

`docs/seed_ideas.md` holds the seed ideas. Two separate Claude runs turn each
idea into a plan, under different instructions, giving two competing plans per
idea. `fin-discrim-item` pairs a seed idea with its two plans and writes an eval
item; `fin-discrim` then puts those items to one or more models and scores the
answers.

```
docs/seed_ideas.md  ──┬──>  docs/seed_idea_plans/        (plan A)
                      └──>  docs/evaluation_idea_plans/  (plan B)
                                      │
                                      │  fin-discrim-item
                                      v
                            data/eval_items/*.json
                                      │
                                      │  fin-discrim
                                      v
                            text report + evals/*.json
```

## Project structure

| Path | Contents |
| --- | --- |
| `docs/seed_ideas.md` | The seed research ideas, one per bullet. A mixture — some are testable quantitative signals, others are barely-specified theses. |
| `docs/seed_plan_generation.md` | How `seed_idea_plans/` was produced — the prompt given to Claude, the settings used, and notes on what had to be refined to get a useful answer. |
| `docs/seed_idea_plans/` | One plan per seed idea, written by Claude and then hand-annotated. |
| `docs/evaluation_plan_generation.md` | The same record for `evaluation_idea_plans/`. |
| `docs/evaluation_idea_plans/` | The second plan per idea, written to a prompt that asks for a simple market-data evaluation of the signal rather than a full P&L study. Only ideas that test a quantitative signal were included, so this folder covers fewer ideas than `seed_idea_plans/`. |
| `data/eval_items/` | One JSON eval item per idea, built by `fin-discrim-item` from a seed idea and the two matching plan files. Holds both plans plus the hand-written gold preference and critiques used for scoring. |
| `evals/` | Saved `--json-out` runs. `haiku.json` is an example, from a run of `claude-haiku-4-5` over the five items. |
| `src/fin_discrim/` | The package behind the commands — see its [README](src/fin_discrim/README.md) for the module layout, the options, and how position bias is measured. |
| `tests/` | Test suite, run with `uv run --locked pytest`. |

Each plan markdown file carries the plan, then a `## Critique of the Plan`
section Claude wrote about its own plan, then a hand-added `## My Verdict` with
`### Plan` and `### Critique` subsections. `fin-discrim-item` reads the plan,
the critique, and the `### Plan` verdict out of each file; the gold preference
itself and the reasons why the alternative is convincing are filled in by hand.

## Setup

This project requires Python 3.14 and uses `uv` to manage its virtual
environment and locked dependencies. If you don't have `uv`, install it with:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

If your `/home` is on a disk with limited storage space, you can move uv's
cache and tool directories elsewhere, for example:

```
export UV_CACHE_DIR=/build/${USER}/uv_cache_dir
export UV_TOOL_DIR=/build/${USER}/uv_tool_dir
export UV_TOOL_BIN_DIR=/build/${USER}/uv_tool_bin_dir
```

Clone the repository, create a fresh virtual environment, and install the
project and all dependency groups from the lockfile:

```
git clone git@github.com:jamesfissler/ant.git
cd ant
uv sync --locked --all-groups
```

You can run code quality checks and tests using

```
uv run --locked pyright
uv run --locked ruff check .
uv run --locked pytest
```

## Running the tools

```
uv run --locked fin-discrim --both-orders --json-out evals/latest.json
uv run --locked fin-discrim-item --seed-ideas docs/seed_ideas.md --list-seeds
uv run --locked fin-pointwise --list-dimensions
```

`fin-discrim` is the pairwise comparison: two plans for the same idea, scored
against the expert preference. `fin-pointwise` is an early, deliberately small
pointwise alternative — it scores a single plan and its critique against named
quality dimensions, and is meant to be extended with more dimensions over time.

The judging commands need Anthropic credentials — `export ANTHROPIC_API_KEY=...` or
`ant auth login`. `fin-discrim --help` and the package
[README](src/fin_discrim/README.md) cover the rest of the options.
