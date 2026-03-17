import asyncio
import json
from datetime import datetime, timezone
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.daily_insight import DailyInsight

def datetime_handler(x):
    if isinstance(x, datetime):
        return x.isoformat()
    raise TypeError("Unknown type")

async def main():
    async with async_session_factory() as db:
        print("Fetching daily insights for today...")
        today = datetime.now(timezone.utc).date()
        stmt = select(DailyInsight).where(DailyInsight.insight_date == today)
        result = await db.execute(stmt)
        insight = result.scalar_one_or_none()
        
        if not insight:
            print("No daily insight found!")
            return
            
        data = {
            "insight_date": str(insight.insight_date),
            "companies_spiking": insight.companies_spiking[:2] if insight.companies_spiking else [],
            "companies_struggling": insight.companies_struggling[:2] if insight.companies_struggling else [],
            "new_entrants": insight.new_entrants[:2] if insight.new_entrants else [],
            "domain_surges": insight.domain_surges[:2] if insight.domain_surges else [],
            "ghost_posters": insight.ghost_posters[:2] if insight.ghost_posters else [],
            "salary_signals": insight.salary_signals[:2] if insight.salary_signals else [],
            "total_jobs_today": insight.total_jobs_today,
            "total_companies_active_today": insight.total_companies_active_today,
            "computed_at": insight.computed_at
        }
        
        print(json.dumps(data, indent=2, default=datetime_handler))

if __name__ == "__main__":
    asyncio.run(main())
