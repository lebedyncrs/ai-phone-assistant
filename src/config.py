import os

from pipecat.services.cartesia.tts import CartesiaTTSService, GenerationConfig
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService

from src.prompts import SYSTEM_INSTRUCTION

STT_MIN_CONFIDENCE = 0.50
EMPTY_TURN_FALLBACK_AFTER = 2


def build_llm() -> OpenAILLMService:
    return OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        settings=OpenAILLMService.Settings(
            model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
            system_instruction=SYSTEM_INSTRUCTION,
        ),
    )


def build_stt() -> DeepgramSTTService:
    return DeepgramSTTService(
        api_key=os.getenv("DEEPGRAM_API_KEY", ""),
        settings=DeepgramSTTService.Settings(
            language="pl",
        ),
    )


def build_tts(testing: bool = False) -> CartesiaTTSService:
    return CartesiaTTSService(
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
