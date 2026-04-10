FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Keep image smaller and deterministic by using pinned runtime dependencies.
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir .

EXPOSE 8001

# Default to a network-accessible MCP server transport for container usage.
CMD ["kitconc-mcp", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8001"]
