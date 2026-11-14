"""Constants for the Meteonetwork integration."""
from datetime import timedelta

DOMAIN = "meteonetwork"
CONF_STATION_CODE = "station_code"

# API Configuration
API_BASE_URL = "https://api.meteonetwork.it/v3/data-realtime"
API_TIMEOUT = 10

# Scan interval defaults and limits (in minutes)
DEFAULT_SCAN_INTERVAL = 5
MIN_SCAN_INTERVAL = 1
MAX_SCAN_INTERVAL = 60
DEFAULT_SCAN_INTERVAL_TIMEDELTA = timedelta(minutes=DEFAULT_SCAN_INTERVAL)

# Mapping of internal sensor types to API response keys
SENSOR_KEY_MAP = {
    "temperature": "temperature",
    "pressure": "smlp",
    "humidity": "rh",
    "wind_speed": "wind_speed",
    "wind_direction": "wind_direction",
    "wind_gust": "wind_gust",
    "temp_min": "current_tmin",
    "temp_max": "current_tmax",
    "daily_rain": "daily_rain",
    "rain_rate": "rain_rate",
    "dew_point": "dew_point",
}
