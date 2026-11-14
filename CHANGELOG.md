# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-11-14

### Added
- **Automatic Fallback Station**: support for a secondary backup weather station if the primary station goes offline, returns empty data, or has stale readings.
- **Staleness Detection**: configurable threshold (15-360 minutes, default: 60 min) to detect frozen or outdated observations via `observation_time_utc`.
- **Active Station Sensor** (`sensor.meteonetwork_stazione_attiva`): displays which station (primary or fallback) is currently active, with station code, place name, and timestamp attributes.
- **Fallback Binary Sensor** (`binary_sensor.meteonetwork_fallback_attivo`): problem binary sensor that switches to `ON` when the fallback station is in use, ideal for alerts and automations.
- Dynamic options configuration for the fallback station and staleness threshold directly from the Home Assistant integration UI.

### Changed
- Expanded integration platforms to include `Platform.BINARY_SENSOR`.
- Updated documentation across `README.md` and `INFO.md` to reflect all 13 created entities.

---

## [1.2.0] - 2026-11-14

### Added
- Dedicated constants module (`const.py`) centralizing endpoints, timeouts, domain, and sensor mappings.
- Dedicated coordinator module (`coordinator.py`) decoupling the core integration from the sensor platform.
- Native `asyncio.timeout` replacing the deprecated `async_timeout` package.
- Safe station metadata handling with `configuration_url` in device info linking directly to the Meteonetwork live map.

### Changed
- **Entity ID Naming**: implemented `_attr_suggested_object_id` to generate clean entity IDs in the form `sensor.meteonetwork_<sensor_name>` while keeping the station name in `device_info`.
- Modernized integration lifecycle using `entry.runtime_data = coordinator` and `entry.async_on_unload(...)`.
- Corrected precipitation measurement units using `UnitOfPrecipitationDepth.MILLIMETERS` for daily rainfall and `UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR` for rain rate.
- Enhanced Config Flow with input sanitization (`.strip()`, `.lower()`) and password masking for the API token.
- Cleaned up `hacs.json` removing obsolete fields.

### Fixed
- Fixed critical data corruption where missing sensor values defaulted to `0`, which caused the cardinal `wind_direction` sensor to return `0.0` instead of `None`.
- Fixed authentication error suppression: allowed `ConfigEntryAuthFailed` to propagate cleanly so Home Assistant triggers native re-authentication instead of entering infinite reload loops.
- Fixed unreachable Config Flow error translations for `timeout` and `no_data`.

### Removed
- Removed orphaned `services.yaml` file declaring an unregistered custom service.
- Removed duplicate static station attributes from all sensor entities to optimize Home Assistant recorder database size.

---

## [1.1.1] - 2026-06-03

### Changed
- Initial attempt at modern entity naming with `_attr_has_entity_name = True`.

---

## [1.1.0] - 2026-06-03

### Added
- Configurable polling interval in the options flow.

### Changed
- Updated manifest version to `1.1.0`.

---

## [1.0.0] - 2026-05-18

### Added
- Initial release of the Meteonetwork Home Assistant custom integration.
- Real-time weather data retrieval via Meteonetwork API v3.
- Sensor platform supporting 11 core weather parameters (temperature, humidity, pressure, wind, rain, dew point).
- Config Flow for configuration through the Home Assistant UI.
