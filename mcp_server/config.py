"""MCP server configuration + backend import wiring.

The MCP server reuses the backend's services/tools directly (CompanyService,
RiskService, SECRagService, etc.) rather than reimplementing anything - so it
needs the backend package importable and reads the same .env for API keys.
"""
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load backend/.env before any `app.*` import touches app.config.settings,
# so API keys/DB URL are available exactly like they are for the FastAPI app.
from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_DIR / ".env")

MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8100"))
