from __future__ import annotations

from collections.abc import Awaitable
from typing import TYPE_CHECKING, Any

from livekit.agents import (
    AgentServer,
    cli,
)
from livekit.agents.worker import ServerType

from echo.utils.monitoring import setup_job_tracing

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from livekit.agents import JobContext, JobRequest


class VoiceAgent:
    def __init__(
        self,
        entrypoint: Callable[[JobContext], Awaitable[None]],
        *,
        agent_name: str,
        type: ServerType = ServerType.ROOM,
        on_request: Callable[[JobRequest], Any] | None = None,
        on_session_end: Callable[[JobContext], Any] | None = None,
    ) -> None:
        self.agent_name = agent_name
        self.server = self._setup_server()
        self.entrypoint = self.server.rtc_session(
            func=self._tracing_decorator(entrypoint),
            agent_name=agent_name,
            type=type,
            on_request=on_request,
            on_session_end=on_session_end,
        )

    def _setup_server(self) -> AgentServer:
        server = AgentServer(
            prometheus_port=4123,
            job_memory_warn_mb=700,
        )
        return server

    def _tracing_decorator(
        self, entrypoint: Callable[[JobContext], Awaitable[None]]
    ) -> Callable[[JobContext], Awaitable[None]]:
        async def inner(ctx: JobContext) -> None:
            service_name = f"echo-{self.agent_name}"
            trace_provider = setup_job_tracing(service_name)

            async def flush_trace() -> None:
                trace_provider.force_flush()

            entrypoint(ctx)

            ctx.add_shutdown_callback(flush_trace)

        return inner

    def run_app(self) -> None:
        cli.run_app(self.server)
