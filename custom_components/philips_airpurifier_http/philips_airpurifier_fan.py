import logging
from functools import partial

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import (
    ATTR_ALLERGEN_INDEX,
    ATTR_CARBON_FILTER,
    ATTR_CHILD_LOCK,
    ATTR_DISPLAY_LIGHT,
    ATTR_FUNCTION,
    ATTR_HEPA_FILTER,
    ATTR_HUMIDITY,
    ATTR_LIGHT_BRIGHTNESS,
    ATTR_MODEL,
    ATTR_PM25,
    ATTR_PRE_FILTER,
    ATTR_TARGET_HUMIDITY,
    ATTR_TEMPERATURE,
    ATTR_TIMER_REMAINGING_MINUTES,
    ATTR_TIMER,
    ATTR_USED_INDEX,
    ATTR_WATER_LEVEL,
    ATTR_WICK_FILTER,
    DEFAULT_ICON,
    DISPLAY_LIGHT_MAP,
    FUNCTION_MAP,
    MODE_MANUAL,
    MODE_MAP,
    PHILIPS_ALLERGEN_INDEX,
    PHILIPS_CHILD_LOCK,
    PHILIPS_DISPLAY_LIGHT,
    PHILIPS_FUNCTION,
    PHILIPS_HUMIDITY,
    PHILIPS_LIGHT_BRIGHTNESS,
    PHILIPS_MODE,
    PHILIPS_MODEL_NAME,
    PHILIPS_PM25,
    PHILIPS_POWER,
    PHILIPS_SPEED,
    PHILIPS_TARGET_HUMIDITY,
    PHILIPS_TEMPERATURE,
    PHILIPS_TIMER_REMAINING,
    PHILIPS_TIMER,
    PHILIPS_USED_INDEX,
    PHILIPS_WATER_LEVEL,
    SPEED_MAP,
    USED_INDEX_MAP,
)

from .model_config import (
    DEFAULT_MODEL,
    DEVICE_CONFIG_MODES,
    DEVICE_CONFIG_SPEEDS,
    MODELS,
    DEVICE_CONFIG_CHANGE_TO_MANUAL,
)

_LOGGER = logging.getLogger(__name__)


class PhilipsAirPurifierFan(FanEntity):
    """philips_aurpurifier fan entity."""

    def __init__(self, hass, client, name):
        self.hass = hass
        self._client = client
        self._name = name

        self._available = False
        self._state = None
        self._model = None
        self._session_key = None

        self._fan_speed = None
        self._preset_mode = None

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

    ### Update Fan attributes ###

    async def async_update(self):
        """Fetch state from device."""
        try:
            await self._update_filters()
            await self._update_state()
            await self._update_model()
            self._available = True
        except Exception:
            _LOGGER.error("Error updating the fan.", exc_info=True)
            self._available = False

    async def _update_filters(self):
        filters = await self.hass.async_add_executor_job(self._client.get_filters)
        self._pre_filter = filters["fltsts0"]
        if "wicksts" in filters:
            self._wick_filter = filters["wicksts"]
        self._carbon_filter = filters["fltsts2"]
        self._hepa_filter = filters["fltsts1"]

    async def _update_model(self):
        firmware = await self.hass.async_add_executor_job(self._client.get_firmware)
        if PHILIPS_MODEL_NAME in firmware:
            self._model = firmware[PHILIPS_MODEL_NAME]

    async def _update_state(self):
        status = await self.hass.async_add_executor_job(self._client.get_status)
        if PHILIPS_POWER in status:
            self._state = "on" if status[PHILIPS_POWER] == "1" else "off"
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
            self._preset_mode = MODE_MAP.get(mode, mode)
        if PHILIPS_SPEED in status:
            speed = status[PHILIPS_SPEED]
            self._fan_speed = SPEED_MAP.get(speed, speed)
        if PHILIPS_LIGHT_BRIGHTNESS in status:
            self._light_brightness = status[PHILIPS_LIGHT_BRIGHTNESS]
        if PHILIPS_DISPLAY_LIGHT in status:
            display_light = status[PHILIPS_DISPLAY_LIGHT]
            self._display_light = DISPLAY_LIGHT_MAP.get(display_light, display_light)
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
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def icon(self):
        """Return the default icon for the device."""
        return DEFAULT_ICON

    @property
    def percentage(self) -> int:
        """Return the current percentage."""

        if self._fan_speed != "0":
            percentage = ordered_list_item_to_percentage(
                self._speed_names, self._fan_speed
            )
            return percentage

    @property
    def preset_modes(self) -> [str]:
        """Return all available preset modes."""
        return self._model_config.get(DEVICE_CONFIG_MODES)

    @property
    def preset_mode(self) -> str:
        """Return the current preset mode."""
        return self._preset_mode

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return (
            FanEntityFeature.SET_SPEED
            | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.TURN_ON
            | FanEntityFeature.TURN_OFF
        )

    @property
    def speed_count(self) -> int:
        return len(self._speed_names)

    async def async_turn_on(self, percentage=None, preset_mode=None, **kwargs) -> None:
        """Turn on the fan."""

        values = {PHILIPS_POWER: "1"}
        await self._async_set_values(values)

        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
        elif percentage is not None:
            await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the fan."""
        values = {PHILIPS_POWER: "0"}
        await self._async_set_values(values)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""

        if percentage == 0:
            await self.async_turn_off()
            return

        speed_name = percentage_to_ordered_list_item(self._speed_names, percentage)
        speed = self._find_key(SPEED_MAP, speed_name)
        values = {PHILIPS_SPEED: speed}

        if self._should_change_to_manual:
            values[PHILIPS_MODE] = self._find_key(MODE_MAP, MODE_MANUAL)

        await self._async_set_values(values)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set a preset mode on the fan."""

        if preset_mode in MODE_MAP.values():
            philips_mode = self._find_key(MODE_MAP, preset_mode)
            await self._async_set_values({PHILIPS_MODE: philips_mode})
        else:
            _LOGGER.warning('Unsupported preset mode "%s"', preset_mode)

    async def async_set_used_index(self, used_index: str) -> None:
        """Set the used_index of the fan."""
        philips_used_index = self._find_key(USED_INDEX_MAP, used_index)
        await self._async_set_values({PHILIPS_USED_INDEX: philips_used_index})

    async def async_set_function(self, function: str):
        """Set the function of the fan."""
        philips_function = self._find_key(FUNCTION_MAP, function)
        await self._async_set_values({PHILIPS_FUNCTION: philips_function})

    async def async_set_target_humidity(self, humidity: int):
        """Set the target humidity of the fan."""
        await self._async_set_values({PHILIPS_TARGET_HUMIDITY: humidity})

    async def async_set_light_brightness(self, level: int):
        """Set the light brightness of the fan."""
        values = {}
        values[PHILIPS_LIGHT_BRIGHTNESS] = level
        values[PHILIPS_DISPLAY_LIGHT] = self._find_key(DISPLAY_LIGHT_MAP, level != 0)
        await self._async_set_values(values)

    async def async_set_child_lock(self, lock: bool):
        """Set the child lock of the fan."""
        await self._async_set_values({PHILIPS_CHILD_LOCK: lock})

    async def async_set_timer(self, hours: int):
        """Set the off timer of the fan."""
        await self._async_set_values({PHILIPS_TIMER: hours})

    async def async_set_display_light(self, light: bool):
        """Set the display light of the fan."""
        light = self._find_key(DISPLAY_LIGHT_MAP, light)
        await self._async_set_values({PHILIPS_DISPLAY_LIGHT: light})

    @property
    def extra_state_attributes(self):
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

    async def _async_set_values(self, values):
        try:
            await self.hass.async_add_executor_job(
                partial(self._client.set_values, values)
            )
        except Exception as exc:
            _LOGGER.error("Error setting new values.", exc)
            self._available = False
            return False

    def _find_key(self, value_map, search_value):
        if search_value in value_map.values():
            return [key for key, value in value_map.items() if value == search_value][0]

        return None

    @property
    def _model_config(self):
        return MODELS.get(self._model, MODELS.get(DEFAULT_MODEL))

    @property
    def _speed_names(self):
        return self._model_config.get(DEVICE_CONFIG_SPEEDS)

    @property
    def _should_change_to_manual(self):
        return self._model_config.get(DEVICE_CONFIG_CHANGE_TO_MANUAL)
