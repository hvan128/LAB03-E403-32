"""
Main runner: Chatbot vs Agent v1 vs Agent v2 comparison.

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


TEST_CASES = [
    # Simple factual (chatbot should handle)
    "What is the capital of France?",
    # Requires tool (weather)
    "What is the weather in Hanoi right now?",
    # Requires tool (calculator)
    "What is 1234 * 5678?",
    # Multi-step: needs search + calculator
    "What is the population of Vietnam? Multiply it by 2.",
    # Multi-step: weather + calculator
    "What is the temperature in Tokyo? Convert it from Celsius to Fahrenheit.",
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

        # Chatbot
        print("\n--- Chatbot ---")
        try:
            cb_answer = chatbot.run(query)
            print(f"Answer: {cb_answer[:200]}")
            row["chatbot"] = cb_answer
        except Exception as e:
            print(f"Error: {e}")
            row["chatbot"] = f"ERROR: {e}"

        # Agent v1
        print("\n--- Agent v1 ---")
        try:
            v1_answer = agent_v1.run(query)
            print(f"Answer: {v1_answer[:200]}")
            row["agent_v1"] = v1_answer
        except Exception as e:
            print(f"Error: {e}")
            row["agent_v1"] = f"ERROR: {e}"

        # Agent v2
        print("\n--- Agent v2 ---")
        try:
            v2_answer = agent_v2.run(query)
            print(f"Answer: {v2_answer[:200]}")
            row["agent_v2"] = v2_answer
        except Exception as e:
            print(f"Error: {e}")
            row["agent_v2"] = f"ERROR: {e}"

        results.append(row)

    # Save results
    os.makedirs("logs", exist_ok=True)
    with open("logs/comparison_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print metrics summary
    print(f"\n{'='*70}")
    print("METRICS SUMMARY")
    print("="*70)
    for m in tracker.session_metrics:
        print(json.dumps(m, indent=2))

    print(f"\nTotal requests tracked: {len(tracker.session_metrics)}")
    print(f"Results saved to logs/comparison_results.json")


def run_interactive():
    llm = create_llm()
    chatbot = Chatbot(llm)
    agent_v1 = ReActAgent(llm, TOOLS, max_steps=5)
    agent_v2 = ReActAgentV2(llm, TOOLS, max_steps=7)

    print("Lab 3: Chatbot vs ReAct Agent")
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
    parser = argparse.ArgumentParser(description="Lab 3: Chatbot vs ReAct Agent")
    parser.add_argument("--compare", action="store_true", help="Run comparison on test cases")
    parser.add_argument("--query", type=str, help="Run a single query on all systems")
    args = parser.parse_args()

    if args.compare:
        run_comparison()
    elif args.query:
        run_single_query(args.query)
    else:
        run_interactive()
