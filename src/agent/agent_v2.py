import re
from typing import List, Dict, Any, Callable, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class ReActAgentV2:
    """
    Agent v2: Improved ReAct Agent with few-shot examples, better parsing,
    hallucination guardrails, and retry logic.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 7):
        self.llm = llm
        self.tools = {t["name"]: t for t in tools}
        self.max_steps = max_steps
        self.max_parse_retries = 2
        self.trace = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            f"- {name}({t.get('arg_name', 'input')}): {t['description']}"
            for name, t in self.tools.items()
        )
        tool_names = ", ".join(self.tools.keys())

        return f"""You are an intelligent assistant that solves tasks step-by-step using the ReAct framework.

## Available Tools
{tool_descriptions}

## Output Format (STRICT)
You MUST follow this format exactly. Do not deviate.

Thought: <your reasoning>
Action: <tool_name>(<argument>)

Wait for the Observation, then continue:

Thought: <your reasoning based on the observation>
Action: <tool_name>(<argument>)

When you have enough information:

Thought: I now have all the information needed.
Final Answer: <your complete answer>

## Rules
1. Only use tools from this list: [{tool_names}].
2. Call exactly ONE tool per step.
3. Action format MUST be: tool_name(argument) — no quotes around the function call.
4. The argument should be a simple string (no JSON, no key=value).
5. Always begin with Thought before Action or Final Answer.
6. If a tool returns an error, reason about it and try a different approach.

## Example

User question: What is the weather in Hanoi and what is 25 * 4?

Thought: I need to find the weather in Hanoi first.
Action: get_weather(Hanoi)

Observation: Weather in Hanoi: Sunny, 32°C, Humidity: 70%

Thought: Now I need to calculate 25 * 4.
Action: calculator(25 * 4)

Observation: 100

Thought: I now have all the information needed.
Final Answer: The weather in Hanoi is Sunny at 32°C with 70% humidity, and 25 × 4 = 100.
"""

    def _emit(self, entry: dict, on_step=None):
        self.trace.append(entry)
        if on_step:
            on_step(list(self.trace))

    def run(self, user_input: str, on_step=None) -> str:
        logger.log_event("AGENT_V2_START", {"input": user_input, "model": self.llm.model_name})

        self.trace = []
        self._emit({"type": "input", "content": user_input}, on_step)

        history = [f"User question: {user_input}"]
        steps = 0
        parse_retries = 0
        total_tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        total_latency = 0

        while steps < self.max_steps:
            steps += 1
            current_prompt = "\n\n".join(history)

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

            logger.log_event("AGENT_V2_STEP", {"step": steps, "llm_output": content[:500]})

            thought_text = ""
            if "Thought:" in content:
                thought_text = content.split("Thought:")[-1].split("Action:")[0].split("Final Answer:")[0].strip()

            # --- Check for Final Answer ---
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
                logger.log_event("AGENT_V2_END", {
                    "steps": steps, "status": "success",
                    "total_tokens": total_tokens, "total_latency_ms": total_latency,
                })
                return answer

            # --- Parse Action ---
            action_match = re.search(
                r"Action:\s*(\w+)\(\s*[\"']?(.*?)[\"']?\s*\)", content, re.DOTALL,
            )

            if not action_match:
                parse_retries += 1
                self._emit({
                    "type": "error", "step": steps,
                    "error_type": "parse_error",
                    "content": content[:200],
                    "tokens": dict(usage), "latency_ms": latency,
                }, on_step)
                logger.log_event("AGENT_V2_PARSE_ERROR", {
                    "step": steps, "retry": parse_retries, "raw_output": content[:300],
                })
                if parse_retries > self.max_parse_retries:
                    self._emit({
                        "type": "final_answer", "step": steps,
                        "content": "Parse error exceeded",
                        "total_tokens": dict(total_tokens),
                        "total_latency_ms": total_latency,
                        "status": "parse_error_exceeded",
                    }, on_step)
                    logger.log_event("AGENT_V2_END", {
                        "steps": steps, "status": "parse_error_exceeded",
                        "total_tokens": total_tokens, "total_latency_ms": total_latency,
                    })
                    return "I encountered repeated formatting errors and could not complete the task."

                history.append(
                    f"Observation: FORMAT ERROR — Your response did not contain a valid Action.\n"
                    f"Remember: use exactly this format:\n"
                    f"Thought: <reasoning>\n"
                    f"Action: tool_name(argument)\n"
                    f"Available tools: {', '.join(self.tools.keys())}"
                )
                continue

            tool_name = action_match.group(1).strip()
            tool_arg = action_match.group(2).strip()

            # --- Guardrail: hallucinated tool ---
            if tool_name not in self.tools:
                self._emit({
                    "type": "error", "step": steps,
                    "error_type": "hallucination",
                    "content": f"Hallucinated tool: {tool_name}",
                    "tokens": dict(usage), "latency_ms": latency,
                }, on_step)
                logger.log_event("AGENT_V2_HALLUCINATION", {
                    "step": steps, "hallucinated_tool": tool_name,
                })
                history.append(
                    f"Observation: ERROR — Tool '{tool_name}' does not exist.\n"
                    f"Available tools: {', '.join(self.tools.keys())}.\n"
                    f"Please choose one of the available tools."
                )
                continue

            # --- Record thought ---
            self._emit({
                "type": "thought", "step": steps,
                "content": thought_text,
                "tokens": dict(usage), "latency_ms": latency,
            }, on_step)

            # --- Execute tool ---
            observation = self._execute_tool(tool_name, tool_arg)
            parse_retries = 0

            self._emit({
                "type": "action", "step": steps,
                "tool": tool_name, "arg": tool_arg,
                "observation": observation[:500],
            }, on_step)

            logger.log_event("AGENT_V2_TOOL_CALL", {
                "step": steps, "tool": tool_name,
                "arg": tool_arg, "result": observation[:300],
            })

            history.append(f"Thought: {thought_text}")
            history.append(f"Action: {tool_name}({tool_arg})")
            history.append(f"Observation: {observation}")

        self._emit({
            "type": "final_answer", "step": steps,
            "content": "Max steps exceeded",
            "total_tokens": dict(total_tokens),
            "total_latency_ms": total_latency,
            "status": "max_steps_exceeded",
        }, on_step)
        logger.log_event("AGENT_V2_END", {
            "steps": steps, "status": "max_steps_exceeded",
            "total_tokens": total_tokens, "total_latency_ms": total_latency,
        })
        return "I reached the maximum number of reasoning steps without finding a complete answer."

    def _execute_tool(self, tool_name: str, args: str) -> str:
        tool = self.tools.get(tool_name)
        if not tool:
            return f"Error: Tool '{tool_name}' not found."
        try:
            func: Callable = tool["function"]
            return func(args)
        except Exception as e:
            return f"Error executing {tool_name}: {e}"
