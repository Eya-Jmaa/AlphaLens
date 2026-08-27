"""Ad-hoc MCP client smoke test: connect over streamable-HTTP, list tools, call a few.
Not part of the app - just used to verify the server end-to-end during development."""
import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main():
    async with streamable_http_client("http://127.0.0.1:8100/mcp") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("TOOLS:", [t.name for t in tools.tools])

            print("\n--- get_stock_price(NVDA) ---")
            result = await session.call_tool("get_stock_price", {"ticker": "NVDA"})
            print(result.content[0].text if result.content else result)

            print("\n--- calculate_technical_indicators(AAPL) ---")
            result = await session.call_tool("calculate_technical_indicators", {"ticker": "AAPL"})
            data = json.loads(result.content[0].text) if result.content else {}
            print({k: data.get(k) for k in ["ticker", "latest_price", "sma_20", "rsi"]})

            print("\n--- calculate_risk(['AAPL','MSFT'], [0.5, 0.5]) ---")
            result = await session.call_tool("calculate_risk", {"tickers": ["AAPL", "MSFT"], "weights": [0.5, 0.5]})
            data = json.loads(result.content[0].text) if result.content else {}
            print({k: data.get("metrics", {}).get(k) for k in ["volatility", "sharpe_ratio"]})


if __name__ == "__main__":
    asyncio.run(main())
