import os
from typing import Any

from loguru import logger
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from pipecat.utils.tracing.setup import setup_tracing

_TRACING_INITIALIZED = False


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def init_tracing() -> bool:
    """Initialize OpenTelemetry tracing once per process."""
    global _TRACING_INITIALIZED

    if _TRACING_INITIALIZED:
        return True

    if not _is_truthy(os.getenv("ENABLE_TRACING", "false")):
        return False

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    insecure = _is_truthy(os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true"))
    service_name = os.getenv("OTEL_SERVICE_NAME", "voice-assistant")
    console_export = _is_truthy(os.getenv("OTEL_CONSOLE_EXPORT", "false"))

    exporter = OTLPSpanExporter(
        endpoint=endpoint,
        insecure=insecure,
    )

    setup_tracing(
        service_name=service_name,
        exporter=exporter,
        console_export=console_export,
    )
    _TRACING_INITIALIZED = True
    logger.info("OpenTelemetry tracing enabled for service '{}'", service_name)
    return True


def tracing_context(call_sid: str | None) -> tuple[str | None, dict[str, Any] | None]:
    """Build optional conversation metadata for tracing spans."""
    if not call_sid:
        return None, None
    return call_sid, {"call.sid": call_sid}
