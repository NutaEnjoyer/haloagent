"""
Start a test call using Voximplant Platform API.
The scenario will call +79019433546 and test ASR integration.
"""
import os
import sys
import requests
import uuid
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

ACCOUNT_ID = os.getenv("VOXIMPLANT_ACCOUNT_ID")
API_KEY = os.getenv("VOXIMPLANT_API_KEY")
RULE_ID = os.getenv("VOXIMPLANT_RULE_ID")
BACKEND_URL = os.getenv("BACKEND_URL")

# Generate unique call ID
call_id = str(uuid.uuid4())

print("=== Starting ASR Test Call ===")
print(f"Call ID: {call_id}")
print(f"Target number: +79019433546")
print(f"Backend webhook: {BACKEND_URL}/voximplant/events")

# Start call via Platform API
# This will trigger the rule, which runs the ASR_AI scenario
response = requests.post('https://api.voximplant.com/platform_api/StartScenarios', data={
    'account_id': ACCOUNT_ID,
    'api_key': API_KEY,
    'rule_id': RULE_ID,
    'script_custom_data': f'{{"call_id": "{call_id}", "webhook_url": "{BACKEND_URL}/voximplant/events"}}'
})

result = response.json()

if "error" in result:
    print(f"\n❌ Error: {result['error']['msg']}")
    print(f"Code: {result['error']['code']}")
else:
    print(f"\n✅ Call started successfully!")
    print(f"Media session UID: {result.get('media_session_uid')}")
    print(f"\n📞 Voximplant звонит на +79019433546...")
    print(f"🎤 Приготовься ответить и говорить с AI-ассистентом!")
    print(f"\n📊 Смотри логи:")
    print(f"   - VoxEngine: https://manage.voximplant.com/applications")
    print(f"   - Backend: docker-compose logs -f backend")

print("\n" + "="*60)
