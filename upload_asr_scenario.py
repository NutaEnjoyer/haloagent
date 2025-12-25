"""
Upload and bind the new ASR-based scenario to Voximplant.
This scenario uses real-time ASR instead of call.record().
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("VOXIMPLANT_ACCOUNT_ID")
API_KEY = os.getenv("VOXIMPLANT_API_KEY")
RULE_ID = os.getenv("VOXIMPLANT_RULE_ID")

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Read ASR scenario
print("Reading ASR scenario...")
with open('VOXIMPLANT_SCENARIO.js', encoding='utf-8') as f:
    code = f.read()

# Step 1: Delete old scenarios if they exist
print("\n=== Cleaning up old scenarios ===")
old_scenarios = ['WorkingAI', 'SimpleAI', 'RecorderAPI', 'MinimalScenario']
for scenario_name in old_scenarios:
    print(f"Attempting to delete {scenario_name}...")
    r = requests.post('https://api.voximplant.com/platform_api/DelScenario', data={
        'account_id': ACCOUNT_ID,
        'api_key': API_KEY,
        'scenario_name': scenario_name
    })
    result = r.json()
    if "error" in result:
        print(f"  ⚠️  {result['error']['msg']} (OK if scenario doesn't exist)")
    else:
        print(f"  ✅ Deleted")

# Step 2: Create new ASR scenario
import time
scenario_name = f'ASR_AI_v{int(time.time())}'
print(f"\n=== Creating ASR scenario: {scenario_name} ===")
r = requests.post('https://api.voximplant.com/platform_api/AddScenario', data={
    'account_id': ACCOUNT_ID,
    'api_key': API_KEY,
    'scenario_name': scenario_name,
    'scenario_script': code,
    'rewrite': 'false'
})
result = r.json()

if "error" in result:
    print(f"❌ Error creating scenario: {result['error']['msg']}")
    sys.exit(1)

scenario_id = result.get('scenario_id')
print(f"✅ Created scenario ID: {scenario_id}")

# Step 3: Bind to rule
print("\n=== Binding to rule ===")
r = requests.post('https://api.voximplant.com/platform_api/BindScenario', data={
    'account_id': ACCOUNT_ID,
    'api_key': API_KEY,
    'rule_id': RULE_ID,
    'scenario_id': str(scenario_id),
    'bind': 'true'
})
result = r.json()

if "error" in result:
    print(f"❌ Error binding scenario: {result['error']['msg']}")
    sys.exit(1)

print(f"✅ Scenario bound to rule")

print("\n" + "="*60)
print("🎉 ASR scenario deployed successfully!")
print("="*60)
print("\nКлючевые изменения:")
print("  ✅ Использует ASR для распознавания речи в реальном времени")
print("  ✅ Событие ASREvents.Result предоставляет транскрипцию")
print("  ✅ Не нужно ждать RecordStopped (который срабатывает только после hangup)")
print("  ✅ Новый эндпоинт /process_text для обработки текста")
print("\nГотово к тестированию!")
