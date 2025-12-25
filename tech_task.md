Техническое задание №2
к договору 0708_01 от 08 октября 2025 года. 

Стоимость и оплата
Стоимость работ: 20 000 руб.
Порядок оплаты: Оплата в полном объёме на расчётный счёт Исполнителя в течение 3 (трех) рабочих дней после подписания Акта приёма-сдачи работ Заказчиком.
Сроки
Срок выполнения: до 15 октября 2025 г. 


Реализовать MVP сервиса голосового обзвона, который:
по вызову HTTP-эндпоинта инициирует исходящий звонок на номер РФ,
при ответе абонента ведёт реалистичный диалог на русском с помощью OpenAI (Whisper + GPT + TTS),
по окончании звонка сохраняет результат и транскрипт в Google Sheets.
Основная цель — доказать реализуемость голосового ассистента с приемлемой задержкой (до ~2 сек между репликами) и реалистичным поведением.

1. Технический стек
Backend: Python 3.11+, FastAPI
Запуск: Uvicorn / Gunicorn (на Render)
Развёртывание: Render (Docker / Blueprint – на усмотрение разработчика)
Внешние сервисы:
OpenAI API:
/v1/audio/transcriptions (Whisper STT),
/v1/chat/completions (GPT),
/v1/audio/speech (TTS).
Провайдер телефонии (пока абстрактно — реализовать через интерфейс, чтобы можно было подложить Voximplant / Zadarma / Mango).
Google Sheets (через сервисный аккаунт).

2. Общая архитектура
2.1. Компоненты
HTTP API (FastAPI):
POST /call — инициировать звонок.
(внутренние) callback-эндпоинты для провайдера телефонии.
Call Orchestrator:
отвечает за жизненный цикл звонка: создание, обновление статуса, запуск диалога, завершение.
Telephony Adapter:
абстракция над конкретным провайдером телефонии:
методы: initiate_call, send_audio, обработка callback-событий, получение аудиочанков.
Dialog Manager:
управляет диалогом с абонентом:
цикл: аудио → STT → GPT → TTS → аудио.
OpenAI Client:
обёртка над вызовами Whisper / GPT / TTS,
единая точка конфигурации (ключ, таймауты, ретраи).
Google Sheets Client:
запись результатов звонка и транскрипта.
Persistence (минимально):
в MVP достаточно:
либо in-memory (dict) + логирование,
либо SQLite/PostgreSQL (по желанию).
Но обязательна сущность CallSession в коде.
2.2. Модель данных (логическая)
CallSession:
id: UUID
phone: str
status: enum[created, dialing, no_answer, in_progress, completed, failed]
final_disposition: enum[interested, not_interested, call_later, neutral, unknown]
started_at: datetime | None
ended_at: datetime | None
duration_sec: int | None
transcript: list[DialogTurn] (в памяти, для сохранения в Sheets)
short_summary: str | None
DialogTurn:
speaker: enum["user", "assistant"]
text: str
timestamp: datetime

3. Пользовательский флоу
Внешняя система отправляет запрос на POST /call с номером телефона.
Backend создаёт CallSession (status = created), генерирует call_id.
Backend вызывает TelephonyAdapter.initiate_call(call_id, phone).
Провайдер звонит на номер и по событиям дергает наш callback:
ringing → обновить статус на dialing;
answered → статус in_progress, старт диалога;
busy / no_answer / error → статус no_answer/failed, запись в Sheets, завершение.
При answered:
запускается цикл диалога:
получение аудиофрагмента от абонента;
STT → текст;
GPT → ответ + обновление контекста;
TTS → аудио;
отправка аудио абоненту;
ограничение по общему времени разговора ≈ 2 минуты.
После завершения диалога:
статус completed;
классификация final_disposition через GPT по всей истории диалога;
генерация short_summary;
запись строки в Google Sheets.

4. API-спецификация
4.1. Внешний эндпоинт
POST /call
Запрос (JSON):
{
  "phone": "+79XXXXXXXXX"
}

Ответ (JSON):
{
  "call_id": "uuid-v4",
  "status": "created"
}

Валидация:
обязательное поле phone;
базовая проверка формата: ^(\+7|8)\d{10}$ (на уровне бэка).
Ошибка:
при неверном формате → 400, JSON с кодом ошибки и описанием.
4.2. Callback-эндпоинт для событий телефонии
POST /telephony/events
Формат — абстрактный, нужно предусмотреть возможность адаптации под провайдера.
Пример унифицированного JSON, который адаптер должен приводить к общему виду:
{
  "call_id": "uuid-v4",
  "event": "answered", 
  "timestamp": "2025-11-17T16:10:00Z",
  "reason": null
}

Список возможных event:
ringing
answered
hangup
busy
no_answer
error
При получении answered — запуск диалога (см. Dialog Manager).
4.3. Аудио-интерфейс
Варианты, зависят от провайдера, но в архитектуре предусмотреть:
либо WebSocket /telephony/audio/{call_id}:
бинарные сообщения — аудио чанки от абонента,
текстовые/бинарные — аудио ассистента в ответ;
либо POST /telephony/audio с чанками + отдача ссылки на аудио-ответ.
Важно: TelephonyAdapter должен инкапсулировать этот протокол, наружу отдаётся абстракция:
class TelephonyAdapter(Protocol):
    async def initiate_call(self, call_id: str, phone: str) -> None: ...
    async def send_audio(self, call_id: str, audio_bytes: bytes) -> None: ...


5. Логика диалога (Dialog Manager)
5.1. Общий цикл
Диалог turn-based, не стриминговый:
Ждём аудиофрагмент от абонента (либо до “тишины”, либо по событию от провайдера).
Отправляем аудио в Whisper:
язык: auto/ru,
таймаут запроса — до 10 сек.
Получаем user_text.
Добавляем в transcript как DialogTurn(speaker="user", text=user_text).
Передаём в GPT:
системный промпт (роль оператора),
вся история диалога (ограниченная по длине),
возможно текущий шаг сценария.
GPT возвращает:
assistant_text — ответ ассистента.
Добавляем в transcript DialogTurn(speaker="assistant", text=assistant_text).
Гоним через TTS, получаем audio_bytes.
TelephonyAdapter.send_audio(call_id, audio_bytes).
Повторяем до:
превышения лимита по времени (≈ 2 минуты),
явного завершения диалога (ассистент попрощался),
разрыва звонка (hangup).
5.2. Ограничения
Общая длительность разговора — не более 120 секунд после answered.
Максимальное количество ходов (turns) — например, 10–12 пар “вопрос–ответ”.
При достижении лимита ассистент должен:
кратко подвести итог,
попрощаться,
завершить.
5.3. Системный промпт (описание, не текст)
В системном промпте для GPT зафиксировать:
Роль: вежливый, нейтральный оператор.
Цель: представить продукт, узнать интерес, зафиксировать один из статусов:
интересен / не интересен / перезвонить позже / непонятно.
Требования:
не спорить и не давить;
не обсуждать посторонние темы;
не говорить, что он ИИ;
говорить короткими фразами (1–2 предложения).

6. OpenAI-интеграция (детали для разработки)
6.1. Whisper (STT)
Эндпоинт: /v1/audio/transcriptions
Формат: multipart/form-data с файлом file и параметром model = "whisper-1" (или актуальной моделью).
Вход: аудио-чанк в формате, который легче всего получить от провайдера (при необходимости конвертировать в wav/ogg).
Выход: текст на русском.
6.2. GPT (Chat Completions)
Эндпоинт: /v1/chat/completions
Модель: gpt-4.1 / gpt-4o или актуальная.
Контекст:
system: описание роли оператора.
messages: история диалога (user/assistant).
Параметры:
temperature: 0.7 (для небольшой вариативности).
max_tokens: ограничить (например, 150–200).
Отдельный вызов GPT после завершения разговора:
Вход: весь транскрипт (как текст) + инструкция “классифицируй интерес”.
Выход:
final_disposition (interested / not_interested / call_later / neutral),
short_summary (1–2 предложения).
6.3. TTS
Эндпоинт: /v1/audio/speech
Параметры:
модель TTS (например, gpt-4o-mini-tts или актуальную),
голос — нейтральный (выбрать из доступных).
Вход: assistant_text.
Выход: аудио-байты (mp3/wav/ogg) — формат согласовать с телефонией.

7. Интеграция с Google Sheets
7.1. Авторизация
Использовать service account с доступом к конкретному документу.
JSON-ключ хранить в переменной окружения (например, GOOGLE_CREDENTIALS_JSON или путь к файлу).
7.2. Структура листа
Колонки (фиксированные):
timestamp (UTC или МСК)
call_id
phone
status (итоговый статус звонка)
final_disposition
duration_sec
short_summary
transcript (весь текст диалога; можно склеить через разделитель)
7.3. Момент записи
Записывать одну строку по завершении звонка, независимо от успеха:
при no_answer / failed:
final_disposition = "unknown",
duration_sec = 0,
short_summary = короткое пояснение (“Не дозвонились: статус no_answer”).

8. Нефункциональные требования
8.1. Задержки и производительность
Цель: время между фразой клиента и началом ответа ассистента ≤ 2 сек.
Учитывать:
время сети РФ ↔ Render ↔ OpenAI,
обработку аудио и запросов.
MVP рассчитан на:
до 3 параллельных звонков.
8.2. Логирование
Обязательные точки логирования (уровень INFO/ERROR):
Запрос на /call (call_id, phone).
События от телефонии (event, call_id).
Начало/конец диалога (call_id).
Ошибки OpenAI (STT/LLM/TTS).
Ошибки работы с Google Sheets.
Итоговая строка (status, final_disposition).

9. Конфигурация и секреты
Используем переменные окружения:
OPENAI_API_KEY
GOOGLE_SHEETS_SPREADSHEET_ID
GOOGLE_CREDENTIALS_JSON или GOOGLE_CREDENTIALS_FILE
TELEPHONY_API_KEY / TELEPHONY_CONFIG (по провайдеру)
API_AUTH_KEY (для защиты /call — простой ключ в заголовке X-API-Key)

10. Структура проекта (рекомендация)
app/
  main.py                # FastAPI app, routes
  config.py              # settings (Pydantic BaseSettings)
  api/
    __init__.py
    routes_call.py       # /call
    routes_telephony.py  # callbacks / events / audio
  core/
    models.py            # CallSession, DialogTurn, enums
    orchestrator.py      # CallOrchestrator
    dialog_manager.py    # DialogManager
  integrations/
    openai_client.py     # Whisper/GPT/TTS
    telephony_base.py    # интерфейс TelephonyAdapter
    telephony_stub.py    # заглушка / базовая реализация
    google_sheets.py     # клиент для записи результатов
  utils/
    logging.py           # настройка логирования
    time.py

