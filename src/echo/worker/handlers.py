from livekit import api
from livekit.protocol.egress import AzureBlobUpload, EncodedFileOutput, RoomCompositeEgressRequest
from livekit.protocol.sip import CreateSIPParticipantRequest

import echo.config as cfg
import echo.events.v1 as events
from echo.logger import configure_logger
from echo.utils import db
from echo.worker.email_asesor.main import run_email_asesor_workflow
from echo.worker.registry import register_handler

log = configure_logger(__name__)


@register_handler(events.SessionStarted)
async def set_session_start(event: events.SessionStarted) -> None:
    db.set_room_start(
        room_id=event.room_id,
        opportunity_id=event.opportunity_id,
        start_time=event.timestamp,
    )


@register_handler(events.SessionEnded)
async def set_session_ended(event: events.SessionEnded) -> None:
    db.set_room_end(
        room_id=event.room_id,
        end_time=event.timestamp,
    )

@register_handler(events.SessionEnded)
async def set_session_url(event: events.SessionEnded) -> None:
    db.set_room_report(
        room_id=event.room_id,
        report_url=event.report_url,
    )


@register_handler(events.SessionEnded)
async def create_session_summary(event: events.SessionEnded) -> None:
    event_payload = {
        "room_id": event.room_id,
        "session_blob": event.report_url,
    }

    await run_email_asesor_workflow(event_payload)


@register_handler(events.StartSessionRequest)
async def start_call(event: events.StartSessionRequest) -> None:
    log.info("Handler triggered for StartSessionRequest")
    livekit_api = api.LiveKitAPI(
        url=cfg.LIVEKIT_URL,
        api_key=cfg.LIVEKIT_API_KEY,
        api_secret=cfg.LIVEKIT_API_SECRET,
    )

    room_name = f"room-{event.room_id}"
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

        sip_participant = await livekit_api.sip.create_sip_participant(sip_request)

        log.info(f"SIP participant created: {sip_participant.participant_id}")

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

        log.info(f"Egress started: {egress_info.egress_id}")

    except Exception as e:
        log.info("Error during start_call:", e)

    finally:
        await livekit_api.aclose()  # type: ignore[no-untyped-call]
