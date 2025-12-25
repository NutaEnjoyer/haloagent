"""
Fix Voximplant rule to use OutboundCallStreaming scenario.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("VOXIMPLANT_ACCOUNT_ID")
API_KEY = os.getenv("VOXIMPLANT_API_KEY")
RULE_ID = os.getenv("VOXIMPLANT_RULE_ID")
APPLICATION_ID = os.getenv("VOXIMPLANT_APPLICATION_ID")

API_URL = "https://api.voximplant.com/platform_api"
SCENARIO_NAME = "OutboundCallStreaming"

print("=" * 60)
print("Binding OutboundCallStreaming scenario to rule")
print("=" * 60)
print()

# Step 1: Get scenario ID
print("Step 1: Finding scenario ID...")
response = requests.post(
    f"{API_URL}/GetScenarios",
    data={
        "account_id": ACCOUNT_ID,
        "api_key": API_KEY,
        "scenario_name": SCENARIO_NAME
    }
)

result = response.json()

# Check if there's an error in the response
if "error" in result:
    print(f"[ERROR] Failed to get scenarios: {result}")
    exit(1)

scenarios = result.get("result", [])
if not scenarios:
    print(f"[ERROR] Scenario '{SCENARIO_NAME}' not found!")
    print("Please run: python update_to_streaming_scenario.py")
    exit(1)

scenario_id = scenarios[0]["scenario_id"]
print(f"[OK] Found scenario ID: {scenario_id}")
print()

# Step 2: Bind scenario to rule
print("Step 2: Binding scenario to rule...")
response = requests.post(
    f"{API_URL}/BindScenario",
    data={
        "account_id": ACCOUNT_ID,
        "api_key": API_KEY,
        "rule_id": RULE_ID,
        "scenario_id": scenario_id,
        "bind": "true"
    }
)

result = response.json()

if result.get("result") == 1:
    print(f"[OK] Successfully bound scenario to rule!")
    print()
    print("=" * 60)
    print("Configuration complete!")
    print("=" * 60)
    print()
    print("Test the call now:")
    print('  curl -X POST http://localhost:8000/calls \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"phone": "+79019433546"}\'')
    print()
else:
    print(f"[ERROR] Failed to bind scenario: {result}")
    exit(1)
