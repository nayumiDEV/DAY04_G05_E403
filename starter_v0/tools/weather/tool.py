from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err


def get_weather(city: str = "", units: str = "celsius") -> dict[str, Any]:
    try:
        if not city:
            return {"tool": "get_weather", "error": "missing city", "message": "Please provide a city name."}
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        current = data.get("current_condition", [{}])[0]
        temp_c = current.get("temp_C", "N/A")
        temp_f = current.get("temp_F", "N/A")
        desc = current.get("weatherDesc", [{}])[0].get("value", "N/A")
        humidity = current.get("humidity", "N/A")
        wind = current.get("windspeedKmph", "N/A")
        feels_c = current.get("FeelsLikeC", "N/A")
        feels_f = current.get("FeelsLikeF", "N/A")
        temp = temp_c if units == "celsius" else temp_f
        feels = feels_c if units == "celsius" else feels_f
        unit_label = "°C" if units == "celsius" else "°F"
        return {
            "tool": "get_weather",
            "city": city,
            "temperature": f"{temp}{unit_label}",
            "feels_like": f"{feels}{unit_label}",
            "description": desc,
            "humidity": f"{humidity}%",
            "wind_speed": f"{wind} km/h",
            "summary": f"Weather in {city}: {desc}, {temp}{unit_label}, feels like {feels}{unit_label}.",
        }
    except Exception as exc:
        return err("get_weather", exc)
