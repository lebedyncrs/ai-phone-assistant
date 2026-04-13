import os

import redis.asyncio as aioredis
from loguru import logger
from pipecat.frames.frames import Frame, MetricsFrame
from pipecat.metrics.metrics import LLMUsageMetricsData
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class MetricsProcessor(FrameProcessor):
    """Intercepts MetricsFrame and increments OpenAI token counters in Redis."""

    def __init__(self):
        super().__init__()
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis: aioredis.Redis = aioredis.from_url(redis_url, decode_responses=True)

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, MetricsFrame):
            for data in frame.data:
                if isinstance(data, LLMUsageMetricsData):
                    usage = data.value
                    try:
                        async with self._redis.pipeline() as pipe:
                            pipe.incrby("usage:openai:prompt_tokens", usage.prompt_tokens)
                            pipe.incrby("usage:openai:completion_tokens", usage.completion_tokens)
                            await pipe.execute()
                    except Exception as e:
                        logger.error(f"MetricsProcessor: failed to write to Redis: {e}")

        await self.push_frame(frame, direction)
