import os
from collections.abc import Mapping
from uuid import uuid4

from opentelemetry import _logs, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
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


def setup_tracing(
    *,
    service_name: str,
    attributes: Mapping[str, str] | None = None,
    collector_endpoint: str | None = None,
) -> TracerProvider:
    collector_endpoint = collector_endpoint or os.environ["COLLECTOR_ENDPOINT"]
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


def setup_logging(
    *,
    service_name: str,
    attributes: Mapping[str, str] | None = None,
    collector_endpoint: str | None = None,
) -> LoggerProvider:
    collector_endpoint = collector_endpoint or os.environ["COLLECTOR_ENDPOINT"]
    resource = Resource.create(
        {
            "service.name": service_name,
            **(attributes or {}),
        }
    )

    logger_provider = _logs.get_logger_provider()
    if isinstance(logger_provider, LoggerProvider):
        return logger_provider

    logger_provider = LoggerProvider(resource=resource)

    exporter = OTLPLogExporter(endpoint=collector_endpoint)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(exporter)
    )

    _logs.set_logger_provider(logger_provider)

    return logger_provider
