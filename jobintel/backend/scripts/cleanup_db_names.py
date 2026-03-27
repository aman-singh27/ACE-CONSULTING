"""
Cleanup script to fix URL-like company names in the database.
Uses the same logic as the ingestion pipeline to extract real names from URLs.
"""

import asyncio
import sys
import os

# Add the project root to PYTHONPATH so we can import app
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.company import Company
from app.services.dedup.name_sanitizer import is_url_like, sanitize_company_name
from app.services.dedup.company_normalizer import normalize_company


async def cleanup_companies():
    print("Connecting to database...")
    async with async_session_factory() as db:
        # 1. Fetch all companies
        print("Fetching companies...")
        result = await db.execute(select(Company))
        companies = result.scalars().all()
        
        print(f"Analyzing {len(companies)} companies...")
        
        to_update = []
        needs_merge = []
        
        # Build a map of existing normalized names to avoid collisions
        # (excluding the ones we are about to change)
        existing_normalized = {c.company_name_normalized for c in companies if c.company_name_normalized}

        for company in companies:
            name = company.company_name or ""
            if is_url_like(name):
                new_name = sanitize_company_name(name)
                new_normalized = normalize_company(new_name)
                
                if new_name == name:
                    continue
                
                # Check for collision
                if new_normalized in existing_normalized and new_normalized != company.company_name_normalized:
                    # Find the target company for logging
                    target = next((c for c in companies if c.company_name_normalized == new_normalized), None)
                    needs_merge.append({
                        "id": str(company.id),
                        "old_name": name,
                        "new_name": new_name,
                        "target_id": str(target.id) if target else "unknown"
                    })
                    continue

                # Update the record
                old_name = company.company_name
                company.company_name = new_name
                company.company_name_normalized = new_normalized
                
                to_update.append((old_name, new_name))
                # Update our map to avoid internal collisions during this loop
                if new_normalized:
                    existing_normalized.add(new_normalized)

        # 2. Results
        if to_update:
            print("\nUpdating the following companies:")
            for old, new in to_update:
                print(f"  [FIX] {old} -> {new}")
            
            confirm = input(f"\nProceed with updating {len(to_update)} records? (y/n): ")
            if confirm.lower() == 'y':
                await db.commit()
                print("Database updated successfully.")
            else:
                await db.rollback()
                print("Update cancelled.")
        else:
            print("\nNo companies found that need sanitization (without collisions).")

        if needs_merge:
            print("\nThe following companies could not be renamed because the target name already exists:")
            print("(These will need a manual merge to combine job/contact records)")
            for item in needs_merge:
                print(f"  [COLLISION] {item['old_name']} -> {item['new_name']} (Target ID: {item['target_id']})")


if __name__ == "__main__":
    try:
        asyncio.run(cleanup_companies())
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"\nError: {e}")
