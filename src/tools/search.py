"""Simulated web search tool for the ReAct agent."""

_KNOWLEDGE_BASE = {
    "vietnam population": "Vietnam has a population of approximately 100 million people (2024).",
    "python creator": "Python was created by Guido van Rossum and first released in 1991.",
    "largest ocean": "The Pacific Ocean is the largest and deepest ocean on Earth, covering about 165.25 million km².",
    "capital of france": "The capital of France is Paris.",
    "capital of vietnam": "The capital of Vietnam is Hanoi.",
    "eiffel tower height": "The Eiffel Tower is 330 metres (1,083 ft) tall, including antennas.",
    "speed of light": "The speed of light in vacuum is approximately 299,792,458 metres per second (about 3 × 10^8 m/s).",
    "react agent": "A ReAct agent combines Reasoning and Acting — it uses a Thought-Action-Observation loop to solve tasks step by step.",
    "machine learning": "Machine learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed.",
}


def search(query: str) -> str:
    """
    Searches a simulated knowledge base for information.

    Args:
        query: A search query string, e.g. "capital of France"
    Returns:
        A relevant answer string, or a not-found message.
    """
    query_lower = query.strip().lower()
    for key, value in _KNOWLEDGE_BASE.items():
        if key in query_lower or query_lower in key:
            return value
    # Fuzzy: check if any keyword overlaps
    query_words = set(query_lower.split())
    best_match = None
    best_score = 0
    for key, value in _KNOWLEDGE_BASE.items():
        key_words = set(key.split())
        overlap = len(query_words & key_words)
        if overlap > best_score:
            best_score = overlap
            best_match = value
    if best_match and best_score >= 1:
        return best_match
    return f"No results found for '{query}'."
