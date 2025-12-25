# Voice Caller API - MVP

MVP сервиса голосового обзвона с использованием OpenAI (Whisper + GPT + TTS), провайдера телефонии и Google Sheets.

## Описание

Система автоматически звонит на указанный номер телефона, ведёт диалог с абонентом на русском языке, классифицирует результат разговора и сохраняет транскрипт в Google Sheets.

### Возможности

- ✅ Исходящие звонки на номера РФ
- ✅ Реалистичный диалог с использованием GPT-4
- ✅ Распознавание речи (Whisper STT)
- ✅ Синтез речи (OpenAI TTS)
- ✅ Автоматическая классификация интереса клиента
- ✅ Сохранение результатов в Google Sheets
- ✅ Задержка между репликами ≤ 2 сек

## Требования

- Python 3.11+
- OpenAI API ключ
- Google Cloud Service Account (для Google Sheets)
- Провайдер телефонии (Voximplant / Zadarma / Mango) или Stub для тестирования

## Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd callerapi
```

### 2. Создание виртуального окружения

```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Заполните переменные в `.env`:

```env
# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# Google Sheets
GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id
GOOGLE_CREDENTIALS_JSON={"type": "service_account", ...}
# или
GOOGLE_CREDENTIALS_FILE=/path/to/credentials.json

# API Security
API_AUTH_KEY=your-secret-api-key-here

# Optional
GPT_MODEL=gpt-4o
TTS_VOICE=alloy
MAX_CALL_DURATION_SEC=120
MAX_DIALOG_TURNS=12
```

## Запуск

### Локально

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Приложение будет доступно по адресу: http://localhost:8000

### С Docker

```bash
docker-compose up --build
```

## API Документация

### Основные эндпоинты

#### POST /call
Инициировать исходящий звонок.

**Запрос:**
```bash
curl -X POST http://localhost:8000/call \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{"phone": "+79991234567"}'
```

**Ответ:**
```json
{
  "call_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "created"
}
```

#### GET /health
Проверка здоровья сервиса.

**Запрос:**
```bash
curl http://localhost:8000/health
```

**Ответ:**
```json
{
  "status": "ok",
  "timestamp": "2025-10-15T10:30:00.000000",
  "active_calls": 2,
  "version": "1.0.0"
}
```

#### POST /telephony/events
Обработка событий от провайдера телефонии (webhook).

**Запрос:**
```json
{
  "call_id": "550e8400-e29b-41d4-a716-446655440000",
  "event": "answered",
  "timestamp": "2025-10-15T10:30:00Z",
  "reason": null
}
```

### Интерактивная документация

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Структура проекта

```
callerapi/
├── app/
│   ├── __init__.py
│   ├── main.py              # Главный файл приложения
│   ├── config.py            # Конфигурация
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes_call.py      # Эндпоинт /call
│   │   └── routes_telephony.py # Эндпоинт /telephony/events
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py           # Модели данных
│   │   ├── orchestrator.py     # Управление звонками
│   │   └── dialog_manager.py   # Управление диалогом
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── openai_client.py    # Клиент OpenAI (STT/GPT/TTS)
│   │   ├── google_sheets.py    # Клиент Google Sheets
│   │   ├── telephony_base.py   # Интерфейс телефонии
│   │   └── telephony_stub.py   # Заглушка для тестирования
│   └── utils/
│       ├── __init__.py
│       ├── logging.py          # Настройка логирования
│       └── time.py             # Утилиты для работы со временем
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
└── IMPLEMENTATION_PLAN.md
```

## Настройка Google Sheets

### 1. Создание Service Account

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект (или выберите существующий)
3. Включите Google Sheets API и Google Drive API
4. Создайте Service Account:
   - IAM & Admin → Service Accounts → Create Service Account
   - Скачайте JSON ключ
5. Сохраните JSON ключ в безопасном месте

### 2. Настройка Spreadsheet

1. Создайте новую Google Таблицу
2. Скопируйте ID из URL (длинная строка между `/d/` и `/edit`)
3. Откройте доступ для service account:
   - Нажмите "Share"
   - Добавьте email service account (из JSON ключа)
   - Дайте права "Editor"

### 3. Конфигурация

Вариант 1 (JSON строка):
```env
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}
```

Вариант 2 (файл):
```env
GOOGLE_CREDENTIALS_FILE=/path/to/credentials.json
```

## Настройка провайдера телефонии

### Stub (для тестирования)

По умолчанию используется заглушка (`StubTelephonyAdapter`), которая:
- Имитирует звонок без реальной телефонии
- Генерирует тестовые ответы от "абонента"
- Позволяет протестировать всю логику без реального звонка

### Реальный провайдер (Voximplant / Zadarma / Mango)

Для интеграции реального провайдера:

1. Создайте новый файл `app/integrations/telephony_<provider>.py`
2. Реализуйте класс, соответствующий интерфейсу `TelephonyAdapter`
3. Настройте webhook URL в панели провайдера:
   ```
   https://your-domain.com/telephony/events
   ```
4. Обновите `app/main.py` для использования нового адаптера

## Деплой на VPS

### 1. Подготовка VPS

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y python3.11 python3.11-venv python3-pip git nginx supervisor ffmpeg

# Настройка firewall
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### 2. Установка приложения

```bash
# Клонирование репозитория
cd /opt
sudo git clone <repo-url> callerapi
sudo chown -R $USER:$USER /opt/callerapi

# Установка зависимостей
cd /opt/callerapi
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Создание .env файла
nano .env
# (заполнить переменные окружения)

# Создание директории для логов
sudo mkdir -p /var/log/callerapi
sudo chown $USER:$USER /var/log/callerapi
```

### 3. Настройка Supervisor

Создайте файл `/etc/supervisor/conf.d/callerapi.conf`:

```ini
[program:callerapi]
directory=/opt/callerapi
command=/opt/callerapi/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
user=your-user
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/callerapi/app.log
environment=PATH="/opt/callerapi/venv/bin"
```

Применить:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start callerapi
```

### 4. Настройка Nginx

Создайте файл `/etc/nginx/sites-available/callerapi`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Активировать:
```bash
sudo ln -s /etc/nginx/sites-available/callerapi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. SSL сертификат (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Логирование

Логи пишутся:
- В stdout (консоль)
- В `/var/log/callerapi/app.log` (на VPS)

Просмотр логов:
```bash
# Real-time
tail -f /var/log/callerapi/app.log

# Последние 100 строк
tail -n 100 /var/log/callerapi/app.log

# Поиск по ошибкам
grep ERROR /var/log/callerapi/app.log
```

## Troubleshooting

### Проблема: "Invalid API key"
**Решение**: Проверьте что заголовок `X-API-Key` совпадает с `API_AUTH_KEY` в `.env`

### Проблема: "Failed to connect to Google Sheets"
**Решение**:
- Проверьте что service account имеет доступ к таблице
- Проверьте формат JSON credentials
- Убедитесь что Google Sheets API включен

### Проблема: "OpenAI API error"
**Решение**:
- Проверьте баланс на аккаунте OpenAI
- Проверьте корректность API ключа
- Проверьте лимиты (rate limits)

### Проблема: Задержки > 2 сек
**Решение**:
- Уменьшите размер аудио чанков
- Используйте более быстрые модели (gpt-4o-mini, tts-1)
- Проверьте сетевые задержки (ping api.openai.com)
- Оптимизируйте системный промпт (сделать короче)

## Примеры использования

### Простой звонок

```bash
curl -X POST http://localhost:8000/call \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-secret-key" \
  -d '{"phone": "+79991234567"}'
```

### Проверка статуса

```bash
curl http://localhost:8000/health
```

### Просмотр API документации

Откройте в браузере: http://localhost:8000/docs

## Лицензия

Proprietary - проект создан в рамках договора 0708_01 от 08 октября 2025 года.

## Контакты

По вопросам работы сервиса обращайтесь к разработчику.
