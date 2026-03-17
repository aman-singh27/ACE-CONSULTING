import asyncio
from pprint import pprint
from app.db.session import async_session_factory
from app.services.intelligence.geo_insights import get_country_heatmap, get_city_breakdown

async def main():
    print("Testing Geo Heatmap (Country Level)...")
    async with async_session_factory() as db:
        try:
            # 1. Test Country Heatmap Default
            countries = await get_country_heatmap(db)
            print(f"Successfully retrieved Heatmap. Total Countries: {len(countries)}")
            pprint(countries[:3]) # Show top 3
            
            # 2. Test City Breakdown (assuming AE from previous runs)
            print("\nTesting City Breakdown (group=city, country=AE):")
            cities = await get_city_breakdown(db, "AE")
            pprint(cities[:3])

            # 3. Test Domain Filter
            print("\nTesting Country Heatmap with filter (domain=logistics):")
            logistics_countries = await get_country_heatmap(db, domain="logistics")
            pprint(logistics_countries[:3])

        except Exception as e:
            print("Error during geo trends fetching:", repr(e))
            raise

if __name__ == "__main__":
    asyncio.run(main())
