from dataclasses import dataclass

from src.llm_tools import MIN_MESSAGES_BEFORE_END_CALL


@dataclass(frozen=True)
class TurnOutput:
    text: str
    tool_calls: list[str]


@dataclass(frozen=True)
class MetricScores:
    tool_calling: float
    task_completion: float
    format_compliance: float

    @property
    def total(self) -> float:
        return self.tool_calling + self.task_completion + self.format_compliance


def _word_count(text: str) -> int:
    return len([w for w in text.strip().split(" ") if w])


def _is_single_sentence(text: str) -> bool:
    punctuation_count = sum(text.count(mark) for mark in [".", "!", "?"])
    return punctuation_count <= 1


def _one_question_max(text: str) -> bool:
    return text.count("?") <= 1


def score_format_compliance(outputs: list[TurnOutput]) -> float:
    if not outputs:
        return 0.0
    per_turn = []
    for output in outputs:
        checks = [
            _word_count(output.text) <= 10,
            _is_single_sentence(output.text),
            _one_question_max(output.text),
        ]
        per_turn.append(sum(1 for ok in checks if ok) / len(checks))
    return sum(per_turn) / len(per_turn)


def score_task_completion(outputs: list[TurnOutput], required_keywords: list[str]) -> float:
    if not required_keywords:
        return 1.0
    whole_text = " ".join(output.text.lower() for output in outputs)
    matched = sum(1 for kw in required_keywords if kw.lower() in whole_text)
    return matched / len(required_keywords)


def score_tool_calling(
    outputs: list[TurnOutput],
    should_call_end_call: bool,
    expected_turn_index: int | None,
) -> float:
    end_call_turns = [
        idx for idx, output in enumerate(outputs) if "end_call" in output.tool_calls
    ]
    if not should_call_end_call:
        return 1.0 if not end_call_turns else 0.0
    if not end_call_turns:
        return 0.0

    first_turn = end_call_turns[0]
    message_count_at_call = (first_turn + 1) * 2
    respects_min_messages = message_count_at_call >= MIN_MESSAGES_BEFORE_END_CALL
    matches_expected_turn = expected_turn_index is None or first_turn == expected_turn_index
    no_duplicate_calls = len(end_call_turns) == 1
    checks = [respects_min_messages, matches_expected_turn, no_duplicate_calls]
    return sum(1 for ok in checks if ok) / len(checks)


def evaluate_metrics(
    outputs: list[TurnOutput],
    required_keywords: list[str],
    should_call_end_call: bool,
    expected_turn_index: int | None,
) -> MetricScores:
    return MetricScores(
        tool_calling=score_tool_calling(outputs, should_call_end_call, expected_turn_index),
        task_completion=score_task_completion(outputs, required_keywords),
        format_compliance=score_format_compliance(outputs),
    )
