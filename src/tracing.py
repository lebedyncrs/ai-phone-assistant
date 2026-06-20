import os
import uuid
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass

from loguru import logger

_TRACING_INITIALIZED = False


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _tracing_requested() -> bool:
    if _is_truthy(os.getenv("ENABLE_TRACING", "false")):
        return True
    return bool(os.getenv("ARIZE_SPACE_ID", "").strip() and os.getenv("ARIZE_API_KEY", "").strip())


def init_tracing() -> bool:
    """Initialize Arize AX tracing via OpenInference instrumentation."""
    global _TRACING_INITIALIZED

    if _TRACING_INITIALIZED:
        return True

    if not _tracing_requested():
        return False

    space_id = os.getenv("ARIZE_SPACE_ID", "").strip()
    api_key = os.getenv("ARIZE_API_KEY", "").strip()
    if not space_id or not api_key:
        logger.warning("Tracing requested but ARIZE_SPACE_ID or ARIZE_API_KEY is missing")
        return False

    from arize.otel import Endpoint, register
    from openinference.instrumentation.openai import OpenAIInstrumentor
    from openinference.instrumentation.pipecat import PipecatInstrumentor

    project_name = os.getenv("ARIZE_PROJECT_NAME", "voice-assistant")
    log_to_console = _is_truthy(os.getenv("OTEL_CONSOLE_EXPORT", "false"))

    endpoint: str | Endpoint = Endpoint.ARIZE_EUROPE
    endpoint_override = os.getenv("ARIZE_ENDPOINT", "").strip()
    if endpoint_override:
        endpoint = endpoint_override

    tracer_provider = register(
        space_id=space_id,
        api_key=api_key,
        project_name=project_name,
        endpoint=endpoint,
        log_to_console=log_to_console,
    )
    PipecatInstrumentor().instrument(tracer_provider=tracer_provider)
    OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)

    _TRACING_INITIALIZED = True
    logger.info("Arize AX tracing enabled for project '{}'", project_name)
    return True


def _resolve_session_id(call_sid: str | None) -> str | None:
    sid = (call_sid or "").strip()
    if sid:
        return sid
    if _TRACING_INITIALIZED:
        return f"webrtc-{uuid.uuid4()}"
    return None


@dataclass(frozen=True)
class TracingSession:
    session_id: str
    user_id: str | None = None


def build_tracing_session(
    call_sid: str | None,
    user_id: str | None = None,
) -> TracingSession | None:
    """Build session/user identifiers for Arize AX Sessions view."""
    if not _TRACING_INITIALIZED:
        return None
    session_id = _resolve_session_id(call_sid)
    if not session_id:
        return None
    uid = (user_id or "").strip() or None
    return TracingSession(session_id=session_id, user_id=uid)


def tracing_session_context(session: TracingSession | None) -> AbstractContextManager[None]:
    """Attach session.id and user.id to spans via OpenInference context."""
    if session is None:
        return nullcontext()

    from openinference.instrumentation import using_attributes

    kwargs: dict[str, str] = {"session_id": session.session_id}
    if session.user_id:
        kwargs["user_id"] = session.user_id
    return using_attributes(**kwargs)
