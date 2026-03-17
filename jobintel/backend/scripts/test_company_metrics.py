import asyncio
from pprint import pprint
from sqlalchemy import select
from app.db.session import async_session_factory
from app.services.intelligence.company_metrics import calculate_company_metrics
from app.models.company import Company

async def main():
    print("Testing calculate_company_metrics()...")
    async with async_session_factory() as db:
        try:
            summary = await calculate_company_metrics(db)
            print(f"Metrics recalculated successfully! Summary: {summary}")
            
            print("\nVerifying updated database values...")
            # Spot check 3 random updated companies 
            # (or top 3 by priority_score to make sure it mutated logic properly)
            stmt = select(Company).order_by(Company.bd_priority_score.desc()).limit(3)
            res = await db.execute(stmt)
            for c in res.scalars():
                print(f"[{c.company_name}] - Priority: {c.bd_priority_score} | 7d: {c.total_postings_7d} | 30d: {c.avg_postings_30d} | velocity: {c.hiring_velocity_score} | tags: {c.bd_tags}")
                
        except Exception as e:
            print("Error during company metrics update:", repr(e))
            raise

if __name__ == "__main__":
    asyncio.run(main())
