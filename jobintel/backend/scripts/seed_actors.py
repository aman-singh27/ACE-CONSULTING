"""
Seed script – Creates 3 consolidated actors (1 per platform).

Platforms: LinkedIn, NaukriGulf, Bayt
Domains:   Logistics + Manufacturing (combined keywords)
Region:    GCC (UAE focus)

Each actor targets ~200 results per scrape.

Input schema notes (from Apify docs):
  LinkedIn   - keyword: string[], location: string, maxItems: int
  NaukriGulf - keyword: string (single), region: string (single), results_wanted: int
  Bayt       - startUrl: string (URL-based filtering), results_wanted: int, max_pages: int

Usage:
    python scripts/seed_actors.py                        # uses http://localhost:8000
    python scripts/seed_actors.py <base_url>             # custom backend URL
    python scripts/seed_actors.py <base_url> --clean     # delete all existing actors first
"""

import sys
import httpx

BASE_URL = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "http://localhost:8000"
API = f"{BASE_URL}/api/v1/actors"
CLEAN = "--clean" in sys.argv

GCC_LOCATIONS = [
    "United Arab Emirates",
    "Saudi Arabia",
    "Qatar",
    "Kuwait",
    "Oman",
    "Bahrain",
]

# ── Combined keywords: Logistics + Manufacturing ───────────────────────────

COMBINED_KEYWORDS = [
    # Logistics / Supply Chain
    "Logistics Manager",
    "Supply Chain Manager",
    "Warehouse Manager",
    "Fleet Manager",
    "Distribution Manager",
    "Procurement Manager",
    "Inventory Manager",
    "Transport Manager",
    "Operations Manager Logistics",
    "3PL Manager",
    # Manufacturing
    "Production Manager",
    "Plant Manager",
    "Manufacturing Engineer",
    "Maintenance Manager",
    "Quality Engineer",
    "Industrial Engineer",
    "Process Engineer",
    "Factory Manager",
    "Lean Manufacturing Manager",
    "Operations Manager Manufacturing",
]

# ── Actor definitions ──────────────────────────────────────────────────────

ACTORS = [
    # ── LinkedIn ──────────────────────────────────────────────
    # Supports: keyword (string[]), location (string), maxItems (int)
    {
        "actor_id": "cheap_scraper/linkedin-job-scraper",
        "actor_name": "LinkedIn Logistics & Manufacturing GCC",
        "platform": "linkedin",
        "domain": "logistics_manufacturing",
        "frequency_days": 1,
        "normalizer_key": "linkedin",
        "keywords": COMBINED_KEYWORDS,
        "locations": GCC_LOCATIONS,
        "monthly_budget_usd": 15.0,
        "apify_input_template": {
            "jobType": ["full-time", "contract"],
            "keyword": COMBINED_KEYWORDS,
            "distance": "50",
            "location": "United Arab Emirates",
            "maxItems": 200,
            "workType": ["on-site", "hybrid"],
            "publishedAt": "r86400",
            "experienceLevel": ["entry-level", "associate", "mid-senior"],
            "enrichCompanyData": False,
            "saveOnlyUniqueItems": True,
        },
    },

    # ── NaukriGulf ────────────────────────────────────────────
    # Supports: keyword (single string), region (single string), results_wanted (int)
    # Since only 1 keyword per run, we create 2 actors: one logistics, one manufacturing
    {
        "actor_id": "shahidirfan/nukrigulf-job-scraper",
        "actor_name": "NaukriGulf Logistics GCC",
        "platform": "naukrigulf",
        "domain": "logistics",
        "frequency_days": 1,
        "normalizer_key": "naukrigulf",
        "keywords": ["logistics manager", "supply chain", "warehouse", "procurement"],
        "locations": GCC_LOCATIONS,
        "monthly_budget_usd": 10.0,
        "apify_input_template": {
            "keyword": "logistics manager",
            "region": "Dubai",
            "results_wanted": 200,
        },
    },
    {
        "actor_id": "shahidirfan/nukrigulf-job-scraper",
        "actor_name": "NaukriGulf Manufacturing GCC",
        "platform": "naukrigulf",
        "domain": "manufacturing",
        "frequency_days": 1,
        "normalizer_key": "naukrigulf",
        "keywords": ["manufacturing engineer", "production manager", "plant manager", "quality engineer"],
        "locations": GCC_LOCATIONS,
        "monthly_budget_usd": 10.0,
        "apify_input_template": {
            "keyword": "manufacturing engineer",
            "region": "Dubai",
            "results_wanted": 200,
        },
    },

    # ── Bayt ──────────────────────────────────────────────────
    # Supports: startUrl (string), results_wanted (int), max_pages (int)
    # No keyword/location params – filtering is via the startUrl
    # Using keyword-style URLs for targeting
    {
        "actor_id": "shahidirfan/bayt-jobs-scraper",
        "actor_name": "Bayt Logistics GCC",
        "platform": "bayt",
        "domain": "logistics",
        "frequency_days": 1,
        "normalizer_key": "bayt",
        "keywords": ["logistics manager", "supply chain", "warehouse"],
        "locations": GCC_LOCATIONS,
        "monthly_budget_usd": 10.0,
        "apify_input_template": {
            "startUrl": "https://www.bayt.com/en/international/jobs/logistics-manager-jobs/",
            "results_wanted": 200,
            "max_pages": 20,
        },
    },
    {
        "actor_id": "shahidirfan/bayt-jobs-scraper",
        "actor_name": "Bayt Manufacturing GCC",
        "platform": "bayt",
        "domain": "manufacturing",
        "frequency_days": 1,
        "normalizer_key": "bayt",
        "keywords": ["manufacturing engineer", "production manager"],
        "locations": GCC_LOCATIONS,
        "monthly_budget_usd": 10.0,
        "apify_input_template": {
            "startUrl": "https://www.bayt.com/en/international/jobs/manufacturing-jobs/",
            "results_wanted": 200,
            "max_pages": 20,
        },
    },
]


# ── Main ───────────────────────────────────────────────────────────────────

def clean_existing():
    """Delete all existing actor configs."""
    print("Fetching existing actors...")
    resp = httpx.get(API, timeout=30.0)
    if resp.status_code != 200:
        print(f"  Failed to list actors: {resp.status_code}")
        return
    actors = resp.json()
    print(f"  Found {len(actors)} existing actors. Deleting...")
    for a in actors:
        r = httpx.delete(f"{API}/{a['id']}", timeout=30.0)
        status = "deleted" if r.status_code == 204 else f"status {r.status_code}"
        print(f"  {a['actor_name']}  ->  {status}")
    print()


def main():
    if CLEAN:
        clean_existing()

    print(f"Creating {len(ACTORS)} actors against {API} ...\n")

    created = 0
    failed = 0

    for actor in ACTORS:
        name = actor["actor_name"]
        try:
            resp = httpx.post(API, json=actor, timeout=30.0)
            if resp.status_code == 201:
                new_id = resp.json()["id"]
                print(f"  [OK] {name}  ->  id={new_id}")
                created += 1
            else:
                print(f"  [FAIL] {name}  ->  {resp.status_code}: {resp.text}")
                failed += 1
        except Exception as exc:
            print(f"  [FAIL] {name}  ->  ERROR: {exc}")
            failed += 1

    print(f"\nDone: {created} created, {failed} failed.")


if __name__ == "__main__":
    main()
