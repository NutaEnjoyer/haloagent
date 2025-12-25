"""
Check current Voximplant rule configuration.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("VOXIMPLANT_ACCOUNT_ID")
API_KEY = os.getenv("VOXIMPLANT_API_KEY")
RULE_ID = os.getenv("VOXIMPLANT_RULE_ID")

API_URL = "https://api.voximplant.com/platform_api"

# Get rule info
response = requests.post(
    f"{API_URL}/GetRules",
    data={
        "account_id": ACCOUNT_ID,
        "api_key": API_KEY,
        "rule_id": RULE_ID
    }
)

result = response.json()

if result.get("result") == 1:
    rules = result.get("result", [])
    if rules:
        rule = rules[0]
        print(f"Rule ID: {rule.get('rule_id')}")
        print(f"Rule Name: {rule.get('rule_name')}")
        print(f"Pattern: {rule.get('rule_pattern')}")
        print(f"Scenarios: {rule.get('scenarios')}")
        print()
        print("Full rule data:")
        print(rule)
    else:
        print("No rules found")
else:
    print(f"Error: {result}")
