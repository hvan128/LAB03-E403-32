import math


def calculator(expression: str) -> str:
    """
    Evaluates a mathematical expression and returns the result.
    Supports basic arithmetic (+, -, *, /) and common math functions (sqrt, pow, sin, cos, etc.).

    Args:
        expression: A math expression string, e.g. "2 + 3 * 4" or "sqrt(144)"
    Returns:
        The computed result as a string, or an error message.
    """
    allowed_names = {
        "sqrt": math.sqrt,
        "pow": math.pow,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "abs": abs,
        "round": round,
        "pi": math.pi,
        "e": math.e,
    }
    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Error: {e}"
