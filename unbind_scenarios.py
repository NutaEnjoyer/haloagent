"""
Unbind old scenarios and keep only the latest one
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv('VOXIMPLANT_ACCOUNT_ID')
API_KEY = os.getenv('VOXIMPLANT_API_KEY')
RULE_ID = os.getenv('VOXIMPLANT_RULE_ID')

# List of old scenario IDs to unbind
old_scenarios = [2993135, 2994811, 2993067]

print('Unbinding old scenarios...')
for scenario_id in old_scenarios:
    r = requests.post('https://api.voximplant.com/platform_api/BindScenario', data={
        'account_id': ACCOUNT_ID,
        'api_key': API_KEY,
        'rule_id': RULE_ID,
        'scenario_id': str(scenario_id),
        'bind': 'false'
    })
    result = r.json()
    if 'error' in result:
        print(f'  Scenario {scenario_id}: {result["error"]["msg"]}')
    else:
        print(f'  OK: Unbound scenario {scenario_id}')

print('\nBinding only the latest scenario (2994981)...')
r = requests.post('https://api.voximplant.com/platform_api/BindScenario', data={
    'account_id': ACCOUNT_ID,
    'api_key': API_KEY,
    'rule_id': RULE_ID,
    'scenario_id': '2994981',
    'bind': 'true'
})
result = r.json()
if 'error' in result:
    print(f'  ERROR: {result["error"]["msg"]}')
else:
    print('  OK: Bound scenario 2994981')

print('\nDone! Only one scenario is now bound to the rule.')
