import os
import json
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("VOXIMPLANT_ACCOUNT_ID")
API_KEY = os.getenv("VOXIMPLANT_API_KEY")
RULE_ID = os.getenv("VOXIMPLANT_RULE_ID")
SCENARIO_ID = "2993071"  # MinimalScenario

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("Binding MinimalScenario to Rule (CORRECTLY)")
print("=" * 60)

# First, unbind all scenarios from rule
print("\nStep 1: Getting current bindings...")
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
    print(f"Currently bound scenarios: {[s['scenario_id'] for s in current_scenarios]}")

# Unbind all current scenarios
if current_scenarios:
    print("\nStep 2: Unbinding old scenarios...")
    for scenario in current_scenarios:
        scenario_id = scenario["scenario_id"]
        print(f"  Unbinding {scenario['scenario_name']} ({scenario_id})...")

        response = requests.post(
            "https://api.voximplant.com/platform_api/DelScenario",
            data={
                "account_id": ACCOUNT_ID,
                "api_key": API_KEY,
                "rule_id": RULE_ID,
                "scenario_id": str(scenario_id)
            }
        )

        unbind_result = response.json()
        if unbind_result.get("result") == 1:
            print(f"    [OK] Unbound")
        else:
            print(f"    [ERROR] {unbind_result}")

# Bind MinimalScenario
print(f"\nStep 3: Binding MinimalScenario ({SCENARIO_ID})...")

response = requests.post(
    "https://api.voximplant.com/platform_api/BindScenario",
    data={
        "account_id": ACCOUNT_ID,
        "api_key": API_KEY,
        "rule_id": RULE_ID,
        "scenario_id": SCENARIO_ID,
        "bind": "true"
    }
)

bind_result = response.json()

if bind_result.get("result") == 1:
    print("[OK] MinimalScenario bound successfully!")
else:
    print(f"[ERROR] {bind_result}")
    sys.exit(1)

# Verify
print("\nStep 4: Verifying...")
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

if result.get("result"):
    scenarios = result["result"][0].get("scenarios", [])
    print(f"Now bound scenarios:")
    for s in scenarios:
        print(f"  - {s['scenario_name']} (ID: {s['scenario_id']})")

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)
