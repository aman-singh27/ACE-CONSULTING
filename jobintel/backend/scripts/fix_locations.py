import asyncio
from sqlalchemy import select, update
from app.db.session import async_session_factory
from app.models.job_posting import JobPosting
from app.services.normalizers.linkedin_normalizer import _extract_location_parts

async def main():
    async with async_session_factory() as db:
        print("Finding jobs with null location_country but valid location_raw...")
        
        # Get jobs that need fixing
        stmt = select(JobPosting).where(
            JobPosting.location_country.is_(None),
            JobPosting.location_raw.is_not(None)
        )
        res = await db.execute(stmt)
        jobs = res.scalars().all()
        
        print(f"Found {len(jobs)} jobs to backfill location data...")
        
        updates = 0
        for job in jobs:
            # We construct a mock 'raw' dict to feed into our new extraction logic
            raw_mock = {"location": job.location_raw}
            city, country, region = _extract_location_parts(raw_mock)
            
            if country or city or region:
                job.location_city = city
                job.location_country = country  
                job.location_region = region
                updates += 1
                
        if updates > 0:
            await db.commit()
            print(f"Successfully updated {updates} job locations!")
        else:
            print("No locations could be parsed.")

if __name__ == "__main__":
    asyncio.run(main())
