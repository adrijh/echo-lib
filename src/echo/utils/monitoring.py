import os
from uuid import uuid4
from collections.abc import Mapping

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_job_tracing(
    service_name: str,
    endpoint: str = "",
    attributes: dict[str, str] | None = None,
) -> TracerProvider:
    attributes = attributes or {"langfuse.session.id": str(uuid4())}
    endpoint = endpoint or os.environ["COLLECTOR_ENDPOINT"]

    trace_provider = setup_tracing(
        service_name=service_name,
        attributes=attributes,
        collector_endpoint=endpoint,
    )
    return trace_provider

    # async def flush_trace() -> None:
    #     trace_provider.force_flush()

    # ctx.add_shutdown_callback(flush_trace)


def setup_tracing(
    *,
    service_name: str,
    attributes: Mapping[str, str] | None = None,
    collector_endpoint: str,
) -> TracerProvider:
    resource = Resource.create(
        {
            "service.name": service_name,
            **(attributes or {}),
        }
    )

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=collector_endpoint)))
    trace.set_tracer_provider(tracer_provider)

    return tracer_provider
