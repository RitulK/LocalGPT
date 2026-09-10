import unittest

from router import ModelRouter


class ModelRouterTest(unittest.TestCase):
    def setUp(self):
        self.router = ModelRouter()

    def test_route_selects_a_configured_model(self):
        selected = self.router.route("write a python function to sort a list")

        self.assertIn(selected, self.router.MODEL_CAPABILITIES)

    def test_get_all_scores_returns_scores_for_available_models(self):
        scores = self.router.get_all_scores("explain quantum mechanics")

        self.assertTrue(scores)
        self.assertTrue(set(scores).issubset(self.router.MODEL_CAPABILITIES))

    def test_routing_reasoning_describes_selection(self):
        reasoning = self.router.get_routing_reasoning("fix this TypeError")

        self.assertIn("Detected debugging request", reasoning)


if __name__ == "__main__":
    unittest.main()
