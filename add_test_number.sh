#!/bin/bash

# Добавить тестовый номер для исходящих звонков в Voximplant

ACCOUNT_ID="10042950"
API_KEY="633eadbc-6cb2-447e-a0b1-c40d2c5e4bef"
PHONE_NUMBER="79279052818"  # Без +

# Добавляем номер
curl -X POST "https://api.voximplant.com/platform_api/AddOutboundTestPhoneNumber/" \
  -d "account_id=${ACCOUNT_ID}" \
  -d "api_key=${API_KEY}" \
  -d "phone_number=${PHONE_NUMBER}"

echo ""
echo "Voximplant позвонит на ${PHONE_NUMBER} и продиктует код."
echo "После получения кода, введите его:"
read -p "Код верификации: " CODE

# Активируем номер с кодом
curl -X POST "https://api.voximplant.com/platform_api/ActivateOutboundTestPhoneNumber/" \
  -d "account_id=${ACCOUNT_ID}" \
  -d "api_key=${API_KEY}" \
  -d "verification_code=${CODE}"

echo ""
echo "Готово! Проверяем статус:"

# Проверяем статус
curl "https://api.voximplant.com/platform_api/GetOutboundTestPhoneNumbers/?account_id=${ACCOUNT_ID}&api_key=${API_KEY}"
