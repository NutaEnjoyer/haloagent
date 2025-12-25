"""
Demo data generator for HALO demo cabinet.
Generates 50 demo calls and 50 demo chats for wow-effect.
"""
import random
from datetime import datetime, timedelta
from uuid import uuid4

from app.core.models import (
    DemoCall,
    DemoChat,
    ChatMessage,
    DialogTurn,
    Speaker,
    FinalDisposition,
    CRMRecord,
)


# Demo call scenarios (Russian)
CALL_SCENARIOS = [
    {
        "disposition": FinalDisposition.INTERESTED,
        "summary": "Клиент заинтересован в продукте, попросил отправить коммерческое предложение",
        "interest": "узнать стоимость и получить КП",
        "transcript": [
            {"speaker": Speaker.ASSISTANT, "text": "Здравствуйте! Меня зовут Алиса, я представляю компанию HALO. Удобно сейчас разговаривать?"},
            {"speaker": Speaker.USER, "text": "Да, здравствуйте. Слушаю вас."},
            {"speaker": Speaker.ASSISTANT, "text": "Отлично! Мы предлагаем инновационное решение для автоматизации обработки обращений клиентов. Хотели бы узнать подробнее?"},
            {"speaker": Speaker.USER, "text": "Звучит интересно. А какая стоимость?"},
            {"speaker": Speaker.ASSISTANT, "text": "Стоимость зависит от объема обращений. Могу отправить коммерческое предложение на вашу почту?"},
            {"speaker": Speaker.USER, "text": "Да, отправьте, пожалуйста."},
        ]
    },
    {
        "disposition": FinalDisposition.NOT_INTERESTED,
        "summary": "Клиент отказался, сказал что уже используют другое решение",
        "interest": None,
        "transcript": [
            {"speaker": Speaker.ASSISTANT, "text": "Добрый день! Это компания HALO, представляем ИИ-ассистентов для бизнеса."},
            {"speaker": Speaker.USER, "text": "Спасибо, но нам это не нужно."},
            {"speaker": Speaker.ASSISTANT, "text": "Понимаю. Может быть, вас заинтересует бесплатный пилот на месяц?"},
            {"speaker": Speaker.USER, "text": "Нет, у нас уже есть решение. Спасибо."},
        ]
    },
    {
        "disposition": FinalDisposition.CALL_LATER,
        "summary": "Клиент попросил перезвонить через неделю, сейчас неудобно обсуждать",
        "interest": "перезвонить позже",
        "transcript": [
            {"speaker": Speaker.ASSISTANT, "text": "Здравствуйте! Меня зовут Алиса из компании HALO."},
            {"speaker": Speaker.USER, "text": "Добрый день. Сейчас неудобно, я на встрече."},
            {"speaker": Speaker.ASSISTANT, "text": "Понимаю. Когда вам будет удобно обсудить наше предложение?"},
            {"speaker": Speaker.USER, "text": "Перезвоните через неделю, пожалуйста."},
        ]
    },
    {
        "disposition": FinalDisposition.INTERESTED,
        "summary": "Клиент заинтересован, договорились о встрече для демонстрации",
        "interest": "назначить встречу для демо",
        "transcript": [
            {"speaker": Speaker.ASSISTANT, "text": "Доброго времени суток! Компания HALO, ИИ-ассистенты для бизнеса."},
            {"speaker": Speaker.USER, "text": "Здравствуйте. Что именно вы предлагаете?"},
            {"speaker": Speaker.ASSISTANT, "text": "Мы автоматизируем обработку звонков и чатов с помощью искусственного интеллекта. Могу показать демо?"},
            {"speaker": Speaker.USER, "text": "Да, интересно посмотреть. Когда можете показать?"},
            {"speaker": Speaker.ASSISTANT, "text": "Отлично! Предлагаю завтра в 15:00. Подходит?"},
            {"speaker": Speaker.USER, "text": "Да, подходит. Жду."},
        ]
    },
    {
        "disposition": FinalDisposition.NEUTRAL,
        "summary": "Разговор прошел нейтрально, клиент попросил информацию на почту",
        "interest": "получить информацию на почту",
        "transcript": [
            {"speaker": Speaker.ASSISTANT, "text": "Здравствуйте! HALO, автоматизация клиентского сервиса."},
            {"speaker": Speaker.USER, "text": "Да, слушаю."},
            {"speaker": Speaker.ASSISTANT, "text": "Хотел бы рассказать о нашем решении для автоматизации."},
            {"speaker": Speaker.USER, "text": "Хорошо, пришлите информацию на почту."},
        ]
    },
]


# Demo chat scenarios (follow-up messages)
CHAT_SCENARIOS = [
    {
        "summary": "Follow-up с коммерческим предложением",
        "messages": [
            {
                "from": "assistant",
                "text": "Спасибо за разговор! Как и обещала, отправляю коммерческое предложение. В нем вы найдете детальную информацию о тарифах и возможностях нашей платформы. Если возникнут вопросы — пишите, всегда на связи! 📄"
            }
        ]
    },
    {
        "summary": "Follow-up с подтверждением встречи",
        "messages": [
            {
                "from": "assistant",
                "text": "Отлично пообщались! Напоминаю: наша встреча назначена на завтра в 15:00. Я вышлю вам ссылку на видеоконференцию. До встречи! 👋"
            }
        ]
    },
    {
        "summary": "Follow-up с дополнительной информацией",
        "messages": [
            {
                "from": "assistant",
                "text": "Благодарю за уделенное время! Отправляю вам ссылку на запись вебинара, где мы подробно показываем возможности HALO. Также прикрепляю кейсы наших клиентов. Буду рада ответить на вопросы! 🎯"
            }
        ]
    },
    {
        "summary": "Follow-up с предложением бесплатного пилота",
        "messages": [
            {
                "from": "assistant",
                "text": "Спасибо за разговор! Я подумала, что вам может быть интересен бесплатный пилот нашей системы на 14 дней. Это отличная возможность протестировать все возможности без обязательств. Интересно? ✨"
            }
        ]
    },
    {
        "summary": "Follow-up с благодарностью",
        "messages": [
            {
                "from": "assistant",
                "text": "Благодарю за время! Если ситуация изменится и вам понадобится автоматизация клиентского сервиса — буду рада помочь. Всего доброго! 😊"
            }
        ]
    },
]


PHONE_PREFIXES = ["+7916", "+7903", "+7926", "+7985", "+7495", "+7812", "+7964"]


def generate_phone() -> str:
    """Generate a random Russian phone number."""
    prefix = random.choice(PHONE_PREFIXES)
    number = "".join([str(random.randint(0, 9)) for _ in range(7)])
    return f"{prefix}{number}"


def mask_phone(phone: str) -> str:
    """Mask phone number for display."""
    # +79161234567 -> +7 9XX XXX-12-34
    if len(phone) < 11:
        return phone
    return f"{phone[:2]} {phone[2]}XX XXX-{phone[-4:-2]}-{phone[-2:]}"


def generate_demo_calls(count: int = 50) -> list[DemoCall]:
    """Generate demo calls with realistic data."""
    demo_calls = []
    now = datetime.utcnow()

    for i in range(count):
        # Random timestamp in the past 30 days
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        created_at = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

        # Random scenario
        scenario = random.choice(CALL_SCENARIOS)

        # Random duration between 30 and 180 seconds
        duration_sec = random.randint(30, 180)

        # Generate phone
        phone = generate_phone()
        phone_masked = mask_phone(phone)

        # Build transcript
        transcript = []
        for turn in scenario["transcript"]:
            transcript.append(DialogTurn(
                speaker=turn["speaker"],
                text=turn["text"],
                timestamp=created_at
            ))

        # CRM record
        crm_record = CRMRecord(
            status="added",
            interest=scenario["interest"],
            telegram_link_sent=random.choice([True, False]),
            telegram_connected=random.choice([True, False])
        )

        call = DemoCall(
            id=uuid4(),
            is_demo=True,
            phone=phone,
            phone_masked=phone_masked,
            created_at=created_at,
            duration_sec=duration_sec,
            disposition=scenario["disposition"],
            summary=scenario["summary"],
            transcript=transcript,
            crm_record=crm_record
        )

        demo_calls.append(call)

    # Sort by created_at descending (newest first)
    demo_calls.sort(key=lambda x: x.created_at, reverse=True)

    return demo_calls


def generate_demo_chats(count: int = 50) -> list[DemoChat]:
    """Generate demo chats with follow-up messages."""
    demo_chats = []
    now = datetime.utcnow()

    for i in range(count):
        # Random timestamp in the past 30 days
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        created_at = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

        # Random scenario
        scenario = random.choice(CHAT_SCENARIOS)

        # Build messages
        messages = []
        for msg in scenario["messages"]:
            messages.append(ChatMessage(
                from_=msg["from"],
                text=msg["text"],
                timestamp=created_at
            ))

        chat = DemoChat(
            id=uuid4(),
            is_demo=True,
            call_id=None,
            created_at=created_at,
            summary=scenario["summary"],
            messages=messages
        )

        demo_chats.append(chat)

    # Sort by created_at descending (newest first)
    demo_chats.sort(key=lambda x: x.created_at, reverse=True)

    return demo_chats


# Generate demo data on module import
DEMO_CALLS = generate_demo_calls(50)
DEMO_CHATS = generate_demo_chats(50)
