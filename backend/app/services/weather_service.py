import json
import urllib.request
from typing import Optional


class WeatherService:
    def get_weather(self, latitude: float = 17.3850, longitude: float = 78.4867):
        """
        Fetch current weather context from Open-Meteo.
        Fails gracefully without throwing errors if network is unavailable.
        """
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}&longitude={longitude}"
            f"&current=temperature_2m,relative_humidity_2m,precipitation,rain,weather_code"
            f"&temperature_unit=celsius"
            f"&timezone=auto"
        )

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CropDiseaseAI/1.0"})
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            current = data.get("current", {})
            weather_code = current.get("weather_code", 0)

            condition_desc = self._interpret_weather_code(weather_code)

            temp = current.get("temperature_2m")
            humidity = current.get("relative_humidity_2m")
            precip = current.get("precipitation")
            rain = current.get("rain")

            # Risk assessment for crop disease
            risk_message = self._assess_disease_risk(humidity, rain, precip)

            return {
                "available": True,
                "temperature": round(temp, 1) if temp is not None else None,
                "humidity": round(humidity) if humidity is not None else None,
                "precipitation": round(precip, 1) if precip is not None else 0.0,
                "rain": round(rain, 1) if rain is not None else 0.0,
                "weather_code": weather_code,
                "condition": condition_desc,
                "risk_message": risk_message,
                "latitude": latitude,
                "longitude": longitude,
                "units": {
                    "temperature": "°C",
                    "humidity": "%",
                    "precipitation": "mm",
                    "rain": "mm"
                }
            }
        except Exception as exc:
            # Graceful failure as requested
            return {
                "available": False,
                "error": str(exc),
                "temperature": None,
                "humidity": None,
                "precipitation": 0.0,
                "rain": 0.0,
                "condition": "Unavailable",
                "risk_message": "Weather context is currently unavailable.",
                "units": {}
            }

    def _interpret_weather_code(self, code: int) -> str:
        if code == 0:
            return "Clear sky"
        elif code in (1, 2, 3):
            return "Partly cloudy"
        elif code in (45, 48):
            return "Foggy"
        elif code in (51, 53, 55):
            return "Drizzle"
        elif code in (61, 63, 65):
            return "Rain"
        elif code in (80, 81, 82):
            return "Rain showers"
        elif code in (95, 96, 99):
            return "Thunderstorm"
        return "Overcast"

    def _assess_disease_risk(self, humidity, rain, precip) -> str:
        h = humidity or 0
        r = (rain or 0) + (precip or 0)
        if h >= 80 or r > 0:
            return "High humidity or rainfall detected: wet foliage elevates fungal and bacterial infection risk."
        elif h >= 65:
            return "Moderate humidity: monitor vulnerable crops for early signs of fungal leaf spots."
        return "Dry atmospheric conditions: low immediate fungal spore dispersal risk."


weather_service = WeatherService()
