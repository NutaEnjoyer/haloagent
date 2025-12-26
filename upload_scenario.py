import requests
import os
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("VOXIMPLANT_ACCOUNT_ID")
API_KEY = os.getenv("VOXIMPLANT_API_KEY")
SCENARIO_ID = os.getenv("VOXIMPLANT_SCENARIO_ID")

# Read scenario
with open("VOXIMPLANT_SCENARIO.js", "r", encoding="utf-8") as f:
    scenario_script = f.read()

print(f"Uploading scenario {SCENARIO_ID}...")
print(f"Scenario size: {len(scenario_script)} bytes")

# Upload to Voximplant using correct API method
url = "https://api.voximplant.com/platform_api/SetScenarioInfo"
response = requests.post(url, data={
    "account_id": ACCOUNT_ID,
    "api_key": API_KEY,
    "scenario_id": SCENARIO_ID,
    "scenario_script": scenario_script
})

print(f"\nResponse: {response.text}")
result = response.json()
if "result" in result and result["result"] == 1:
    print("SUCCESS - Scenario uploaded!")
else:
    print("FAILED - Upload error")
    if "error" in result:
        print(f"Error: {result['error']}")
