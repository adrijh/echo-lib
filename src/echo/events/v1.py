from datetime import UTC, datetime
from typing import Annotated, Any, Literal, cast
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, TypeAdapter, ValidationError, field_serializer, field_validator

from echo.utils.capabilities import Capabilities


class BaseEvent(BaseModel):
    version: Literal["v1"] = Field(default="v1", frozen=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

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


class SessionEvent(BaseEvent):
    thread_id: UUID = Field(default_factory=uuid4)
    opportunity_id: str
    capabilities: Capabilities = Field(default_factory=Capabilities)


class SessionStarted(SessionEvent):
    type: Literal["session_started"] = Field(default="session_started", frozen=True)
    room_id: str


class SessionEnded(SessionEvent):
    type: Literal["session_ended"] = Field(default="session_ended", frozen=True)
    room_id: str
    report_url: str


class RunContext(SessionEvent):
    type: Literal["run_context"] = Field(default="run_context", frozen=True)
    room_id: str
    report_url: str

class RunEvaluations(SessionEvent):
    type: Literal["run_evaluations"] = Field(default="run_evaluations", frozen=True)
    room_id: str
    report_url: str


class StartSessionRequest(SessionEvent):
    type: Literal["start_session_request"] = Field(default="start_session_request", frozen=True)
    room_id: str
    phone_number: str
    market: str
    first_name: str
    last_name: str
    agent_name: str | None = None


class SendWhatsappTemplate(SessionEvent):
    type: Literal["send_whatsapp_template"] = Field(default="send_whatsapp_template", frozen=True)
    phone_number: str


class WhatsappMessageReceived(SessionEvent):
    type: Literal["whatsapp_message_received"] = Field(default="whatsapp_message_received", frozen=True)


class CreateWhatsappSummary(SessionEvent):
    type: Literal["create_whatsapp_summary"] = Field(default="create_whatsapp_summary", frozen=True)


class ScheduleCall(BaseEvent):
    type: Literal["schedule_call"] = Field(default="schedule_call", frozen=True)
    target: Literal["ai", "asesor"]
    thread_id: UUID = Field(default_factory=uuid4)
    datetime: str
    first_name: str
    last_name: str
    phone_number: str


class ProcessLivekitEvent(BaseEvent):
    type: Literal["process_livekit_event"] = Field(default="process_livekit_event", frozen=True)
    body: str


class UpdateCampaignStatus(SessionEvent):
    type: Literal["update_campaign_status"] = "update_campaign_status"
    phone_number: str
    status: str
    reason: str | None = None


class FetchTranscriptions(BaseEvent):
    type: Literal["fetch_transcriptions"] = "fetch_transcriptions"
    payload: dict[str, Any] = Field(default_factory=dict)


class SendSalesforceCoupon(BaseEvent):
    type: Literal["send_salesforce_coupon"] = "send_salesforce_coupon"
    data: dict[str, Any] = Field(default_factory=dict)
    opportunity_id: str


SessionEventDiscriminator = Annotated[
    SessionStarted
    | SessionEnded
    | RunContext
    | RunEvaluations
    | StartSessionRequest
    | SendWhatsappTemplate
    | WhatsappMessageReceived
    | CreateWhatsappSummary
    | ScheduleCall
    | ProcessLivekitEvent
    | UpdateCampaignStatus
    | FetchTranscriptions
    | SendSalesforceCoupon,
    Field(discriminator="type"),
]

SessionEventAdapter = TypeAdapter[SessionEvent](SessionEventDiscriminator)


def deserialize_event(body: bytes) -> SessionEventDiscriminator:
    try:
        event = cast(SessionEventDiscriminator, SessionEventAdapter.validate_json(body))
        return event
    except ValidationError as exc:
        raise ValueError("Invalid session event") from exc
