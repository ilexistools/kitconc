# AGENTS.md

Guidance for AI coding agents (Codex, Claude Code, Cursor, Copilot and others) working **on the
Kitconc repository**. To **use** Kitconc for corpus analysis instead, read
[Using Kitconc as an agent](#using-kitconc-as-an-agent) below.

## Project at a glance

Kitconc is a corpus linguistics package for Python (PyPI: `kitconc`, Python >= 3.10, MIT). It has
three faces built on the same core:

| Face | Entry point | Code |
|---|---|---|
| Python API | `kitconc.kit_corpus.Corpus` | `kitconc/kit_corpus.py`, `kitconc/py_*.py` (analyses) |
| Desktop app | `kitconc-app` | `kitconc/cli_app.py`, `kitconc/kit_app*.py` |
| Agent interface | `kitconc-mcp`, `kitconc-tool`, `kitconc-gui`, `kitconc-skill` | `kitconc/agent/` |

`kitconc/agent/` in detail:

| File / folder | Role |
|---|---|
| `actions.py` | `KitconcActions`: workspace-level operations over corpora (legacy 3.x tool set) |
| `tools.py` | `KitconcTools` + `TOOL_SPECS` (`_SPEC_ROWS`): the curated tool catalog (name, annotations, title, group) |
| `mcp_server.py` | FastMCP server (`kitconc-mcp`): stdio, SSE, Streamable HTTP |
| `resources.py` | MCP resources, recipe prompts and argument completion |
| `tool_cli.py` | `kitconc-tool`: runs the same tools in-process and prints JSON |
| `dashboard.py` + `dashboard.html` | `kitconc-gui`: the MCP Console (browser UI), `/mcp`, `/sse` and the REST API `/api/...` |
| `results.py`, `result_ops.py`, `expressions.py` | stored results (`result_id`) and the operations / expression language over them |
| `pipeline.py`, `recipes.py`, `recipes/*.json` | declarative pipelines and the built-in recipes |
| `jobs.py`, `progress.py` | background jobs and progress reporting |
| `guides/*.md` | documentation served to agents by the `guide_read` tool |
| `skill/kitconc/`, `skill/kitconc-recipe-author/` | Agent Skills installed by `kitconc-skill` |
| `CONTRACT.md` | the `KitconcActions` action-layer contract and MCP tool surface; read it before changing tool behavior |

Other folders:
- `tests/`: the pytest suite.
- `docs/MCP.md`: full MCP, console and REST reference.
- `howto/`: Python examples.
- `scripts/`: the console start/stop scripts behind `start-gui.*` and `stop-gui.*`.

## Setup and checks

Use [uv](https://docs.astral.sh/uv/) with the lockfile; do not edit `uv.lock` by hand.

```bash
uv sync --locked --dev                 # environment (add --python 3.12 to pin)
uv run --locked pytest                 # full suite, same as CI
uv run --locked pytest tests/test_mcp_dashboard.py -q   # one file
uv run --locked kitconc-gui --workspace kitconc_corpora --no-browser --port 8790   # try the console
```

CI (`.github/workflows/tests.yml`) runs pytest on Ubuntu and Windows with Python 3.10 and 3.12,
then `uv build` and `twine check`. Run the relevant tests before proposing a change.
`tests/test_agent_workflows.py::test_job_runs_recipe_and_persists` is timing-sensitive and
occasionally fails on CI (`interrupted` instead of `succeeded`). Re-run it before investigating
if your change does not touch jobs.

## Conventions

- **Adding or changing an agent tool:**
  1. Implement the method on `KitconcTools`. Its docstring becomes the MCP description.
  2. Add a row to `_SPEC_ROWS` with read-only, writes or destructive annotations, a title and a
     group.
  3. Add an icon in `TOOL_ICONS` in `dashboard.html`.
  4. Update `docs/MCP.md` (tool catalog), the `kitconc` skill when agents should know about it,
     and the tests.
  5. Respect `--read-only`: write tools must not be registered in read-only mode.
- **Errors** from tools are structured: `{"error": {"code", "message", "hint", "candidates"}}`.
  Raise `ToolFailure` rather than returning ad-hoc strings.
- **Packaging:** non-Python files shipped in the wheel must be listed in
  `[tool.setuptools.package-data]` in `pyproject.toml`. This covers the dashboard HTML, guides,
  recipes and skills.
- **Versions:** keep `version` in `pyproject.toml` and `kitconc/version.py` in sync, and add an
  entry to `CHANGES.txt` (newest first; use "Unreleased" until a release).
- **User-facing docs:** `README.md` is the GitHub and PyPI front page. Use relative links and keep
  the existing sections; `docs/MCP.md` is the detailed reference. Both are in English, like the
  code and UI.
- **The MCP Console:**
  - Self-contained: `dashboard.html` has inline CSS, JS and SVG and makes no external requests.
  - Binds only to `127.0.0.1`.
  - Keep `TrustedHostMiddleware` in place, and keep the `application/json` requirement on
    `POST /api/tools/*`, which blocks cross-site requests.
- **Line endings** are pinned in `.gitattributes`: LF for `*.sh` and `*.command` (which must stay
  executable, mode 100755), CRLF for `*.cmd` and `*.ps1`.
- **Never commit:** `.claude/`, `.venv/`, `kitconc.tmp`, workspace contents, `*.log`,
  `.kitconc-gui.pid` or model files under `embeddings/models/`.
- **Git:** `master` is protected and only accepts changes through pull requests. Create a branch,
  open a PR, and let CI pass. Squash merges are the norm (title suffix `(#N)`).

## Using Kitconc as an agent

To analyze corpora with Kitconc (rather than develop it), install the bundled skills. They work
for Claude, Codex and any agent that reads the Agent Skills format:

```bash
uvx --from kitconc kitconc-skill install                  # Claude (~/.claude/skills) and Codex (~/.agents/skills)
uvx --from kitconc kitconc-skill install --scope project  # into ./.claude/skills and ./.agents/skills
```

- [`kitconc`](kitconc/agent/skill/kitconc/SKILL.md): the corpus analysis workflow. It covers
  access through MCP, `kitconc-tool` or the console's REST API, recipes, result operations and
  measures.
- [`kitconc-recipe-author`](kitconc/agent/skill/kitconc-recipe-author/SKILL.md): designing,
  validating and saving reusable recipes.

Ways to reach the tools, all on the same workspace:

| Route | How |
|---|---|
| MCP (stdio) | `kitconc-mcp --transport stdio --workspace DIR` |
| MCP (HTTP / SSE) | `kitconc-gui` then `http://127.0.0.1:8787/mcp` or `/sse` |
| REST API | `kitconc-gui` then `POST http://127.0.0.1:8787/api/tools/{name}` with a JSON body |
| CLI | `kitconc-tool --workspace DIR <tool> '<json>'` (`--list` for the catalog) |

Inside the tools, `guide_read {"topic": "overview"}` returns the built-in documentation.
