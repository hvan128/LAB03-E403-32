from typing import Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class Chatbot:
    """
    Simple LLM Chatbot baseline — no tools, no reasoning loop.
    Just sends the user query to the LLM and returns the response.
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def run(self, user_input: str) -> str:
        logger.log_event("CHATBOT_START", {"input": user_input, "model": self.llm.model_name})

        system_prompt = (
            "You are a helpful assistant. Answer the user's question directly and concisely."
        )

        result = self.llm.generate(user_input, system_prompt=system_prompt)

        tracker.track_request(
            provider=result.get("provider", "unknown"),
            model=self.llm.model_name,
            usage=result.get("usage", {}),
            latency_ms=result.get("latency_ms", 0),
        )

        logger.log_event("CHATBOT_END", {
            "latency_ms": result.get("latency_ms", 0),
            "tokens": result.get("usage", {}),
        })

        return result["content"]
