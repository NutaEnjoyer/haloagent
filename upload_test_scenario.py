import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("VOXIMPLANT_ACCOUNT_ID")
API_KEY = os.getenv("VOXIMPLANT_API_KEY")
RULE_ID = os.getenv("VOXIMPLANT_RULE_ID")
SCENARIO_FILE = "voximplant_scenario_TEST.js"
SCENARIO_NAME = "TestScenario"

# Set console encoding to UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("Uploading and binding TEST scenario")
print("=" * 60)

# Step 1: Read scenario code
with open(SCENARIO_FILE, 'r', encoding='utf-8') as f:
    scenario_code = f.read()

print(f"Loaded scenario from {SCENARIO_FILE}")

# Step 2: Create or update scenario
print(f"\nCreating/updating scenario '{SCENARIO_NAME}'...")

response = requests.post(
    "https://api.voximplant.com/platform_api/AddScenario",
    data={
        "account_id": ACCOUNT_ID,
        "api_key": API_KEY,
        "scenario_name": SCENARIO_NAME,
        "scenario_script": scenario_code,
        "rewrite": "true"  # Overwrite if exists
    }
)

result = response.json()

if result.get("result") == 1:
    scenario_id = result.get("scenario_id")
    print(f"[OK] Scenario created/updated | scenario_id={scenario_id}")
else:
    print(f"[ERROR] Failed to create scenario: {result}")
    sys.exit(1)

# Step 3: Bind scenario to rule
print(f"\nBinding scenario to rule {RULE_ID}...")

response = requests.post(
    "https://api.voximplant.com/platform_api/SetRuleInfo",
    data={
        "account_id": ACCOUNT_ID,
        "api_key": API_KEY,
        "rule_id": RULE_ID,
        "scenarios": scenario_id
    }
)

result = response.json()

if result.get("result") == 1:
    print("[OK] Scenario bound to rule successfully!")
else:
    print(f"[ERROR] Failed to bind scenario: {result}")
    sys.exit(1)

print("\n" + "=" * 60)
print("TEST scenario is ready!")
print("=" * 60)
