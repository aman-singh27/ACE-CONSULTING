import os, sys, asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import async_session_factory
from sqlalchemy import text

async def main():
    async with async_session_factory() as db:
        print("Recent actor runs details:")
        r = await db.execute(text("SELECT id, status, apify_run_id, error_log, started_at, completed_at, total_scraped FROM actor_runs ORDER BY started_at DESC LIMIT 10"))
        for row in r.fetchall():
            for k, v in zip(r.keys(), row):
                print(f"{k}: {v}")
            print("-" * 40)

asyncio.run(main())
