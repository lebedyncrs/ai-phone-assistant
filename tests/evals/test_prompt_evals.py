import unittest
from dataclasses import dataclass

from src.prompts import PROMPT_VARIANTS
from tests.evals.scenarios import SCENARIOS, Scenario
from tests.evals.scoring import MetricScores, TurnOutput, evaluate_metrics


@dataclass(frozen=True)
class EvalResult:
    scenario_id: str
    prompt_variant: str
    metrics: MetricScores


class LLMAdapter:
    async def respond(
        self, prompt_variant: str, scenario: Scenario, turn_index: int, user_text: str
    ) -> TurnOutput:
        raise NotImplementedError


class MockLLMAdapter(LLMAdapter):
    def __init__(self):
        self._responses = {
            "baseline": {
                "unknown_caller_full_flow": [
                    TurnOutput("Dzień dobry, co mam przekazać Sergiuszowi?", []),
                    TurnOutput("Rozumiem, doprecyzuje Pani temat rozmowy?", []),
                    TurnOutput("Dziękuję Marta, przekażę wiadomość Sergiuszowi.", []),
                    TurnOutput("Dziękuję, do usłyszenia.", ["end_call"]),
                ],
                "silence_fallback": [
                    TurnOutput("Przepraszam, nie słyszę. Czy może Pan/Pani powtórzyć?", []),
                    TurnOutput("Dziękuję, przekażę informację o spotkaniu.", []),
                    TurnOutput("Dziękuję, do usłyszenia.", ["end_call"]),
                ],
                "short_info_no_premature_end": [
                    TurnOutput("Jasne, co dokładnie mam przekazać Sergiuszowi?", []),
                    TurnOutput("Rozumiem, czy mogę jeszcze w czymś pomóc?", []),
                ],
                "insurance_sales_call": [
                    TurnOutput("Dzień dobry, co mam przekazać Sergiuszowi?", []),
                    TurnOutput("Rozumiem, chodzi o ofertę ubezpieczenia mieszkania?", []),
                    TurnOutput("Dziękuję Tomasz, przekażę prośbę o kontakt jutro.", []),
                    TurnOutput("Dziękuję, do usłyszenia.", ["end_call"]),
                ],
                "listing_inquiry_call": [
                    TurnOutput("Dzień dobry, co mam przekazać o ogłoszeniu?", []),
                    TurnOutput("Rozumiem, zapytanie dotyczy aktualności ogłoszenia?", []),
                    TurnOutput("Dziękuję Asia, przekażę prośbę o kontakt po 18.", []),
                    TurnOutput("Dziękuję, do usłyszenia.", ["end_call"]),
                ],
                "known_caller_quick_close": [
                    TurnOutput("Cześć, co mam przekazać Sergiuszowi?", []),
                    TurnOutput("Dziękuję, przekażę że będziesz około 19.", []),
                    TurnOutput("Dziękuję, do usłyszenia.", ["end_call"]),
                ],
            },
            "candidate_concise": {
                "unknown_caller_full_flow": [
                    TurnOutput("Dzień dobry, co mam przekazać Sergiuszowi?", []),
                    TurnOutput("Jaki dokładnie temat faktury mam przekazać?", []),
                    TurnOutput("Dziękuję Marta, przekażę sprawę faktury Sergiuszowi.", []),
                    TurnOutput("Dziękuję, do usłyszenia.", ["end_call"]),
                ],
                "silence_fallback": [
                    TurnOutput("Przepraszam, nie słyszę. Czy może Pan/Pani powtórzyć?", []),
                    TurnOutput("Dziękuję, przekażę spotkanie jutro o 15.", []),
                    TurnOutput("Dziękuję, do usłyszenia.", ["end_call"]),
                ],
                "short_info_no_premature_end": [
                    TurnOutput("Jasne, co mam przekazać?", []),
                    TurnOutput("Rozumiem, czy mogę jeszcze pomóc?", []),
                ],
                "insurance_sales_call": [
                    TurnOutput("Dzień dobry, co z ubezpieczenia mam przekazać?", []),
                    TurnOutput("Rozumiem, chodzi o polisę mieszkania tańszą o 20 procent?", []),
                    TurnOutput("Dziękuję Tomasz, przekażę kontakt jutro w tej sprawie.", []),
                    TurnOutput("Dziękuję, do usłyszenia.", ["end_call"]),
                ],
                "listing_inquiry_call": [
                    TurnOutput("Dzień dobry, co mam przekazać o ogłoszeniu?", []),
                    TurnOutput("Rozumiem, pytanie dotyczy aktualności oferty mieszkania?", []),
                    TurnOutput("Dziękuję Asia, przekażę kontakt po godzinie 18.", []),
                    TurnOutput("Dziękuję, do usłyszenia.", ["end_call"]),
                ],
                "known_caller_quick_close": [
                    TurnOutput("Cześć Michał, co mam przekazać Sergiuszowi?", []),
                    TurnOutput("Dziękuję, przekażę że będziesz około 19.", []),
                    TurnOutput("Dziękuję, do usłyszenia.", ["end_call"]),
                ],
            },
            "candidate_clarifying": {
                "unknown_caller_full_flow": [
                    TurnOutput(
                        "Dzień dobry, co mam przekazać i czy zna Pani Sergiusza?",
                        [],
                    ),
                    TurnOutput(
                        "Rozumiem, proszę podać temat, kontekst i pilność sprawy.",
                        [],
                    ),
                    TurnOutput("Dziękuję Marta, przekażę wiadomość Sergiuszowi.", []),
                    TurnOutput("Dziękuję, do usłyszenia.", ["end_call", "end_call"]),
                ],
                "silence_fallback": [
                    TurnOutput("Przepraszam, nie słyszę. Proszę powtórzyć i doprecyzować.", []),
                    TurnOutput("Dobrze przekażę Sergiuszowi informację o spotkaniu jutro o 15.", []),
                    TurnOutput("Dziękuję, do usłyszenia.", ["end_call"]),
                ],
                "short_info_no_premature_end": [
                    TurnOutput("Co mam przekazać i kto dzwoni i czego dotyczy sprawa?", []),
                    TurnOutput("Rozumiem.", ["end_call"]),
                ],
                "insurance_sales_call": [
                    TurnOutput("Dzień dobry, z jakiego ubezpieczenia i dla kogo oferta?", []),
                    TurnOutput("Proszę podać dokładnie zakres polisy, warunki oraz pilność.", []),
                    TurnOutput("Dziękuję Tomasz, przekażę wiadomość Sergiuszowi.", []),
                    TurnOutput("Dziękuję, do usłyszenia.", ["end_call", "end_call"]),
                ],
                "listing_inquiry_call": [
                    TurnOutput("Dzień dobry, którego ogłoszenia dotyczy temat i lokalizacja?", []),
                    TurnOutput("Czy jest numer oferty oraz szczegóły zapytania?", []),
                    TurnOutput("Dziękuję Asia, przekażę prośbę o kontakt.", []),
                    TurnOutput("Dziękuję, do usłyszenia.", ["end_call"]),
                ],
                "known_caller_quick_close": [
                    TurnOutput("Cześć, co dokładnie i komu mam przekazać i kiedy?", []),
                    TurnOutput("Rozumiem, dziękuję za informacje.", []),
                    TurnOutput("Dziękuję, do usłyszenia.", ["end_call", "end_call"]),
                ],
            },
        }

    async def respond(
        self, prompt_variant: str, scenario: Scenario, turn_index: int, user_text: str
    ) -> TurnOutput:
        return self._responses[prompt_variant][scenario.id][turn_index]


async def run_eval_for_variant(variant: str, adapter: LLMAdapter) -> list[EvalResult]:
    results: list[EvalResult] = []
    for scenario in SCENARIOS:
        outputs: list[TurnOutput] = []
        for turn_index, user_text in enumerate(scenario.user_turns):
            output = await adapter.respond(variant, scenario, turn_index, user_text)
            outputs.append(output)
        metrics = evaluate_metrics(
            outputs=outputs,
            required_keywords=scenario.must_collect,
            should_call_end_call=scenario.should_call_end_call,
            expected_turn_index=scenario.end_call_turn_index,
        )
        results.append(EvalResult(scenario.id, variant, metrics))
    return results


class TestPromptEvaluations(unittest.IsolatedAsyncioTestCase):
    async def test_all_variants_are_evaluable(self):
        adapter = MockLLMAdapter()
        for variant in PROMPT_VARIANTS:
            results = await run_eval_for_variant(variant, adapter)
            self.assertEqual(len(results), len(SCENARIOS))

    async def test_candidate_concise_outperforms_baseline(self):
        adapter = MockLLMAdapter()
        baseline_results = await run_eval_for_variant("baseline", adapter)
        concise_results = await run_eval_for_variant("candidate_concise", adapter)

        baseline_total = sum(result.metrics.total for result in baseline_results)
        concise_total = sum(result.metrics.total for result in concise_results)
        self.assertGreaterEqual(concise_total, baseline_total)

    async def test_candidate_clarifying_has_regressions(self):
        adapter = MockLLMAdapter()
        clarifying_results = await run_eval_for_variant("candidate_clarifying", adapter)

        low_format = any(result.metrics.format_compliance < 1.0 for result in clarifying_results)
        low_tool = any(result.metrics.tool_calling < 1.0 for result in clarifying_results)
        self.assertTrue(low_format)
        self.assertTrue(low_tool)


if __name__ == "__main__":
    unittest.main()
