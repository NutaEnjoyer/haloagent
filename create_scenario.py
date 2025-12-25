import requests

# Read scenario code
with open(r'C:\Users\user\Desktop\callerapi\voximplant_clean.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Create scenario in Voximplant
data = {
    'account_id': '10042950',
    'api_key': '633eadbc-6cb2-447e-a0b1-c40d2c5e4bef',
    'scenario_name': 'OutboundCall',
    'scenario_script': code
}

response = requests.post('https://api.voximplant.com/platform_api/AddScenario/', data=data)
result = response.json()
print(result)

if result.get('result') == 1:
    scenario_id = result.get('scenario_id')
    print(f"\n✓ Scenario created successfully!")
    print(f"  Scenario ID: {scenario_id}")
    print(f"  Scenario name: OutboundCall")
