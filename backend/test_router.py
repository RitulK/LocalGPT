import unittest

from router import ModelRouter


from dataclasses import dataclass
from typing import List, Optional

@dataclass
class MockSettings:
    router_models: Optional[List[str]] = None
    default_coding_model: Optional[str] = None
    default_reasoning_model: Optional[str] = None
    default_general_model: Optional[str] = None

class ModelRouterTest(unittest.TestCase):
    def setUp(self):
        self.router = ModelRouter()

    def test_route_selects_a_configured_model(self):
        selected = self.router.route("write a python function to sort a list")

        self.assertIn(selected, self.router.MODEL_CAPABILITIES)


    def test_route_table_driven(self):
        cases = [
            # Basic capability tests
            ("hello", None, "qwen:4b"),
            ("write a python function to sort a list", None, "nvidia/nemotron-3-ultra-550b-a55b"),
            ("debug this error: exception stack trace unexpected null", None, "nvidia/nemotron-3-ultra-550b-a55b"),
            ("analyze and compare the philosophical implications of this theory", None, "nvidia/nemotron-3-ultra-550b-a55b"),
            ("write a creative story narrative about a character", None, "nvidia/nemotron-3-ultra-550b-a55b"),
            ("translate this text from english to spanish", None, "nvidia/nemotron-3-ultra-550b-a55b"),
            ("what is the capital of france?", None, "nvidia/nemotron-3-ultra-550b-a55b"),
            ("please create a list", None, "qwen:4b"),

            # Settings overrides
            ("write a python function to sort a list", MockSettings(default_coding_model="qwen2.5-coder:7b"), "qwen2.5-coder:7b"),
            ("analyze and compare these theories", MockSettings(default_reasoning_model="qwen:4b"), "qwen:4b"),
            ("hello", MockSettings(default_general_model="Llama-3_3-Nemotron-Super-49B-v1_5"), "Llama-3_3-Nemotron-Super-49B-v1_5"),

            # Settings restricted models
            ("write a python function to sort a list", MockSettings(router_models=["qwen:4b", "qwen2.5-coder:7b"]), "qwen2.5-coder:7b"),
            ("analyze and compare these theories", MockSettings(router_models=["qwen:4b", "qwen2.5-coder:7b"]), "qwen2.5-coder:7b"),
            ("hello", MockSettings(router_models=["qwen:4b", "qwen2.5-coder:7b"]), "qwen:4b"),

            # Edge case: empty string
            ("", None, "qwen:4b"),

            # Edge case: code detection through symbols
            ("```python\nprint('hello')\n```", None, "qwen2.5-coder:7b"),
        ]

        for prompt, settings, expected in cases:
            with self.subTest(prompt=prompt, settings=settings):
                actual = self.router.route(prompt, settings)
                self.assertEqual(actual, expected)

    def test_get_all_scores_returns_scores_for_available_models(self):
        scores = self.router.get_all_scores("explain quantum mechanics")

        self.assertTrue(scores)
        self.assertTrue(set(scores).issubset(self.router.MODEL_CAPABILITIES))

    def test_routing_reasoning_describes_selection(self):
        reasoning = self.router.get_routing_reasoning("fix this TypeError")

        self.assertIn("Detected debugging request", reasoning)


if __name__ == "__main__":
    unittest.main()
