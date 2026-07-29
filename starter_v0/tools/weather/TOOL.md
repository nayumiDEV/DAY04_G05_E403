---
name: weather
track: core
kind: lookup
requires_env: []
inputs: [city, units]
outputs: [city, temperature, feels_like, description, humidity, wind_speed, summary]
side_effect: false
---
# weather

Get current weather conditions for any city worldwide using wttr.in (free API, no key required).
Use when the user asks about "weather", "thời tiết", "temperature", or current conditions.
Returns temperature, feels-like, description, humidity, and wind speed.
