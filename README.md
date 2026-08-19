# fin-discrim

## Intro

This project looks at financial research plan discrimination

### Setup

This project requires Python 3.14 and uses `uv` to manage its virtual
environment and locked dependencies. If you don't have `uv`, install it with:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

If your `/home` is on a disk with limited storage space, you can move uv's
cache and tool directories elsewhere:

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
