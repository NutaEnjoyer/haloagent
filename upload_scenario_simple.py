import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("VOXIMPLANT_ACCOUNT_ID")
API_KEY = os.getenv("VOXIMPLANT_API_KEY")
SCENARIO_FILE = "voximplant_scenario_STREAMING.js"
SCENARIO_NAME = "OutboundCallStreaming"

# Set console encoding to UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("Updating scenario:", SCENARIO_NAME)
print("=" * 60)

# Read scenario code
with open(SCENARIO_FILE, 'r', encoding='utf-8') as f:
    scenario_code = f.read()

print(f"Loaded scenario from {SCENARIO_FILE}")

# Update scenario
response = requests.post(
    "https://api.voximplant.com/platform_api/SetScenarioInfo",
    data={
        "account_id": ACCOUNT_ID,
        "api_key": API_KEY,
        "scenario_id": "2993031",
        "scenario_script": scenario_code
    }
)

result = response.json()

if result.get("result") == 1:
    print("[OK] Scenario updated successfully!")
else:
    print(f"[ERROR] Failed to update scenario: {result}")
    sys.exit(1)
