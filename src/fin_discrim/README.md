## Discriminator evaluation

Have one or more json files with the ideas, plans, preferences, gold critiques etc in

Write a small script which iterates through them, asks a given claude model which plan it prefers, and reports the performance vs the gold preference

### Usage

```bash
export ANTHROPIC_API_KEY=...            # or `ant auth login`

uv run --locked fin-discrim                       # default: claude-opus-5
uv run --locked fin-discrim --model claude-opus-5 --model claude-sonnet-5
uv run --locked fin-discrim --both-orders --json-out data/runs/latest.json
```

Key options: `--model` (repeat to compare several models), `--items-dir`
(default `data/eval_items`), `--item` (repeat to restrict the run to named
items), `--effort`, `--concurrency`, `--json-out` (writes every verdict's
reasoning for inspection). `fin-discrim --help` lists them all.

### What the judge sees

Only `seed_idea`, `plan_A`, and `plan_B` — the latter two shown as neutral
"Plan 1"/"Plan 2" headings. `gold_preference`, `gold_critique_A`,
`gold_critique_B`, and `why_B_is_convincing` are never sent; they are used
client-side for scoring only. `tests/test_cli.py` asserts this against the real
item files.

### Position bias

Every item in `data/eval_items` currently has `gold_preference: "A"`. A judge
that simply favours whichever plan it reads first would therefore score 100%
without discriminating at all. Run `--both-orders` to separate the two: each
item is judged twice, once with the plans swapped, and the report adds

- **picked 1st** — how often the model chose whichever plan was shown first
  (~50% is unbiased, ~100% means it is reading position, not content);
- **flips** — items where the answer changed when the plans swapped places.

Accuracy is only meaningful when the flip rate is low. `--order swapped` runs a
single pass with B shown first, if you want the cheaper one-sided check.

### Comparing across model generations

Adaptive thinking and `--effort` only exist on the 4.6 generation and later.
Older models (`claude-haiku-4-5`, and any id `judge.py` does not recognise)
reject both with a 400, so `judge.request_params` omits them and those models
answer with no reasoning pass at all. `MODEL_CAPABILITIES` in `judge.py` records
which is which; dated snapshot ids such as `claude-haiku-4-5-20251001` resolve
through their base alias, and the run prints a note on stderr naming any model
affected.

This means a cross-generation run is **not** apples-to-apples: a difference in
accuracy or flip rate between `claude-opus-5` and `claude-haiku-4-5` conflates
model capability with thinking configuration. Read those numbers as a comparison
of deployed configurations, not of the models themselves. For a like-for-like
run, older models would need `thinking={"type": "enabled", "budget_tokens": N}`
instead; the capability table already carries the flag needed to choose per
model.

### Layout

| Module | Responsibility |
| --- | --- |
| `items.py` | Load and validate eval items; parse gold preferences |
| `judge.py` | Build the prompt, call the model, map the verdict back to A/B |
| `scoring.py` | Accuracy, choice balance, position bias per model |
| `report.py` | Text report and JSON dump |
| `cli.py` | Argument parsing and the parallel run loop |
