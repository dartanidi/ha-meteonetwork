# README.md
# Home Assistant Meteonetwork Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]

A Home Assistant custom component to integrate Meteonetwork weather stations.

## Features

- ⭐ Real-time weather data from your Meteonetwork station
- 🌡️ Temperature, humidity, pressure sensors
- 💨 Wind speed, direction, and gusts
- 🌧️ Rain data (daily total and current rate)
- ⚙️ Configurable polling interval (1-60 minutes)
- 🎛️ Easy setup through Home Assistant UI
- 🔄 Automatic updates via HACS

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations" 
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/dartanidi/ha-meteonetwork`
6. Select category "Integration"
7. Click "Add"
8. Find "Meteonetwork" in HACS and install it
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/dartanidi/ha-meteonetwork/releases)
2. Copy the `meteonetwork` folder to your `custom_components` directory
3. Restart Home Assistant

## Configuration

### Through UI (Recommended)

1. Go to **Configuration** → **Integrations**
2. Click **Add Integration**
3. Search for "**Meteonetwork**"
4. Enter your:
   - **Station Code** (e.g., "IEMR0001")
   - **API Token** (from your Meteonetwork account)  
   - **Polling Interval** (1-60 minutes, default: 5)
5. Click **Submit**

### Getting Your Credentials

1. Register at [Meteonetwork.it](https://www.meteonetwork.it/)
2. Find your station code in your dashboard
3. Generate an API token in your account settings

## Sensors Created

The integration creates these sensors for your station:

| Sensor | Description | Unit |
|--------|-------------|------|
| `sensor.meteonetwork_temperatura` | Temperature | °C |
| `sensor.meteonetwork_umidita` | Humidity | % |
| `sensor.meteonetwork_pressione` | Atmospheric pressure | hPa |
| `sensor.meteonetwork_velocita_vento` | Wind speed | km/h |
| `sensor.meteonetwork_direzione_vento` | Wind direction | ° |
| `sensor.meteonetwork_raffiche_vento` | Wind gusts | km/h |
| `sensor.meteonetwork_temperatura_minima` | Daily minimum temperature | °C |
| `sensor.meteonetwork_temperatura_massima` | Daily maximum temperature | °C |
| `sensor.meteonetwork_pioggia_giornaliera` | Daily rainfall | mm |
| `sensor.meteonetwork_intensita_pioggia` | Rain rate | mm/h |
| `sensor.meteonetwork_punto_di_rugiada` | Dew point | °C |

## Options

You can modify these settings after installation:

- **Polling Interval**: How often to update data (1-60 minutes)

## Troubleshooting

### Integration not appearing
- Make sure all files are in `custom_components/meteonetwork/`
- Restart Home Assistant
- Check logs for errors

### Configuration errors
- Verify your API token is valid
- Check that the station code exists
- Ensure internet connectivity

### API errors
- Check Meteonetwork API status
- Verify your account has API access
- Try increasing polling interval if rate limited

## Support

- 🐛 [Report bugs](https://github.com/yourusername/ha-meteonetwork/issues)
- 💡 [Request features](https://github.com/yourusername/ha-meteonetwork/issues)
- 💬 [Discussions](https://github.com/yourusername/ha-meteonetwork/discussions)

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- Developed for the Home Assistant community
- Weather data provided by [Meteonetwork](https://www.meteonetwork.it/)

---

[releases-shield]: https://img.shields.io/github/release/dartanidi/ha-meteonetwork.svg
[releases]: https://github.com/dartanidi/ha-meteonetwork/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/dartanidi/ha-meteonetwork.svg
[commits]: https://github.com/dartanidi/ha-meteonetwork/commits/main
[license-shield]: https://img.shields.io/github/license/dartanidi/ha-meteonetwork.svg
[maintenance-shield]: https://img.shields.io/badge/maintainer-yourusername-blue.svg

---
