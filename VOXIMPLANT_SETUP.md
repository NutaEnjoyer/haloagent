# Настройка Voximplant для HALO Demo

Это руководство описывает, как настроить Voximplant для работы с демо-кабинетом HALO.

## Предварительные требования

1. Аккаунт Voximplant (зарегистрируйтесь на [voximplant.com](https://voximplant.com))
2. Пополненный баланс для исходящих звонков
3. Арендованный номер или подключенный SIP-провайдер
4. Публично доступный URL вашего backend (для webhooks)

---

## Шаг 1: Создание Application

1. Войдите в [Voximplant Control Panel](https://manage.voximplant.com/)
2. Перейдите в раздел **Applications**
3. Нажмите **Create Application**
4. Введите имя: `HALO_DEMO`
5. Сохраните **Application ID** - он понадобится для конфигурации

---

## Шаг 2: Создание VoxEngine Scenario

### 2.1. Создать Scenario

1. В приложении `HALO_DEMO` перейдите в **Scenarios**
2. Нажмите **Create Scenario**
3. Имя: `OutboundCallWithAI`
4. Вставьте код сценария (см. ниже)

### 2.2. VoxEngine Scenario Code

```javascript
/**
 * VoxEngine Scenario для исходящих звонков с интеграцией OpenAI
 * Phase 1: Базовый звонок с webhook уведомлениями
 */

// Глобальные переменные
let callSession = null;
let customData = {};
let webhookUrl = "";

// Обработчик запуска сценария
VoxEngine.addEventListener(AppEvents.Started, function(e) {
    Logger.write("Scenario started");

    try {
        // Парсим custom data от backend
        customData = JSON.parse(e.customData);

        const callId = customData.call_id;
        const phone = customData.phone;
        const callerId = customData.caller_id;
        webhookUrl = customData.webhook_url;

        Logger.write("Custom data parsed: " + JSON.stringify(customData));

        // Создаем исходящий PSTN звонок
        callSession = VoxEngine.callPSTN(phone, callerId);

        // Подписываемся на события звонка
        callSession.addEventListener(CallEvents.Connected, onCallConnected);
        callSession.addEventListener(CallEvents.Disconnected, onCallDisconnected);
        callSession.addEventListener(CallEvents.Failed, onCallFailed);
        callSession.addEventListener(CallEvents.AnsweringMachinDetection, onAMDDetected);

        Logger.write("Outbound call initiated to: " + phone);

    } catch (error) {
        Logger.write("Error in scenario start: " + error);
        sendWebhook({
            event: "Failed",
            call_id: customData.call_id || "unknown",
            reason: "Scenario error: " + error
        });
        VoxEngine.terminate();
    }
});

// Звонок соединен (абонент поднял трубку)
function onCallConnected(e) {
    Logger.write("Call connected");

    sendWebhook({
        event: "Connected",
        call_id: customData.call_id,
        timestamp: Date.now()
    });

    // Phase 1: Проигрываем приветственное сообщение
    // Phase 2: Здесь будет интеграция с OpenAI Realtime API

    callSession.say("Здравствуйте! Это тестовый звонок от HALO. Спасибо, что приняли звонок.", Language.RU_RUSSIAN_FEMALE);

    // Для Phase 1 завершаем через 5 секунд
    setTimeout(function() {
        if (callSession) {
            callSession.hangup();
        }
    }, 5000);
}

// Звонок завершен
function onCallDisconnected(e) {
    Logger.write("Call disconnected");

    sendWebhook({
        event: "Disconnected",
        call_id: customData.call_id,
        reason: "normal",
        timestamp: Date.now()
    });

    VoxEngine.terminate();
}

// Звонок не удался
function onCallFailed(e) {
    Logger.write("Call failed: " + e.code + " - " + e.reason);

    let reason = "unknown";

    // Определяем причину
    if (e.code === 486) {
        reason = "busy";
    } else if (e.code === 480 || e.code === 408) {
        reason = "no answer";
    } else {
        reason = "error: " + e.reason;
    }

    sendWebhook({
        event: "Failed",
        call_id: customData.call_id,
        reason: reason,
        code: e.code,
        timestamp: Date.now()
    });

    VoxEngine.terminate();
}

// Определение автоответчика (опционально)
function onAMDDetected(e) {
    Logger.write("AMD detected: " + (e.isHuman ? "Human" : "Machine"));

    // Можно завершить звонок, если автоответчик
    if (!e.isHuman) {
        sendWebhook({
            event: "Failed",
            call_id: customData.call_id,
            reason: "answering machine detected"
        });

        callSession.hangup();
    }
}

// Отправка webhook в backend
function sendWebhook(data) {
    if (!webhookUrl) {
        Logger.write("No webhook URL configured");
        return;
    }

    try {
        Logger.write("Sending webhook to: " + webhookUrl);
        Logger.write("Webhook data: " + JSON.stringify(data));

        Net.httpRequest(webhookUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            postData: JSON.stringify(data)
        }, function(response) {
            if (response.code === 200) {
                Logger.write("Webhook sent successfully");
            } else {
                Logger.write("Webhook failed: " + response.code);
            }
        });

    } catch (error) {
        Logger.write("Error sending webhook: " + error);
    }
}
```

---

## Шаг 3: Создание Routing Rule

1. В приложении `HALO_DEMO` перейдите в **Routing**
2. Нажмите **Create Rule**
3. Настройте правило:
   - **Rule name**: `OutboundCallRule`
   - **Rule pattern**: `.*` (любой pattern, т.к. вызов через API)
   - **Assign scenario**: Выберите `OutboundCallWithAI`
4. Сохраните **Rule ID** - он понадобится для конфигурации

---

## Шаг 4: Получение API credentials

1. Перейдите в **Account Settings** → **API Keys**
2. Создайте новый API Key или используйте существующий
3. Сохраните:
   - **Account ID**
   - **API Key**

---

## Шаг 5: Настройка арендованного номера

### Вариант А: Аренда номера от Voximplant

1. Перейдите в **Numbers** → **Buy Number**
2. Выберите страну и номер
3. Арендуйте номер
4. Привяжите номер к приложению `HALO_DEMO`

### Вариант Б: Подключение SIP-провайдера

1. Перейдите в **SIP Registrations**
2. Настройте подключение к вашему SIP-провайдеру
3. Используйте этот номер как `VOXIMPLANT_CALLER_ID`

---

## Шаг 6: Конфигурация Backend

Обновите `.env` файл:

```bash
# Voximplant Configuration
VOXIMPLANT_ACCOUNT_ID=1234567  # Ваш Account ID
VOXIMPLANT_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  # Ваш API Key
VOXIMPLANT_APPLICATION_ID=987654  # Application ID из Шага 1
VOXIMPLANT_RULE_ID=123  # Rule ID из Шага 3
VOXIMPLANT_CALLER_ID=+74951234567  # Арендованный номер
BACKEND_URL=https://your-domain.com  # Публичный URL вашего backend
USE_VOXIMPLANT=true  # Включить Voximplant (вместо Stub)

# API Security
API_AUTH_KEY=your-secret-api-key-here

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
```

---

## Шаг 7: Проверка webhook URL

Убедитесь, что ваш backend доступен по адресу:
```
https://your-domain.com/voximplant/events
```

Вы можете проверить доступность:
```bash
curl https://your-domain.com/voximplant/health
```

Должно вернуть:
```json
{
  "status": "ok",
  "service": "voximplant_webhook"
}
```

---

## Шаг 8: Тестирование

### 8.1. Запустите backend

```bash
python -m uvicorn app.main:app --reload
```

### 8.2. Проверьте логи

При старте должно быть:
```
INFO:     Voximplant adapter initialized | account_id=1234567 | webhook_url=https://your-domain.com/voximplant/events
```

### 8.3. Создайте тестовый звонок

Через frontend или API:

```bash
curl -X POST http://localhost:8000/demo/session \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+79991234567",
    "language": "auto",
    "voice": "female",
    "prompt": "Вы - вежливый оператор HALO. Представьтесь и узнайте интерес клиента."
  }'
```

### 8.4. Проверьте логи

Должны появиться:
```
[Voximplant] Initiating call | call_id=... | phone=+79991234567
[Voximplant Webhook] Received event | call_id=... | event=Connected
[Voximplant Webhook] Received event | call_id=... | event=Disconnected
```

---

## Troubleshooting

### Проблема: Звонок не инициируется

- Проверьте баланс аккаунта Voximplant
- Проверьте правильность API credentials
- Проверьте логи backend на ошибки

### Проблема: Webhooks не приходят

- Убедитесь, что `BACKEND_URL` публично доступен
- Проверьте firewall и CORS настройки
- Используйте ngrok для локального тестирования:
  ```bash
  ngrok http 8000
  # Используйте ngrok URL в BACKEND_URL
  ```

### Проблема: Звонок завершается сразу

- Проверьте логи VoxEngine в Voximplant Control Panel → Calls → History
- Проверьте, что сценарий не содержит ошибок
- Проверьте наличие баланса и прав на звонки

---

## Phase 2: Streaming Integration

В Phase 2 мы добавим:
- WebSocket streaming для real-time audio
- Интеграция с OpenAI Realtime API
- Двусторонний обмен аудио

Сценарий будет обновлен для поддержки WebSocket соединения с backend.

---

## Полезные ссылки

- [Voximplant Documentation](https://voximplant.com/docs)
- [VoxEngine API Reference](https://voximplant.com/docs/references/voxengine)
- [HTTP API Reference](https://voximplant.com/docs/references/httpapi)
- [VoxEngine Examples](https://github.com/voximplant/voxengine-examples)
