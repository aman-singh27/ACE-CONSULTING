import httpx
import sys

BASE_URL = "http://localhost:8000/api/v1"
ACTOR_ID = "2e34b018-21c9-4b22-b1d0-224e50472888"

def main():
    print("Deleting actor...")
    resp = httpx.delete(f"{BASE_URL}/actors/{ACTOR_ID}")
    print("Delete response:", resp.status_code, resp.text)
    
    print("Creating actor...")
    payload = {
      "actor_id": "cheap_scraper/linkedin-job-scraper",
      "actor_name": "LinkedIn Logistics UAE",
      "platform": "linkedin",
      "domain": "logistics",
      "frequency_days": 1,
      "normalizer_key": "linkedin",
      "apify_input_template": {
        "jobType": ["full-time","contract"],
        "keyword": [
          "Manufacturing Engineer",
          "Production Manager",
          "Plant Manager",
          "Quality Engineer",
          "Industrial Engineer",
          "Maintenance Engineer",
          "Operations Manager",
          "Supply Chain Manager"
        ],
        "distance": "50",
        "location": "United Arab Emirates",
        "maxItems": 151,
        "workType": ["on-site","hybrid"],
        "publishedAt": "r86400",
        "experienceLevel": ["entry-level","associate","mid-senior"],
        "enrichCompanyData": False,
        "saveOnlyUniqueItems": True
      }
    }
    
    resp2 = httpx.post(f"{BASE_URL}/actors", json=payload)
    print("Create response:", resp2.status_code, resp2.text)
    
    if resp2.status_code == 201:
        new_id = resp2.json()["id"]
        print("Triggering actor...")
        resp3 = httpx.post(f"{BASE_URL}/actors/{new_id}/trigger")
        print("Trigger response:", resp3.status_code, resp3.text)

if __name__ == "__main__":
    main()
