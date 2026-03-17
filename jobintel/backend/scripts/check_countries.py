import asyncio
from sqlalchemy import text
from app.db.session import async_session_factory

async def main():
    async with async_session_factory() as db:
        r = await db.execute(text("SELECT location_country, COUNT(*) FROM job_postings GROUP BY 1"))
        print(r.fetchall())

if __name__ == "__main__":
    asyncio.run(main())
