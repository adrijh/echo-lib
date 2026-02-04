from __future__ import annotations

import asyncio
import json

from livekit import api
from livekit.api.twirp_client import TwirpError
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

    async def _get_active_phones(self) -> tuple[set[str], dict[str, int]]:
        user_phones: set[str] = set()
        ai_phones_usage: dict[str, int] = {n: 0 for n in cfg.SIP_NUMBER}
        try:
            req = api.ListRoomsRequest()
            res = await self.lk_api.room.list_rooms(req)

            for room in res.rooms:
                if not room.metadata:
                    continue
                try:
                    meta = json.loads(room.metadata)
                    if u := meta.get("user_phone"):
                        user_phones.add(u)
                    if a := meta.get("ai_phone"):
                        ai_phones_usage[a] = ai_phones_usage.get(a, 0) + 1
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            log.error(f"Error checking active phones: {e}", exc_info=True)
        return user_phones, ai_phones_usage

    async def allocate_resources(
        self,
        phone_number: str,
        max_retries: int = cfg.SIP_CALL_MAX_RETRIES,
        wait_seconds: int = cfg.SIP_CALL_WAIT_SECONDS
    ) -> str | None:

        for i in range(max_retries):
            active_users, ai_usage = await self._get_active_phones()

            if phone_number in active_users:
                log.warning(f"User {phone_number} busy. Retry {i+1}/{max_retries} in {wait_seconds}s...")
                await asyncio.sleep(wait_seconds)
                continue

            available_ai = next(
                (n for n in cfg.SIP_NUMBER if ai_usage.get(n, 0) < cfg.SIP_MAX_CONCURRENT_CALLS),
                None
            )

            if not available_ai:
                log.warning(f"All AI lines busy (At capacity). Retry {i+1}/{max_retries} in {wait_seconds}s...")
                await asyncio.sleep(wait_seconds)
                continue

            return available_ai

        return None

    async def create_room_for_call(self, event: events.StartSessionRequest, ai_number: str) -> str:
        room_name = f"room-{event.room_id}"

        await self.lk_api.room.create_room(
             api.CreateRoomRequest(name=room_name, empty_timeout=60)
        )

        meta_payload = json.dumps({
            "ai_phone": ai_number,
            "opportunity_id": event.opportunity_id,
            "user_phone": event.phone_number,
            "created_at": event.timestamp.isoformat()
        })

        await self.lk_api.room.update_room_metadata(
            api.UpdateRoomMetadataRequest(room=room_name, metadata=meta_payload)
        )

        return room_name

    async def initiate_sip_call(self, room_name: str, event: events.StartSessionRequest, ai_number: str) -> None:
        log.info(f"Initiating call to  {event.participant_name} - {event.phone_number} from {ai_number} in room {room_name}")

        try:
            sip_request = CreateSIPParticipantRequest(
                sip_trunk_id=cfg.SIP_TRUNK_ID,
                sip_number=ai_number,
                sip_call_to=event.phone_number,
                room_name=room_name,
                participant_identity=f"sip-{event.opportunity_id}",
                participant_name=event.participant_name,
                krisp_enabled=True,
                wait_until_answered=True,
            )

            await self.lk_api.sip.create_sip_participant(sip_request)
            log.info(f"Call answered. Participant {event.participant_name} number: {event.phone_number}")

            await self._start_recording(room_name, event.room_id)

        except TwirpError as e:
            if ("Busy Here" in str(e) or
                e.code == "unavailable" or
                (e.metadata and e.metadata.get("sip_status_code") == "486")):
                log.warning(
                    f"User {event.participant_name} busy or unavailable ({event.phone_number}). "
                    f"Code: 486/Busy. Room {room_name} will be closed."
                )
                await self.cleanup_room(room_name)
                return

            log.error(f"Twirp Error in call {room_name}: {e}", exc_info=True)
            await self.cleanup_room(room_name)
            raise e

        except Exception as e:
            log.error(f"Unexpected Error in call {room_name}: {e}", exc_info=True)
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
    async def run_background_call(cls, room_name: str, event: events.StartSessionRequest, ai_number: str) -> None:
        service = cls()
        try:
            await service.initiate_sip_call(room_name, event, ai_number)
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
