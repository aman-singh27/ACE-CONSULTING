import os
import sys
import pandas as pd
from datetime import datetime
import asyncio

# Setup path so importing app works
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import async_session_factory
from app.models.company import Company
from app.models.job_posting import JobPosting
from sqlalchemy.future import select

# To run this script, python scripts/seed_data.py
async def main():
    print("Loading data.txt...")
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data.txt')
    
    # Read the TSV file
    df = pd.read_csv(file_path, sep='\t', quoting=3, on_bad_lines='skip')
    df = df.fillna('')
    
    print(f"Loaded {len(df)} rows.")

    async with async_session_factory() as db:
        companies_added = 0
        jobs_added = 0
        
        for _, row in df.iterrows():
            company_name = str(row.get('companyName', '')).strip()
            if not company_name:
                continue
                
            # Upsert company
            query = select(Company).where(Company.company_name == company_name)
            result = await db.execute(query)
            company = result.scalar_one_or_none()
            
            company_url = str(row.get('companyUrl', ''))
            
            if not company:
                company = Company(
                    company_name=company_name,
                    company_name_normalized=company_name.lower(),
                    linkedin_url=company_url if 'linkedin.com' in company_url else None,
                    website=company_url if 'linkedin.com' not in company_url and company_url else None
                )
                db.add(company)
                await db.flush()  # To get the ID
                companies_added += 1

            # Job details
            job_title = str(row.get('jobTitle', '')).strip()
            job_url = str(row.get('jobUrl', '')).strip()
            job_id_str = str(row.get('jobId', '')).strip()
            
            # Basic validation to skip malformed rows
            if not job_title or not job_url or not job_id_str:
                continue
            if not job_id_str.isdigit():
                continue
                
            # Upsert Job
            query = select(JobPosting).where(JobPosting.job_url == job_url)
            result = await db.execute(query)
            job = result.scalar_one_or_none()
            
            if not job:
                # Format datetime string
                published_at_str = str(row.get('publishedAt', ''))
                published_at = None
                if published_at_str:
                    try:
                        # e.g., 2026-03-02T00:00:00.000Z
                        published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                    except Exception:
                        pass
                
                # Check required fields
                try:
                    job = JobPosting(
                        job_id=job_id_str,
                        title=job_title,
                        company_name=company_name,
                        company_id=company.id,
                        domain="linkedin.com",
                        source_platform="linkedin",
                        actor_id="seed_script",
                        location_raw=str(row.get('location', '')),
                        job_url=job_url,
                        description_raw=str(row.get('jobDescription', '')),
                        posted_at=published_at or datetime.utcnow()
                    )
                    db.add(job)
                    jobs_added += 1
                except Exception as e:
                    print(f"Failed to add job {job_title}: {e}")

        await db.commit()
        print(f"Successfully seeded {companies_added} companies and {jobs_added} jobs into the database.")

if __name__ == "__main__":
    asyncio.run(main())
