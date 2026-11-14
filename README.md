# Home Assistant Meteonetwork Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

A Home Assistant custom component to integrate Meteonetwork weather stations with automatic fallback support.

## Features

- ⭐ Real-time weather data from your Meteonetwork station
- 🔄 **Automatic Fallback Station**: seamless switch to a backup station if your primary station goes offline, returns empty data, or has stale readings
- 🌡️ Temperature, humidity, pressure sensors
- 💨 Wind speed, cardinal direction, and gusts
- 🌧️ Rain data (daily total and current precipitation rate)
- 📡 Active station status monitor & problem binary sensor
- ⚙️ Configurable polling interval (1-60 minutes) and staleness threshold (15-360 minutes)
- 🎛️ Easy setup and options through Home Assistant UI
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
   - **Station Code**: Primary station (e.g., "lmb015")
   - **API Token**: Personal API token from Meteonetwork
   - **Fallback Station Code** *(Optional)*: Backup station (e.g., "lmb254")
   - **Polling Interval**: Update frequency (1-60 minutes, default: 5)
   - **Stale Threshold**: Minutes of inactivity before considering primary station offline (15-360 minutes, default: 60)
5. Click **Submit**

### Getting Your Credentials

1. Register and get a free API token at [Meteonetwork.it](https://www.meteonetwork.it/supporto/meteonetwork-api/)
2. Find your station code in the [weather stations map](https://www.meteonetwork.it/rete/livemap/)

## Entities Created

### Weather Sensors

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

### Monitoring & Fallback Sensors

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.meteonetwork_stazione_attiva` | Sensor | Indicates whether the primary or fallback station is active (e.g. `Principale: Bologna (LMB015)`) |
| `binary_sensor.meteonetwork_fallback_attivo` | Binary Sensor (Problem) | Turns `ON` when the fallback station is in use, `OFF` when the primary station is working normally |

## Options

You can modify these settings anytime after installation from **Settings** → **Devices & Services** → **Meteonetwork** → **Configure**:

- **Fallback Station Code**: Add, change, or remove the backup station
- **Polling Interval**: How often to fetch data (1-60 minutes)
- **Stale Threshold**: Minutes without new data after which the primary station is marked offline (15-360 minutes)

## Troubleshooting

### Integration not appearing
- Make sure all files are in `custom_components/meteonetwork/`
- Restart Home Assistant
- Check Home Assistant logs for errors

### Configuration errors
- Verify your API token is valid
- Check that both primary and fallback station codes exist on Meteonetwork
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
