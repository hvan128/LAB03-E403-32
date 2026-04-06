import random

# Simulated weather database
_WEATHER_DATA = {
    "hanoi": {"temp_c": 32, "condition": "Sunny", "humidity": 70},
    "ho chi minh": {"temp_c": 34, "condition": "Partly Cloudy", "humidity": 75},
    "da nang": {"temp_c": 30, "condition": "Rainy", "humidity": 85},
    "new york": {"temp_c": 18, "condition": "Cloudy", "humidity": 60},
    "london": {"temp_c": 12, "condition": "Rainy", "humidity": 80},
    "tokyo": {"temp_c": 22, "condition": "Sunny", "humidity": 55},
    "paris": {"temp_c": 15, "condition": "Cloudy", "humidity": 65},
    "sydney": {"temp_c": 25, "condition": "Sunny", "humidity": 50},
}


def get_weather(city: str) -> str:
    """
    Returns the current weather for a given city.

    Args:
        city: Name of the city (case-insensitive), e.g. "Hanoi", "New York"
    Returns:
        A string describing the weather, or an error if city not found.
    """
    city_lower = city.strip().lower()
    data = _WEATHER_DATA.get(city_lower)
    if data:
        return (
            f"Weather in {city.title()}: {data['condition']}, "
            f"{data['temp_c']}°C, Humidity: {data['humidity']}%"
        )
    return f"Weather data not found for '{city}'. Available cities: {', '.join(c.title() for c in _WEATHER_DATA)}"
