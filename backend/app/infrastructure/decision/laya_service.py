from typing import List, Dict
import time

class LayaDecisionService:
    """
    Simulates a local, lightweight Decision Service running Laya
    (ModernBERT-large non-autoregressive encoder) via onnxruntime.
    """

    def __init__(self):
        # In a real implementation, this would load the ONNX model using onnxruntime.InferenceSession.
        pass

    def predict_noul(self, prompt: str, question: str) -> float:
        """
        Calibrated binary probability 0.0 to 1.0.
        Simulates the model evaluation taking < 40ms.
        """
        start_time = time.perf_counter()

        prob = 0.5

        if question == "Does this prompt require searching uploaded knowledge documents?":
            lower_prompt = prompt.lower().strip()
            if lower_prompt in ["hi", "hello", "thanks", "thank you", "hello there"]:
                prob = 0.1
            elif "policy" in lower_prompt or "handbook" in lower_prompt or "document" in lower_prompt:
                prob = 0.9
            else:
                prob = 0.2

        elif question == "Does this message declare a persistent rule, instruction, or preference for future conversations?":
            lower_prompt = prompt.lower().strip()
            if "always" in lower_prompt and ("write" in lower_prompt or "format" in lower_prompt):
                prob = 0.95
            else:
                prob = 0.1

        elapsed = time.perf_counter() - start_time
        if elapsed > 0.04:
            pass

        return prob

    def predict_choice(self, prompt: str, categories: List[str]) -> Dict[str, float]:
        if not categories:
            return {}

        prob = 1.0 / len(categories)
        return {cat: prob for cat in categories}

laya_decision_service = LayaDecisionService()
