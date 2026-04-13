import asyncio
import io
import wave
import os
from typing import Optional, cast

from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer, VADParams
from pipecat.frames.frames import Frame, LLMRunFrame, TranscriptionFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.processors.audio.audio_buffer_processor import AudioBufferProcessor
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.runner.types import RunnerArguments
from pipecat.services.cartesia.tts import GenerationConfig
from src.llm_tools import TOOLS_SCHEMA, register_tools
from src.prompts import SYSTEM_INSTRUCTION
from src.services.open_api_service import summarize_conversation
from src.services.telegram_service import send_message, send_voice

from pipecat.runner.utils import parse_telephony_websocket
from src.dto.call_info import CallInfo
from src.services.twilio_service import get_call_info
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)

from src.dto.call_data import CallData

load_dotenv(override=True)

STT_MIN_CONFIDENCE = 0.65


class STTConfidenceFilter(FrameProcessor):
    """Drops TranscriptionFrames whose Deepgram confidence falls below the threshold."""

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, TranscriptionFrame) and frame.result is not None:
            try:
                confidence = frame.result.channel.alternatives[0].confidence
                if confidence < STT_MIN_CONFIDENCE:
                    logger.debug(
                        f"STTConfidenceFilter: dropped '{frame.text}' "
                        f"(confidence={confidence:.2f} < {STT_MIN_CONFIDENCE})"
                    )
                    return
            except (AttributeError, IndexError):
                pass
        await self.push_frame(frame, direction)


async def run_bot(transport: BaseTransport, handle_sigint: bool, testing: bool, call_info: Optional[CallInfo] = None, call_sid: Optional[str] = None):
    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        settings=OpenAILLMService.Settings(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
            system_instruction=SYSTEM_INSTRUCTION,
        ),
    )

    stt = DeepgramSTTService(
        api_key=os.getenv("DEEPGRAM_API_KEY", ""),
        settings=DeepgramSTTService.Settings(
            language="pl",
        ),
    )

    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY", ""),
        settings=CartesiaTTSService.Settings(
            voice=os.getenv("CARTESIA_VOICE_ID", ""),
            model="sonic-3",
            language=os.getenv("CARTESIA_LANGUAGE", "pl"),
            generation_config=GenerationConfig(
                speed=1.2,
            ),
        ),
        push_silence_after_stop=testing,
    )

    audiobuffer = AudioBufferProcessor(num_channels=1)

    context = LLMContext()
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2))
        ),
    )

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            STTConfidenceFilter(),
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
            audiobuffer,
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=8000,
            audio_out_sample_rate=8000,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    context.set_tools(TOOLS_SCHEMA)
    register_tools(llm, task, context, call_sid=call_sid)

    @audiobuffer.event_handler("on_audio_data")
    async def on_audio_data(buffer, audio, sample_rate, num_channels):
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(num_channels)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio)
        from_number = call_info.from_number if call_info else "unknown"
        try:
            await send_voice(buf.getvalue(), f"📼 Recording ({from_number})")
        except Exception as e:
            logger.error(f"Failed to send recording: {e}")

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected, greeting user")
        from_number = call_info.from_number if call_info else "unknown"
        forwarded_from = call_info.forwarded_from if call_info else "unknown"
        asyncio.create_task(send_message(f"📞 Call started from: {from_number}, forwarded from: {forwarded_from}"))
        await audiobuffer.start_recording()
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client) -> None:
        await audiobuffer.stop_recording()
        try:
            messages = context.get_messages()
            if messages:
                summary = await summarize_conversation(messages)
                from_number = call_info.from_number if call_info else "unknown"
                await send_message(f"📋 Call summary ({from_number}):\n{summary}")
        except Exception as e:
            logger.error(f"Failed to generate call summary: {e}")
        await task.cancel()

    # We use `handle_sigint=False` because `uvicorn` is controlling keyboard
    # interruptions. We use `force_gc=True` to force garbage collection after
    # the runner finishes running a task which could be useful for long running
    # applications with multiple clients connecting.
    runner = PipelineRunner(handle_sigint=handle_sigint, force_gc=True)

    await runner.run(task)


async def bot(runner_args: RunnerArguments, testing: Optional[bool] = False):
    """Main bot entry point compatible with Pipecat Cloud."""
    from pipecat.runner.types import SmallWebRTCRunnerArguments

    if isinstance(runner_args, SmallWebRTCRunnerArguments):
        from pipecat.transports.base_transport import TransportParams
        from pipecat.transports.network.small_webrtc import SmallWebRTCTransport

        transport = SmallWebRTCTransport(
            webrtc_connection=runner_args.webrtc_connection,
            params=TransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
            ),
        )
        await run_bot(transport, handle_sigint=False, testing=True)
        return

    result = await parse_telephony_websocket(runner_args.websocket)
    call_data = cast(CallData, result[1])

    # Fetch call information from Twilio REST API
    # With the call information, you can make a request to your API to get the user's information
    # and inject that information into your bot's configuration.
    call_info = await get_call_info(call_data["call_id"])
    if call_info:
        logger.info(f"Call from: {call_info.from_number} to: {call_info.to_number}, forwarded from: {call_info.forwarded_from}")

    serializer = TwilioFrameSerializer(
        stream_sid=call_data["stream_id"],
        call_sid=call_data["call_id"],
        account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
        auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
    )

    transport = FastAPIWebsocketTransport(
        websocket=runner_args.websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            serializer=serializer,
        ),
    )

    await run_bot(transport, runner_args.handle_sigint, testing, call_info, call_sid=call_data["call_id"])


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
