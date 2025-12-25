# План выполнения MVP сервиса голосового обзвона

## Общая информация
- **Срок выполнения**: до 15 октября 2025 г.
- **Стоимость**: 20 000 руб.
- **Технологии**: Python 3.11+, FastAPI, OpenAI API, Google Sheets
- **Деплой**: VPS (Ubuntu/Debian)

---

## ЭТАП 1: Подготовка инфраструктуры и базовой структуры проекта
**Цель**: Создать основу проекта, настроить окружение

### Checkpoint 1.1: Инициализация проекта
- [ ] Создать структуру папок согласно ТЗ:
  ```
  app/
    main.py
    config.py
    api/
      __init__.py
      routes_call.py
      routes_telephony.py
    core/
      models.py
      orchestrator.py
      dialog_manager.py
    integrations/
      openai_client.py
      telephony_base.py
      telephony_stub.py
      google_sheets.py
    utils/
      logging.py
      time.py
  ```
- [ ] Создать `requirements.txt` с зависимостями:
  - fastapi
  - uvicorn[standard]
  - pydantic
  - pydantic-settings
  - openai
  - gspread / google-auth
  - httpx
  - python-multipart
  - python-dotenv
- [ ] Создать `.env.example` с шаблоном переменных окружения
- [ ] Создать `.gitignore` (исключить .env, credentials, __pycache__)
- [ ] Создать `Dockerfile` для контейнеризации
- [ ] Создать `docker-compose.yml` для удобного деплоя
- [ ] Инициализировать git-репозиторий

**Критерий завершения**: Структура проекта создана, зависимости перечислены

---

## ЭТАП 2: Разработка моделей данных и конфигурации
**Цель**: Определить базовые структуры данных и настройки

### Checkpoint 2.1: Модели данных (core/models.py)
- [ ] Создать enum `CallStatus`:
  - created, dialing, no_answer, in_progress, completed, failed
- [ ] Создать enum `FinalDisposition`:
  - interested, not_interested, call_later, neutral, unknown
- [ ] Создать enum `Speaker`:
  - user, assistant
- [ ] Создать Pydantic-модель `DialogTurn`:
  - speaker: Speaker
  - text: str
  - timestamp: datetime
- [ ] Создать Pydantic-модель `CallSession`:
  - id: UUID
  - phone: str
  - status: CallStatus
  - final_disposition: FinalDisposition | None
  - started_at: datetime | None
  - ended_at: datetime | None
  - duration_sec: int | None
  - transcript: list[DialogTurn]
  - short_summary: str | None

### Checkpoint 2.2: Конфигурация (config.py)
- [ ] Создать класс `Settings(BaseSettings)` с переменными:
  - OPENAI_API_KEY: str
  - GOOGLE_SHEETS_SPREADSHEET_ID: str
  - GOOGLE_CREDENTIALS_JSON: str | None
  - GOOGLE_CREDENTIALS_FILE: str | None
  - TELEPHONY_API_KEY: str | None
  - API_AUTH_KEY: str
  - MAX_CALL_DURATION_SEC: int = 120
  - MAX_DIALOG_TURNS: int = 12
  - GPT_MODEL: str = "gpt-4o"
  - TTS_VOICE: str = "alloy"
  - HOST: str = "0.0.0.0"
  - PORT: int = 8000
- [ ] Настроить загрузку из `.env` файла
- [ ] Создать singleton-инстанс settings

**Критерий завершения**: Модели данных определены, конфигурация готова

---

## ЭТАП 3: Логирование и утилиты
**Цель**: Настроить систему логирования

### Checkpoint 3.1: Настройка логирования (utils/logging.py)
- [ ] Настроить логгер с форматом: timestamp, level, module, message
- [ ] Уровень логирования: INFO для продакшена, DEBUG для разработки
- [ ] Логирование в stdout + файл (для VPS: /var/log/callerapi/)
- [ ] Ротация логов (по размеру или по дате)
- [ ] Создать вспомогательные функции для структурированного логирования событий звонков

### Checkpoint 3.2: Утилиты времени (utils/time.py)
- [ ] Функция для получения текущего времени в UTC
- [ ] Функция для форматирования времени в ISO 8601
- [ ] Функция для расчета длительности между двумя timestamp

**Критерий завершения**: Логирование работает, утилиты созданы

---

## ЭТАП 4: Интеграция с OpenAI
**Цель**: Реализовать клиент для работы с Whisper, GPT, TTS

### Checkpoint 4.1: OpenAI клиент (integrations/openai_client.py)
- [ ] Создать класс `OpenAIClient`:
  - Инициализация с API ключом из конфига
  - Настройка timeout, retry логики
- [ ] Реализовать метод `transcribe_audio(audio_bytes: bytes) -> str`:
  - Вызов Whisper API (/v1/audio/transcriptions)
  - model = "whisper-1"
  - language = "ru"
  - Обработка ошибок, логирование
  - Измерение времени выполнения
- [ ] Реализовать метод `generate_response(messages: list[dict]) -> str`:
  - Вызов Chat Completions API
  - model из конфига (gpt-4o)
  - temperature = 0.7
  - max_tokens = 200
  - Обработка ошибок, логирование
  - Измерение времени выполнения
- [ ] Реализовать метод `classify_call(transcript_text: str) -> tuple[FinalDisposition, str]`:
  - Специальный промпт для классификации интереса
  - Возвращает (final_disposition, short_summary)
- [ ] Реализовать метод `text_to_speech(text: str) -> bytes`:
  - Вызов TTS API (/v1/audio/speech)
  - model = "tts-1" или из конфига
  - voice из конфига
  - Возвращает аудио в формате mp3/ogg
  - Обработка ошибок, логирование
  - Измерение времени выполнения

### Checkpoint 4.2: Системный промпт для диалога
- [ ] Создать константу SYSTEM_PROMPT в openai_client.py:
  - Роль: вежливый оператор call-центра
  - Цель: представить продукт, узнать интерес
  - Требования: короткие фразы (1-2 предложения), не спорить, не упоминать что это ИИ
  - Поведение: естественное, дружелюбное
- [ ] Создать промпт для классификации CLASSIFICATION_PROMPT:
  - Анализ всего диалога
  - Определение interested/not_interested/call_later/neutral
  - Генерация короткого саммари

### Checkpoint 4.3: Тестирование OpenAI интеграции
- [ ] Создать простой тест-скрипт для проверки:
  - STT: загрузить тестовый аудиофайл → получить текст
  - GPT: отправить тестовое сообщение → получить ответ
  - TTS: отправить текст → получить аудио
- [ ] Проверить задержки (засечь время каждого вызова)
- [ ] Цель: STT + GPT + TTS < 2 сек суммарно

**Критерий завершения**: OpenAI клиент работает, все методы протестированы

---

## ЭТАП 5: Интеграция с Google Sheets
**Цель**: Реализовать запись результатов звонков

### Checkpoint 5.1: Google Sheets клиент (integrations/google_sheets.py)
- [ ] Создать класс `GoogleSheetsClient`:
  - Инициализация с credentials из конфига
  - Авторизация через service account
  - Подключение к spreadsheet по ID
  - Обработка ошибок соединения
- [ ] Реализовать метод `write_call_result(call_session: CallSession)`:
  - Формат строки: [timestamp, call_id, phone, status, final_disposition, duration_sec, short_summary, transcript]
  - timestamp: форматировать в читаемом виде (МСК или UTC)
  - transcript: склеить все DialogTurn через "\n" с префиксами "Клиент: " / "Ассистент: "
  - Добавление строки в конец листа
  - Обработка ошибок API, логирование
  - Retry логика (до 3 попыток)
- [ ] Создать метод для инициализации заголовков листа (если лист пустой):
  - timestamp | call_id | phone | status | final_disposition | duration_sec | short_summary | transcript
  - Проверка: если первая строка пустая → записать заголовки

### Checkpoint 5.2: Тестирование Google Sheets
- [ ] Создать тестовый Google Spreadsheet
- [ ] Создать service account в Google Cloud Console
- [ ] Получить JSON-ключ credentials
- [ ] Дать доступ service account к spreadsheet (по email)
- [ ] Протестировать запись тестовой строки
- [ ] Проверить корректность форматирования данных
- [ ] Проверить работу с кириллицей

**Критерий завершения**: Google Sheets клиент работает, данные корректно записываются

---

## ЭТАП 6: Абстракция телефонии (заглушка)
**Цель**: Создать интерфейс для работы с провайдером телефонии и заглушку для тестирования

### Checkpoint 6.1: Интерфейс телефонии (integrations/telephony_base.py)
- [ ] Создать Protocol `TelephonyAdapter`:
  ```python
  class TelephonyAdapter(Protocol):
      async def initiate_call(self, call_id: str, phone: str) -> None: ...
      async def send_audio(self, call_id: str, audio_bytes: bytes) -> None: ...
      async def receive_audio(self, call_id: str) -> bytes | None: ...
      async def hangup(self, call_id: str) -> None: ...
  ```
- [ ] Определить enum `TelephonyEvent`:
  - ringing, answered, hangup, busy, no_answer, error
- [ ] Создать callback-интерфейс для событий телефонии

### Checkpoint 6.2: Заглушка телефонии (integrations/telephony_stub.py)
- [ ] Создать класс `StubTelephonyAdapter(TelephonyAdapter)`:
  - `initiate_call`: логирует вызов, через 2 сек эмулирует событие "ringing", затем "answered"
  - `send_audio`: логирует получение аудио, сохраняет в память
  - `receive_audio`: возвращает заранее подготовленные аудиофрагменты (имитация речи абонента)
  - `hangup`: логирует завершение
- [ ] Создать набор тестовых аудиофайлов с русской речью:
  - "Да, интересно, расскажите подробнее"
  - "Нет, спасибо, не интересует"
  - "Перезвоните мне завтра"
  - Или генерировать через OpenAI TTS заранее
- [ ] Реализовать callback-механизм для отправки событий в CallOrchestrator

**Критерий завершения**: Заглушка телефонии работает, можно тестировать диалоги без реального провайдера

---

## ЭТАП 7: Dialog Manager
**Цель**: Реализовать управление диалогом (цикл STT → GPT → TTS)

### Checkpoint 7.1: Менеджер диалога (core/dialog_manager.py)
- [ ] Создать класс `DialogManager`:
  - Зависимости: OpenAIClient, TelephonyAdapter
  - Параметры: max_duration_sec, max_turns
- [ ] Реализовать метод `run_dialog(call_id: str, call_session: CallSession)`:
  - Инициализация контекста диалога:
    - Системный промпт (роль оператора)
    - История сообщений (для GPT)
  - Основной цикл:
    1. Получить аудио от абонента через telephony.receive_audio()
    2. Если аудио None или тишина → продолжить/пропустить
    3. STT → user_text
    4. Добавить DialogTurn(speaker="user", text=user_text, timestamp=now)
    5. Обновить историю сообщений для GPT
    6. GPT → assistant_text
    7. Добавить DialogTurn(speaker="assistant", text=assistant_text, timestamp=now)
    8. TTS → audio_bytes
    9. Отправить telephony.send_audio(call_id, audio_bytes)
    10. Проверить условия выхода:
        - Превышен лимит времени (duration > MAX_CALL_DURATION_SEC)
        - Превышен лимит ходов (turns > MAX_DIALOG_TURNS)
        - Событие hangup получено
        - Ассистент явно попрощался (детектировать по ключевым словам)
  - Логирование каждого хода с метриками времени
  - Обработка ошибок на каждом этапе (try-except, продолжение или graceful exit)
- [ ] Реализовать детектирование тишины (VAD - Voice Activity Detection):
  - Простой вариант: если аудио слишком короткое или низкая амплитуда
  - Или использовать библиотеку (webrtcvad, silero-vad)

### Checkpoint 7.2: Логика завершения диалога
- [ ] При достижении лимитов:
  - Сформировать финальную фразу: "Спасибо за уделенное время, до свидания"
  - TTS → аудио прощания
  - Отправить абоненту
  - Вызвать telephony.hangup(call_id)
- [ ] Детектирование намерения завершить разговор:
  - В ответе ассистента искать: "до свидания", "всего доброго", "прощайте"
  - Можно попросить GPT добавлять JSON-маркер: `{"should_end": true}`
  - При обнаружении → завершить после отправки

### Checkpoint 7.3: Обработка ошибок OpenAI
- [ ] Retry логика для транзиентных ошибок (rate limit, timeout)
- [ ] При критической ошибке (invalid API key, превышена квота):
  - Логировать ERROR
  - Отправить абоненту заготовленное сообщение: "Извините, произошла техническая ошибка"
  - Завершить звонок
  - Пометить call_session.status = "failed"

**Критерий завершения**: DialogManager работает, цикл диалога выполняется корректно

---

## ЭТАП 8: Call Orchestrator
**Цель**: Управление жизненным циклом звонка

### Checkpoint 8.1: Оркестратор звонков (core/orchestrator.py)
- [ ] Создать класс `CallOrchestrator`:
  - Зависимости: TelephonyAdapter, DialogManager, GoogleSheetsClient, OpenAIClient
  - In-memory хранилище: dict[str, CallSession] для активных звонков
  - Lock для thread-safety (asyncio.Lock или threading.Lock)
- [ ] Реализовать метод `create_call(phone: str) -> CallSession`:
  - Валидация номера телефона: regex `^(\+7|8)\d{10}$`
  - Генерация UUID для call_id
  - Создать CallSession:
    - id = UUID
    - phone = normalized_phone (+7...)
    - status = "created"
    - started_at = None
    - все остальное = None/[]
  - Сохранить в хранилище
  - Логировать: "Call created: call_id={}, phone={}"
  - Вернуть CallSession
- [ ] Реализовать метод `start_call(call_id: str)`:
  - Найти CallSession в хранилище
  - Обновить статус на "created" (уже так)
  - Вызвать telephony.initiate_call(call_id, phone)
  - Логировать: "Initiating call: call_id={}, phone={}"
  - Обработка ошибок телефонии
- [ ] Реализовать метод `handle_telephony_event(call_id: str, event: TelephonyEvent, reason: str | None)`:
  - Найти CallSession
  - По типу события:
    - **ringing**:
      - Обновить status = "dialing"
      - Логировать
    - **answered**:
      - Обновить status = "in_progress"
      - Установить started_at = now()
      - Запустить DialogManager.run_dialog(call_id, call_session) асинхронно
      - Логировать: "Call answered, starting dialog"
    - **busy / no_answer / error**:
      - Обновить status соответствующий ("no_answer" / "failed")
      - Установить ended_at = now()
      - Вызвать finalize_call(call_id)
      - Логировать с reason
    - **hangup**:
      - Если диалог идет → прервать
      - Обновить status = "completed"
      - Вызвать finalize_call(call_id)
      - Логировать
  - Обработка ошибок, логирование
- [ ] Реализовать метод `finalize_call(call_id: str)`:
  - Найти CallSession
  - Если не установлен ended_at → установить now()
  - Рассчитать duration_sec = (ended_at - started_at).total_seconds() если started_at существует
  - Если transcript не пустой (диалог был):
    - Склеить весь transcript в текст
    - Вызвать openai_client.classify_call(transcript_text)
    - Получить (final_disposition, short_summary)
    - Обновить call_session
  - Если transcript пустой (не дозвонились):
    - final_disposition = "unknown"
    - short_summary = f"Не дозвонились: статус {status}"
    - duration_sec = 0
  - Записать в Google Sheets через sheets_client.write_call_result(call_session)
  - Логировать итоговую строку: "Call finalized: call_id={}, status={}, disposition={}, duration={}"
  - Удалить из активного хранилища (освободить память)
  - Обработка ошибок (если Sheets не доступен → логировать ERROR, но не падать)

### Checkpoint 8.2: Обработка ошибок
- [ ] Обернуть критичные участки в try-except
- [ ] При ошибках в диалоге:
  - Логировать ERROR с трейсом
  - Обновить status = "failed"
  - Вызвать finalize_call() для сохранения результата
- [ ] При ошибках Google Sheets:
  - Логировать ERROR
  - Опционально: сохранить в локальный файл как fallback
  - Не блокировать завершение звонка

### Checkpoint 8.3: Thread-safety и конкурентность
- [ ] Использовать asyncio.Lock при доступе к хранилищу звонков
- [ ] Убедиться что параллельные звонки не конфликтуют
- [ ] Тестирование: запустить 2-3 звонка одновременно

**Критерий завершения**: CallOrchestrator управляет полным циклом звонка

---

## ЭТАП 9: FastAPI эндпоинты
**Цель**: Реализовать HTTP API

### Checkpoint 9.1: Эндпоинт POST /call (api/routes_call.py)
- [ ] Создать Pydantic модель запроса:
  ```python
  class CallRequest(BaseModel):
      phone: str

      @field_validator('phone')
      def validate_phone(cls, v):
          if not re.match(r'^(\+7|8)\d{10}$', v):
              raise ValueError('Invalid phone format')
          return v
  ```
- [ ] Создать Pydantic модель ответа:
  ```python
  class CallResponse(BaseModel):
      call_id: str
      status: str
  ```
- [ ] Реализовать эндпоинт `POST /call`:
  - Dependency для проверки X-API-Key header:
    ```python
    async def verify_api_key(x_api_key: str = Header(...)):
        if x_api_key != settings.API_AUTH_KEY:
            raise HTTPException(401, "Invalid API key")
    ```
  - Парсинг CallRequest
  - Вызов orchestrator.create_call(phone)
  - Запуск orchestrator.start_call(call_id) в background task (через BackgroundTasks)
  - Возврат CallResponse(call_id=str(call.id), status=call.status)
- [ ] Обработка ошибок:
  - ValidationError → 400 с деталями
  - Exception → 500 Internal Server Error
  - Логирование всех запросов

### Checkpoint 9.2: Эндпоинт POST /telephony/events (api/routes_telephony.py)
- [ ] Создать Pydantic модель события:
  ```python
  class TelephonyEventRequest(BaseModel):
      call_id: str
      event: str  # "ringing", "answered", "hangup", etc.
      timestamp: str
      reason: str | None = None
  ```
- [ ] Реализовать эндпоинт `POST /telephony/events`:
  - Парсинг TelephonyEventRequest
  - Маппинг event string → TelephonyEvent enum
  - Вызов orchestrator.handle_telephony_event(call_id, event, reason)
  - Возврат 200 OK с {"status": "ok"}
  - Логирование входящих событий
- [ ] Обработка неизвестных событий:
  - Логировать WARNING
  - Не падать, вернуть 200

### Checkpoint 9.3: Эндпоинт для аудио (если требуется провайдером)
- [ ] Определить формат взаимодействия с провайдером:
  - WebSocket: `/telephony/audio/{call_id}`
  - HTTP POST: `/telephony/audio`
- [ ] Если WebSocket:
  - Установить соединение
  - Читать бинарные сообщения (аудио от абонента)
  - Передавать в DialogManager через очередь
  - Отправлять аудио ассистента обратно
- [ ] Если HTTP POST:
  - Получать чанки аудио в теле запроса
  - Передавать в DialogManager
  - Возвращать URL на аудио-ответ или байты
- [ ] Логирование потока аудио (размер, формат)

### Checkpoint 9.4: Главный файл приложения (main.py)
- [ ] Инициализация FastAPI app:
  ```python
  app = FastAPI(title="Voice Caller API", version="1.0.0")
  ```
- [ ] Подключение роутеров:
  - app.include_router(routes_call.router, tags=["calls"])
  - app.include_router(routes_telephony.router, tags=["telephony"])
- [ ] Middleware для логирования запросов:
  - Логировать: method, path, status_code, duration
- [ ] CORS middleware (если нужен фронтенд):
  - Настроить разрешенные origins
- [ ] Инициализация всех клиентов при startup:
  - OpenAIClient
  - GoogleSheetsClient
  - TelephonyAdapter (Stub или реальный)
  - CallOrchestrator
  - Сохранить в app.state
- [ ] Health check endpoint `GET /health`:
  ```python
  @app.get("/health")
  async def health():
      return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
  ```
- [ ] Обработка shutdown:
  - Завершить активные звонки gracefully
  - Сохранить незаписанные результаты
- [ ] Обработка необработанных исключений:
  ```python
  @app.exception_handler(Exception)
  async def global_exception_handler(request, exc):
      logger.error(f"Unhandled exception: {exc}", exc_info=True)
      return JSONResponse(status_code=500, content={"detail": "Internal server error"})
  ```

**Критерий завершения**: API эндпоинты работают, можно делать запросы

---

## ЭТАП 10: Интеграция и локальное тестирование
**Цель**: Проверить работу всей системы локально

### Checkpoint 10.1: Локальный запуск
- [ ] Создать `.env` файл с тестовыми ключами:
  - OPENAI_API_KEY=sk-...
  - GOOGLE_SHEETS_SPREADSHEET_ID=...
  - GOOGLE_CREDENTIALS_JSON=...
  - API_AUTH_KEY=test-secret-key
  - GPT_MODEL=gpt-4o
  - TTS_VOICE=alloy
- [ ] Установить зависимости:
  ```bash
  python -m venv venv
  source venv/bin/activate  # или venv\Scripts\activate на Windows
  pip install -r requirements.txt
  ```
- [ ] Запустить сервер:
  ```bash
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```
- [ ] Проверить /health endpoint:
  ```bash
  curl http://localhost:8000/health
  ```

### Checkpoint 10.2: Тестирование флоу через заглушку
- [ ] Сделать POST /call запрос:
  ```bash
  curl -X POST http://localhost:8000/call \
    -H "Content-Type: application/json" \
    -H "X-API-Key: test-secret-key" \
    -d '{"phone": "+79991234567"}'
  ```
- [ ] Проверить в логах последовательность событий:
  - ✓ Call created: call_id=..., phone=+79991234567
  - ✓ Initiating call: call_id=...
  - ✓ Event received: ringing
  - ✓ Status updated: dialing
  - ✓ Event received: answered
  - ✓ Status updated: in_progress
  - ✓ Starting dialog
  - ✓ Dialog turn 1: user said "..."
  - ✓ Dialog turn 1: assistant said "..."
  - ✓ TTS completed in X ms
  - ✓ Audio sent to caller
  - ✓ Dialog turn 2: ...
  - ✓ Dialog completed after N turns
  - ✓ Classifying call result...
  - ✓ Final disposition: interested/not_interested/...
  - ✓ Writing to Google Sheets...
  - ✓ Call finalized: call_id=..., status=completed
- [ ] Проверить запись в Google Sheets:
  - Открыть таблицу
  - Проверить последнюю строку:
    - timestamp корректный
    - call_id совпадает
    - phone = +79991234567
    - status = completed
    - final_disposition определен
    - duration_sec > 0
    - short_summary содержательный
    - transcript читаемый, с репликами обеих сторон
- [ ] Замерить задержки:
  - Время между user_text и assistant_text < 2 сек?
  - Общее время диалога разумное?

### Checkpoint 10.3: Тестирование граничных случаев
- [ ] **Невалидный номер телефона**:
  ```bash
  curl -X POST http://localhost:8000/call \
    -H "Content-Type: application/json" \
    -H "X-API-Key: test-secret-key" \
    -d '{"phone": "123"}'
  ```
  - Ожидаем: 400 Bad Request, ошибка валидации
- [ ] **Неверный API ключ**:
  ```bash
  curl -X POST http://localhost:8000/call \
    -H "Content-Type: application/json" \
    -H "X-API-Key: wrong-key" \
    -d '{"phone": "+79991234567"}'
  ```
  - Ожидаем: 401 Unauthorized
- [ ] **Звонок no_answer**:
  - Настроить заглушку на возврат события "no_answer"
  - Проверить:
    - status = "no_answer"
    - final_disposition = "unknown"
    - duration_sec = 0
    - short_summary = "Не дозвонились: статус no_answer"
    - Запись в Sheets корректная
- [ ] **Звонок с превышением лимита времени**:
  - Уменьшить MAX_CALL_DURATION_SEC до 10 сек
  - Запустить звонок
  - Проверить что диалог завершился автоматически с прощанием
- [ ] **Звонок с превышением лимита ходов**:
  - Уменьшить MAX_DIALOG_TURNS до 3
  - Запустить звонок
  - Проверить автоматическое завершение
- [ ] **Ошибка OpenAI API**:
  - Использовать неверный OPENAI_API_KEY
  - Запустить звонок
  - Проверить:
    - Логирование ERROR
    - status = "failed"
    - Запись в Sheets с описанием ошибки
- [ ] **Ошибка Google Sheets API**:
  - Отключить интернет или использовать неверный SPREADSHEET_ID
  - Запустить звонок
  - Проверить:
    - Звонок завершается корректно
    - Ошибка логируется ERROR
    - Данные НЕ теряются (fallback в файл или повторная попытка)

### Checkpoint 10.4: Нагрузочное тестирование (локально)
- [ ] Запустить 3 параллельных звонка:
  ```bash
  curl -X POST ... &
  curl -X POST ... &
  curl -X POST ... &
  ```
- [ ] Проверить:
  - Все 3 звонка обрабатываются независимо
  - Нет перемешивания логов (call_id разные)
  - Записи в Google Sheets корректные для всех звонков
  - Нет race conditions или deadlocks
- [ ] Мониторинг ресурсов:
  - CPU usage
  - Memory usage
  - Проверить отсутствие утечек памяти

**Критерий завершения**: Система работает локально стабильно, все сценарии протестированы

---

## ЭТАП 11: Подготовка к деплою на VPS
**Цель**: Настроить окружение на VPS, задеплоить приложение

### Checkpoint 11.1: Подготовка VPS
- [ ] Арендовать VPS:
  - Рекомендуемые параметры: 2 CPU, 4 GB RAM, 20 GB SSD
  - OS: Ubuntu 22.04 или Debian 11
  - Провайдеры: Hetzner, DigitalOcean, Timeweb, Selectel
- [ ] Настроить SSH доступ:
  - Создать SSH ключ
  - Добавить в authorized_keys
  - Отключить password authentication
- [ ] Обновить систему:
  ```bash
  sudo apt update && sudo apt upgrade -y
  ```
- [ ] Установить необходимые пакеты:
  ```bash
  sudo apt install -y python3.11 python3.11-venv python3-pip git nginx supervisor
  ```
- [ ] Настроить firewall (UFW):
  ```bash
  sudo ufw allow ssh
  sudo ufw allow http
  sudo ufw allow https
  sudo ufw enable
  ```

### Checkpoint 11.2: Установка и настройка приложения
- [ ] Клонировать репозиторий на VPS:
  ```bash
  cd /opt
  sudo git clone <repo-url> callerapi
  sudo chown -R $USER:$USER /opt/callerapi
  cd /opt/callerapi
  ```
- [ ] Создать виртуальное окружение:
  ```bash
  python3.11 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  ```
- [ ] Создать `.env` файл с продакшен переменными:
  ```bash
  nano .env
  ```
  - Заполнить OPENAI_API_KEY, GOOGLE_SHEETS_SPREADSHEET_ID, и т.д.
  - API_AUTH_KEY: сгенерировать сильный ключ
- [ ] Создать папку для логов:
  ```bash
  sudo mkdir -p /var/log/callerapi
  sudo chown $USER:$USER /var/log/callerapi
  ```
- [ ] Проверить запуск вручную:
  ```bash
  source venv/bin/activate
  uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```
  - Проверить /health с другой машины
  - Остановить (Ctrl+C)

### Checkpoint 11.3: Настройка Supervisor для автозапуска
- [ ] Создать конфиг Supervisor:
  ```bash
  sudo nano /etc/supervisor/conf.d/callerapi.conf
  ```
  Содержимое:
  ```ini
  [program:callerapi]
  directory=/opt/callerapi
  command=/opt/callerapi/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
  user=<your-user>
  autostart=true
  autorestart=true
  redirect_stderr=true
  stdout_logfile=/var/log/callerapi/app.log
  environment=PATH="/opt/callerapi/venv/bin"
  ```
- [ ] Обновить Supervisor:
  ```bash
  sudo supervisorctl reread
  sudo supervisorctl update
  sudo supervisorctl start callerapi
  ```
- [ ] Проверить статус:
  ```bash
  sudo supervisorctl status callerapi
  ```
  - Должно быть: RUNNING
- [ ] Проверить логи:
  ```bash
  tail -f /var/log/callerapi/app.log
  ```

### Checkpoint 11.4: Настройка Nginx как reverse proxy
- [ ] Создать конфиг Nginx:
  ```bash
  sudo nano /etc/nginx/sites-available/callerapi
  ```
  Содержимое:
  ```nginx
  server {
      listen 80;
      server_name your-domain.com;  # или IP адрес

      location / {
          proxy_pass http://127.0.0.1:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }

      location /telephony/audio {
          proxy_pass http://127.0.0.1:8000;
          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection "upgrade";
          proxy_read_timeout 3600s;
          proxy_send_timeout 3600s;
      }
  }
  ```
- [ ] Активировать конфиг:
  ```bash
  sudo ln -s /etc/nginx/sites-available/callerapi /etc/nginx/sites-enabled/
  sudo nginx -t
  sudo systemctl restart nginx
  ```
- [ ] Проверить доступность:
  ```bash
  curl http://your-domain.com/health
  ```

### Checkpoint 11.5: Настройка SSL (HTTPS) с Let's Encrypt
- [ ] Установить Certbot:
  ```bash
  sudo apt install -y certbot python3-certbot-nginx
  ```
- [ ] Получить сертификат:
  ```bash
  sudo certbot --nginx -d your-domain.com
  ```
  - Следовать инструкциям
  - Выбрать редирект HTTP → HTTPS
- [ ] Проверить автообновление:
  ```bash
  sudo certbot renew --dry-run
  ```
- [ ] Проверить HTTPS:
  ```bash
  curl https://your-domain.com/health
  ```

### Checkpoint 11.6: Проверка деплоя
- [ ] Проверить /health endpoint через HTTPS
- [ ] Сделать тестовый POST /call запрос:
  ```bash
  curl -X POST https://your-domain.com/call \
    -H "Content-Type: application/json" \
    -H "X-API-Key: <your-prod-key>" \
    -d '{"phone": "+79991234567"}'
  ```
- [ ] Проверить логи на VPS:
  ```bash
  tail -f /var/log/callerapi/app.log
  ```
- [ ] Проверить запись в Google Sheets
- [ ] Замерить задержки (учитывая сеть РФ ↔ VPS ↔ OpenAI)

**Критерий завершения**: Приложение задеплоено на VPS, работает стабильно

---

## ЭТАП 12: Интеграция реального провайдера телефонии
**Цель**: Заменить заглушку на реальный провайдер (Voximplant / Zadarma / Mango)

### Checkpoint 12.1: Выбор и изучение провайдера
- [ ] Согласовать с заказчиком выбор провайдера:
  - **Voximplant**: хороший API, WebRTC, WebSocket
  - **Zadarma**: простой REST API, популярен в РФ
  - **Mango Office**: корпоративная телефония
- [ ] Изучить документацию API выбранного провайдера:
  - Как инициировать исходящий звонок (REST API)
  - Как получать события (webhook / callback URL)
  - Как передавать/получать аудио (WebSocket / HTTP streaming)
  - Формат аудио: codec (G.711, Opus), sample rate (8kHz, 16kHz)
  - Ограничения API (rate limits)
- [ ] Создать аккаунт у провайдера:
  - Регистрация
  - Верификация (если требуется)
  - Получение API ключей / credentials
  - Настройка SIP trunk / номера (если нужно)
- [ ] Пополнить баланс для тестов

### Checkpoint 12.2: Реализация адаптера провайдера
- [ ] Создать файл `integrations/telephony_[provider].py`:
  - Например: `telephony_voximplant.py`
- [ ] Реализовать класс `[Provider]TelephonyAdapter`:
  - Наследоваться от базового интерфейса
  - Инициализация: API credentials, base URL
- [ ] Метод `initiate_call(call_id: str, phone: str)`:
  - Вызов REST API провайдера для старта звонка
  - Параметры:
    - Номер получателя (phone)
    - Callback URL для событий (webhook)
    - Идентификатор звонка (call_id) для связывания
  - Обработка ответа API:
    - Успех → логировать
    - Ошибка → выбросить исключение, логировать
- [ ] Метод `send_audio(call_id: str, audio_bytes: bytes)`:
  - Формат аудио: конвертировать из mp3/ogg в формат провайдера если нужно
  - Отправка через WebSocket или HTTP POST
  - Обработка ошибок
- [ ] Метод `receive_audio(call_id: str) -> bytes | None`:
  - Чтение аудио от абонента
  - Если WebSocket: чтение из буфера
  - Если HTTP: получение через polling или callback
  - Конвертация в формат для Whisper (mp3, ogg, wav)
- [ ] Метод `hangup(call_id: str)`:
  - Вызов API для завершения звонка
  - Логирование
- [ ] Обработка событий от провайдера:
  - Настроить webhook endpoint (POST /telephony/events)
  - Парсинг формата событий провайдера
  - Маппинг на внутренние TelephonyEvent:
    - ringing, answered, busy, no_answer, hangup, error
  - Вызов orchestrator.handle_telephony_event()

### Checkpoint 12.3: Конвертация аудио форматов
- [ ] Определить требуемые форматы:
  - OpenAI Whisper: принимает mp3, mp4, mpeg, mpga, m4a, wav, webm
  - OpenAI TTS: возвращает mp3, opus, aac, flac
  - Провайдер: например, G.711 (ulaw/alaw), Opus
- [ ] Установить библиотеку для конвертации:
  ```bash
  pip install pydub
  sudo apt install -y ffmpeg  # на VPS
  ```
- [ ] Реализовать утилиты конвертации:
  - `convert_to_wav(audio_bytes: bytes) -> bytes`
  - `convert_to_g711(audio_bytes: bytes) -> bytes`
- [ ] Тестирование конвертации:
  - Загрузить тестовый файл
  - Конвертировать туда-обратно
  - Проверить воспроизведение

### Checkpoint 12.4: Настройка webhook для событий
- [ ] Обновить Nginx конфиг для приема событий:
  - Убедиться что /telephony/events доступен извне
- [ ] Зарегистрировать webhook URL в панели провайдера:
  - URL: `https://your-domain.com/telephony/events`
  - Формат: JSON
  - События: все (ringing, answered, hangup, etc.)
- [ ] Тестирование webhook:
  - Сделать тестовый звонок через панель провайдера
  - Проверить что события приходят на /telephony/events
  - Логировать входящие payload
  - Проверить корректность маппинга

### Checkpoint 12.5: Интеграционное тестирование
- [ ] Обновить конфигурацию:
  - В main.py заменить StubTelephonyAdapter на реальный
  - Добавить в .env ключи провайдера
- [ ] Перезапустить приложение на VPS:
  ```bash
  sudo supervisorctl restart callerapi
  ```
- [ ] Первый тестовый звонок:
  - POST /call с реальным номером (свой телефон)
  - Проверить:
    - ✓ Звонок поступает на телефон
    - ✓ При ответе слышен голос ассистента
    - ✓ Качество голоса приемлемое
    - ✓ Речь распознается корректно
    - ✓ Ответы ассистента релевантные
    - ✓ Задержка между репликами ≤ 2-3 сек
    - ✓ Звонок корректно завершается
    - ✓ Транскрипт сохраняется в Sheets
- [ ] Тестирование различных сценариев:
  - **Сценарий 1: Заинтересованный абонент**
    - Ответить на звонок
    - Сказать "Да, интересно, расскажите подробнее"
    - Задавать уточняющие вопросы
    - Попрощаться
    - Проверить: final_disposition = "interested"
  - **Сценарий 2: Незаинтересованный абонент**
    - Ответить
    - Сказать "Нет, спасибо, не интересует"
    - Повесить трубку
    - Проверить: final_disposition = "not_interested"
  - **Сценарий 3: Перезвонить позже**
    - Ответить
    - Сказать "Сейчас неудобно, перезвоните завтра"
    - Проверить: final_disposition = "call_later"
  - **Сценарий 4: Нет ответа**
    - Не отвечать на звонок
    - Проверить: status = "no_answer", final_disposition = "unknown"
  - **Сценарий 5: Сброс звонка**
    - Сбросить сразу при звонке
    - Проверить корректную обработку
- [ ] Проверить задержки в продакшене:
  - Засечь время между вопросом и ответом
  - Если > 2 сек → оптимизировать (см. этап 13)

### Checkpoint 12.6: Отладка и исправление проблем
- [ ] Собрать список проблем из тестов
- [ ] Типовые проблемы:
  - Плохое качество звука → проверить codec, битрейт
  - Задержки > 2 сек → оптимизировать (streaming, параллелизм)
  - Неправильное распознавание → проверить формат аудио, sample rate
  - Обрывы звонка → проверить timeout, keepalive
- [ ] Исправить проблемы, повторить тесты

**Критерий завершения**: Реальный провайдер телефонии интегрирован, звонки работают стабильно

---

## ЭТАП 13: Оптимизация задержек и производительности
**Цель**: Добиться задержки ≤ 2 сек между репликами, стабильной работы под нагрузкой

### Checkpoint 13.1: Профилирование задержек
- [ ] Добавить детальное логирование времени каждого этапа:
  ```python
  t0 = time.time()
  audio = await telephony.receive_audio(call_id)
  t1 = time.time()
  logger.info(f"Received audio in {t1-t0:.3f}s")

  text = await openai_client.transcribe_audio(audio)
  t2 = time.time()
  logger.info(f"STT completed in {t2-t1:.3f}s")

  response = await openai_client.generate_response(messages)
  t3 = time.time()
  logger.info(f"GPT completed in {t3-t2:.3f}s")

  audio_response = await openai_client.text_to_speech(response)
  t4 = time.time()
  logger.info(f"TTS completed in {t4-t3:.3f}s")

  await telephony.send_audio(call_id, audio_response)
  t5 = time.time()
  logger.info(f"Audio sent in {t5-t4:.3f}s")
  logger.info(f"Total turn time: {t5-t0:.3f}s")
  ```
- [ ] Провести несколько тестовых звонков
- [ ] Собрать статистику:
  - Среднее время STT: ?
  - Среднее время GPT: ?
  - Среднее время TTS: ?
  - Среднее общее время: ?
- [ ] Выявить узкие места

### Checkpoint 13.2: Оптимизация запросов к OpenAI
- [ ] **STT (Whisper)**:
  - Уменьшить размер аудио чанков (если > 5 сек → 2-3 сек)
  - Конвертировать в оптимальный формат (ogg/opus сжатие лучше mp3)
  - Использовать httpx с connection pooling
- [ ] **GPT (Chat Completions)**:
  - Ограничить max_tokens (150-200, не больше)
  - Сократить системный промпт (убрать лишнее)
  - Ограничить историю сообщений (последние 5-7 ходов)
  - Рассмотреть более быструю модель (gpt-4o-mini вместо gpt-4o если качество устраивает)
- [ ] **TTS**:
  - Использовать tts-1 (быстрее) вместо tts-1-hd
  - Формат: opus (меньше размер → быстрее передача)
- [ ] Параллелизация:
  - Если возможно: получение аудио от абонента параллельно с обработкой предыдущего хода (pipeline)

### Checkpoint 13.3: Оптимизация сети
- [ ] Проверить пинг до OpenAI API:
  ```bash
  ping api.openai.com
  ```
- [ ] Если задержки большие:
  - Рассмотреть VPS ближе к серверам OpenAI (Europe/US)
  - Использовать CDN/proxy (если доступно)
- [ ] Убедиться что используется HTTP/2 для OpenAI (httpx поддерживает)
- [ ] Connection pooling для повторных запросов

### Checkpoint 13.4: Нагрузочное тестирование
- [ ] Запустить 3 параллельных звонка одновременно
- [ ] Проверить:
  - Все звонки обрабатываются без деградации
  - Задержки не увеличиваются значительно
  - Нет ошибок timeout
  - CPU/RAM в пределах нормы
- [ ] Если проблемы:
  - Увеличить количество workers в uvicorn (--workers 4)
  - Оптимизировать асинхронность (убедиться что все I/O операции async)
  - Рассмотреть использование очередей задач (Celery/RQ) для долгих операций

### Checkpoint 13.5: Мониторинг ресурсов
- [ ] Установить htop на VPS:
  ```bash
  sudo apt install -y htop
  ```
- [ ] Мониторить во время звонков:
  - CPU usage
  - RAM usage
  - Network I/O
- [ ] Если превышение:
  - Оптимизировать код (профилирование с cProfile)
  - Увеличить ресурсы VPS (upgrade)

### Checkpoint 13.6: Проверка стабильности
- [ ] Провести 10 последовательных звонков без перерыва
- [ ] Проверить:
  - Все звонки успешно завершены
  - Нет утечек памяти (RAM не растет постоянно)
  - Нет накопления незакрытых соединений
  - Логи чистые (нет повторяющихся ERROR)
- [ ] Long-running тест:
  - Запустить 1 звонок в час в течение 8 часов
  - Проверить отсутствие деградации

**Критерий завершения**: Задержки ≤ 2 сек, система стабильна под нагрузкой

---

## ЭТАП 14: Логирование, мониторинг, безопасность
**Цель**: Настроить полноценное логирование, мониторинг, укрепить безопасность

### Checkpoint 14.1: Расширенное логирование
- [ ] Проверить все обязательные точки логирования из ТЗ:
  - ✓ Запрос на /call (call_id, phone)
  - ✓ События от телефонии (event, call_id)
  - ✓ Начало/конец диалога (call_id)
  - ✓ Ошибки OpenAI (STT/LLM/TTS)
  - ✓ Ошибки работы с Google Sheets
  - ✓ Итоговая строка (status, final_disposition)
- [ ] Добавить логирование:
  - Время выполнения каждого этапа (performance metrics)
  - Размер аудио чанков
  - Количество активных звонков
  - Использование OpenAI API (tokens, cost)
- [ ] Структурированное логирование:
  - Использовать JSON формат для логов
  - Библиотека: python-json-logger или structlog
  - Формат: {"timestamp": "...", "level": "INFO", "call_id": "...", "event": "...", "duration": 1.234}
- [ ] Ротация логов:
  - Настроить logrotate:
    ```bash
    sudo nano /etc/logrotate.d/callerapi
    ```
    ```
    /var/log/callerapi/*.log {
        daily
        rotate 14
        compress
        delaycompress
        missingok
        notifempty
    }
    ```

### Checkpoint 14.2: Мониторинг
- [ ] Настроить базовый мониторинг:
  - Endpoint /metrics для экспорта метрик
  - Счетчики: количество звонков (total, успешные, failed)
  - Гистограммы: время выполнения операций
  - Gauge: количество активных звонков
- [ ] Опционально: интеграция с Prometheus + Grafana
  - Установить prometheus-fastapi-instrumentator
  - Экспорт метрик на /metrics
  - Настроить Prometheus для scraping
  - Создать dashboard в Grafana
- [ ] Альтернатива: простой health check с метриками:
  ```python
  @app.get("/health")
  async def health():
      return {
          "status": "ok",
          "active_calls": len(orchestrator.active_calls),
          "total_calls": orchestrator.total_calls,
          "uptime": time.time() - start_time
      }
  ```

### Checkpoint 14.3: Безопасность
- [ ] **API аутентификация**:
  - ✓ X-API-Key уже реализован
  - Генерировать сильный ключ (32+ символов, random)
  - Хранить в .env, не коммитить в git
- [ ] **Rate limiting**:
  - Установить slowapi или использовать Nginx rate limiting
  - Ограничить POST /call: 10 запросов/минуту с одного IP
  - Ограничить /telephony/events: 100 запросов/минуту
- [ ] **Валидация входных данных**:
  - ✓ Pydantic модели уже используются
  - Дополнительно: санитизация номера телефона (нормализация)
  - Проверка на SQL injection (если используется БД)
- [ ] **Защита секретов**:
  - .env файл: chmod 600
  - Google credentials JSON: chmod 600
  - Не логировать API ключи
- [ ] **HTTPS**:
  - ✓ Уже настроен через Let's Encrypt
  - Форсировать редирект HTTP → HTTPS
  - HSTS заголовок:
    ```nginx
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    ```
- [ ] **Firewall**:
  - ✓ UFW уже настроен
  - Разрешить только 22 (SSH), 80 (HTTP), 443 (HTTPS)
  - Закрыть все остальные порты
- [ ] **Обновления**:
  - Настроить автообновления безопасности:
    ```bash
    sudo apt install -y unattended-upgrades
    sudo dpkg-reconfigure -plow unattended-upgrades
    ```

### Checkpoint 14.4: Обработка ошибок и восстановление
- [ ] Graceful shutdown:
  - При получении SIGTERM:
    - Перестать принимать новые звонки
    - Дождаться завершения активных звонков (timeout 60 сек)
    - Сохранить незаписанные результаты
    - Закрыть соединения
- [ ] Автоматический рестарт при падении:
  - ✓ Supervisor уже настроен с autorestart=true
  - Проверить: если процесс упал → Supervisor его перезапустит
- [ ] Fallback для Google Sheets:
  - Если API недоступен:
    - Логировать ERROR
    - Сохранить результат в локальный JSON файл
    - Фоновая задача: retry отправки в Sheets каждые 5 минут
- [ ] Alerts при критических ошибках:
  - Опционально: отправка уведомлений (email, Telegram)
  - При ошибках: OpenAI quota exceeded, Google Sheets недоступен > 5 минут

**Критерий завершения**: Логирование полное, мониторинг настроен, безопасность укреплена

---

## ЭТАП 15: Документация и передача проекта
**Цель**: Подготовить документацию для заказчика

### Checkpoint 15.1: README.md
- [ ] Создать полный README.md:
  - **Описание проекта**
  - **Функционал**: что умеет система
  - **Требования**: Python 3.11+, OS, зависимости
  - **Установка локально**:
    - Клонирование репозитория
    - Создание venv
    - Установка зависимостей
    - Настройка .env
    - Запуск
  - **Деплой на VPS**:
    - Пошаговая инструкция
    - Настройка Nginx
    - Настройка Supervisor
    - SSL сертификат
  - **Конфигурация**:
    - Описание всех переменных окружения
    - Примеры значений
  - **API документация**:
    - POST /call: описание, пример запроса/ответа
    - POST /telephony/events: формат
    - GET /health: health check
  - **Примеры использования**:
    - curl команды
    - Пример ответа
  - **Структура проекта**:
    - Описание папок и файлов
  - **Логирование**: где находятся логи, как их читать
  - **Troubleshooting**: типовые проблемы и решения

### Checkpoint 15.2: OpenAPI документация
- [ ] FastAPI автоматически генерирует OpenAPI схему
- [ ] Проверить доступность:
  - /docs (Swagger UI)
  - /redoc (ReDoc)
- [ ] Добавить описания к эндпоинтам:
  ```python
  @app.post("/call", summary="Initiate outbound call", description="...")
  ```
- [ ] Добавить примеры запросов/ответов в Pydantic моделях:
  ```python
  class CallRequest(BaseModel):
      phone: str = Field(..., example="+79991234567")
  ```

### Checkpoint 15.3: Документация провайдера телефонии
- [ ] Создать TELEPHONY_SETUP.md:
  - **Выбранный провайдер**: название, ссылка
  - **Регистрация**: пошаговая инструкция
  - **Получение API ключей**
  - **Настройка webhook**: URL, формат событий
  - **Настройка номера/SIP trunk** (если нужно)
  - **Тестирование**: как сделать тестовый звонок
  - **Troubleshooting**: типовые проблемы

### Checkpoint 15.4: Документация Google Sheets
- [ ] Создать GOOGLE_SHEETS_SETUP.md:
  - **Создание Google Spreadsheet**
  - **Настройка Google Cloud Project**:
    - Включение Google Sheets API
    - Создание service account
    - Генерация JSON ключа
  - **Предоставление доступа**: добавить email service account в Sheets
  - **Формат таблицы**: описание колонок
  - **Пример записи**

### Checkpoint 15.5: Примеры и коллекции запросов
- [ ] Создать Postman/Insomnia коллекцию:
  - Запрос POST /call
  - Запрос GET /health
  - Переменные окружения (API_KEY, BASE_URL)
- [ ] Экспортировать коллекцию в JSON
- [ ] Добавить в репозиторий: docs/postman_collection.json
- [ ] Инструкция по импорту

### Checkpoint 15.6: Юнит-тесты (опционально для MVP)
- [ ] Создать базовые тесты:
  - tests/test_models.py: тесты Pydantic моделей
  - tests/test_openai_client.py: мокирование OpenAI API
  - tests/test_orchestrator.py: логика оркестратора
- [ ] Запуск тестов:
  ```bash
  pip install pytest pytest-asyncio
  pytest tests/
  ```
- [ ] Добавить в README инструкцию по запуску тестов

### Checkpoint 15.7: Видео-демонстрация (опционально)
- [ ] Записать screencast:
  - Запуск POST /call через Postman
  - Показать реальный звонок (экран телефона)
  - Диалог с ассистентом
  - Запись в Google Sheets
  - Логи в терминале
- [ ] Загрузить на YouTube (unlisted)
- [ ] Добавить ссылку в README

**Критерий завершения**: Документация полная, понятная, готова к передаче

---

## ЭТАП 16: Приемка и закрытие проекта
**Цель**: Демонстрация работы, приемка заказчиком

### Checkpoint 16.1: Подготовка к демонстрации
- [ ] Подготовить демо-сценарий:
  1. Показать архитектуру (диаграмма или схема)
  2. Демонстрация POST /call через Postman
  3. Реальный звонок в режиме реального времени:
     - Звонок на телефон демонстратора
     - Ответ и диалог
     - Завершение
  4. Показать логи на VPS (tail -f)
  5. Показать запись в Google Sheets
  6. Показать метрики (/health или /metrics)
- [ ] Подготовить тестовые данные:
  - Несколько номеров для звонков
  - Разные сценарии (заинтересован, не заинтересован, перезвонить)
- [ ] Проверить стабильность:
  - Сделать несколько пробных звонков
  - Убедиться что все работает

### Checkpoint 16.2: Демонстрация заказчику
- [ ] Провести демонстрацию:
  - Показать функционал системы
  - Ответить на вопросы заказчика
  - Показать код (если интересно)
  - Показать документацию
- [ ] Собрать обратную связь:
  - Что понравилось?
  - Что нужно улучшить?
  - Есть ли критичные замечания?
- [ ] Зафиксировать список доработок (если есть)

### Checkpoint 16.3: Исправление замечаний
- [ ] Если есть замечания в рамках ТЗ:
  - Зафиксировать в TODO
  - Расставить приоритеты
  - Внести исправления
  - Повторное тестирование
- [ ] Если замечания вне ТЗ:
  - Обсудить с заказчиком
  - Либо отказаться (вне scope)
  - Либо договориться о допработах (дополнительная оплата)
- [ ] Повторная демонстрация (если требуется)

### Checkpoint 16.4: Передача проекта
- [ ] Подготовить все материалы для передачи:
  - **Код**: доступ к git-репозиторию (GitHub/GitLab)
  - **Документация**: README, setup guides
  - **Credentials**:
    - .env файл (шаблон и заполненный для продакшена)
    - Google service account JSON ключ
    - API ключи провайдера телефонии
    - SSL сертификаты (если не через Let's Encrypt)
  - **Доступы**:
    - SSH ключ к VPS
    - Доступ к панели провайдера телефонии
    - Доступ к Google Sheets
  - **Инструкции**:
    - Как перезапустить сервис (sudo supervisorctl restart callerapi)
    - Как посмотреть логи (tail -f /var/log/callerapi/app.log)
    - Как обновить код (git pull, restart)
    - Контакты для поддержки
- [ ] Передать заказчику
- [ ] Убедиться что заказчик получил все материалы

### Checkpoint 16.5: Подписание акта приёма-сдачи
- [ ] Подготовить акт приёма-сдачи работ:
  - Дата
  - Номер договора (0708_01 от 08 октября 2025)
  - Описание выполненных работ
  - Стоимость (20 000 руб.)
  - Подписи сторон
- [ ] Отправить заказчику на подпись
- [ ] Получить подписанный акт
- [ ] Сохранить копию

### Checkpoint 16.6: Получение оплаты
- [ ] Выставить счет на оплату:
  - Сумма: 20 000 руб.
  - Реквизиты исполнителя
  - Основание: Акт приёма-сдачи по договору 0708_01
- [ ] Отправить счет заказчику
- [ ] Отследить оплату (срок: 3 рабочих дня после подписания акта)
- [ ] Подтвердить получение оплаты
- [ ] Выписать закрывающие документы (если требуется)

### Checkpoint 16.7: Пост-релизная поддержка (опционально)
- [ ] Договориться с заказчиком о поддержке:
  - Срок гарантийной поддержки (например, 2 недели)
  - Что входит: исправление критических багов
  - Что НЕ входит: новые фичи, изменения требований
- [ ] Быть на связи в течение гарантийного периода
- [ ] Исправлять критические баги оперативно
- [ ] Закрыть гарантийный период

**Критерий завершения**: Проект сдан, акт подписан, оплата получена ✅

---

## КРИТИЧЕСКИЕ РИСКИ И МИТИГАЦИЯ

### Риск 1: Задержки при обработке речи > 2 сек
**Вероятность**: Средняя
**Влияние**: Высокое (основное требование ТЗ)
**Митигация**:
- Использовать асинхронные вызовы API
- Оптимизировать размер аудио чанков (2-3 сек вместо 5-10 сек)
- Использовать быстрые модели (tts-1, gpt-4o-mini)
- Сжатие аудио (opus codec)
- VPS с низким пингом до OpenAI (Europe/US region)
- Pipeline обработка (параллелизм)

### Риск 2: Проблемы с провайдером телефонии
**Вероятность**: Средняя
**Влияние**: Критическое (без телефонии система не работает)
**Митигация**:
- Заранее протестировать API провайдера на простых примерах
- Использовать абстракцию TelephonyAdapter для легкой замены
- Иметь fallback на альтернативного провайдера (Zadarma + Voximplant)
- Детальное логирование событий телефонии
- Поддержка провайдера: убедиться что есть техподдержка

### Риск 3: Ограничения OpenAI API (rate limits, quota)
**Вероятность**: Средняя
**Влияние**: Высокое (система перестанет работать)
**Митигация**:
- Проверить текущие лимиты аккаунта OpenAI (tier)
- Запросить увеличение лимитов заранее (через OpenAI support)
- Реализовать retry с exponential backoff
- Мониторинг использования API (логировать tokens, cost)
- Fallback: при превышении квоты → graceful degradation (сообщение абоненту)

### Риск 4: Проблемы с Google Sheets API (квоты, задержки)
**Вероятность**: Низкая
**Влияние**: Среднее (данные могут быть потеряны)
**Митигация**:
- Проверить квоты Google Sheets API (обычно достаточно для MVP)
- Retry логика при ошибках (до 3 попыток)
- Fallback: локальное хранение в JSON файл, отложенная отправка
- Альтернатива: использовать БД (PostgreSQL) вместо Sheets

### Риск 5: Недостаточная производительность VPS
**Вероятность**: Низкая
**Влияние**: Среднее (медленная работа, не выдержит нагрузку)
**Митигация**:
- Выбрать VPS с достаточными ресурсами (2 CPU, 4 GB RAM)
- Оптимизировать код (async, минимум блокировок)
- Мониторинг ресурсов (CPU, RAM, network)
- Масштабирование: при необходимости upgrade тарифа VPS
- Горизонтальное масштабирование: несколько инстансов + load balancer (для будущего)

### Риск 6: Проблемы с качеством распознавания речи (STT)
**Вероятность**: Средняя
**Влияние**: Высокое (некорректные диалоги)
**Митигация**:
- Использовать правильный формат аудио (16kHz sample rate оптимально для Whisper)
- Проверить качество аудио от провайдера телефонии
- Настроить VAD (Voice Activity Detection) для фильтрации шума
- Указать язык явно (language="ru") в Whisper API
- Тестирование с различными акцентами и шумом

### Риск 7: Некорректное поведение ассистента (GPT)
**Вероятность**: Средняя
**Влияние**: Среднее (плохой UX, неправильная классификация)
**Митигация**:
- Тщательно составить системный промпт
- Тестирование различных сценариев диалога
- Ограничить max_tokens (чтобы ответы были краткими)
- Few-shot примеры в промпте (если нужно)
- Итеративная доработка промпта на основе тестов

### Риск 8: Проблемы с безопасностью (DDoS, утечка данных)
**Вероятность**: Низкая
**Влияние**: Критическое (потеря данных, репутации)
**Митигация**:
- Rate limiting (ограничение запросов с одного IP)
- Сильный API ключ (X-API-Key)
- HTTPS + HSTS
- Firewall (UFW)
- Не логировать секреты
- Регулярные обновления системы (unattended-upgrades)
- Защита credentials (chmod 600)

### Риск 9: Превышение бюджета на API вызовы
**Вероятность**: Низкая (для MVP)
**Влияние**: Среднее (финансовые потери)
**Митигация**:
- Оценить стоимость заранее (Whisper + GPT + TTS на 1 звонок ≈ $0.10-0.20)
- Установить лимиты в OpenAI аккаунте (billing limits)
- Мониторинг расходов (логировать tokens usage)
- Оптимизация: использовать более дешевые модели где возможно (gpt-4o-mini)

### Риск 10: Невыполнение в срок (до 15 октября 2025)
**Вероятность**: Средняя (зависит от непредвиденных проблем)
**Влияние**: Высокое (штрафы, репутация)
**Митигация**:
- Следовать плану поэтапно
- Приоритизация: сначала core функционал, потом доп. фичи
- Агрессивное тестирование на ранних этапах
- Буфер времени: закладывать 20% на непредвиденные проблемы
- Регулярная коммуникация с заказчиком (статус апдейты)

---

## КОНТРОЛЬНЫЕ ТОЧКИ (MILESTONES)

1. **День 1-2**: Этапы 1-3 завершены
   - Структура проекта создана
   - Модели данных определены
   - Логирование настроено

2. **День 3-4**: Этапы 4-5 завершены
   - OpenAI клиент работает
   - Google Sheets интеграция работает

3. **День 5-7**: Этапы 6-10 завершены
   - Логика диалога реализована
   - API эндпоинты работают
   - Локальное тестирование пройдено

4. **День 8**: Этап 11 завершен
   - Деплой на VPS выполнен

5. **День 9-10**: Этап 12 завершен
   - Реальный провайдер телефонии интегрирован
   - Тестовые звонки проходят успешно

6. **День 11**: Этапы 13-14 завершены
   - Оптимизация задержек
   - Безопасность и мониторинг

7. **День 12**: Этапы 15-16 завершены
   - Документация готова
   - Приемка заказчиком
   - Проект сдан

---

## ЧЕКЛИСТ ПЕРЕД СДАЧЕЙ

### Функциональные требования
- [ ] ✅ POST /call принимает номер телефона РФ и инициирует звонок
- [ ] ✅ При ответе абонента начинается диалог на русском языке
- [ ] ✅ Используется OpenAI Whisper для STT
- [ ] ✅ Используется GPT (gpt-4o или аналог) для генерации ответов
- [ ] ✅ Используется OpenAI TTS для озвучки
- [ ] ✅ Задержка между репликами ≤ 2 сек (в большинстве случаев)
- [ ] ✅ Диалог ведет вежливый оператор (согласно системному промпту)
- [ ] ✅ Диалог ограничен по времени (≤ 120 сек)
- [ ] ✅ Диалог ограничен по количеству ходов (≤ 12 пар)
- [ ] ✅ По окончании звонка результат записывается в Google Sheets
- [ ] ✅ Транскрипт полный и читаемый
- [ ] ✅ final_disposition определяется корректно (interested/not_interested/call_later/neutral)
- [ ] ✅ short_summary содержательный (1-2 предложения)

### Обработка событий
- [ ] ✅ Обработка события "no_answer" (не дозвонились)
- [ ] ✅ Обработка события "busy" (занято)
- [ ] ✅ Обработка события "hangup" (абонент повесил трубку)
- [ ] ✅ Обработка ошибок OpenAI API
- [ ] ✅ Обработка ошибок Google Sheets API
- [ ] ✅ Обработка ошибок провайдера телефонии

### API и валидация
- [ ] ✅ API защищен ключом (X-API-Key)
- [ ] ✅ Валидация номера телефона (формат РФ: `^(\+7|8)\d{10}$`)
- [ ] ✅ Валидация входных данных (Pydantic)
- [ ] ✅ Корректные HTTP коды ответов (200, 400, 401, 500)
- [ ] ✅ Обработка ошибок с понятными сообщениями

### Логирование
- [ ] ✅ Запросы на /call логируются (call_id, phone)
- [ ] ✅ События от телефонии логируются (event, call_id)
- [ ] ✅ Начало/конец диалога логируется
- [ ] ✅ Ошибки OpenAI логируются (уровень ERROR)
- [ ] ✅ Ошибки Google Sheets логируются (уровень ERROR)
- [ ] ✅ Итоговая строка логируется (status, final_disposition, duration)
- [ ] ✅ Логи структурированы и читаемы
- [ ] ✅ Логи ротируются (не заполняют диск)

### Безопасность
- [ ] ✅ HTTPS настроен (SSL сертификат)
- [ ] ✅ Firewall настроен (UFW)
- [ ] ✅ Секреты не в коде (.env, credentials защищены)
- [ ] ✅ Rate limiting настроен
- [ ] ✅ Нет SQL injection, XSS уязвимостей
- [ ] ✅ Автообновления безопасности настроены

### Производительность и стабильность
- [ ] ✅ Система выдерживает 3 параллельных звонка
- [ ] ✅ Нет утечек памяти (проверено long-running тестом)
- [ ] ✅ Нет деградации производительности со временем
- [ ] ✅ Автоматический рестарт при падении (Supervisor)
- [ ] ✅ Graceful shutdown работает

### Деплой
- [ ] ✅ Приложение задеплоено на VPS
- [ ] ✅ Сервис запускается автоматически (Supervisor)
- [ ] ✅ Nginx настроен как reverse proxy
- [ ] ✅ SSL сертификат установлен и обновляется автоматически
- [ ] ✅ Доступ по HTTPS работает
- [ ] ✅ Health check endpoint доступен

### Документация
- [ ] ✅ README.md полный и понятный
- [ ] ✅ OpenAPI документация доступна (/docs)
- [ ] ✅ Инструкция по настройке провайдера телефонии
- [ ] ✅ Инструкция по настройке Google Sheets
- [ ] ✅ Примеры API запросов (Postman коллекция)
- [ ] ✅ Описание всех переменных окружения

### Передача проекта
- [ ] ✅ Код в git-репозитории, доступ передан заказчику
- [ ] ✅ Все credentials переданы (API ключи, SSH, и т.д.)
- [ ] ✅ Инструкции по эксплуатации переданы
- [ ] ✅ Демонстрация проведена успешно
- [ ] ✅ Акт приёма-сдачи подписан
- [ ] ✅ Оплата получена

---

## ИТОГОВАЯ ПРОВЕРКА

Перед сдачей проекта выполнить финальный тест:

1. **Полный флоу звонка**:
   ```bash
   # 1. Инициировать звонок
   curl -X POST https://your-domain.com/call \
     -H "Content-Type: application/json" \
     -H "X-API-Key: YOUR_KEY" \
     -d '{"phone": "+79991234567"}'

   # 2. Ответить на звонок и провести диалог
   # 3. Проверить логи
   ssh user@vps "tail -n 100 /var/log/callerapi/app.log"

   # 4. Проверить запись в Google Sheets
   # Открыть таблицу, проверить последнюю строку

   # 5. Проверить метрики
   curl https://your-domain.com/health
   ```

2. **Проверка всех граничных случаев** (см. Checkpoint 10.3)

3. **Проверка документации**: прочитать README глазами новичка

4. **Финальная демонстрация заказчику**

✅ **ПРОЕКТ ГОТОВ К СДАЧЕ!**
