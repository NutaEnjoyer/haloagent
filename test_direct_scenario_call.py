import os
import json
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("VOXIMPLANT_ACCOUNT_ID")
API_KEY = os.getenv("VOXIMPLANT_API_KEY")
SCENARIO_ID = "2993067"  # TestScenario ID
BACKEND_URL = "https://472c00656e14.ngrok-free.app"

# Set console encoding to UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("Testing direct scenario call (without rule)")
print("=" * 60)

# Prepare custom data
custom_data = {
    "call_id": "direct-test-123",
    "phone": "+79019433546",
    "caller_id": "+78652594087",
    "webhook_url": f"{BACKEND_URL}/voximplant/events"
}

print(f"Custom data: {json.dumps(custom_data, indent=2)}")

# Call scenario directly
payload = {
    "account_id": ACCOUNT_ID,
    "api_key": API_KEY,
    "scenario_id": SCENARIO_ID,
    "script_custom_data": json.dumps(custom_data)
}

print("\nCalling StartScenarios with scenario_id...")
response = requests.post(
    "https://api.voximplant.com/platform_api/StartScenarios",
    data=payload
)

result = response.json()
print(f"\nResponse: {json.dumps(result, indent=2)}")

if result.get("result") == 1:
    print("\n[OK] Scenario started successfully!")
    print(f"Media session ID: {result.get('media_session_access_url')}")
else:
    print("\n[ERROR] Failed to start scenario")
