import asyncio
from pprint import pprint
from app.db.session import async_session_factory
from app.services.intelligence.domain_insights import get_domain_trends

async def main():
    print("Testing get_domain_trends()...")
    async with async_session_factory() as db:
        try:
            trends = await get_domain_trends(db)
            print(f"Successfully retrieved Domain Trends. Total Domains: {len(trends)}")
            pprint(trends[:3]) # Top 3 domains
            
            print("\nTesting single domain filter (logistics):")
            logistics = await get_domain_trends(db, domain="logistics")
            pprint(logistics)
        except Exception as e:
            print("Error during domain trends fetching:", repr(e))
            raise

if __name__ == "__main__":
    asyncio.run(main())
