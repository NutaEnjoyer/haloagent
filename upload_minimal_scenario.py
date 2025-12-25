import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("VOXIMPLANT_ACCOUNT_ID")
API_KEY = os.getenv("VOXIMPLANT_API_KEY")
RULE_ID = os.getenv("VOXIMPLANT_RULE_ID")
SCENARIO_FILE = "voximplant_scenario_MINIMAL.js"
SCENARIO_NAME = "MinimalScenario"

# Set console encoding to UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("Uploading MINIMAL scenario")
print("=" * 60)

# Read scenario
with open(SCENARIO_FILE, 'r', encoding='utf-8') as f:
    scenario_code = f.read()

print(f"Loaded {len(scenario_code)} bytes from {SCENARIO_FILE}")

# Create/update scenario
response = requests.post(
    "https://api.voximplant.com/platform_api/AddScenario",
    data={
        "account_id": ACCOUNT_ID,
        "api_key": API_KEY,
        "scenario_name": SCENARIO_NAME,
        "scenario_script": scenario_code,
        "rewrite": "true"
    }
)

result = response.json()

if result.get("result") == 1:
    scenario_id = result.get("scenario_id")
    print(f"[OK] Scenario created: {scenario_id}")
else:
    print(f"[ERROR] {result}")
    sys.exit(1)

# Bind to rule
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
    print("[OK] Scenario bound to rule!")
    print("=" * 60)
    print("Ready to test!")
    print("=" * 60)
else:
    print(f"[ERROR] {result}")
    sys.exit(1)
