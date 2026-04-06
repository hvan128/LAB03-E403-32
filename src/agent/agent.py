import re
from typing import List, Dict, Any, Callable, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class ReActAgent:
    """
    Agent v1: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Implements the core loop logic and tool execution.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = {t["name"]: t for t in tools}
        self.max_steps = max_steps

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            f"- {name}: {t['description']}" for name, t in self.tools.items()
        )
        return f"""You are an intelligent assistant that solves tasks step-by-step.

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

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_V1_START", {"input": user_input, "model": self.llm.model_name})

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

            logger.log_event("AGENT_V1_STEP", {
                "step": steps,
                "llm_output": content[:500],
            })

            # Check for Final Answer
            final_match = re.search(r"Final Answer:\s*(.+)", content, re.DOTALL)
            if final_match:
                answer = final_match.group(1).strip()
                logger.log_event("AGENT_V1_END", {
                    "steps": steps,
                    "status": "success",
                    "total_tokens": total_tokens,
                    "total_latency_ms": total_latency,
                })
                return answer

            # Parse Action
            action_match = re.search(r"Action:\s*(\w+)\((.+?)\)", content)
            if not action_match:
                logger.log_event("AGENT_V1_PARSE_ERROR", {
                    "step": steps,
                    "raw_output": content[:300],
                })
                prompt_parts.append(
                    f"\nObservation: ERROR - Could not parse your Action. "
                    f"Please use the format: Action: tool_name(argument)"
                )
                continue

            tool_name = action_match.group(1).strip()
            tool_arg = action_match.group(2).strip().strip("\"'")

            observation = self._execute_tool(tool_name, tool_arg)

            logger.log_event("AGENT_V1_TOOL_CALL", {
                "step": steps,
                "tool": tool_name,
                "arg": tool_arg,
                "result": observation[:300],
            })

            prompt_parts.append(f"\nThought: {content.split('Thought:')[-1].split('Action:')[0].strip() if 'Thought:' in content else ''}")
            prompt_parts.append(f"Action: {tool_name}({tool_arg})")
            prompt_parts.append(f"Observation: {observation}")

        logger.log_event("AGENT_V1_END", {
            "steps": steps,
            "status": "max_steps_exceeded",
            "total_tokens": total_tokens,
            "total_latency_ms": total_latency,
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
