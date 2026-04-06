import time
from typing import Dict, Any, List
from src.telemetry.logger import logger

class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.
    """
    def __init__(self):
        self.session_metrics = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int):
        """
        Logs a single request metric to our telemetry.
        """
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "cost_estimate": self._calculate_cost(model, usage) # Mock cost calculation
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    # GPT pricing (USD per 1M tokens) — cập nhật tháng 4/2026
    PRICING = {
        # OpenAI
        "gpt-4o":           {"prompt": 2.50,  "completion": 10.00},
        "gpt-4o-mini":      {"prompt": 0.15,  "completion": 0.60},
        "gpt-4-turbo":      {"prompt": 10.00, "completion": 30.00},
        "gpt-4":            {"prompt": 30.00, "completion": 60.00},
        "gpt-3.5-turbo":    {"prompt": 0.50,  "completion": 1.50},
        # Google
        "gemini-1.5-pro":   {"prompt": 1.25,  "completion": 5.00},
        "gemini-1.5-flash":  {"prompt": 0.075, "completion": 0.30},
        # Anthropic
        "claude-3-5-sonnet": {"prompt": 3.00, "completion": 15.00},
        "claude-3-haiku":    {"prompt": 0.25,  "completion": 1.25},
    }

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """Tính cost thực tế theo model pricing (USD)."""
        pricing = self.PRICING.get(model)
        if not pricing:
            # fallback: tìm partial match
            for key, p in self.PRICING.items():
                if key in model.lower():
                    pricing = p
                    break
        if not pricing:
            pricing = {"prompt": 2.50, "completion": 10.00}  # default gpt-4o

        prompt_cost = usage.get("prompt_tokens", 0) / 1_000_000 * pricing["prompt"]
        completion_cost = usage.get("completion_tokens", 0) / 1_000_000 * pricing["completion"]
        return round(prompt_cost + completion_cost, 6)

# Global tracker instance
tracker = PerformanceTracker()
