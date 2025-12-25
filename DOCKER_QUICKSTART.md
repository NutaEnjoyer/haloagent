# 🐳 Docker Quickstart

## Шаг 1: Настройка .env

Откройте `.env` и **обязательно замените**:

```env
OPENAI_API_KEY=sk-ваш-реальный-ключ-openai
```

Остальное можно оставить как есть:
```env
API_AUTH_KEY=test-key-123
USE_MOCK_SHEETS=true
```

## Шаг 2: Сборка и запуск через Docker Compose

```bash
docker-compose up --build
```

**Что происходит:**
- Собирается Docker образ с Python 3.11 + зависимостями
- Запускается контейнер на порту 8000
- Монтируются volume для логов

## Шаг 3: Проверка статуса

Откройте новый терминал и выполните:

```bash
curl http://localhost:8000/health
```

**Ожидаемый ответ:**
```json
{
  "status": "ok",
  "timestamp": "2025-10-15T10:30:00.000000",
  "active_calls": 0,
  "version": "1.0.0"
}

```

## Шаг 4: Тестовый звонок

```bash
curl -X POST http://localhost:8000/call \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-123" \
  -d "{\"phone\": \"+79991234567\"}"
```

**Ожидаемый ответ:**
```json
{
  "call_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "created"
}
```

## Шаг 5: Мониторинг логов

В первом терминале (где запущен docker-compose) вы увидите:
- ✅ Создание звонка
- ✅ События: ringing → answered
- ✅ Начало диалога
- ✅ Вызовы OpenAI GPT/TTS
- ✅ Имитацию ответов от абонента
- ✅ Классификацию результата
- ✅ Сохранение в mock_sheets_data/

## Шаг 6: Проверка результатов

```bash
# Посмотреть все звонки (CSV)
cat mock_sheets_data/calls.csv

# Посмотреть детальный результат последнего звонка (JSON)
ls -lt mock_sheets_data/*.json | head -1 | awk '{print $9}' | xargs cat
```

## 🛑 Остановка контейнера

```bash
# Ctrl+C в терминале с docker-compose
# Или в другом терминале:
docker-compose down
```

## 🔍 Полезные команды

### Посмотреть логи контейнера
```bash
docker-compose logs -f callerapi
```

### Зайти внутрь контейнера
```bash
docker-compose exec callerapi bash
```

### Пересобрать образ (если изменили код)
```bash
docker-compose up --build
```

### Очистить всё (контейнеры, volumes, образы)
```bash
docker-compose down -v
docker rmi callerapi-callerapi
```

## 🐛 Troubleshooting

### Ошибка: "Cannot connect to Docker daemon"
```bash
# Windows: убедитесь что Docker Desktop запущен
# Linux:
sudo systemctl start docker
```

### Ошибка: "Port 8000 already in use"
Измените порт в `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # внешний:внутренний
```

### Контейнер падает сразу после запуска
```bash
# Посмотрите логи
docker-compose logs callerapi

# Скорее всего проблема с .env (OPENAI_API_KEY)
```

### Нет доступа к mock_sheets_data/
```bash
# Создайте папку вручную
mkdir mock_sheets_data

# Или дайте права
chmod 777 mock_sheets_data
```

## ✅ Критерии успешного запуска

- [ ] `docker-compose up --build` завершился без ошибок
- [ ] В логах: "Voice Caller API started successfully"
- [ ] `curl http://localhost:8000/health` возвращает 200 OK
- [ ] POST /call создает звонок
- [ ] В логах видны вызовы к OpenAI
- [ ] Создается файл в mock_sheets_data/

## 📊 Ожидаемый вывод логов

```
callerapi  | 2025-10-15 10:30:00 - callerapi - INFO - main:46 - Starting Voice Caller API...
callerapi  | 2025-10-15 10:30:00 - callerapi - INFO - main:50 - Initializing OpenAI client...
callerapi  | 2025-10-15 10:30:00 - callerapi - INFO - main:55 - Initializing Google Sheets client (MOCK mode)...
callerapi  | 2025-10-15 10:30:00 - callerapi - INFO - google_sheets_mock:24 - [MOCK] Google Sheets client initialized (saving to mock_sheets_data/)
callerapi  | 2025-10-15 10:30:00 - callerapi - INFO - main:63 - Initializing Telephony adapter (Stub mode)...
callerapi  | 2025-10-15 10:30:00 - callerapi - INFO - main:80 - Voice Caller API started successfully
callerapi  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## 🎯 Что дальше?

После успешного теста в Docker:
1. Настроить реальный Google Sheets (убрать USE_MOCK_SHEETS=true)
2. Интегрировать реального провайдера телефонии
3. Задеплоить на VPS
