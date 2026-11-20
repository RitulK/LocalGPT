from pathlib import Path
from typing import Dict, List, Optional

import math
import numpy as np

from app.core.config import settings


class LayaDecisionService:
    """Optional ONNX-backed System 1 decision service with a bounded heuristic fallback."""

    RAG_QUESTION = "Does this prompt require searching uploaded knowledge documents?"
    PREFERENCE_QUESTION = (
        "Does this message declare a persistent rule, instruction, or preference "
        "for future conversations?"
    )

    def __init__(
        self,
        model_path: Optional[str] = None,
        tokenizer_path: Optional[str] = None,
    ):
        self.model_path = model_path or settings.LAYA_MODEL_PATH
        self.tokenizer_path = tokenizer_path or settings.LAYA_TOKENIZER_PATH
        self.session = None
        self.tokenizer = None

        if self.model_path and self.tokenizer_path:
            model = Path(self.model_path)
            tokenizer = Path(self.tokenizer_path)
            if model.is_file() and tokenizer.is_file():
                try:
                    import onnxruntime as ort
                    from tokenizers import Tokenizer

                    self.tokenizer = Tokenizer.from_file(str(tokenizer))
                    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
                    self.session = ort.InferenceSession(str(model), providers=providers)
                except Exception:
                    self.session = None
                    self.tokenizer = None

    def _infer_logits(self, prompt: str, question: str) -> Optional[np.ndarray]:
        if self.session is None or self.tokenizer is None:
            return None

        encoded = self.tokenizer.encode(prompt, question)
        input_ids = np.asarray([encoded.ids], dtype=np.int64)
        attention_mask = np.asarray([encoded.attention_mask], dtype=np.int64)

        feeds = {}
        input_names = {name.name: name for name in self.session.get_inputs()}
        if "input_ids" in input_names:
            feeds["input_ids"] = input_ids
        if "attention_mask" in input_names:
            feeds["attention_mask"] = attention_mask
        if "token_type_ids" in input_names:
            feeds["token_type_ids"] = np.asarray([encoded.type_ids], dtype=np.int64)

        if not feeds:
            return None

        output = self.session.run(None, feeds)[0]
        return np.asarray(output)

    def predict_noul(self, prompt: str, question: str) -> float:
        logits = self._infer_logits(prompt, question)
        if logits is not None:
            flat = logits.reshape(-1)
            if flat.size == 1:
                prob = 1.0 / (1.0 + math.exp(-float(flat[0])))
            elif flat.size == 2:
                values = flat.astype(np.float64)
                values -= np.max(values)
                probabilities = np.exp(values) / np.exp(values).sum()
                prob = float(probabilities[-1])
            else:
                prob = float(np.clip(np.mean(flat), 0.0, 1.0))
            return float(np.clip(prob, 0.0, 1.0))

        lower_prompt = prompt.lower().strip()
        if question == self.RAG_QUESTION:
            if lower_prompt in {"hi", "hello", "thanks", "thank you", "hello there"}:
                return 0.1
            if any(word in lower_prompt for word in ("policy", "handbook", "document", "section", "pdf")):
                return 0.9
            return 0.2

        if question == self.PREFERENCE_QUESTION:
            preference_markers = (
                "always ", "never ", "use ", "prefer ", "format ",
                "responses in", "write in", "coding style",
            )
            if "always" in lower_prompt or "never" in lower_prompt:
                if any(marker in lower_prompt for marker in preference_markers):
                    return 0.95
            return 0.1

        return 0.5

    def predict_choice(self, prompt: str, categories: List[str]) -> Dict[str, float]:
        if not categories:
            return {}

        logits = self._infer_logits(prompt, "Which category best matches this prompt?")
        if logits is not None:
            flat = logits.reshape(-1)
            if flat.size >= len(categories):
                values = flat[:len(categories)].astype(np.float64)
                values -= np.max(values)
                probabilities = np.exp(values) / np.exp(values).sum()
                return {
                    category: float(probabilities[index])
                    for index, category in enumerate(categories)
                }

        probability = 1.0 / len(categories)
        return {category: probability for category in categories}


laya_decision_service = LayaDecisionService()
