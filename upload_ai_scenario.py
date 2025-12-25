import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("VOXIMPLANT_ACCOUNT_ID")
API_KEY = os.getenv("VOXIMPLANT_API_KEY")
RULE_ID = os.getenv("VOXIMPLANT_RULE_ID")
SCENARIO_FILE = "voximplant_scenario_WORKING_AI.js"
SCENARIO_NAME = "WorkingAI"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("Uploading and binding WorkingAI scenario")
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
    print(f"[OK] Scenario created/updated: {scenario_id}")
else:
    print(f"[ERROR] {result}")
    sys.exit(1)

# Get current bindings
print("\nGetting current rule bindings...")
response = requests.post(
    "https://api.voximplant.com/platform_api/GetRules",
    data={
        "account_id": ACCOUNT_ID,
        "api_key": API_KEY,
        "rule_id": RULE_ID,
        "with_scenarios": "true"
    }
)

result = response.json()
current_scenarios = []

if result.get("result"):
    current_scenarios = result["result"][0].get("scenarios", [])
    print(f"Currently bound: {[s['scenario_name'] for s in current_scenarios]}")

# Unbind all current scenarios
if current_scenarios:
    print("\nUnbinding old scenarios...")
    for scenario in current_scenarios:
        sid = scenario["scenario_id"]
        print(f"  Unbinding {scenario['scenario_name']}...")

        response = requests.post(
            "https://api.voximplant.com/platform_api/DelScenario",
            data={
                "account_id": ACCOUNT_ID,
                "api_key": API_KEY,
                "rule_id": RULE_ID,
                "scenario_id": str(sid)
            }
        )

        if response.json().get("result") == 1:
            print(f"    [OK]")

# Bind new scenario
print(f"\nBinding WorkingAI scenario...")

response = requests.post(
    "https://api.voximplant.com/platform_api/BindScenario",
    data={
        "account_id": ACCOUNT_ID,
        "api_key": API_KEY,
        "rule_id": RULE_ID,
        "scenario_id": scenario_id,
        "bind": "true"
    }
)

if response.json().get("result") == 1:
    print("[OK] WorkingAI scenario bound successfully!")
    print("\n" + "=" * 60)
    print("Ready to test AI integration!")
    print("=" * 60)
else:
    print(f"[ERROR] {response.json()}")
    sys.exit(1)
