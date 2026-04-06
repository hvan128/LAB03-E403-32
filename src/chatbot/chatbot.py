import os
import sys
from typing import Optional
from dotenv import load_dotenv

load_dotenv(override=True)

if __package__ is None or __package__ == "":
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )

from src.core.llm_provider import LLMProvider
from src.core.scope_guard import build_out_of_scope_response, is_in_scope_query
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class Chatbot:
    """
    Simple LLM Chatbot baseline — focused on product comparison and price questions.
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def get_system_prompt(self) -> str:
        return (
            "You are a helpful shopping assistant for product search, comparison, and price calculation. "
            "Only answer questions about phones, laptops, their specs, comparisons, discounts, or simple pricing math. "
            "If the user asks about unrelated topics like politics, war, news, or weather, politely refuse and redirect them back to product questions."
        )

    def run(self, user_input: str) -> str:
        logger.log_event("CHATBOT_START", {"input": user_input, "model": self.llm.model_name})

        if not is_in_scope_query(user_input):
            response = build_out_of_scope_response()
            logger.log_event("CHATBOT_SCOPE_GUARD", {"input": user_input, "status": "blocked"})
            logger.log_event("CHATBOT_END", {
                "status": "out_of_scope",
                "latency_ms": 0,
                "tokens": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            })
            return response

        system_prompt = self.get_system_prompt()

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


def run_openai_chatbot() -> None:


    from src.core.openai_provider import OpenAIProvider

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        raise ValueError("OPENAI_API_KEY is missing in `.env`.")

    model_name = os.getenv("DEFAULT_MODEL", "gpt-4o")
    chatbot = Chatbot(OpenAIProvider(model_name=model_name, api_key=api_key))

    print(f"OpenAI chatbot is ready ({model_name}). Type 'quit' to exit.")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        try:
            answer = chatbot.run(user_input)
            print(f"Assistant: {answer}\n")
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    run_openai_chatbot()
