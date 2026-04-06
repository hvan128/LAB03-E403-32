"""Central registry of all available tools for the ReAct agent."""

from src.tools.calculator import calculator
from src.tools.weather import get_weather
from src.tools.search import search

TOOLS = [
    {
        "name": "calculator",
        "description": "Evaluates a mathematical expression. Supports +, -, *, /, sqrt, pow, sin, cos, log, etc.",
        "arg_name": "expression",
        "function": calculator,
    },
    {
        "name": "get_weather",
        "description": "Returns current weather for a city (e.g. Hanoi, Tokyo, London, New York, Paris, Sydney, Ho Chi Minh, Da Nang).",
        "arg_name": "city",
        "function": get_weather,
    },
    {
        "name": "search",
        "description": "Searches a knowledge base for factual information. Use for general knowledge questions.",
        "arg_name": "query",
        "function": search,
    },
]
