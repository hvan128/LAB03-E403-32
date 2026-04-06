"""
Main runner: Baseline Chatbot vs ReAct Agent v1 vs ReAct Agent v2.

Usage:
    python main.py --mode chatbot      # Interactive baseline chatbot
    python main.py --mode v1           # Interactive ReAct Agent v1
    python main.py --mode v2           # Interactive ReAct Agent v2
    python main.py --compare           # Run predefined test cases and compare
    python main.py --query "question"  # Run one query using the selected mode
"""

import os
import sys
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

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
        model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        resolved_path = Path(model_path)
        if not resolved_path.is_absolute():
            resolved_path = PROJECT_ROOT / resolved_path
        return LocalProvider(model_path=str(resolved_path))
    else:
        raise ValueError(f"Unknown provider: {provider}")


# Test cases cho đề tài So sánh Sản phẩm
TEST_CASES = [
    # Simple — chatbot có thể trả lời
    "iPhone 15 có những thông số gì?",
    # Cần 1 tool
    "Tìm cho tôi các laptop có sẵn",
    # Cần tool thời tiết
    "Hôm nay thời tiết thế nào",
    # Câu hỏi thời tiết khác
    "Thời tiết hôm nay thế nào ?",
    # Cần product_compare
    "So sánh iPhone 15 và Samsung Galaxy S24",
    # Multi-step: search + price_calculator
    "iPhone 15 Pro Max giảm giá 20%, giá còn bao nhiêu?",
    # Multi-step: compare + calculator
    "So sánh MacBook Air M2 và Dell XPS 13, cái nào rẻ hơn bao nhiêu tiền?",
    # Complex multi-step
    "Samsung S24 Ultra giá bao nhiêu USD? So sánh với iPhone 15 Pro Max xem cái nào đắt hơn?",
]

MODE_LABELS = {
    "chatbot": "Baseline Chatbot",
    "v1": "ReAct Agent v1",
    "v2": "ReAct Agent v2",
}


def build_systems():
    llm = create_llm()
    return {
        "chatbot": Chatbot(llm),
        "v1": ReActAgent(llm, TOOLS, max_steps=5),
        "v2": ReActAgentV2(llm, TOOLS, max_steps=7),
    }


def run_comparison():
    systems = build_systems()
    chatbot = systems["chatbot"]
    agent_v1 = systems["v1"]
    agent_v2 = systems["v2"]

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


def run_interactive(start_mode: str = "v2"):
    systems = build_systems()

    print("Lab 3: Chatbot vs ReAct Agent")
    print("Available modes: chatbot (baseline), v1 (ReAct v1), v2 (ReAct v2)")
    print("Commands: 'quit' to exit, 'mode <chatbot|v1|v2>' to switch")
    print(f"Provider: {os.getenv('DEFAULT_PROVIDER', 'openai')}")
    print()

    mode = start_mode if start_mode in systems else "v2"
    print(f"Starting mode: {mode} - {MODE_LABELS[mode]}")

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


def run_single_query(query: str, mode: str | None = None):
    systems = build_systems()

    print(f"Query: {query}\n")

    if mode:
        print(f"--- {MODE_LABELS[mode]} ---")
        try:
            answer = systems[mode].run(query)
            print(f"Answer: {answer}\n")
        except Exception as e:
            print(f"Error: {e}\n")
        return

    for key in ["chatbot", "v1", "v2"]:
        print(f"--- {MODE_LABELS[key]} ---")
        try:
            answer = systems[key].run(query)
            print(f"Answer: {answer}\n")
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lab 3: Trợ lý So sánh Sản phẩm")
    parser.add_argument("--compare", action="store_true", help="Run comparison on test cases")
    parser.add_argument("--query", type=str, help="Run a single query")
    parser.add_argument(
        "--mode",
        choices=["chatbot", "v1", "v2"],
        default="v2",
        help="Choose which UI mode to start: baseline chatbot, ReAct v1, or ReAct v2",
    )
    args = parser.parse_args()

    if args.compare:
        run_comparison()
    elif args.query:
        run_single_query(args.query, mode=args.mode)
    else:
        run_interactive(start_mode=args.mode)
