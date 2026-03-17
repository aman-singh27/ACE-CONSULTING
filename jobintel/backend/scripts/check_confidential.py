import asyncio
from sqlalchemy import select, func
from app.db.session import async_session_factory
from app.models.job_posting import JobPosting

async def main():
    async with async_session_factory() as db:
        stmt = select(JobPosting.source_platform, func.count()).where(JobPosting.company_name == 'Confidential').group_by(JobPosting.source_platform)
        res = await db.execute(stmt)
        for row in res.fetchall():
            print(row)

if __name__ == '__main__':
    asyncio.run(main())
