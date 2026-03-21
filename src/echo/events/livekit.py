import json
from abc import abstractmethod
from typing import Annotated, Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, field_validator


class BaseConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")


class Codec(BaseConfig):
    mime: str | None = None
    mime_type: str | None = Field(alias="mimeType", default=None)
    mid: str | None = None
    cid: str | None = None


class Version(BaseConfig):
    unix_micro: str = Field(alias="unixMicro")


class Permission(BaseConfig):
    can_subscribe: bool | None = Field(default=None, alias="canSubscribe")
    can_publish: bool | None = Field(default=None, alias="canPublish")
    can_publish_data: bool | None = Field(default=None, alias="canPublishData")
    can_update_metadata: bool | None = Field(default=None, alias="canUpdateMetadata")
    hidden: bool | None = None
    recorder: bool | None = None
    agent: bool | None = None


class Room(BaseConfig):
    sid: str
    name: str
    empty_timeout: int | None = Field(default=None, alias="emptyTimeout")
    departure_timeout: int | None = Field(default=None, alias="departureTimeout")
    creation_time: str | None = Field(default=None, alias="creationTime")
    creation_time_ms: str | None = Field(default=None, alias="creationTimeMs")
    turn_password: str | None = Field(default=None, alias="turnPassword")
    enabled_codecs: list["Codec"] | None = Field(default=None, alias="enabledCodecs")
    num_participants: int | None = Field(default=None, alias="numParticipants")
    num_publishers: int | None = Field(default=None, alias="numPublishers")
    active_recording: bool | None = Field(default=None, alias="activeRecording")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata", mode="before")
    @classmethod
    def parse_metadata(cls, v: Any) -> dict[str, Any]:
        if isinstance(v, str):
            return json.loads(v) if v else {}

        return cast(dict[str, Any], v)


class Participant(BaseConfig):
    sid: str | None = None
    identity: str | None = None
    state: str | None = None
    joined_at: str | None = Field(default=None, alias="joinedAt")
    joined_at_ms: str | None = Field(default=None, alias="joinedAtMs")
    name: str | None = None
    version: int | None = None
    permission: Permission | None = None
    kind: Literal["SIP", "EGRESS", "AGENT", "INGRESS", "STANDARD"] | None = None
    attributes: dict[str, str] | None = None
    is_publisher: bool | None = Field(default=None, alias="isPublisher")
    disconnect_reason: str | None = Field(default=None, alias="disconnectReason")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata", mode="before")
    @classmethod
    def parse_metadata(cls, v: Any) -> dict[str, Any]:
        if isinstance(v, str):
            return json.loads(v) if v else {}

        return cast(dict[str, Any], v)


class Track(BaseConfig):
    sid: str | None = None
    name: str | None = None
    source: str | None = None
    mime_type: str | None = Field(default=None, alias="mimeType")
    mid: str | None = None
    codecs: list["Codec"] | None = None
    stream: str | None = None
    version: Version | None = None
    backup_codec_policy: str | None = Field(default=None, alias="backupCodecPolicy")


class S3Config(BaseConfig):
    access_key: str = Field(alias="accessKey")
    secret: str
    region: str
    endpoint: str
    bucket: str
    force_path_style: bool = Field(alias="forcePathStyle")


class FileOutput(BaseConfig):
    filepath: str
    s3: S3Config | None = None


class RoomComposite(BaseConfig):
    room_name: str = Field(alias="roomName")
    audio_only: bool = Field(alias="audioOnly")
    file_outputs: list[FileOutput] = Field(alias="fileOutputs")


class FileInfo(BaseConfig):
    filename: str | None = None
    started_at: str | None = Field(default=None, alias="startedAt")
    ended_at: str | None = Field(default=None, alias="endedAt")
    duration: str | None = None
    size: str | None = None
    location: str | None = None


class EgressInfo(BaseConfig):
    egress_id: str = Field(alias="egressId")
    room_id: str = Field(alias="roomId")
    room_name: str | None = Field(default=None, alias="roomName")
    status: str | None = None
    started_at: str | None = Field(default=None, alias="startedAt")
    ended_at: str | None = Field(default=None, alias="endedAt")
    updated_at: str | None = Field(default=None, alias="updatedAt")
    room_composite: RoomComposite | None = Field(default=None, alias="roomComposite")
    file: FileInfo | None = None
    file_results: list[FileInfo] | None = Field(default=None, alias="fileResults")


class BaseEvent(BaseConfig):
    id: str
    created_at: str = Field(alias="createdAt")

    @abstractmethod
    def to_compact(self) -> dict[str, Any]: ...


class RoomStartedEvent(BaseEvent):
    event: Literal["room_started"]
    room: Room

    @property
    def room_id(self) -> str:
        return self.room.sid

    def to_compact(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "id": self.id,
            "timestamp": self.room.creation_time,
        }


class RoomFinishedEvent(BaseEvent):
    event: Literal["room_finished"]
    room: Room

    @property
    def room_id(self) -> str:
        return self.room.sid

    def to_compact(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "id": self.id,
            "timestamp": self.created_at,
        }


class ParticipantJoinedEvent(BaseEvent):
    event: Literal["participant_joined"]
    room: Room
    participant: Participant

    @property
    def room_id(self) -> str:
        return self.room.sid

    def to_compact(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "id": self.id,
            "kind": self.participant.kind,
            "timestamp": self.participant.joined_at,
        }

class ParticipantLeftEvent(BaseEvent):
    event: Literal["participant_left"]
    room: Room
    participant: Participant

    @property
    def room_id(self) -> str:
        return self.room.sid

    def to_compact(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "id": self.id,
            "kind": self.participant.kind,
            "timestamp": self.created_at,
            "disconnect_reason": self.participant.disconnect_reason
        }

class TrackPublishedEvent(BaseEvent):
    event: Literal["track_published"]
    room: Room
    participant: Participant
    track: Track

    @property
    def room_id(self) -> str:
        return self.room.sid

    def to_compact(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "id": self.id,
            "timestamp": self.created_at,
        }


class TrackUnpublishedEvent(BaseEvent):
    event: Literal["track_unpublished"]
    room: Room
    participant: Participant
    track: Track

    @property
    def room_id(self) -> str:
        return self.room.sid

    def to_compact(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "id": self.id,
            "timestamp": self.created_at,
        }

class EgressStartedEvent(BaseEvent):
    event: Literal["egress_started"]
    egress_info: EgressInfo = Field(alias="egressInfo")

    @property
    def room_id(self) -> str:
        return self.egress_info.room_id

    def to_compact(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "id": self.id,
            "timestamp": self.created_at,
        }


class EgressUpdatedEvent(BaseEvent):
    event: Literal["egress_updated"]
    egress_info: EgressInfo = Field(alias="egressInfo")

    @property
    def room_id(self) -> str:
        return self.egress_info.room_id

    def to_compact(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "id": self.id,
            "timestamp": self.created_at,
        }


class EgressEndedEvent(BaseEvent):
    event: Literal["egress_ended"]
    egress_info: EgressInfo = Field(alias="egressInfo")

    @property
    def room_id(self) -> str:
        return self.egress_info.room_id

    def to_compact(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "id": self.id,
            "timestamp": self.created_at,
        }


WebhookEventDiscriminator = Annotated[
    RoomStartedEvent
    | RoomFinishedEvent
    | ParticipantJoinedEvent
    | ParticipantLeftEvent
    | TrackPublishedEvent
    | TrackUnpublishedEvent
    | EgressStartedEvent
    | EgressUpdatedEvent
    | EgressEndedEvent,
    Field(discriminator="event"),
]


WebhookEventAdapter = TypeAdapter[BaseEvent](WebhookEventDiscriminator)


def deserialize_lk_webhook_event(data: bytes | dict[str, Any]) -> WebhookEventDiscriminator:
    try:
        if isinstance(data, (bytes, str)):
            return cast(WebhookEventDiscriminator, WebhookEventAdapter.validate_json(data))

        return cast(WebhookEventDiscriminator, WebhookEventAdapter.validate_python(data))

    except ValidationError as exc:
        raise ValueError("Invalid session event") from exc
