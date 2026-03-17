import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, Date, cast, text
from app.db.session import async_session_factory
from app.models.company import Company
from app.models.job_posting import JobPosting

async def main():
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    thirty_days_ago = today - timedelta(days=30)

    async with async_session_factory() as db:
        res = await db.execute(select(Company))
        companies = res.scalars().all()
        for c in companies:
            jobs_res = await db.execute(select(JobPosting).where(JobPosting.company_id == c.id))
            jobs = jobs_res.scalars().all()
            
            # Count how many are returned by a basic query
            if len(jobs) > 0 and len(jobs) != c.total_postings_30d:
                print(f"==========================================")
                print(f"Company: {c.company_name} (ID: {c.id})")
                print(f"  DB metrics -> 7d: {c.total_postings_7d}, 30d: {c.total_postings_30d}, alltime: {c.total_postings_alltime}")
                print(f"  Actual Jobs related -> Total: {len(jobs)}")
                
                # Check how many are within 30 days based on their posted_at
                jobs_30d = [j for j in jobs if j.posted_at and j.posted_at.date() >= thirty_days_ago]
                print(f"  Jobs physically in 30 days window: {len(jobs_30d)}")
                
                for j in jobs:
                    print(f"    Job ID: {j.id}, posted_at: {j.posted_at}, created_at: {j.created_at}, title: {j.title}")

if __name__ == "__main__":
    asyncio.run(main())
