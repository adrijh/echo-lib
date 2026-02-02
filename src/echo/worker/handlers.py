from uuid import uuid4

from livekit import api
from livekit.protocol.egress import AzureBlobUpload, EncodedFileOutput, RoomCompositeEgressRequest
from livekit.protocol.sip import CreateSIPParticipantRequest

import echo.config as cfg
import echo.events.v1 as events
from echo.logger import configure_logger
from echo.worker.registry import register_handler

logger = configure_logger(__name__)

from echo.worker.email_asesor.main import run_email_asesor_workflow

@register_handler(events.SessionStarted)
async def set_session_start(event: events.SessionStarted) -> None:
    pass


@register_handler(events.SessionEnded)
async def set_session_ended(event: events.SessionEnded) -> None:
    pass


@register_handler(events.SessionEnded)
async def create_session_summary(event: events.SessionEnded) -> None:
    logger.info(f"Handler triggered for SessionEnded: {event.session_id}")
    
    event_payload = {
        "room_id": event.session_id,
        "session_blob": event.transcript_uri,
    }
    
    await run_email_asesor_workflow(event_payload)

@register_handler(events.StartSessionRequest)
async def start_call(event: events.StartSessionRequest) -> None:
    livekit_api = api.LiveKitAPI()

    room_name = f"{event.room_id}-{uuid4()}"
    phone_number = event.metadata.get("phone_number")
    participant_name = event.metadata.get("participant_name")
    try:
        sip_request = CreateSIPParticipantRequest(
            sip_trunk_id=cfg.SIP_TRUNK_ID,
            sip_number=cfg.SIP_NUMBER,
            sip_call_to=phone_number,
            room_name=room_name,
            participant_identity=f"sip-{event.opportunity_id}",
            participant_name=participant_name,
            krisp_enabled=True,
            wait_until_answered=True,
        )

        sip_participant = await livekit_api.sip.create_sip_participant(sip_request)

        logger.info(f"SIP participant created: {sip_participant.participant_id}")

        egress_request = RoomCompositeEgressRequest(
            room_name=room_name,
            audio_only=True,
            audio_mixing="DEFAULT_MIXING",
            file_outputs=[
                EncodedFileOutput(
                    filepath=(f"recordings/" f"{event.room_id}-{room_name}-{{time}}.ogg"),
                    azure=AzureBlobUpload(
                        account_name=cfg.AZURE_ACCOUNT_NAME,
                        account_key=cfg.AZURE_ACCOUNT_KEY,
                        container_name=cfg.AZURE_CONTAINER,
                    ),
                )
            ],
        )

        egress_info = await livekit_api.egress.start_room_composite_egress(egress_request)

        logger.info(f"Egress started: {egress_info.egress_id}")

    except Exception as e:
        logger.info("Error during start_call:", e)

        if hasattr(e, "metadata"):
            logger.info("SIP status code:", e.metadata.get("sip_status_code"))
            logger.info("SIP status message:", e.metadata.get("sip_status"))

        raise

    finally:
        await livekit_api.aclose()
