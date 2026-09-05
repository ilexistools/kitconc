FROM python:3.11-slim

# Use uv for locked, reproducible dependency installation.
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Keep image deterministic using the committed uv.lock file.
COPY pyproject.toml uv.lock README.txt LICENSE.txt ./
RUN uv sync --locked --all-extras --no-dev --no-install-project

COPY . .
RUN uv sync --locked --all-extras --no-dev --no-editable

EXPOSE 8001

# Default to a network-accessible MCP server transport for container usage.
CMD ["/app/.venv/bin/kitconc-mcp", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8001"]
