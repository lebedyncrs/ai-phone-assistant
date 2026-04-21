import asyncio
import os
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)

from src.llm_tools import END_CALL_TOOL_NAME
from src.prompts import PROMPT_VARIANTS
from tests.evals.scenarios import SCENARIOS, Scenario
from tests.evals.scoring import MetricScores, TurnOutput, evaluate_metrics

OPENAI_TOOL_SCHEMA: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": END_CALL_TOOL_NAME,
            "description": "Ends the phone call after a goodbye in the same response.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    }
]


@dataclass(frozen=True)
class EvalResult:
    scenario_id: str
    prompt_variant: str
    metrics: MetricScores


class LiveLLMAdapter:
    """Runs real prompt evals using text-only conversation turns."""

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for live prompt evals")
        self._model = os.getenv("OPENAI_MODEL", "gpt-4.1")
        self._call_delay_seconds = float(os.getenv("LIVE_EVAL_CALL_DELAY_MS", "500")) / 1000
        self._client = AsyncOpenAI(api_key=api_key)

    async def respond(
        self,
        prompt_variant: str,
        scenario: Scenario,
        conversation: list[ChatCompletionMessageParam],
        user_text: str,
    ) -> tuple[TurnOutput, list[ChatCompletionMessageParam]]:
        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": PROMPT_VARIANTS[prompt_variant],
            },
            *conversation,
            {
                "role": "user",
                "content": user_text,
            },
        ]

        if self._call_delay_seconds > 0:
            await asyncio.sleep(self._call_delay_seconds)

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=OPENAI_TOOL_SCHEMA,
        )
        choice = response.choices[0].message
        content = choice.content or ""
        tool_calls = choice.tool_calls or []
        called_tools = [call.function.name for call in tool_calls if call.function]

        assistant_message: ChatCompletionAssistantMessageParam = {
            "role": "assistant",
            "content": content,
        }
        if tool_calls:
            assistant_message["tool_calls"] = [call.model_dump() for call in tool_calls]

        next_conversation = [
            *conversation,
            {"role": "user", "content": user_text},
            assistant_message,
        ]

        return TurnOutput(text=content, tool_calls=called_tools), next_conversation


async def run_eval_for_variant_live(variant: str, adapter: LiveLLMAdapter) -> list[EvalResult]:
    results: list[EvalResult] = []
    for scenario in SCENARIOS:
        outputs: list[TurnOutput] = []
        conversation: list[ChatCompletionMessageParam] = []
        for user_text in scenario.user_turns:
            output, conversation = await adapter.respond(
                prompt_variant=variant,
                scenario=scenario,
                conversation=conversation,
                user_text=user_text,
            )
            outputs.append(output)

        metrics = evaluate_metrics(
            outputs=outputs,
            required_keywords=scenario.must_collect,
            should_call_end_call=scenario.should_call_end_call,
            expected_turn_index=scenario.end_call_turn_index,
        )
        results.append(EvalResult(scenario.id, variant, metrics))
    return results


def summarize_scores(results: list[EvalResult]) -> dict[str, Any]:
    if not results:
        return {"total": 0.0, "tool_calling": 0.0, "task_completion": 0.0, "format_compliance": 0.0}
    count = len(results)
    return {
        "total": sum(result.metrics.total for result in results) / count,
        "tool_calling": sum(result.metrics.tool_calling for result in results) / count,
        "task_completion": sum(result.metrics.task_completion for result in results) / count,
        "format_compliance": sum(result.metrics.format_compliance for result in results) / count,
    }
