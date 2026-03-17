import httpx
from app.core.config import settings

class ApolloClient:
    def __init__(self):
        self.base_url = settings.APOLLO_BASE_URL
        self.api_key = settings.APOLLO_API_KEY

    async def enrich_company(self, domain: str) -> dict:
        url = f"{self.base_url}/organizations/enrich"
        params = {
            "domain": domain,
            "api_key": self.api_key
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)

        response.raise_for_status()
        return response.json()

    async def search_people(self, domain: str) -> dict:
        url = f"{self.base_url}/mixed_people/search"
        payload = {
            "api_key": self.api_key,
            "q_organization_domains": [domain],
            "person_titles": [
                "HR",
                "Talent",
                "Recruiter",
                "Engineering Manager",
                "CTO",
                "Head of Engineering"
            ],
            "page": 1,
            "per_page": 10
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)

        response.raise_for_status()
        return response.json()
