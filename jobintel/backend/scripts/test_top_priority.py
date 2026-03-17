import asyncio
from pprint import pprint
from app.db.session import async_session_factory
from app.services.intelligence.priority_engine import get_bd_priority_list

async def main():
    print("Testing get_bd_priority_list()...")
    async with async_session_factory() as db:
        try:
            companies = await get_bd_priority_list(db, limit=5)
            print("Successfully retrieved Priority List. Top 5:")
            pprint(companies)
        except Exception as e:
            print("Error during priority listing:", repr(e))
            raise

if __name__ == "__main__":
    asyncio.run(main())
