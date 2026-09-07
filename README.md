# i-DE (Iberdrola Distribución) Custom Integration for Home Assistant

<!-- HomeAssistant badges -->
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![hassfest validation](https://github.com/alessbarb/ha-ideenergy/workflows/Validate%20with%20hassfest/badge.svg)](https://github.com/alessbarb/ha-ideenergy/actions/workflows/hassfest.yml)
[![HACS validation](https://github.com/alessbarb/ha-ideenergy/workflows/Validate%20with%20HACS/badge.svg)](https://github.com/alessbarb/ha-ideenergy/actions/workflows/hacs.yml)

<!-- Code and releases -->
![GitHub Release (latest SemVer including pre-releases)](https://img.shields.io/github/v/release/alessbarb/ha-ideenergy?include_prereleases)
[![CodeQL](https://github.com/alessbarb/ha-ideenergy/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/alessbarb/ha-ideenergy/actions/workflows/codeql-analysis.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

[ideenergy](https://github.com/alessbarb/ideenergy) integration for [Home Assistant](https://home-assistant.io/).

i-DE (Iberdrola Distribución) Custom Integration for Home Assistant, providing energy data for customers of the Spanish electricity distributor [i-DE](https://i-de.es).

This integration requires an **advanced** user profile on the i-DE website.

> **3.x is an alpha series.** It is a rewrite of the 2.x integration and uses Home Assistant statistics instead of manipulating the recorder database directly. Read the [upgrade notes](UPGRADE-TO-3.x.md) before migrating an existing installation.

**Please read the [FAQ](FAQ.md), Dependencies and Warnings sections before installing.**

## Maintained fork

This repository is a maintained fork of [`ldotlopez/ha-ideenergy`](https://github.com/ldotlopez/ha-ideenergy). Original authorship and GPL-3.0 licensing are preserved. Issues, compatibility fixes and releases for this fork are tracked in [`alessbarb/ha-ideenergy`](https://github.com/alessbarb/ha-ideenergy).

## Features in 3.x

- Home Assistant Energy Dashboard integration through statistics.
- Accumulated consumption sensor based on direct meter readings.
- Historical consumption statistics with sub-kWh precision.
- Historical generation statistics, disabled by default.
- Support for multiple contracts/service points as separate config entries.
- Configuration through the Home Assistant UI; no YAML configuration is required.
- Asynchronous API access and Home Assistant `DataUpdateCoordinator` integration.
- Persistent per-dataset request throttling, so restart cycles do not reset the normal fetch interval.

### Current request intervals

The coordinator itself wakes periodically, but remote i-DE datasets are fetched only when their own refresh window is due:

| Dataset | After a successful fetch | After a failed attempt |
| --- | ---: | ---: |
| Accumulated/direct meter reading | 6 hours | 5 minutes |
| Historical consumption | 12 hours | 5 minutes |
| Historical generation | 12 hours | 5 minutes |

These limits are intentional. The i-DE service-point API is unreliable and excessive requests can result in temporary account blocking.

### Two-factor authentication

i-DE can require an SMS verification code before allowing a session. The private web API used by this integration does not currently expose a documented, stable OTP challenge flow that the maintained client can safely implement, so 3.x does **not** claim native SMS/OTP support.

Ordinary expired credentials or rejected sessions can enter Home Assistant's re-authentication lifecycle. An i-DE SMS challenge is different: complete the required verification through i-DE's own website or app. The integration deliberately does not increase background request frequency merely to keep a post-2FA session alive, because i-DE can block accounts for excessive automated access. See the [FAQ](FAQ.md) for details.

### Not currently exposed in 3.x

The 3.x code can receive an instantaneous value together with a direct meter reading, but it does **not** currently expose a separate Instant Consumption entity. Documentation from the 2.x series that referred to an instant sensor or to an hourly minute-50-to-59 update window does not describe the current 3.x implementation.

## Dependencies

You need an i-DE username and access to the customer website. You can register through the [i-DE customer area](https://www.i-de.es/consumidores/web/guest/login).

An **Advanced User** profile is also required. If your account does not have one, request it from the profile area on the i-DE website.

The integration pins the maintained [`alessbarb/ideenergy`](https://github.com/alessbarb/ideenergy) client to an immutable Git commit and also depends on [`homeassistant-historical-sensor`](https://github.com/ldotlopez/ha-historical-sensor).

## Installation

### HACS custom repository

1. Open HACS in Home Assistant.
2. Add `https://github.com/alessbarb/ha-ideenergy` as a **Custom repository** with category **Integration**.
3. Download the desired release.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration** and select **i-DE Energy Monitor**.
6. Enter your i-DE credentials and select the contract/service point to monitor.

To monitor more than one service point, add one config entry per contract.

### Manual installation

1. Download or clone this repository.
2. Copy `custom_components/ideenergy` into the `custom_components` directory of your Home Assistant configuration.
3. Restart Home Assistant.
4. Add **i-DE Energy Monitor** from **Settings → Devices & services**.
5. Enter your credentials and select the contract to monitor.

## Screenshots

*Accumulated energy sensor*

![snapshot](screenshots/accumulated.png)

*Historical energy sensor*

![snapshot](screenshots/historical.png)

*Configuration wizard*

![snapshot](screenshots/configuration-1.png)
![snapshot](screenshots/configuration-2.png)

## Warnings

- The 3.x series is still alpha software and can change between prereleases.
- i-DE does not provide a public API contract for this integration. Changes to its website/private endpoints can break authentication or data retrieval without notice.
- i-DE may require SMS two-factor authentication. Native OTP challenge handling is not currently implemented.
- Direct meter readings are notably less reliable than historical data. Do not build safety-critical or unattended control logic around them.
- Be conservative with direct-reading sensors when several contracts are configured. Excessive service-point requests can trigger temporary blocking by i-DE.
- Historical data is delayed by i-DE, commonly by roughly 24 to 48 hours.

## License

This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE).

## Disclaimer

THIS PROJECT IS NOT IN ANY WAY ASSOCIATED WITH OR RELATED TO THE IBERDROLA GROUP COMPANIES OR ANY OTHER. The information here and online is for educational and resource purposes only and therefore the developers do not endorse or condone any inappropriate use of it, and take no legal responsibility for the functionality or security of your devices.
