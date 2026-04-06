import re
from typing import List, Dict, Any, Callable, Optional
from src.core.llm_provider import LLMProvider
from src.core.scope_guard import build_out_of_scope_response, is_in_scope_query
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class ReActAgent:
    """
    Agent v1: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = {t["name"]: t for t in tools}
        self.max_steps = max_steps
        self.trace = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            f"- {name}: {t['description']}" for name, t in self.tools.items()
        )
        return f"""You are a product comparison assistant that solves shopping tasks step-by-step.

You only support questions about phones, laptops, product specs, price comparison, discounts, and simple calculations.
If the user asks about unrelated topics such as politics, war, weather, or general news, do not answer them and instead politely redirect back to product-related questions.

You have access to the following tools:
{tool_descriptions}

You MUST use the following format strictly:

Thought: <your reasoning about what to do next>
Action: <tool_name>(<argument>)

After you receive an Observation (the tool result), continue with another Thought/Action if needed.

When you have enough information to answer, respond with:
Thought: I now have enough information to answer.
Final Answer: <your final response to the user>

Rules:
- Only call ONE tool per step.
- The Action format must be exactly: tool_name(argument)
- Do NOT invent tools that are not listed above.
- Always start with a Thought before an Action or Final Answer.
"""

    def _emit(self, entry: dict, on_step=None):
        self.trace.append(entry)
        if on_step:
            on_step(list(self.trace))

    def run(self, user_input: str, on_step=None) -> str:
        logger.log_event("AGENT_V1_START", {"input": user_input, "model": self.llm.model_name})

        self.trace = []
        self._emit({"type": "input", "content": user_input}, on_step)

        if not is_in_scope_query(user_input):
            response = build_out_of_scope_response()
            self._emit({
                "type": "final_answer", "step": 0,
                "content": response,
                "total_tokens": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "total_latency_ms": 0,
                "status": "out_of_scope",
            }, on_step)
            logger.log_event("AGENT_V1_SCOPE_GUARD", {"input": user_input, "status": "blocked"})
            logger.log_event("AGENT_V1_END", {
                "steps": 0, "status": "out_of_scope",
                "total_tokens": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "total_latency_ms": 0,
            })
            return response

        prompt_parts = [f"User question: {user_input}"]
        steps = 0
        total_tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        total_latency = 0

        while steps < self.max_steps:
            steps += 1
            current_prompt = "\n".join(prompt_parts)

            result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())

            content = result["content"]
            usage = result.get("usage", {})
            latency = result.get("latency_ms", 0)
            for k in total_tokens:
                total_tokens[k] += usage.get(k, 0)
            total_latency += latency

            tracker.track_request(
                provider=result.get("provider", "unknown"),
                model=self.llm.model_name,
                usage=usage,
                latency_ms=latency,
            )

            logger.log_event("AGENT_V1_STEP", {"step": steps, "llm_output": content[:500]})

            thought_text = ""
            if "Thought:" in content:
                thought_text = content.split("Thought:")[-1].split("Action:")[0].split("Final Answer:")[0].strip()

            # Check for Final Answer
            final_match = re.search(r"Final Answer:\s*(.+)", content, re.DOTALL)
            if final_match:
                answer = final_match.group(1).strip()
                self._emit({
                    "type": "thought", "step": steps,
                    "content": thought_text,
                    "tokens": dict(usage), "latency_ms": latency,
                }, on_step)
                self._emit({
                    "type": "final_answer", "step": steps,
                    "content": answer,
                    "total_tokens": dict(total_tokens),
                    "total_latency_ms": total_latency,
                    "status": "success",
                }, on_step)
                logger.log_event("AGENT_V1_END", {
                    "steps": steps, "status": "success",
                    "total_tokens": total_tokens, "total_latency_ms": total_latency,
                })
                return answer

            # Parse Action
            action_match = re.search(r"Action:\s*(\w+)\((.+?)\)", content)
            if not action_match:
                self._emit({
                    "type": "error", "step": steps,
                    "error_type": "parse_error",
                    "content": content[:200],
                    "tokens": dict(usage), "latency_ms": latency,
                }, on_step)
                logger.log_event("AGENT_V1_PARSE_ERROR", {"step": steps, "raw_output": content[:300]})
                prompt_parts.append(
                    "\nObservation: ERROR - Could not parse your Action. "
                    "Please use the format: Action: tool_name(argument)"
                )
                continue

            tool_name = action_match.group(1).strip()
            tool_arg = action_match.group(2).strip().strip("\"'")

            self._emit({
                "type": "thought", "step": steps,
                "content": thought_text,
                "tokens": dict(usage), "latency_ms": latency,
            }, on_step)

            observation = self._execute_tool(tool_name, tool_arg)

            self._emit({
                "type": "action", "step": steps,
                "tool": tool_name, "arg": tool_arg,
                "observation": observation[:500],
            }, on_step)

            logger.log_event("AGENT_V1_TOOL_CALL", {
                "step": steps, "tool": tool_name,
                "arg": tool_arg, "result": observation[:300],
            })

            prompt_parts.append(f"\nThought: {thought_text}")
            prompt_parts.append(f"Action: {tool_name}({tool_arg})")
            prompt_parts.append(f"Observation: {observation}")

        self._emit({
            "type": "final_answer", "step": steps,
            "content": "Max steps exceeded",
            "total_tokens": dict(total_tokens),
            "total_latency_ms": total_latency,
            "status": "max_steps_exceeded",
        }, on_step)
        logger.log_event("AGENT_V1_END", {
            "steps": steps, "status": "max_steps_exceeded",
            "total_tokens": total_tokens, "total_latency_ms": total_latency,
        })
        return "I was unable to find a complete answer within the allowed number of steps."

    def _execute_tool(self, tool_name: str, args: str) -> str:
        tool = self.tools.get(tool_name)
        if not tool:
            return f"Error: Tool '{tool_name}' not found. Available tools: {', '.join(self.tools.keys())}"
        try:
            func: Callable = tool["function"]
            return func(args)
        except Exception as e:
            return f"Error executing {tool_name}: {e}"
