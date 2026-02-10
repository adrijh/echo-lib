from datetime import UTC, datetime
from typing import Annotated, Any, Literal, cast
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, TypeAdapter, ValidationError, field_serializer, field_validator


class SessionEvent(BaseModel):
    version: Literal["v1"] = Field(default="v1", frozen=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)
    thread_id: UUID = Field(default_factory=uuid4)
    opportunity_id: str

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_unix_ts(cls, v: float | int | datetime) -> datetime:
        if isinstance(v, int | float):
            return datetime.fromtimestamp(v, tz=UTC)

        return v

    @field_validator("timestamp")
    @classmethod
    def enforce_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")

        return v.astimezone(UTC)

    @field_serializer("timestamp")
    def serialize_unix_ts(self, v: datetime) -> float:
        return v.timestamp()


class SessionStarted(SessionEvent):
    type: Literal["session_started"] = Field(default="session_started", frozen=True)
    room_id: str


class SessionEnded(SessionEvent):
    type: Literal["session_ended"] = Field(default="session_ended", frozen=True)
    room_id: str
    report_url: str


class StartSessionRequest(SessionEvent):
    type: Literal["start_session_request"] = Field(default="start_session_request", frozen=True)
    room_id: str
    phone_number: str
    first_name: str
    last_name: str


class SendWhatsappTemplate(SessionEvent):
    type: Literal["send_whatsapp_template"] = Field(default="send_whatsapp_template", frozen=True)
    phone_number: str


class WhatsappMessageReceived(SessionEvent):
    type: Literal["whatsapp_message_received"] = Field(default="whatsapp_message_received", frozen=True)


SessionEventDiscriminator = Annotated[
    SessionStarted | SessionEnded | StartSessionRequest | SendWhatsappTemplate | WhatsappMessageReceived,
    Field(discriminator="type"),
]


SessionEventAdapter = TypeAdapter[SessionEvent](SessionEventDiscriminator)


def deserialize_event(body: bytes) -> SessionEventDiscriminator:
    try:
        event = cast(SessionEventDiscriminator, SessionEventAdapter.validate_json(body))
        return event
    except ValidationError as exc:
        raise ValueError("Invalid session event") from exc
