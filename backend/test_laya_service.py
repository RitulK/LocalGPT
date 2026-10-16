import unittest
import time
from app.infrastructure.decision.laya_service import laya_decision_service

class LayaDecisionServiceTest(unittest.TestCase):
    def test_predict_noul_speed(self):
        start = time.perf_counter()
        prob = laya_decision_service.predict_noul("test prompt", "test question")
        elapsed = time.perf_counter() - start

        self.assertLess(elapsed, 0.04) # < 40ms
        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)

if __name__ == "__main__":
    unittest.main()
