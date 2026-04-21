import unittest

from src.prompts import PROMPT_VARIANTS
from tests.evals.live_adapter import LiveLLMAdapter, run_eval_for_variant_live, summarize_scores


class TestPromptEvaluationsLive(unittest.IsolatedAsyncioTestCase):
    async def test_live_variants_generate_scores(self):
        adapter = LiveLLMAdapter()
        per_variant_totals: dict[str, float] = {}

        for variant in PROMPT_VARIANTS:
            results = await run_eval_for_variant_live(variant, adapter)
            summary = summarize_scores(results)
            per_variant_totals[variant] = summary["total"]
            print(
                f"[live-eval] variant={variant} "
                f"total={summary['total']:.3f} "
                f"tool={summary['tool_calling']:.3f} "
                f"task={summary['task_completion']:.3f} "
                f"format={summary['format_compliance']:.3f}"
            )

        # Sanity assertion: all variants produced a non-negative aggregate score.
        self.assertTrue(all(score >= 0.0 for score in per_variant_totals.values()))
