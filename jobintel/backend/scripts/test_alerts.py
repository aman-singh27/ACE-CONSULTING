import asyncio
from pprint import pprint
from app.db.session import async_session_factory
from app.services.intelligence.alerts_engine import get_dashboard_alerts

async def main():
    print("Testing get_dashboard_alerts()...")
    async with async_session_factory() as db:
        try:
            alerts = await get_dashboard_alerts(db)
            print(f"Successfully retrieved {len(alerts)} alerts:")
            pprint(alerts)
        except Exception as e:
            print("Error during alerts fetching:", repr(e))
            raise

if __name__ == "__main__":
    asyncio.run(main())
