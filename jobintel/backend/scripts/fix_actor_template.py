"""Fix the apify_input_template for the LinkedIn Logistics UAE actor to the correct values."""
import os, sys, asyncio, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import async_session_factory
from sqlalchemy import text

CORRECT_TEMPLATE = {
    "keyword": ["logistics"],
    "location": "UAE",
    "maxItems": 155,
    "publishedAt": "r604800",
    "enrichCompanyData": True,
    "saveOnlyUniqueItems": True
}

async def main():
    async with async_session_factory() as db:
        print(f"Setting template to: {json.dumps(CORRECT_TEMPLATE, indent=2)}")
        await db.execute(
            text("UPDATE actor_configs SET apify_input_template = :tmpl WHERE actor_name = :name"),
            {"tmpl": json.dumps(CORRECT_TEMPLATE), "name": "LinkedIn Logistics UAE"}
        )
        await db.commit()
        print("[Done] Fixed!")
        
        # Verify
        r = await db.execute(text("SELECT actor_name, apify_input_template::text FROM actor_configs"))
        for row in r.fetchall():
            print(f"  {row[0]}: {row[1]}")

asyncio.run(main())
