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
print("Checking Voximplant Rule Configuration")
print("=" * 60)

# Get rule info
response = requests.post(
    "https://api.voximplant.com/platform_api/GetRules",
    data={
        "account_id": ACCOUNT_ID,
        "api_key": API_KEY,
        "rule_id": RULE_ID
    }
)

result = response.json()

print("\nRule Info:")
print(json.dumps(result, indent=2))

# Get application info
if result.get("result"):
    for rule in result.get("result", []):
        app_id = rule.get("application_id")
        print(f"\n" + "=" * 60)
        print(f"Application ID: {app_id}")
        print("=" * 60)

        app_response = requests.post(
            "https://api.voximplant.com/platform_api/GetApplications",
            data={
                "account_id": ACCOUNT_ID,
                "api_key": API_KEY,
                "application_id": app_id
            }
        )

        app_result = app_response.json()
        print("\nApplication Info:")
        print(json.dumps(app_result, indent=2))
