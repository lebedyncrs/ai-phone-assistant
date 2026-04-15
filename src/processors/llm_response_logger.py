from loguru import logger
from pipecat.frames.frames import Frame, LLMFullResponseEndFrame, LLMTextFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class LLMResponseLogger(FrameProcessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._parts: list[str] = []

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, LLMTextFrame):
            self._parts.append(frame.text)
        elif isinstance(frame, LLMFullResponseEndFrame):
            if self._parts:
                logger.info(f"LLM: {''.join(self._parts)}")
                self._parts.clear()
        await self.push_frame(frame, direction)
