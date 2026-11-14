# Home Assistant Meteonetwork Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

A Home Assistant custom component to integrate Meteonetwork weather stations.

## Features

- ⭐ Real-time weather data from your Meteonetwork station
- 🌡️ Temperature, humidity, pressure sensors
- 💨 Wind speed, cardinal direction, and gusts
- 🌧️ Rain data (daily total and current precipitation rate)
- ⚙️ Configurable polling interval (1-60 minutes)
- 🎛️ Easy setup through Home Assistant UI
- 🔄 Automatic updates via Home Assistant Marketplace / HACS

## Installation

### Marketplace / HACS (Recommended)

#### Home Assistant 2026.11+ (Native Marketplace)
1. In Home Assistant, navigate to **Settings** → **Marketplace**
2. Click the three dots in the top right corner
3. Select **Custom repositories**
4. Add repository URL: `https://github.com/dartanidi/ha-meteonetwork`
5. Select category: **Integration**
6. Click **Add**, find **Meteonetwork** and install it
7. Restart Home Assistant

#### Older Home Assistant versions (HACS)
1. Open **HACS** in Home Assistant
2. Go to **Integrations** 
3. Click the three dots in the top right corner
4. Select **Custom repositories**
5. Add repository URL: `https://github.com/dartanidi/ha-meteonetwork`
6. Select category: **Integration**
7. Click **Add**, find **Meteonetwork** and install it
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/dartanidi/ha-meteonetwork/releases)
2. Copy the `custom_components/meteonetwork` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

### Through UI (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "**Meteonetwork**"
4. Enter your:
   - **Station Code** (e.g., "lmb015")
   - **API Token** (from your Meteonetwork account)  
   - **Polling Interval** (1-60 minutes, default: 5)
5. Click **Submit**

### Getting Your Credentials

1. Register and get a free API token at [Meteonetwork.it](https://www.meteonetwork.it/supporto/meteonetwork-api/)
2. Find your station code in the [weather stations map](https://www.meteonetwork.it/rete/livemap/)

## Sensors Created

The integration creates these 11 sensors for your station:

| Sensor | Description | Unit |
|--------|-------------|------|
| `sensor.meteonetwork_temperatura` | Temperature | °C |
| `sensor.meteonetwork_umidita` | Humidity | % |
| `sensor.meteonetwork_pressione` | Atmospheric pressure | hPa |
| `sensor.meteonetwork_velocita_vento` | Wind speed | km/h |
| `sensor.meteonetwork_direzione_vento` | Wind direction | Cardinal (e.g. N, SW) |
| `sensor.meteonetwork_raffiche_vento` | Wind gusts | km/h |
| `sensor.meteonetwork_temperatura_minima` | Daily minimum temperature | °C |
| `sensor.meteonetwork_temperatura_massima` | Daily maximum temperature | °C |
| `sensor.meteonetwork_pioggia_giornaliera` | Daily rainfall | mm |
| `sensor.meteonetwork_intensita_pioggia` | Rain rate | mm/h |
| `sensor.meteonetwork_punto_di_rugiada` | Dew point | °C |

## Options

You can modify these settings after installation:

- **Polling Interval**: How often to update data (1-60 minutes) directly from the integration Options menu.

## Troubleshooting

### Integration not appearing
- Make sure all files are in `custom_components/meteonetwork/`
- Restart Home Assistant
- Check Home Assistant logs for errors

### Configuration errors
- Verify your API token is valid
- Check that the station code exists
- Ensure internet connectivity

### API errors
- Check Meteonetwork API status
- Verify your account has API access
- Try increasing polling interval if rate limited

## Support

- 🐛 [Report bugs](https://github.com/dartanidi/ha-meteonetwork/issues)
- 💡 [Request features](https://github.com/dartanidi/ha-meteonetwork/issues)
- 💬 [Discussions](https://github.com/dartanidi/ha-meteonetwork/discussions)

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
