[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

# Philips AirPurifier

_A platform which give you access to your Philips Air Purifier._

## Note:

**FAN SERVICES NOT WORKING FOR NOW, WILL BE ADDED IN NEXT UPDATES**

## Installation:

Just copy paste the content of the `fan.philips_airpurifier/custom_components` folder in your `config/custom_components` directory.

## Usage:

```yaml
fan:
  platform: philips_airpurifier
  host: 192.168.0.17
```

## Configuration variables:
  
Field | Value | Necessity | Description
--- | --- | --- | ---
platform | `philips_airpurifier` | *Required* | The platform name.
host | 192.168.0.17 | *Required* | IP address of your Purifier.
name | Philips Air Purifier | Optional | Name of the Fan.

***
