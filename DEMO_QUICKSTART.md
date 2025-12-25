# HALO Demo Cabinet - Быстрый старт

## Что реализовано

### Backend (FastAPI)
- ✅ **Новые модели данных**: DemoSession, DemoCall, DemoChat, Analytics
- ✅ **Генератор демо-данных**: 50 звонков + 50 чатов с реалистичными транскриптами
- ✅ **API эндпоинты**:
  - `POST /demo/session` - создать демо-сессию
  - `GET /demo/session/{id}` - статус демо-сессии
  - `GET /demo/analytics` - аналитика (звонки, чаты, воронка)
  - `GET /demo/interactions` - список всех обращений (демо + реальные)
  - `GET /demo/interaction/{id}` - детали звонка или чата
- ✅ **Multi-language support**: 10 языков (RU, UZ, TJ, KK, KY, TM, AZ, FA-AF, EN, TR)
- ✅ **Voice selection**: male / female / neutral
- ✅ **Custom prompts**: настраиваемые промпты для ассистента

### Frontend (React + Vite)
- ✅ **LaunchDemo**: форма запуска демо (телефон, язык, голос, промпт)
- ✅ **StatusDemo**: экран статуса с индикаторами прогресса
- ✅ **Analytics**: аналитика, метрики, воронка, таблица обращений
- ✅ **CallDetailModal**: детальная информация о звонке с транскриптом
- ✅ **ChatDetailModal**: детальная информация о чате (follow-up)
- ✅ **Красивый UI**: градиенты, анимации, адаптивный дизайн

## Запуск с Docker

### Шаг 1: Убедитесь что .env настроен

```bash
# .env файл должен содержать:
OPENAI_API_KEY=sk-your-key
USE_MOCK_SHEETS=true  # Пока без реальных звонков используем mock
```

### Шаг 2: Запуск

```bash
# Собрать и запустить оба контейнера
docker-compose up --build

# Или в фоновом режиме
docker-compose up -d --build
```

### Шаг 3: Открыть в браузере

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Шаг 4: Проверить логи

```bash
# Логи backend
docker logs halo-backend -f

# Логи frontend
docker logs halo-frontend -f
```

### Шаг 5: Остановить

```bash
docker-compose down
```

## Локальная разработка (без Docker)

### Backend

```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Установить зависимости
npm install

# Запустить dev-сервер
npm run dev

# Фронтенд будет доступен на http://localhost:3000
```

## Структура проекта

```
callerapi/
├── app/
│   ├── core/
│   │   ├── models.py                  # ✅ Новые модели (DemoSession, etc.)
│   │   └── demo_data_generator.py     # ✅ Генератор демо-данных
│   ├── api/
│   │   └── routes_demo.py             # ✅ Новые endpoints
│   └── ...
├── frontend/                           # ✅ Новый фронтенд
│   ├── src/
│   │   ├── components/
│   │   │   ├── LaunchDemo.jsx
│   │   │   ├── StatusDemo.jsx
│   │   │   ├── Analytics.jsx
│   │   │   ├── CallDetailModal.jsx
│   │   │   └── ChatDetailModal.jsx
│   │   ├── api/
│   │   │   └── client.js              # API клиент
│   │   └── styles/
│   │       └── App.css
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
└── docker-compose.yml                  # ✅ Обновлен для фронтенда

```

## Что можно делать сейчас

1. **Запустить демо** - открыть http://localhost:3000 и заполнить форму
2. **Посмотреть статус** - увидеть индикаторы прогресса (имитация)
3. **Посмотреть аналитику**:
   - 50 демо-звонков с реалистичными транскриптами
   - 50 демо-чатов с follow-up сообщениями
   - Воронка: позвонили → разговаривали → заинтересованы → лиды
   - Метрики: общее кол-во звонков, чатов, конверсия, средняя длительность
4. **Просмотреть детали** - кликнуть на любой звонок/чат в таблице:
   - Для звонков: транскрипт диалога, CRM-данные, summary
   - Для чатов: follow-up сообщения

## Что НЕ реализовано (пока)

- ❌ Реальные звонки через Voximplant (интеграция позже)
- ❌ Потоковая обработка (streaming STT/TTS)
- ❌ SMS интеграция
- ❌ Telegram bot и deep-link
- ❌ Реальная отправка follow-up сообщений
- ❌ Реальный статус звонка (сейчас имитация)

## Следующие шаги

1. **Интеграция Voximplant** - для реальных звонков
2. **Streaming обработка** - Deepgram STT + ElevenLabs TTS
3. **SMS провайдер** - SMS.ru или SMSC
4. **Telegram bot** - для deep-link и follow-up
5. **Real-time статус** - WebSocket для обновления статуса

## Тестирование API

### Создать демо-сессию

```bash
curl -X POST http://localhost:8000/demo/session \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+79991234567",
    "language": "auto",
    "voice": "female",
    "prompt": "Вы - вежливый оператор call-центра"
  }'
```

### Получить статус

```bash
curl http://localhost:8000/demo/session/{session_id}
```

### Получить аналитику

```bash
curl http://localhost:8000/demo/analytics
```

### Получить все обращения

```bash
curl http://localhost:8000/demo/interactions
```

### Получить детали обращения

```bash
curl http://localhost:8000/demo/interaction/{interaction_id}
```

## Troubleshooting

### Frontend не может подключиться к backend

Проверьте:
1. Backend запущен и доступен на порту 8000
2. В docker-compose оба сервиса в одной сети `halo-network`
3. В nginx.conf прокси настроен на `http://backend:8000`

### Не устанавливаются npm зависимости

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Ошибки при сборке Docker

```bash
# Очистить все контейнеры и образы
docker-compose down -v
docker system prune -a

# Пересобрать
docker-compose up --build
```

## Контакты

По вопросам разработки обращайтесь к команде разработки.
