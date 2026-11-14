# info.md
## Meteonetwork Integration for Home Assistant

Integrates your Meteonetwork weather station data directly into Home Assistant with automatic fallback support.

### Features

- Real-time weather data from your personal station
- Automatic fallback station when primary station is offline, empty, or stale
- 11 weather sensors (temperature, humidity, wind, rain, dew point, etc.)
- Active station monitor sensor and fallback binary sensor
- Configurable update intervals (1-60 minutes) and staleness threshold
- Easy setup and options through Home Assistant UI

### Requirements

- Active Meteonetwork account
- API token from Meteonetwork
- Station code (and optional fallback station code)

### Quick Setup

1. Install via Home Assistant Marketplace / HACS or manually
2. Go to Settings → Devices & Services → Add Integration
3. Add "Meteonetwork" integration
4. Enter your station code, API token, and optional fallback station
5. Choose polling interval and staleness threshold

### Support

- [Documentation](https://github.com/dartanidi/ha-meteonetwork)
- [Issues & Bugs](https://github.com/dartanidi/ha-meteonetwork/issues)
- [Feature Requests](https://github.com/dartanidi/ha-meteonetwork/discussions)
