import requests

# Read scenario code
with open(r'C:\Users\user\Desktop\callerapi\temp_scenario.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Upload to Voximplant
data = {
    'account_id': '10042950',
    'api_key': '633eadbc-6cb2-447e-a0b1-c40d2c5e4bef',
    'scenario_id': '2992893',
    'scenario_script': code
}

response = requests.post('https://api.voximplant.com/platform_api/SetScenarioInfo/', data=data)
print(response.text)
