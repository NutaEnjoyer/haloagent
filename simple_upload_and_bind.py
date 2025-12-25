import os, sys, requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("VOXIMPLANT_ACCOUNT_ID")
API_KEY = os.getenv("VOXIMPLANT_API_KEY")
RULE_ID = os.getenv("VOXIMPLANT_RULE_ID")

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Read scenario
with open('voximplant_scenario_WORKING_AI.js', encoding='utf-8') as f:
    code = f.read()

# Create scenario
print("Creating WorkingAI scenario...")
r = requests.post('https://api.voximplant.com/platform_api/AddScenario', data={
    'account_id': ACCOUNT_ID,
    'api_key': API_KEY,
    'scenario_name': 'WorkingAI',
    'scenario_script': code,
    'rewrite': 'true'
})
result = r.json()
scenario_id = result.get('scenario_id')
print(f"Created scenario ID: {scenario_id}")

# Bind to rule
print("Binding to rule...")
r = requests.post('https://api.voximplant.com/platform_api/BindScenario', data={
    'account_id': ACCOUNT_ID,
    'api_key': API_KEY,
    'rule_id': RULE_ID,
    'scenario_id': str(scenario_id),
    'bind': 'true'
})
print(f"Bind result: {r.json()}")
