"""
Main runner: Chatbot vs Agent v1 vs Agent v2 — Trợ lý So sánh Sản phẩm.

Usage:
    python main.py                     # Interactive mode
    python main.py --compare           # Run predefined test cases and compare
    python main.py --query "question"  # Single query on all 3 systems
"""

import os
import sys
import argparse
import json
from dotenv import load_dotenv

load_dotenv()

from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider
from src.chatbot.chatbot import Chatbot
from src.agent.agent import ReActAgent
from src.agent.agent_v2 import ReActAgentV2
from src.tools.tool_registry import TOOLS
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


def create_llm():
    provider = os.getenv("DEFAULT_PROVIDER", "openai")
    if provider == "openai":
        return OpenAIProvider(
            model_name=os.getenv("DEFAULT_MODEL", "gpt-4o"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    elif provider == "google":
        return GeminiProvider(
            model_name=os.getenv("DEFAULT_MODEL", "gemini-1.5-flash"),
            api_key=os.getenv("GEMINI_API_KEY"),
        )
    elif provider == "local":
        from src.core.local_provider import LocalProvider
        return LocalProvider(model_path=os.getenv("LOCAL_MODEL_PATH"))
    else:
        raise ValueError(f"Unknown provider: {provider}")


# Test cases cho đề tài So sánh Sản phẩm
TEST_CASES = [
    # Simple — chatbot có thể trả lời
    "iPhone 15 có những thông số gì?",
    # Cần 1 tool
    "Tìm cho tôi các laptop có sẵn",
    # Cần product_compare
    "So sánh iPhone 15 và Samsung Galaxy S24",
    # Multi-step: search + price_calculator
    "iPhone 15 Pro Max giảm giá 20%, giá còn bao nhiêu?",
    # Multi-step: compare + calculator
    "So sánh MacBook Air M2 và Dell XPS 13, cái nào rẻ hơn bao nhiêu tiền?",
    # Complex multi-step
    "Samsung S24 Ultra giá bao nhiêu USD? So sánh với iPhone 15 Pro Max xem cái nào đắt hơn?",
]


def run_comparison():
    llm = create_llm()
    chatbot = Chatbot(llm)
    agent_v1 = ReActAgent(llm, TOOLS, max_steps=5)
    agent_v2 = ReActAgentV2(llm, TOOLS, max_steps=7)

    results = []

    for i, query in enumerate(TEST_CASES, 1):
        print(f"\n{'='*70}")
        print(f"Test Case {i}: {query}")
        print("="*70)

        row = {"query": query}

        for name, system in [("chatbot", chatbot), ("agent_v1", agent_v1), ("agent_v2", agent_v2)]:
            print(f"\n--- {name.upper()} ---")
            try:
                answer = system.run(query)
                print(f"Answer: {answer[:300]}")
                row[name] = answer
            except Exception as e:
                print(f"Error: {e}")
                row[name] = f"ERROR: {e}"

        results.append(row)

    # Save results
    os.makedirs("logs", exist_ok=True)
    with open("logs/comparison_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print metrics summary
    print(f"\n{'='*70}")
    print("METRICS SUMMARY")
    print("="*70)
    total_cost = sum(m.get("cost_estimate", 0) for m in tracker.session_metrics)
    total_tokens = sum(m.get("total_tokens", 0) for m in tracker.session_metrics)
    print(f"Total requests: {len(tracker.session_metrics)}")
    print(f"Total tokens: {total_tokens:,}")
    print(f"Estimated cost: ${total_cost:.4f}")
    print(f"\nResults saved to logs/comparison_results.json")
    print(f"Run 'python scripts/analyze_logs.py' for detailed analysis.")


def run_interactive():
    llm = create_llm()
    chatbot = Chatbot(llm)
    agent_v1 = ReActAgent(llm, TOOLS, max_steps=5)
    agent_v2 = ReActAgentV2(llm, TOOLS, max_steps=7)

    print("=== Trợ lý So sánh Sản phẩm ===")
    print("Commands: 'quit' to exit, 'mode <chatbot|v1|v2>' to switch")
    print(f"Provider: {os.getenv('DEFAULT_PROVIDER', 'openai')}")
    print()

    mode = "v2"
    systems = {"chatbot": chatbot, "v1": agent_v1, "v2": agent_v2}

    while True:
        user_input = input(f"[{mode}] You: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            break
        if user_input.lower().startswith("mode "):
            new_mode = user_input.split(" ", 1)[1].strip()
            if new_mode in systems:
                mode = new_mode
                print(f"Switched to {mode}")
            else:
                print(f"Unknown mode. Choose from: {', '.join(systems.keys())}")
            continue

        try:
            answer = systems[mode].run(user_input)
            print(f"\nAssistant: {answer}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


def run_single_query(query: str):
    llm = create_llm()
    chatbot = Chatbot(llm)
    agent_v1 = ReActAgent(llm, TOOLS, max_steps=5)
    agent_v2 = ReActAgentV2(llm, TOOLS, max_steps=7)

    print(f"Query: {query}\n")

    for name, system in [("Chatbot", chatbot), ("Agent v1", agent_v1), ("Agent v2", agent_v2)]:
        print(f"--- {name} ---")
        try:
            answer = system.run(query)
            print(f"Answer: {answer}\n")
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lab 3: Trợ lý So sánh Sản phẩm")
    parser.add_argument("--compare", action="store_true", help="Run comparison on test cases")
    parser.add_argument("--query", type=str, help="Run a single query on all systems")
    args = parser.parse_args()

    if args.compare:
        run_comparison()
    elif args.query:
        run_single_query(args.query)
    else:
        run_interactive()
