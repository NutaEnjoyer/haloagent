"""
Upload STREAMING scenario to Voximplant.

This script uploads voximplant_scenario_STREAMING.js to your Voximplant account.
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Voximplant API credentials
ACCOUNT_ID = os.getenv("VOXIMPLANT_ACCOUNT_ID")
API_KEY = os.getenv("VOXIMPLANT_API_KEY")
APPLICATION_ID = os.getenv("VOXIMPLANT_APPLICATION_ID")

# Voximplant API endpoint
API_URL = "https://api.voximplant.com/platform_api"

SCENARIO_NAME = "OutboundCallStreaming"
SCENARIO_FILE = "voximplant_scenario_STREAMING.js"


def read_scenario_code():
    """Read scenario JavaScript code from file."""
    try:
        with open(SCENARIO_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Error: {SCENARIO_FILE} not found!")
        print("Make sure you're running this script from the project root directory.")
        sys.exit(1)


def upload_scenario(scenario_code):
    """Upload scenario to Voximplant via API."""
    print(f"📤 Uploading scenario '{SCENARIO_NAME}' to Voximplant...")

    # Check if scenario exists
    print("Checking if scenario exists...")

    response = requests.post(
        f"{API_URL}/GetScenarios",
        data={
            "account_id": ACCOUNT_ID,
            "api_key": API_KEY,
            "scenario_name": SCENARIO_NAME
        }
    )

    result = response.json()

    if result.get("result") == 1 and len(result.get("result", [])) > 0:
        # Scenario exists - update it
        print(f"Scenario '{SCENARIO_NAME}' exists - updating...")

        scenario_id = result["result"][0]["scenario_id"]

        response = requests.post(
            f"{API_URL}/SetScenarioInfo",
            data={
                "account_id": ACCOUNT_ID,
                "api_key": API_KEY,
                "scenario_id": scenario_id,
                "scenario_script": scenario_code
            }
        )
    else:
        # Scenario doesn't exist - create it
        print(f"Scenario '{SCENARIO_NAME}' doesn't exist - creating...")

        response = requests.post(
            f"{API_URL}/AddScenario",
            data={
                "account_id": ACCOUNT_ID,
                "api_key": API_KEY,
                "scenario_name": SCENARIO_NAME,
                "scenario_script": scenario_code
            }
        )

    result = response.json()

    if result.get("result") == 1:
        print(f"✅ Scenario '{SCENARIO_NAME}' uploaded successfully!")
        return True
    else:
        error_msg = result.get("error", {}).get("msg", "Unknown error")
        print(f"❌ Failed to upload scenario: {error_msg}")
        print(f"Full response: {result}")
        return False


def main():
    """Main function."""
    print("=" * 60)
    print("Voximplant Scenario Upload Tool")
    print("=" * 60)
    print()

    # Validate credentials
    if not all([ACCOUNT_ID, API_KEY, APPLICATION_ID]):
        print("❌ Error: Missing Voximplant credentials!")
        print("Please set the following in your .env file:")
        print("  - VOXIMPLANT_ACCOUNT_ID")
        print("  - VOXIMPLANT_API_KEY")
        print("  - VOXIMPLANT_APPLICATION_ID")
        sys.exit(1)

    print(f"Account ID: {ACCOUNT_ID}")
    print(f"Application ID: {APPLICATION_ID}")
    print()

    # Read scenario code
    scenario_code = read_scenario_code()
    print(f"📄 Loaded scenario from {SCENARIO_FILE}")
    print(f"   Code size: {len(scenario_code)} characters")
    print()

    # Upload scenario
    success = upload_scenario(scenario_code)

    if success:
        print()
        print("=" * 60)
        print("Next steps:")
        print("=" * 60)
        print("1. Go to Voximplant Console")
        print("2. Navigate to Applications → Rules")
        print(f"3. Update your rule to use scenario: '{SCENARIO_NAME}'")
        print("4. Save the rule")
        print()
        print("Then test by making a call:")
        print("  curl -X POST http://localhost:8000/calls \\")
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"phone": "+79019433546"}\'')
        print("=" * 60)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
