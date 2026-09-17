"""AlphaLens MCP Server - exposes financial tools over the Model Context Protocol.

This is a genuine, separately-runnable service for external MCP clients (Claude
Desktop, other agents) - it reuses the exact same backend services the LangGraph
agents use (app.services.*, app.tools.*), so there is one implementation of every
capability, not two. The backend's own agents do NOT route through this server;
they keep their existing fast, direct, already-verified in-process calls.

Run (from the repository root, so `mcp_server` resolves as a package):
    python -m mcp_server.server                 # streamable-HTTP on 0.0.0.0:8100 (default)
    MCP_PORT=9000 python -m mcp_server.server    # custom port
"""
import logging

from mcp.server.mcpserver import MCPServer

from mcp_server import config
from mcp_server.tools import market, news, portfolio, risk, sec, technical

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alphalens.mcp_server")

server = MCPServer(
    name="AlphaLens Tools",
    version="1.0.0",
    instructions=(
        "Financial research tools backed by live market data (yfinance/Alpha Vantage), "
        "NewsAPI sentiment, SEC EDGAR filings (via RAG), and quantitative risk/portfolio "
        "calculations. Every tool returns real data or an explicit error - never invented "
        "figures."
    ),
)

_TOOL_MODULES = (market, news, sec, technical, risk, portfolio)
for module in _TOOL_MODULES:
    module.register(server)

logger.info(f"Registered tools from {len(_TOOL_MODULES)} module(s): {[m.__name__ for m in _TOOL_MODULES]}")


def main() -> None:
    logger.info(f"Starting AlphaLens MCP server on {config.MCP_HOST}:{config.MCP_PORT} (streamable-http)")
    server.run(transport="streamable-http", host=config.MCP_HOST, port=config.MCP_PORT)


if __name__ == "__main__":
    main()
