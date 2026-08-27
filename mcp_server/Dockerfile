# syntax=docker/dockerfile:1
# MCP Server Dockerfile - reuses the backend's services directly (see
# mcp_server/config.py), so this image needs the backend source tree too.
# Build with the REPOSITORY ROOT as context:
#   docker build -f mcp_server/Dockerfile .
FROM python:3.12-slim

WORKDIR /repo

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
# See backend/Dockerfile for why torch is pre-installed CPU-only here.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r backend/requirements.txt

COPY backend ./backend
COPY mcp_server ./mcp_server

RUN useradd -m -u 1000 finagent && chown -R finagent:finagent /repo
USER finagent

ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8100
EXPOSE 8100

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -sf http://localhost:8100/mcp \
        -H "Content-Type: application/json" -H "Accept: text/event-stream, application/json" \
        -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}}}' \
        || exit 1

CMD ["python", "-m", "mcp_server.server"]
