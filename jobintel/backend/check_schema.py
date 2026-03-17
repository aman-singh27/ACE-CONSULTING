import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check_schema():
    try:
        from app.core.config import settings
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.connect() as conn:
            # PostgreSQL query to list columns
            res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'company_contacts'"))
            columns = [r[0] for r in res.all()]
            print(f"Columns in company_contacts: {columns}")
    except Exception as e:
        print(f"Error checking schema: {e}")

if __name__ == "__main__":
    asyncio.run(check_schema())
