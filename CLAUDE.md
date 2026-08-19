## Python standards

- Target Python 3.14.
- Use `uv run --locked` for project commands.
- Keep application code in `src/torch_course/` and tests in `tests/`.
- Preserve type-checking compatibility with pyright. Minimise the use of Any.
- Strongly prefer not to let a function read or manipulate global state, be strict with abstraction boundaries

## Required validation

Run before declaring work complete:

- `uv run --locked ruff check .`
- `uv run --locked pyright`
- `uv run --locked pytest`
