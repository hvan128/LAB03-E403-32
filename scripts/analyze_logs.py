"""
[Vương Trần] Script phân tích logs và tính aggregate metrics.

Đọc file JSON logs từ thư mục logs/, tính:
- Token trung bình, tổng token
- Latency P50, P95, P99
- Số steps trung bình (agent)
- Tỷ lệ lỗi (parse error, hallucination, timeout)
- Cost estimate

Usage:
    python scripts/analyze_logs.py
    python scripts/analyze_logs.py --file logs/2026-04-06.log
"""

import json
import sys
import os
from collections import defaultdict


def parse_log_file(filepath: str) -> list:
    """Parse JSON log file, mỗi dòng là 1 JSON object."""
    events = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError:
                continue
    return events


def analyze(events: list):
    """Phân tích danh sách events và in metrics."""

    metrics = defaultdict(list)
    errors = defaultdict(int)
    agent_steps = []
    cost_by_provider = defaultdict(float)
    question_results = defaultdict(lambda: {"success": 0, "total": 0})
    step_distributions = []
    termination_status = defaultdict(int)

    # Chatbot vs Agent comparison
    chatbot_metrics = {"latency": [], "tokens": [], "cost": []}
    agent_metrics   = {"latency": [], "tokens": [], "cost": []}
    _current_mode = {}  # track mode per session by start event

    for e in events:
        event_type = e.get("event", "")
        data = e.get("data", {})

        if event_type == "CHATBOT_START":
            _current_mode["mode"] = "chatbot"

        elif event_type in ("AGENT_V1_START", "AGENT_V2_START"):
            _current_mode["mode"] = "agent"

        elif event_type == "LLM_METRIC":
            metrics["latency"].append(data.get("latency_ms", 0))
            metrics["prompt_tokens"].append(data.get("prompt_tokens", 0))
            metrics["completion_tokens"].append(data.get("completion_tokens", 0))
            metrics["total_tokens"].append(data.get("total_tokens", 0))
            cost = data.get("cost_estimate", 0)
            metrics["cost"].append(cost)
            provider = data.get("provider", "unknown")
            cost_by_provider[provider] += cost
            # Chatbot vs Agent
            mode = _current_mode.get("mode", "unknown")
            if mode == "chatbot":
                chatbot_metrics["latency"].append(data.get("latency_ms", 0))
                chatbot_metrics["tokens"].append(data.get("total_tokens", 0))
                chatbot_metrics["cost"].append(cost)
            elif mode == "agent":
                agent_metrics["latency"].append(data.get("latency_ms", 0))
                agent_metrics["tokens"].append(data.get("total_tokens", 0))
                agent_metrics["cost"].append(cost)

        elif "PARSE_ERROR" in event_type:
            errors["parse_error"] += 1

        elif "HALLUCINATION" in event_type:
            errors["hallucination"] += 1

        elif event_type in ("AGENT_V1_END", "AGENT_V2_END"):
            steps = data.get("steps", 0)
            agent_steps.append(steps)
            step_distributions.append(steps)
            status = data.get("status", "unknown")
            termination_status[status] += 1
            if status == "max_steps_exceeded":
                errors["timeout"] += 1
            q_type = data.get("question_type", "unknown")
            question_results[q_type]["total"] += 1
            if status == "success":
                question_results[q_type]["success"] += 1

    # Print results
    print("=" * 60)
    print("LOG ANALYSIS REPORT")
    print("=" * 60)

    if metrics["latency"]:
        latencies = sorted(metrics["latency"])
        print(f"\n--- Latency ---")
        print(f"  Total requests: {len(latencies)}")
        print(f"  P50: {_percentile(latencies, 50):.0f} ms")
        print(f"  P95: {_percentile(latencies, 95):.0f} ms")
        print(f"  P99: {_percentile(latencies, 99):.0f} ms")
        print(f"  Avg: {sum(latencies)/len(latencies):.0f} ms")

    if metrics["total_tokens"]:
        tokens = metrics["total_tokens"]
        print(f"\n--- Tokens ---")
        print(f"  Total: {sum(tokens):,}")
        print(f"  Avg per request: {sum(tokens)/len(tokens):,.0f}")
        print(f"  Prompt tokens total: {sum(metrics['prompt_tokens']):,}")
        print(f"  Completion tokens total: {sum(metrics['completion_tokens']):,}")
        prompt_total = sum(metrics["prompt_tokens"])
        comp_total = sum(metrics["completion_tokens"])
        if comp_total > 0:
            print(f"  Prompt/Completion ratio: {prompt_total/comp_total:.2f}")

    if metrics["cost"]:
        print(f"\n--- Cost ---")
        print(f"  Total estimated cost: ${sum(metrics['cost']):.4f}")
        if cost_by_provider:
            print(f"  Breakdown by provider:")
            for provider, cost in sorted(cost_by_provider.items(), key=lambda x: -x[1]):
                print(f"    {provider}: ${cost:.4f}")

    if agent_steps:
        print(f"\n--- Agent Steps (Loop Count) ---")
        print(f"  Total agent runs: {len(agent_steps)}")
        print(f"  Avg steps per run: {sum(agent_steps)/len(agent_steps):.1f}")
        print(f"  Max steps: {max(agent_steps)}")
        print(f"  Min steps: {min(agent_steps)}")
        # Phân bố số steps
        dist = defaultdict(int)
        for s in step_distributions:
            dist[s] += 1
        print(f"  Step distribution:")
        for k in sorted(dist):
            bar = "█" * dist[k]
            print(f"    {k} step(s): {dist[k]:>3}x  {bar}")
        # Termination quality
        print(f"\n--- Termination Quality ---")
        total_runs = len(agent_steps)
        for status, count in sorted(termination_status.items(), key=lambda x: -x[1]):
            pct = count / total_runs * 100
            label = "✓" if status == "success" else "✗"
            print(f"  {label} {status}: {count}/{total_runs} ({pct:.1f}%)")

    print(f"\n--- Failure Analysis ---")
    print(f"  JSON Parse errors  : {errors['parse_error']:>4}  (LLM output wrong Action format)")
    print(f"  Hallucination errors: {errors['hallucination']:>3}  (LLM called non-existent tool)")
    print(f"  Timeouts           : {errors['timeout']:>4}  (exceeded max_steps)")
    total_runs = len(agent_steps) if agent_steps else 1
    total_errors = sum(errors.values())
    print(f"  Total errors: {total_errors}  |  Error rate: {total_errors/total_runs*100:.1f}%")

    if question_results:
        print(f"\n--- Success Rate by Question Type ---")
        for q_type, counts in sorted(question_results.items()):
            rate = counts["success"] / counts["total"] * 100 if counts["total"] else 0
            print(f"  {q_type}: {counts['success']}/{counts['total']} ({rate:.1f}%)")

    # --- Chatbot vs Agent comparison ---
    if chatbot_metrics["latency"] or agent_metrics["latency"]:
        print(f"\n{'='*60}")
        print(f"CHATBOT vs AGENT COMPARISON")
        print(f"{'='*60}")
        def _avg(lst): return sum(lst) / len(lst) if lst else 0
        header = f"  {'Metric':<25} {'Chatbot':>12} {'Agent':>12}"
        print(header)
        print(f"  {'-'*49}")
        print(f"  {'Requests':<25} {len(chatbot_metrics['latency']):>12} {len(agent_metrics['latency']):>12}")
        print(f"  {'Avg Latency (ms)':<25} {_avg(chatbot_metrics['latency']):>12.0f} {_avg(agent_metrics['latency']):>12.0f}")
        print(f"  {'Avg Tokens':<25} {_avg(chatbot_metrics['tokens']):>12.0f} {_avg(agent_metrics['tokens']):>12.0f}")
        print(f"  {'Total Cost ($)':<25} {sum(chatbot_metrics['cost']):>12.4f} {sum(agent_metrics['cost']):>12.4f}")
        print(f"  {'Avg Cost/req ($)':<25} {_avg(chatbot_metrics['cost']):>12.4f} {_avg(agent_metrics['cost']):>12.4f}")

    print("=" * 60)


def _percentile(sorted_list, pct):
    idx = int(len(sorted_list) * pct / 100)
    idx = min(idx, len(sorted_list) - 1)
    return sorted_list[idx]


if __name__ == "__main__":
    log_file = None
    if "--file" in sys.argv:
        idx = sys.argv.index("--file")
        log_file = sys.argv[idx + 1]
    else:
        log_dir = "logs"
        if os.path.exists(log_dir):
            files = sorted([f for f in os.listdir(log_dir) if f.endswith(".log")])
            if files:
                log_file = os.path.join(log_dir, files[-1])

    if not log_file or not os.path.exists(log_file):
        print("No log file found. Run main.py --compare first.")
        sys.exit(1)

    print(f"Analyzing: {log_file}\n")
    events = parse_log_file(log_file)
    analyze(events)
