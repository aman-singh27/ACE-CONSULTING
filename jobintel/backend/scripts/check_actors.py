import os, sys, asyncio, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import async_session_factory
from sqlalchemy import text

async def main():
    async with async_session_factory() as db:
        r = await db.execute(text("SELECT id, actor_id, actor_name, platform, domain, is_active, apify_input_template::text FROM actor_configs"))
        for row in r.fetchall():
            print("=" * 60)
            for k, v in zip(r.keys(), row):
                print(f"  {k}: {v}")

        print("\n\nRecent actor runs:")
        r2 = await db.execute(text("SELECT id, actor_config_id, apify_run_id, status, error_log, started_at FROM actor_runs ORDER BY started_at DESC LIMIT 5"))
        for row in r2.fetchall():
            print("-" * 60)
            for k, v in zip(r2.keys(), row):
                print(f"  {k}: {v}")

asyncio.run(main())
