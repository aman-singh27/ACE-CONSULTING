import asyncio
from sqlalchemy import select, func
from app.db.session import async_session_factory
from app.models.job_posting import JobPosting
from app.models.company import Company
from app.models.company_contact import CompanyContact
from app.models.daily_insight import DailyInsight
from app.models.enrichment_cache import EnrichmentCache
from app.models.actor_config import ActorConfig
from app.models.actor_run import ActorRun

async def main():
    async with async_session_factory() as db:
        tables = [
            ("JobPosting", JobPosting),
            ("Company", Company),
            ("CompanyContact", CompanyContact),
            ("DailyInsight", DailyInsight),
            ("EnrichmentCache", EnrichmentCache),
            ("ActorConfig", ActorConfig),
            ("ActorRun", ActorRun),
        ]
        
        print("--- Table Counts ---")
        for name, model in tables:
            stmt = select(func.count()).select_from(model)
            res = await db.execute(stmt)
            count = res.scalar()
            print(f"{name}: {count}")
            
        print("\n--- Scraper Platforms Configured ---")
        stmt = select(ActorConfig.platform).distinct()
        res = await db.execute(stmt)
        platforms = [row[0] for row in res.fetchall()]
        print(f"Platforms: {platforms}")

        print("\n--- Active Actors ---")
        stmt = select(func.count()).select_from(ActorConfig).where(ActorConfig.is_active == True)
        res = await db.execute(stmt)
        active_count = res.scalar()
        print(f"Active Actors: {active_count}")

if __name__ == '__main__':
    asyncio.run(main())
