"""Support for Phillips Air Purifiers and Humidifiers."""

import asyncio
import logging
from pyairctrl.http_client import HTTPAirClient
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.fan import (
    FanEntity,
    PLATFORM_SCHEMA,
    SUPPORT_SET_SPEED
)

from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
)

from .const import *

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

AIRPURIFIER_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(SERVICE_ATTR_ENTITY_ID): cv.entity_ids}
)

SERVICE_SET_MODE_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(SERVICE_ATTR_MODE): vol.In(MODE_MAP.values())}
)

SERVICE_SET_FUNCTION_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(SERVICE_ATTR_FUNCTION): vol.In(FUNCTION_MAP.values())}
)

SERVICE_SET_TARGET_HUMIDITY_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {
        vol.Required(SERVICE_ATTR_HUMIDITY):
            vol.All(vol.Coerce(int), vol.In(TARGET_HUMIDITY_LIST))
    }
)

SERVICE_SET_LIGHT_BRIGHTNESS_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {
        vol.Required(SERVICE_ATTR_BRIGHTNESS_LEVEL):
            vol.All(vol.Coerce(int), vol.In(LIGHT_BRIGHTNESS_LIST))
    }
)

SERVICE_SET_CHILD_LOCK_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(SERVICE_ATTR_CHILD_LOCK): cv.boolean}
)

SERVICE_SET_TIMER_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {
        vol.Required(SERVICE_ATTR_TIMER_HOURS): vol.All(
            vol.Coerce(int),
            vol.Number(scale=0),
            vol.Range(min=0, max=12)
        )
    }
)

SERVICE_SET_DISPLAY_LIGHT_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(SERVICE_ATTR_DISPLAY_LIGHT): cv.boolean}
)

AIR_PURIFIER_SERVICES = {
    SERVICE_SET_MODE: SERVICE_SET_MODE_SCHEMA,
    SERVICE_SET_FUNCTION: SERVICE_SET_FUNCTION_SCHEMA,
    SERVICE_SET_TARGET_HUMIDITY: SERVICE_SET_TARGET_HUMIDITY_SCHEMA,
    SERVICE_SET_LIGHT_BRIGHTNESS: SERVICE_SET_LIGHT_BRIGHTNESS_SCHEMA,
    SERVICE_SET_CHILD_LOCK: SERVICE_SET_CHILD_LOCK_SCHEMA,
    SERVICE_SET_TIMER: SERVICE_SET_TIMER_SCHEMA,
    SERVICE_SET_DISPLAY_LIGHT: SERVICE_SET_DISPLAY_LIGHT_SCHEMA,
}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the philips_airpurifier platform."""

    name = config[CONF_NAME]
    client = HTTPAirClient(config[CONF_HOST])
    unique_id = None

    wifi = await hass.async_add_executor_job(client.get_wifi)
    if PHILIPS_MAC_ADDRESS in wifi:
        unique_id = wifi[PHILIPS_MAC_ADDRESS]

    device = PhilipsAirPurifierFan(hass, client, name, unique_id)

    if DATA_PHILIPS_FANS not in hass.data:
        hass.data[DATA_PHILIPS_FANS] = []

    hass.data[DATA_PHILIPS_FANS].append(device)

    async_add_entities(hass.data[DATA_PHILIPS_FANS])

    async def async_service_handler(service):
        entity_ids = service.data.get(SERVICE_ATTR_ENTITY_ID)

        # Params to set to method handler. Drop entity_id.
        params = {
            key: value for key, value in service.data.items() if key != SERVICE_ATTR_ENTITY_ID
        }

        if entity_ids:
            devices = [
                device
                for device in hass.data[DATA_PHILIPS_FANS]
                if device.entity_id in entity_ids
            ]
        else:
            devices = hass.data[DATA_PHILIPS_FANS]

        update_tasks = []
        for device in devices:
            # Use the same method name as the service name.
            # Assumes that if there's a service "set_mode", device will have a "set_mode" method.
            if not hasattr(device, service.service):
                continue
            getattr(device, service.service)(**params)
            update_tasks.append(device.async_update_ha_state(True))

        if update_tasks:
            await asyncio.wait(update_tasks)

    for service, schema in AIR_PURIFIER_SERVICES.items():
        hass.services.async_register(DOMAIN, service, async_service_handler, schema=schema)


class PhilipsAirPurifierFan(FanEntity):
    """philips_aurpurifier fan entity."""

    def __init__(self, hass, client, name, unique_id):
        self.hass = hass
        self._client = client
        self._name = name

        self._unique_id = unique_id
        self._available = False
        self._state = None
        self._model = None
        self._session_key = None

        self._fan_speed = None

        self._pre_filter = None
        self._wick_filter = None
        self._carbon_filter = None
        self._hepa_filter = None

        self._pm25 = None
        self._humidity = None
        self._target_humidity = None
        self._allergen_index = None
        self._temperature = None
        self._function = None
        self._light_brightness = None
        self._display_light = None
        self._used_index = None
        self._water_level = None
        self._child_lock = None
        self._timer = None
        self._timer_remaining = None

        self.async_update()

    ### Update Fan attributes ###

    async def async_update(self):
        """Fetch state from device."""
        try:
            await self._update_filters()
            await self._update_state()
            await self._update_model()
            self._available = True
        except Exception:
            self._available = False

    async def _update_filters(self):
        filters = await self.hass.async_add_executor_job(self._client.get_filters)
        self._pre_filter = filters['fltsts0']
        if 'wicksts' in filters:
            self._wick_filter = filters['wicksts']
        self._carbon_filter = filters['fltsts2']
        self._hepa_filter = filters['fltsts1']

    async def _update_model(self):
        firmware = await self.hass.async_add_executor_job(self._client.get_firmware)
        if PHILIPS_MODEL_NAME in firmware:
            self._model = firmware[PHILIPS_MODEL_NAME]

    async def _update_state(self):
        status = await self.hass.async_add_executor_job(self._client.get_status)
        if PHILIPS_POWER in status:
            self._state = 'on' if status[PHILIPS_POWER] == '1' else 'off'
        if PHILIPS_PM25 in status:
            self._pm25 = status[PHILIPS_PM25]
        if PHILIPS_HUMIDITY in status:
            self._humidity = status[PHILIPS_HUMIDITY]
        if PHILIPS_TARGET_HUMIDITY in status:
            self._target_humidity = status[PHILIPS_TARGET_HUMIDITY]
        if PHILIPS_ALLERGEN_INDEX in status:
            self._allergen_index = status[PHILIPS_ALLERGEN_INDEX]
        if PHILIPS_TEMPERATURE in status:
            self._temperature = status[PHILIPS_TEMPERATURE]
        if PHILIPS_FUNCTION in status:
            func = status[PHILIPS_FUNCTION]
            self._function = FUNCTION_MAP.get(func, func)
        if PHILIPS_MODE in status:
            mode = status[PHILIPS_MODE]
            self._fan_speed = MODE_MAP.get(mode, mode)
        if PHILIPS_SPEED in status:
            speed = status[PHILIPS_SPEED]
            speed = SPEED_MAP.get(speed, speed)
            if speed != SPEED_SILENT and self._fan_speed == MODE_MANUAL:
                self._fan_speed = speed
        if PHILIPS_LIGHT_BRIGHTNESS in status:
            self._light_brightness = status[PHILIPS_LIGHT_BRIGHTNESS]
        if PHILIPS_DISPLAY_LIGHT in status:
            display_light = status[PHILIPS_DISPLAY_LIGHT]
            self._display_light = DISPLAY_LIGHT_MAP.get(
                display_light, display_light)
        if PHILIPS_USED_INDEX in status:
            ddp = status[PHILIPS_USED_INDEX]
            self._used_index = USED_INDEX_MAP.get(ddp, ddp)
        if PHILIPS_WATER_LEVEL in status:
            self._water_level = status[PHILIPS_WATER_LEVEL]
        if PHILIPS_CHILD_LOCK in status:
            self._child_lock = status[PHILIPS_CHILD_LOCK]
        if PHILIPS_TIMER in status:
            self._timer = status[PHILIPS_TIMER]
        if PHILIPS_TIMER_REMAINING in status:
            self._timer_remaining = status[PHILIPS_TIMER_REMAINING]

    ### Properties ###

    @property
    def state(self):
        """Return device state."""
        return self._state

    @property
    def available(self):
        """Return True when state is known."""
        return self._available

    @property
    def unique_id(self):
        """Return an unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def icon(self):
        """Return the default icon for the device."""
        return DEFAULT_ICON

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return SUPPORTED_SPEED_LIST

    @property
    def speed(self) -> str:
        """Return the current speed."""
        return self._fan_speed

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_SET_SPEED

    def turn_on(self, speed: str = None, **kwargs) -> None:
        """Turn on the fan."""
        if speed is None:
            values = {PHILIPS_POWER: '1'}
            self._client.set_values(values)
        else:
            self.set_speed(speed)

    def turn_off(self, **kwargs) -> None:
        """Turn off the fan."""
        values = {PHILIPS_POWER: '0'}
        self._client.set_values(values)

    def set_speed(self, speed: str):
        """Set the speed of the fan."""
        if speed in SPEED_MAP.values():
            philips_speed = self._find_key(SPEED_MAP, speed)
            self._client.set_values({PHILIPS_SPEED: philips_speed})
        elif speed in MODE_MAP.values():
            philips_mode = self._find_key(MODE_MAP, speed)
            self._client.set_values({PHILIPS_MODE: philips_mode})
        else:
            _LOGGER.warning("Unsupported speed %s", speed)

    def set_mode(self, mode: str):
        """Set the mode of the fan."""
        philips_mode = self._find_key(MODE_MAP, mode)
        self._client.set_values({PHILIPS_MODE: philips_mode})

    def set_function(self, function: str):
        """Set the function of the fan."""
        philips_function = self._find_key(FUNCTION_MAP, function)
        self._client.set_values({PHILIPS_FUNCTION: philips_function})

    def set_target_humidity(self, humidity: int):
        """Set the target humidity of the fan."""
        self._client.set_values({PHILIPS_TARGET_HUMIDITY: humidity})

    def set_light_brightness(self, level: int):
        """Set the light brightness of the fan."""
        values = {}
        values[PHILIPS_LIGHT_BRIGHTNESS] = level
        values[PHILIPS_DISPLAY_LIGHT] = self._find_key(
            DISPLAY_LIGHT_MAP, level != 0)
        self._client.set_values(values)

    def set_child_lock(self, lock: bool):
        """Set the child lock of the fan."""
        self._client.set_values({PHILIPS_CHILD_LOCK: lock})

    def set_timer(self, hours: int):
        """Set the off timer of the fan."""
        self._client.set_values({PHILIPS_TIMER: hours})

    def set_display_light(self, light: bool):
        """Set the display light of the fan."""
        light = self._find_key(DISPLAY_LIGHT_MAP, light)
        self._client.set_values({PHILIPS_DISPLAY_LIGHT: light})

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {}

        if self._model is not None:
            attr[ATTR_MODEL] = self._model
        if self._function is not None:
            attr[ATTR_FUNCTION] = self._function
        if self._used_index is not None:
            attr[ATTR_USED_INDEX] = self._used_index
        if self._pm25 is not None:
            attr[ATTR_PM25] = self._pm25
        if self._allergen_index is not None:
            attr[ATTR_ALLERGEN_INDEX] = self._allergen_index
        if self._temperature is not None:
            attr[ATTR_TEMPERATURE] = self._temperature
        if self._humidity is not None:
            attr[ATTR_HUMIDITY] = self._humidity
        if self._target_humidity is not None:
            attr[ATTR_TARGET_HUMIDITY] = self._target_humidity
        if self._water_level is not None:
            attr[ATTR_WATER_LEVEL] = self._water_level
        if self._light_brightness is not None:
            attr[ATTR_LIGHT_BRIGHTNESS] = self._light_brightness
        if self._display_light is not None:
            attr[ATTR_DISPLAY_LIGHT] = self._display_light
        if self._child_lock is not None:
            attr[ATTR_CHILD_LOCK] = self._child_lock
        if self._timer is not None:
            attr[ATTR_TIMER] = self._timer
        if self._timer_remaining is not None:
            attr[ATTR_TIMER_REMAINGING_MINUTES] = self._timer_remaining
        if self._pre_filter is not None:
            attr[ATTR_PRE_FILTER] = self._pre_filter
        if self._wick_filter is not None:
            attr[ATTR_WICK_FILTER] = self._wick_filter
        if self._carbon_filter is not None:
            attr[ATTR_CARBON_FILTER] = self._carbon_filter
        if self._hepa_filter is not None:
            attr[ATTR_HEPA_FILTER] = self._hepa_filter

        return attr

    def _find_key(self, value_map, search_value):
        if search_value in value_map.values():
            return [key for key, value in value_map.items() if value == search_value][0]

        return None
