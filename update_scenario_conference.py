import requests

# Read scenario code
with open(r'C:\Users\user\Desktop\callerapi\voximplant_conference.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Update OutboundCall scenario (ID: 2992920)
data = {
    'account_id': '10042950',
    'api_key': '633eadbc-6cb2-447e-a0b1-c40d2c5e4bef',
    'scenario_id': '2992920',
    'scenario_script': code
}

response = requests.post('https://api.voximplant.com/platform_api/SetScenarioInfo/', data=data)
result = response.json()
print(result)

if result.get('result') == 1:
    print("\nScenario updated with Conference support!")
