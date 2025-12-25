# Запуск HALO Demo через Docker Compose

Полная инструкция по запуску демо-кабинета HALO в Docker.

---

## 📋 Предварительные требования

1. **Docker** и **Docker Compose** установлены
2. Файл `.env` настроен (см. ниже)

---

## ⚙️ Настройка .env

### Минимальная конфигурация (для тестирования в Stub режиме):

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
GPT_MODEL=gpt-4o
TTS_VOICE=alloy

# Google Sheets Configuration
GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id
USE_MOCK_SHEETS=true  # Использовать mock вместо реального Sheets

# API Security
API_AUTH_KEY=your-secret-api-key-here

# Voximplant (отключено для первого теста)
USE_VOXIMPLANT=false

# Application Configuration
MAX_CALL_DURATION_SEC=120
MAX_DIALOG_TURNS=12
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

### Полная конфигурация (с Voximplant для реальных звонков):

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
GPT_MODEL=gpt-4o
TTS_VOICE=alloy

# Google Sheets Configuration
GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id
USE_MOCK_SHEETS=true

# API Security
API_AUTH_KEY=your-secret-api-key-here

# Voximplant Configuration
USE_VOXIMPLANT=true
VOXIMPLANT_ACCOUNT_ID=1234567
VOXIMPLANT_API_KEY=your-voximplant-api-key
VOXIMPLANT_APPLICATION_ID=987654
VOXIMPLANT_RULE_ID=123
VOXIMPLANT_CALLER_ID=+74951234567
BACKEND_URL=https://your-public-domain.com  # Для webhooks от Voximplant

# Application Configuration
MAX_CALL_DURATION_SEC=120
MAX_DIALOG_TURNS=12
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

---

## 🚀 Запуск

### 1. Билд и запуск контейнеров

```bash
# Перейдите в корень проекта
cd C:\Users\user\Desktop\callerapi

# Запустите docker-compose
docker-compose up --build
```

### 2. Проверка статуса

Дождитесь сообщений:
```
halo-backend    | INFO:     Application startup complete.
halo-frontend   | ... listening on 80
```

### 3. Откройте в браузере

```
http://localhost:3000
```

---

## 🧪 Тестирование

### Тест 1: Frontend доступен
- Откройте `http://localhost:3000`
- Должна отобразиться форма "Запустить демо HALO"

### Тест 2: Backend API работает
```bash
curl http://localhost:8000/health
```

Ответ:
```json
{
  "status": "ok",
  "timestamp": "2024-12-11T...",
  "active_calls": 0,
  "version": "1.0.0"
}
```

### Тест 3: Demo endpoints работают
```bash
curl http://localhost:8000/demo/analytics
```

Должен вернуть аналитику с demo-данными.

### Тест 4: Запуск демо-звонка (Stub режим)

1. В браузере: `http://localhost:3000`
2. Заполните форму:
   - Телефон: `+79991234567`
   - Язык: `Auto`
   - Голос: `Female`
   - Промпт: оставьте дефолтный
3. Нажмите "Запустить демо"
4. Наблюдайте прогресс статусов
5. После завершения - откроется аналитика

**В Stub режиме**: звонок симулируется, реального звонка не будет.

### Тест 5: Реальный звонок (Voximplant)

**Предварительно**:
1. Настройте Voximplant (см. `VOXIMPLANT_SETUP.md`)
2. Обновите `.env` с настройками Voximplant
3. Убедитесь, что `BACKEND_URL` публично доступен (используйте ngrok для локального тестирования)

**Для webhooks с локального Docker**:

```bash
# В отдельном терминале
ngrok http 8000

# Скопируйте URL (например: https://abc123.ngrok.io)
# Добавьте в .env:
BACKEND_URL=https://abc123.ngrok.io
```

**Перезапуск**:
```bash
docker-compose down
docker-compose up --build
```

**Проверка логов**:
```bash
docker-compose logs -f backend
```

Должно быть:
```
INFO: Voximplant adapter initialized | account_id=... | webhook_url=https://abc123.ngrok.io/voximplant/events
```

**Запустите демо** - должен пойти реальный звонок!

---

## 📊 Мониторинг

### Просмотр логов

**Все сервисы**:
```bash
docker-compose logs -f
```

**Только backend**:
```bash
docker-compose logs -f backend
```

**Только frontend**:
```bash
docker-compose logs -f frontend
```

### Проверка статуса контейнеров

```bash
docker-compose ps
```

Все должны быть в статусе `Up`:
```
NAME                IMAGE               STATUS
halo-backend        callerapi-backend   Up
halo-frontend       callerapi-frontend  Up
```

### Healthcheck

Backend имеет встроенный healthcheck:
```bash
docker inspect halo-backend | grep -A 5 Health
```

---

## 🛠️ Управление

### Остановка

```bash
docker-compose down
```

### Перезапуск

```bash
docker-compose restart
```

### Пересборка после изменений кода

```bash
docker-compose up --build
```

### Очистка volumes и пересборка

```bash
docker-compose down -v
docker-compose up --build
```

---

## 🐛 Troubleshooting

### Проблема: Backend не стартует

**Проверьте логи**:
```bash
docker-compose logs backend
```

**Частые причины**:
- Неверный OPENAI_API_KEY
- Ошибка в .env файле
- Порт 8000 уже занят

**Решение**:
```bash
# Остановите все
docker-compose down

# Проверьте .env
cat .env

# Запустите заново
docker-compose up --build
```

### Проблема: Frontend показывает ошибку при запросе к API

**Проверьте**:
1. Backend запущен и healthy:
   ```bash
   curl http://localhost:8000/health
   ```

2. Nginx proxy настроен корректно:
   ```bash
   docker-compose exec frontend cat /etc/nginx/conf.d/default.conf
   ```

3. Сеть работает:
   ```bash
   docker-compose exec frontend ping backend
   ```

### Проблема: Voximplant webhooks не приходят

**Проверьте**:
1. BACKEND_URL в .env корректный
2. URL публично доступен (для ngrok - проверьте статус)
3. Webhook endpoint доступен:
   ```bash
   curl https://your-domain.com/voximplant/health
   ```

4. В логах VoxEngine (Voximplant Control Panel) нет ошибок

### Проблема: "Permission denied" при билде

**Windows**:
```bash
# Убедитесь, что Docker Desktop запущен с правами администратора
```

**Linux**:
```bash
sudo docker-compose up --build
```

---

## 📁 Структура Docker

```
callerapi/
├── docker-compose.yml          # Оркестрация сервисов
├── Dockerfile                  # Backend image
├── .env                        # Конфигурация (НЕ коммитить!)
├── app/                        # Backend код
└── frontend/
    ├── Dockerfile              # Frontend image (multi-stage build)
    ├── nginx.conf              # Nginx конфигурация для production
    └── src/                    # Frontend код
```

### docker-compose.yml

- **backend**: FastAPI приложение (порт 8000)
- **frontend**: React + Nginx (порт 3000 → 80)
- **halo-network**: Bridge network для связи между сервисами

### Volumes

- `./app:/app/app` - hot reload для backend в dev режиме
- `./logs:/var/log/callerapi` - логи backend
- `./mock_sheets_data:/app/mock_sheets_data` - mock данные Google Sheets

---

## 🎯 Production Deployment

Для production рекомендуется:

1. **Убрать volume mapping** для кода (используйте COPY в Dockerfile)
2. **Настроить reverse proxy** (nginx/traefik) перед docker-compose
3. **Использовать docker secrets** вместо .env
4. **Настроить HTTPS** (Let's Encrypt)
5. **Добавить мониторинг** (Prometheus/Grafana)
6. **Настроить логирование** (ELK stack)

---

## 📚 Полезные команды

```bash
# Посмотреть используемые ресурсы
docker stats

# Посмотреть образы
docker images

# Очистить неиспользуемые образы
docker image prune -a

# Зайти в контейнер backend
docker-compose exec backend bash

# Зайти в контейнер frontend
docker-compose exec frontend sh

# Посмотреть network
docker network ls
docker network inspect callerapi_halo-network
```

---

## ✅ Checklist запуска

- [ ] Docker и Docker Compose установлены
- [ ] `.env` файл создан и заполнен
- [ ] `docker-compose up --build` выполнен успешно
- [ ] `http://localhost:3000` открывается
- [ ] `http://localhost:8000/health` возвращает OK
- [ ] Демо-звонок в Stub режиме работает
- [ ] (Опционально) Voximplant настроен
- [ ] (Опционально) Реальный звонок работает

---

**Готово!** 🚀 Теперь весь проект запускается одной командой: `docker-compose up --build`
