"""
Data models for the voice caller API.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CallStatus(str, Enum):
    """Status of a call."""
    CREATED = "created"
    DIALING = "dialing"
    NO_ANSWER = "no_answer"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class FinalDisposition(str, Enum):
    """Final disposition of a call after classification."""
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    CALL_LATER = "call_later"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class Speaker(str, Enum):
    """Speaker in a dialog."""
    USER = "user"
    ASSISTANT = "assistant"


class DialogTurn(BaseModel):
    """A single turn in the dialog."""
    speaker: Speaker
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CallSession(BaseModel):
    """Model representing a call session."""
    id: UUID = Field(default_factory=uuid4)
    phone: str
    status: CallStatus = CallStatus.CREATED
    final_disposition: Optional[FinalDisposition] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_sec: Optional[int] = None
    transcript: list[DialogTurn] = Field(default_factory=list)
    short_summary: Optional[str] = None

    # Demo settings (for Phase 2 streaming)
    demo_voice: Optional[str] = None  # Voice type (alloy, echo, etc.)
    demo_language: Optional[str] = None  # Language code (ru, uz, auto, etc.)
    demo_prompt: Optional[str] = None  # Custom assistant prompt

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v)
        }

    def add_turn(self, speaker: Speaker, text: str) -> None:
        """Add a dialog turn to the transcript."""
        turn = DialogTurn(speaker=speaker, text=text)
        self.transcript.append(turn)

    def get_transcript_text(self) -> str:
        """Get the full transcript as formatted text."""
        lines = []
        for turn in self.transcript:
            speaker_label = "Клиент" if turn.speaker == Speaker.USER else "Ассистент"
            lines.append(f"{speaker_label}: {turn.text}")
        return "\n".join(lines)

    def calculate_duration(self) -> None:
        """Calculate and set the duration of the call."""
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            self.duration_sec = int(delta.total_seconds())


# ============================================================================
# Demo Cabinet Models (NEW)
# ============================================================================

class DemoSessionStatus(str, Enum):
    """Status of a demo session."""
    INITIATED = "initiated"
    CALL_IN_PROGRESS = "call_in_progress"
    ANALYZING = "analyzing"
    GENERATING_FOLLOWUP = "generating_followup"
    SENDING_SMS = "sending_sms"
    ADDING_TO_CRM = "adding_to_crm"
    COMPLETED = "completed"
    FAILED = "failed"


class Voice(str, Enum):
    """Voice type for assistant."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class Language(str, Enum):
    """Supported languages."""
    AUTO = "auto"
    RU = "ru"  # Русский
    UZ = "uz"  # Узбекский
    TJ = "tj"  # Таджикский
    KK = "kk"  # Казахский
    KY = "ky"  # Киргизский
    TM = "tm"  # Туркменский
    AZ = "az"  # Азербайджанский
    FA_AF = "fa-af"  # Дари / Афганский
    EN = "en"  # Английский
    TR = "tr"  # Турецкий


class InteractionType(str, Enum):
    """Type of interaction."""
    CALL = "call"
    CHAT = "chat"


class Channel(str, Enum):
    """Communication channel."""
    VOICE = "voice"
    TELEGRAM = "telegram"
    SMS = "sms"


class DemoSession(BaseModel):
    """Model representing a demo session."""
    id: UUID = Field(default_factory=uuid4)
    call_id: Optional[UUID] = None
    call_id_hash: str  # Used for deep-link
    phone: str
    language: Language
    voice: Voice
    greeting: str
    prompt: str
    status: DemoSessionStatus = DemoSessionStatus.INITIATED

    # Telegram integration
    telegram_user_id: Optional[int] = None
    telegram_username: Optional[str] = None
    telegram_connected: bool = False

    # Follow-up
    followup_message: Optional[str] = None
    sms_sent: bool = False

    # Analysis results
    analysis_summary: Optional[str] = None  # Brief summary of the conversation
    analysis_interest: Optional[str] = None  # "interested", "not_interested", "maybe"
    analysis_key_points: Optional[list[str]] = None  # Key points from conversation
    transcript: Optional[list[dict]] = None  # Conversation transcript

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None
        }


class CRMRecord(BaseModel):
    """CRM record (mock visualization)."""
    status: str = "added"
    interest: Optional[str] = None
    telegram_link_sent: bool = False
    telegram_connected: bool = False


class ChatMessage(BaseModel):
    """A single message in a chat."""
    from_: str = Field(alias="from")  # "assistant" or "user"
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        populate_by_name = True


class DemoChat(BaseModel):
    """Model representing a demo chat."""
    id: UUID = Field(default_factory=uuid4)
    is_demo: bool = True
    call_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    summary: Optional[str] = None
    messages: list[ChatMessage] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None
        }


class DemoCall(BaseModel):
    """Model representing a demo call (extends CallSession concept)."""
    id: UUID = Field(default_factory=uuid4)
    is_demo: bool = True
    phone: str
    phone_masked: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    duration_sec: int
    disposition: FinalDisposition
    summary: Optional[str] = None
    transcript: list[DialogTurn] = Field(default_factory=list)
    crm_record: Optional[CRMRecord] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None
        }


class Interaction(BaseModel):
    """Model representing an interaction in the list."""
    id: str  # Can be UUID as string
    is_demo: bool
    type: InteractionType
    channel: Channel
    created_at: datetime
    disposition: Optional[FinalDisposition] = None
    summary: Optional[str] = None
    phone_masked: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Funnel(BaseModel):
    """Funnel metrics."""
    called: int
    talked: int
    interested: int
    lead: int


class Analytics(BaseModel):
    """Analytics data."""
    totals: dict = Field(default_factory=lambda: {
        "calls": 0,
        "chats": 0,
        "lead_rate": 0.0,
        "avg_call_duration_sec": 0
    })
    funnel: Funnel = Field(default_factory=lambda: Funnel(
        called=0, talked=0, interested=0, lead=0
    ))
