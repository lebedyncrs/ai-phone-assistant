"""LLM tool definitions and handlers for the voice assistant."""

from __future__ import annotations

from typing import Optional

from loguru import logger
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.frames.frames import EndFrame
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.services.llm_service import FunctionCallParams
from src.services.twilio_service import hangup_call

END_CALL_TOOL_NAME = "end_call"

TOOLS_SCHEMA = ToolsSchema(
    standard_tools=[
        FunctionSchema(
            name=END_CALL_TOOL_NAME,
            description="Kończy rozmowę telefoniczną. WYWOŁAJ W TEJ SAMEJ ODPOWIEDZI co fraza pożegnalna (np. 'Do usłyszenia', 'Dziękuję i do widzenia'), gdy dzwoniący potwierdził że nie potrzebuje już nic więcej. NIE czekaj na kolejną turę — wywołaj narzędzie jednocześnie z pożegnaniem. NIGDY nie wywołuj na początku rozmowy ani przed zebraniem informacji.",
            properties={},
            required=[],
        ),
    ]
)


MIN_MESSAGES_BEFORE_END_CALL = 3


def register_tools(llm, task: PipelineTask, context: LLMContext, call_sid: Optional[str] = None) -> None:
    """Register all LLM tool handlers."""
    _end_call_triggered = False

    async def handle_end_call(params: FunctionCallParams) -> None:
        nonlocal _end_call_triggered
        message_count = len(context.get_messages())
        if message_count < MIN_MESSAGES_BEFORE_END_CALL:
            logger.warning(
                f"end_call blocked — only {message_count} messages in context "
                f"(minimum {MIN_MESSAGES_BEFORE_END_CALL} required)"
            )
            await params.result_callback(None)
            return
        if _end_call_triggered:
            logger.warning("end_call called more than once — ignoring duplicate")
            await params.result_callback(None)
            return
        _end_call_triggered = True
        logger.info(f"end_call triggered after {message_count} messages — ending call")
        await params.result_callback(None)
        if call_sid:
            await hangup_call(call_sid)
        await task.queue_frame(EndFrame())

    llm.register_function(END_CALL_TOOL_NAME, handle_end_call)
