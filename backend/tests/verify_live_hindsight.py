import os
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

def test_live_hindsight():
    api_key = os.getenv("HINDSIGHT_API_KEY")
    base_url = os.getenv("HINDSIGHT_API_URL", "https://api.hindsight.vectorize.io")
    bank_id = os.getenv("HINDSIGHT_BANK_ID", "hindsight_sentinel_bank")
    
    print(f"Connecting to Vectorize Hindsight Cloud API...")
    print(f"Base URL: {base_url}")
    print(f"Bank ID: {bank_id}")
    print(f"API Key present: {bool(api_key)}")
    
    client = Hindsight(base_url=base_url, api_key=api_key)
    
    # 1. Version Check
    v = client.get_version()
    print(f"API Version: {v.api_version}")
    
    # 2. Ensure Bank Exists / Create Bank
    try:
        bank_res = client.create_bank(bank_id=bank_id)
        print(f"Bank Created/Verified: {bank_res}")
    except Exception as e:
        print(f"Bank Creation Notice (Bank may already exist): {e}")
        
    # 3. Retain Test Document
    try:
        retain_res = client.retain(
            bank_id=bank_id,
            content="Context: API v2 release with legacy auth middleware. Lesson: Always preserve X-Legacy-Auth header fallback when upgrading API v2 endpoints.",
            document_id="exp-incident-live-01",
            metadata={"experience_id": "exp-incident-live-01", "service_name": "payment-auth", "source": "live_test"},
            tags=["legacy auth", "api v2"]
        )
        print(f"Hindsight Retain Call Succeeded! Response: {retain_res}")
    except Exception as e:
        print(f"Retain Error: {e}")
        
    # 4. Recall Test Query
    try:
        recall_res = client.recall(bank_id=bank_id, query="API v2 legacy auth middleware")
        print(f"Hindsight Recall Call Succeeded! Recalled {len(recall_res.results)} item(s):")
        for r in recall_res.results:
            print(f"  - Content: {r.text[:60]}... Score: {r.score}")
    except Exception as e:
        print(f"Recall Error: {e}")

if __name__ == "__main__":
    test_live_hindsight()
