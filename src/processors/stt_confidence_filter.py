from loguru import logger
from pipecat.frames.frames import Frame, TranscriptionFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from src.config import EMPTY_TURN_FALLBACK_AFTER, STT_MIN_CONFIDENCE


class STTConfidenceFilter(FrameProcessor):
    """Drops TranscriptionFrames whose Deepgram confidence falls below the threshold.
    Injects a fallback transcription after consecutive turns with no usable transcript
    to prevent the bot from silently freezing."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._user_speaking = False
        self._transcription_passed = False
        self._empty_turns = 0

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, UserStartedSpeakingFrame):
            self._user_speaking = True
            self._transcription_passed = False
        elif isinstance(frame, UserStoppedSpeakingFrame):
            if self._user_speaking and not self._transcription_passed:
                self._empty_turns += 1
                logger.debug(
                    f"STTConfidenceFilter: empty turn #{self._empty_turns} "
                    f"(no usable transcript received)"
                )
                if self._empty_turns >= EMPTY_TURN_FALLBACK_AFTER:
                    self._empty_turns = 0
                    fallback = TranscriptionFrame(text="[cisza]", user_id="", timestamp="")
                    logger.debug("STTConfidenceFilter: injecting fallback transcription")
                    await self.push_frame(fallback, direction)
            else:
                self._empty_turns = 0
            self._user_speaking = False
        elif isinstance(frame, TranscriptionFrame):
            if frame.result is not None:
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
            self._transcription_passed = True

        await self.push_frame(frame, direction)
