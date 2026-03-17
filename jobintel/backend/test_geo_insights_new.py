import asyncio
from sqlalchemy import text
from app.db.session import async_session_factory
from app.services.intelligence.geo_insights import get_country_heatmap

async def main():
    async with async_session_factory() as db:
        print("Testing get_country_heatmap()...")
        heatmap = await get_country_heatmap(db)
        print("Heatmap return value:", heatmap)
        
        # Checking raw counts to see what data looks like
        raw = await db.execute(text("SELECT COALESCE(location_country, 'Unknown'), COUNT(*) FROM job_postings GROUP BY 1"))
        print("\nRaw country counts in job_postings:")
        for row in raw.fetchall():
            print(row)

if __name__ == "__main__":
    asyncio.run(main())
