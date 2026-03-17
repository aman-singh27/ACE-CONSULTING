import asyncio
from app.db.session import async_session_factory
from app.services.intelligence.insights_engine import generate_daily_insights

async def main():
    print("Testing generate_daily_insights...")
    async with async_session_factory() as db:
        try:
            summary = await generate_daily_insights(db)
            print("Successfully completed generation. Summary:", summary)
        except Exception as e:
            print("Error during insight generation:", repr(e))
            raise

if __name__ == "__main__":
    asyncio.run(main())
