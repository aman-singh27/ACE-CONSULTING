import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.api.routes.jobs import list_jobs
from app.api.deps import get_db
import os

# Mock DB session for testing the route logic if possible, 
# but easier to just check if the code runs.

async def test_route():
    # This will likely fail if DB isn't set up or migration missing
    try:
        from app.core.config import settings
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
            print("Hitting list_jobs...")
            res = await list_jobs(page=1, limit=25, db=db)
            print("Success!")
            print(f"Items: {len(res.items)}")
    except Exception as e:
        print(f"Error caught: {e}")

if __name__ == "__main__":
    # We need to set up environment variables or mock settings if they rely on them
    # For now, let's just see if we can catch the error message.
    asyncio.run(test_route())
