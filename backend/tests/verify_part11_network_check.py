import os
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

def verify_hindsight_network_retention(exp_id="exp-4a04ac6e"):
    print("=================================================================")
    print(f" Real Code/Network-Level Verification for {exp_id} ")
    print("=================================================================")
    
    api_key = os.getenv("HINDSIGHT_API_KEY")
    base_url = os.getenv("HINDSIGHT_API_URL", "https://api.hindsight.vectorize.io")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]
    bank_id = os.getenv("HINDSIGHT_BANK_ID", "hindsight_sentinel_bank")
    
    print(f"Target Hindsight API URL: {base_url}")
    print(f"Target Bank ID: {bank_id}")
    print(f"Target Document/Experience ID: {exp_id}")
    print(f"HINDSIGHT_API_KEY Present? {bool(api_key)}")
    
    client = Hindsight(base_url=base_url, api_key=api_key)
    
    # 1. Test version endpoint
    http_status = None
    real_hindsight_storage = "NO"
    local_fallback_storage = "YES"
    
    try:
        ver = client.get_version()
        print(f"1. Hindsight get_version() -> Success! Version: {ver.api_version}")
    except Exception as e:
        print(f"1. Hindsight get_version() Failed: {e}")

    # 2. Test synchronous retain call for exp_id
    content_test = f"Context: Verification test for {exp_id}. Lesson: Always verify network responses directly from Vectorize Hindsight API."
    
    try:
        res = client.retain(
            bank_id=bank_id,
            content=content_test,
            document_id=exp_id,
            metadata={"experience_id": exp_id, "source": "agent_run"},
            tags=["network_check", "verification"]
        )
        print(f"\n2. client.retain() SDK Call Output: {res}")
        if res and getattr(res, "success", False) is True:
            real_hindsight_storage = "YES"
            http_status = 200
        else:
            real_hindsight_storage = "NO"
            http_status = "UNKNOWN_NON_2XX"
    except Exception as e:
        print(f"\n2. client.retain() Raised Exception: {type(e).__name__} - {e}")
        real_hindsight_storage = "NO"
        if hasattr(e, "status"):
            http_status = getattr(e, "status")
        elif hasattr(e, "status_code"):
            http_status = getattr(e, "status_code")
        else:
            http_status = "FAILED / EXCEPTION"

    # 3. Test synchronous recall call to verify document exists in remote bank
    print(f"\n3. Verifying remote document recall from Vectorize Hindsight bank '{bank_id}'...")
    try:
        recall_res = client.recall(bank_id=bank_id, query=f"Verification test for {exp_id}")
        num_found = len(recall_res.results) if recall_res and hasattr(recall_res, "results") else 0
        print(f"Recall Output: {num_found} remote items found.")
        if num_found > 0:
            for idx, item in enumerate(recall_res.results[:3]):
                print(f"   [{idx+1}] ID: {item.id}, Score: {item.score}, Content Snippet: '{item.text[:60]}...'")
    except Exception as e:
        print(f"Recall Exception: {e}")

    print("\n=================================================================")
    print(" VERIFICATION SUMMARY ")
    print("=================================================================")
    print(f"REAL VECTORIZE HINDSIGHT STORAGE: {real_hindsight_storage}")
    print(f"LOCAL FALLBACK STORAGE:           {local_fallback_storage}")
    print(f"HTTP STATUS:                      {http_status}")
    print(f"EXPERIENCE ID:                    {exp_id}")
    print("=================================================================\n")

if __name__ == "__main__":
    verify_hindsight_network_retention()
