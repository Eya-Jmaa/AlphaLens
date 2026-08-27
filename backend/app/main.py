"""Main FastAPI Application Entry Point"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config.settings import settings
from app.core.logging import setup_logging
from app.database.session import is_configured as db_configured

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup/shutdown events"""
    logger.info("Starting FinAgent Backend...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Groq Model: {settings.GROQ_MODEL}")

    # Redis/Postgres/Qdrant connections are all lazy (established on first use,
    # see app/services/cache_service.py, app/database/session.py, and
    # app/rag/vector_store.py) so the app starts even if none are configured.

    yield
    
    logger.info("Shutting down FinAgent Backend...")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multi-Agent Financial Analysis Platform",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "operational",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "checks": {
            "api": "ok",
            "groq": "configured" if settings.GROQ_API_KEY else "not configured",
            "database": "configured" if db_configured() else "not configured",
        },
    }