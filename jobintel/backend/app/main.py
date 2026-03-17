"""
JobIntel API – application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import health, webhook, jobs, companies, dashboard, insights, runs, actors
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import engine

from app.services.scheduler.scheduler import scheduler
from app.services.scheduler.jobs import check_due_actors, run_daily_insights, run_company_metrics

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle events."""
    # ── Startup ──────────────────────────────────────────────
    logger.info("Starting %s (env=%s)", settings.APP_NAME, settings.ENV)

    # Test database connection
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
    except Exception as exc:
        logger.error("Database connection failed: %s", exc)

    # Start the APScheduler
    scheduler.add_job(check_due_actors, "interval", minutes=5, id="check_due_actors")
    scheduler.add_job(
        run_daily_insights,
        "cron",
        hour=2,
        minute=0,
        timezone="UTC",
        id="generate_daily_insights"
    )
    scheduler.add_job(
        run_company_metrics,
        "cron",
        hour=2,
        minute=30,
        timezone="UTC",
        id="recalculate_company_metrics"
    )
    scheduler.start()
    logger.info("Scheduler started")

    yield

    # ── Shutdown ─────────────────────────────────────────────
    scheduler.shutdown()
    logger.info("Scheduler shutdown complete")
    await engine.dispose()
    logger.info("Application shutdown complete")


# App Setup
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
# TODO: configure CORS properly when frontend is integrated
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, prefix="/api/v1")
app.include_router(webhook.router, prefix="/api/v1/webhook")
app.include_router(jobs.router, prefix="/api/v1/jobs")
app.include_router(companies.router, prefix="/api/v1/companies")
app.include_router(dashboard.router, prefix="/api/v1/dashboard")
app.include_router(insights.router, prefix="/api/v1/insights")
app.include_router(runs.router, prefix="/api/v1/runs")
app.include_router(actors.router, prefix="/api/v1/actors")
