import os
import json
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("VOXIMPLANT_ACCOUNT_ID")
API_KEY = os.getenv("VOXIMPLANT_API_KEY")
RULE_ID = os.getenv("VOXIMPLANT_RULE_ID")

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("Checking Rule's Scenarios")
print("=" * 60)

# Get rules with scenarios
response = requests.post(
    "https://api.voximplant.com/platform_api/GetRules",
    data={
        "account_id": ACCOUNT_ID,
        "api_key": API_KEY,
        "rule_id": RULE_ID,
        "with_scenarios": "true"  # Important! Get scenario bindings
    }
)

result = response.json()

print("\nFull Rule Info (with scenarios):")
print(json.dumps(result, indent=2))

# List all scenarios for this account
print("\n" + "=" * 60)
print("All Scenarios in Account")
print("=" * 60)

scenarios_response = requests.post(
    "https://api.voximplant.com/platform_api/GetScenarios",
    data={
        "account_id": ACCOUNT_ID,
        "api_key": API_KEY,
        "with_script": "false"
    }
)

scenarios_result = scenarios_response.json()

print("\nScenarios:")
if scenarios_result.get("result"):
    for scenario in scenarios_result["result"]:
        print(f"  - {scenario['scenario_name']} (ID: {scenario['scenario_id']})")
