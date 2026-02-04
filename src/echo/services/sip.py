from __future__ import annotations

import asyncio
import json

from livekit import api
from livekit.protocol.egress import AzureBlobUpload, EncodedFileOutput, RoomCompositeEgressRequest
from livekit.protocol.sip import CreateSIPParticipantRequest

import echo.config as cfg
import echo.events.v1 as events
from echo.logger import configure_logger

log = configure_logger(__name__)


class SipService:
    def __init__(self) -> None:
        self.lk_api = api.LiveKitAPI(
            url=cfg.LIVEKIT_URL,
            api_key=cfg.LIVEKIT_API_KEY,
            api_secret=cfg.LIVEKIT_API_SECRET,
        )

    async def close(self) -> None:
        await self.lk_api.aclose()  # type: ignore[no-untyped-call]

    async def is_phone_active(self, phone_number: str) -> bool:
        try:
            req = api.ListRoomsRequest()
            res = await self.lk_api.room.list_rooms(req)

            for room in res.rooms:
                if not room.metadata:
                    continue
                try:
                    meta = json.loads(room.metadata)
                    if meta.get("user_phone") == phone_number:
                        return True
                except json.JSONDecodeError:
                    continue
            return False
        except Exception as e:
            log.error(f"Error checking active phone status: {e}", exc_info=True)
            return False

    async def wait_until_line_free(self, phone_number: str, max_retries: int = 10, wait_seconds: int = 30) -> bool:
        for i in range(max_retries):
            is_busy = await self.is_phone_active(phone_number)
            if not is_busy:
                return True

            log.warning(f"Line busy {phone_number}. Retry {i+1}/{max_retries} in {wait_seconds}s...")
            await asyncio.sleep(wait_seconds)

        return False

    async def create_room_for_call(self, event: events.StartSessionRequest) -> str:
        room_name = f"room-{event.room_id}"

        await self.lk_api.room.create_room(
             api.CreateRoomRequest(name=room_name, empty_timeout=60)
        )

        meta_payload = json.dumps({
            "ai_phone": cfg.SIP_NUMBER,
            "opportunity_id": event.opportunity_id,
            "user_phone": event.phone_number,
            "created_at": event.timestamp.isoformat()
        })

        await self.lk_api.room.update_room_metadata(
            api.UpdateRoomMetadataRequest(room=room_name, metadata=meta_payload)
        )

        return room_name

    async def initiate_sip_call(self, room_name: str, event: events.StartSessionRequest) -> None:
        log.info(f"Initiating SIP call to {event.phone_number} in room {room_name}")

        try:
            sip_request = CreateSIPParticipantRequest(
                sip_trunk_id=cfg.SIP_TRUNK_ID,
                sip_number=cfg.SIP_NUMBER,
                sip_call_to=event.phone_number,
                room_name=room_name,
                participant_identity=f"sip-{event.opportunity_id}",
                participant_name=event.participant_name,
                krisp_enabled=True,
                wait_until_answered=True,
            )

            sip_participant = await self.lk_api.sip.create_sip_participant(sip_request)
            log.info(f"Call answered. Participant ID: {sip_participant.participant_id}")

            await self._start_recording(room_name, event.room_id)

        except Exception as e:
            log.error(f"Error in call {room_name}: {e}", exc_info=True)
            try:
                await self.cleanup_room(room_name)
            except Exception as delete_err:
                log.error(f"Error deleting room after call failure: {delete_err}")
            raise e

    async def cleanup_room(self, room_name: str) -> None:
        try:
            await self.lk_api.room.delete_room(api.DeleteRoomRequest(room=room_name))
        except Exception as e:
            log.error(f"Error deleting room {room_name}: {e}")

    @classmethod
    async def run_background_call(cls, room_name: str, event: events.StartSessionRequest) -> None:
        service = cls()
        try:
            await service.initiate_sip_call(room_name, event)
        except Exception as e:
            log.error(f"Error in background task for {room_name}: {e}")
        finally:
            await service.close()

    async def _start_recording(self, room_name: str, room_id: str) -> None:
        egress_request = RoomCompositeEgressRequest(
            room_name=room_name,
            audio_only=True,
            audio_mixing="DEFAULT_MIXING",
            file_outputs=[
                EncodedFileOutput(
                    filepath=(f"recordings/{room_id}/recording.ogg"),
                    azure=AzureBlobUpload(
                        account_name=cfg.AZURE_ACCOUNT_NAME,
                        account_key=cfg.AZURE_ACCOUNT_KEY,
                        container_name=cfg.AZURE_CONTAINER,
                    ),
                )
            ],
        )

        await self.lk_api.egress.start_room_composite_egress(egress_request)
