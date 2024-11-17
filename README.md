[![HACS][hacs-shield]][hacs-link]
[![GitHub Release][releases-shield]][releases-link]
[![Project Maintenance][maintenance-shield]][maintenance-link]

## Overview

This is a hard fork of [xMrVizzy/philips-airpurifier](https://github.com/xMrVizzy/philips-airpurifier).

This is a custom Home Assistant component that enables you to control your Philips Air Purifier devices.
For now, it supports only older models that use the HTTP protocol for communication. CoAP support comming soon. :)

## Installation

### Install manually

Download the `philips_airpurifier_http` folder from this repo and place it in your `custom_components` folder

### Via HACS

Add this repo as a Custom Repository in HACS and install as an Integration from HACS' UI.

## Usage

```yaml
fan:
  platform: philips_airpurifier_http
  host: 192.168.0.17
```

## Configuration variables

| Field    | Value                      | Necessity  | Description                  |
| -------- | -------------------------- | ---------- | ---------------------------- |
| platform | `philips_airpurifier_http` | _Required_ | The platform name.           |
| host     | 192.168.0.17               | _Required_ | IP address of your Purifier. |
| name     | Philips Air Purifier       | Optional   | Name of the Fan.             |

---

## Services

### `fan.set_preset_mode`

Set the device mode (if supported)

| Field       | Value               | Necessity  | Description                                              |
| ----------- | ------------------- | ---------- | -------------------------------------------------------- |
| entity_id   | `"fan.living_room"` | _Required_ | Name(s) of the entities to set mode                      |
| preset_mode | `"allergen"`        | _Required_ | One of "auto", "allergen", "sleep", "bacteria", "night". |

### `philips_airpurifier_http.set_function`

Set the device function (if supported)

| Field     | Value                             | Necessity  | Description                                               |
| --------- | --------------------------------- | ---------- | --------------------------------------------------------- |
| entity_id | `"fan.living_room"`               | _Required_ | Name(s) of the entities to set function                   |
| function  | `"Purification & Humidification"` | _Required_ | One of "Purification" or "Purification & Humidification". |

### `philips_airpurifier.set_target_humidity`

Set the device target humidity (if supported)

| Field     | Value               | Necessity  | Description                                    |
| --------- | ------------------- | ---------- | ---------------------------------------------- |
| entity_id | `"fan.living_room"` | _Required_ | Name(s) of the entities to set target humidity |
| humidity  | `40`                | _Required_ | One of 40, 50, 60                              |

### `philips_airpurifier.set_light_brightness`

Set the device light brightness

| Field     | Value               | Necessity  | Description                                                           |
| --------- | ------------------- | ---------- | --------------------------------------------------------------------- |
| entity_id | `"fan.living_room"` | _Required_ | Name(s) of the entities to set light brightness                       |
| level     | `50`                | _Required_ | One of 0, 25, 50, 75, 100. Turns off the display light if level is 0. |

### `philips_airpurifier_http.set_child_lock`

Set the device child lock on or off

| Field     | Value               | Necessity  | Description                               |
| --------- | ------------------- | ---------- | ----------------------------------------- |
| entity_id | `"fan.living_room"` | _Required_ | Name(s) of the entities to set child lock |
| lock      | `true`              | _Required_ | true or false                             |

### `philips_airpurifier_http.set_timer`

Set the device off time

| Field     | Value               | Necessity  | Description                              |
| --------- | ------------------- | ---------- | ---------------------------------------- |
| entity_id | `"fan.living_room"` | _Required_ | Name(s) of the entities to set off timer |
| hours     | `5`                 | _Required_ | Hours between 0 and 12                   |

### `philips_airpurifier_http.set_display_light`

Set the device display light on or off

| Field     | Value               | Necessity  | Description                                  |
| --------- | ------------------- | ---------- | -------------------------------------------- |
| entity_id | `"fan.living_room"` | _Required_ | Name(s) of the entities to set display light |
| light     | `true`              | _Required_ | true or false                                |

### `philips_airpurifier_http.set_used_index`

Sets the device used index(IAI or PM2.5)

| Field      | Value               | Necessity  | Description                                  |
| ---------- | ------------------- | ---------- | -------------------------------------------- |
| entity_id  | `"fan.living_room"` | _Required_ | Name(s) of the entities to set display light |
| used_index | `"IAI"`             | _Required_ | One of "IAI" or "PM2.5".                     |

## Meta

**Georgi Gardev**

- [gar.dev](https://gar.dev)
- [![GitHub][github-icon]][github-link] [GeorgeSG][github-link]
- [![Twitter][twitter-icon]][twitter-link] [@georgesg92][twitter-link]

[hacs-shield]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-link]: https://github.com/hacs/integration
[releases-shield]: https://img.shields.io/github/release/GeorgeSG/ha-philips-airpurifier.svg
[releases-link]: https://github.com/GeorgeSG/ha-philips-airpurifier/releases
[maintenance-shield]: https://img.shields.io/maintenance/yes/2024.svg
[maintenance-link]: https://github.com/GeorgeSG/ha-philips-airpurifier
[github-icon]: http://i.imgur.com/9I6NRUm.png
[github-link]: https://github.com/GeorgeSG/
[twitter-icon]: http://i.imgur.com/wWzX9uB.png
[twitter-link]: https://twitter.com/georgesg92
