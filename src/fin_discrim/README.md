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

### Layout

| Module | Responsibility |
| --- | --- |
| `items.py` | Load and validate eval items; parse gold preferences |
| `judge.py` | Build the prompt, call the model, map the verdict back to A/B |
| `scoring.py` | Accuracy, choice balance, position bias per model |
| `report.py` | Text report and JSON dump |
| `cli.py` | Argument parsing and the parallel run loop |
