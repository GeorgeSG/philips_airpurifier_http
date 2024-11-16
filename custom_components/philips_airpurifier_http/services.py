import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .const import (
    SERVICE_SET_FUNCTION,
    SERVICE_SET_TARGET_HUMIDITY,
    SERVICE_SET_LIGHT_BRIGHTNESS,
    SERVICE_SET_CHILD_LOCK,
    SERVICE_SET_TIMER,
    SERVICE_SET_DISPLAY_LIGHT,
    SERVICE_SET_USED_INDEX,
    SERVICE_ATTR_ENTITY_ID,
    SERVICE_ATTR_FUNCTION,
    SERVICE_ATTR_HUMIDITY,
    SERVICE_ATTR_BRIGHTNESS_LEVEL,
    SERVICE_ATTR_CHILD_LOCK,
    SERVICE_ATTR_TIMER_HOURS,
    SERVICE_ATTR_DISPLAY_LIGHT,
    SERVICE_ATTR_USED_INDEX,
    TARGET_HUMIDITY_LIST,
    LIGHT_BRIGHTNESS_LIST,
    FUNCTION_MAP,
    USED_INDEX_MAP,
)

AIRPURIFIER_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(SERVICE_ATTR_ENTITY_ID): cv.entity_ids}
)

SERVICE_SET_FUNCTION_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(SERVICE_ATTR_FUNCTION): vol.In(FUNCTION_MAP.values())}
)

SERVICE_SET_TARGET_HUMIDITY_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {
        vol.Required(SERVICE_ATTR_HUMIDITY): vol.All(
            vol.Coerce(int), vol.In(TARGET_HUMIDITY_LIST)
        )
    }
)

SERVICE_SET_LIGHT_BRIGHTNESS_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {
        vol.Required(SERVICE_ATTR_BRIGHTNESS_LEVEL): vol.All(
            vol.Coerce(int), vol.In(LIGHT_BRIGHTNESS_LIST)
        )
    }
)

SERVICE_SET_CHILD_LOCK_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(SERVICE_ATTR_CHILD_LOCK): cv.boolean}
)

SERVICE_SET_TIMER_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {
        vol.Required(SERVICE_ATTR_TIMER_HOURS): vol.All(
            vol.Coerce(int), vol.Number(scale=0), vol.Range(min=0, max=12)
        )
    }
)

SERVICE_SET_DISPLAY_LIGHT_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(SERVICE_ATTR_DISPLAY_LIGHT): cv.boolean}
)

SERVICE_SET_USED_INDEX_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(SERVICE_ATTR_USED_INDEX): vol.In(USED_INDEX_MAP.values())}
)


SERVICE_TO_METHOD = {
    SERVICE_SET_FUNCTION: {
        "method": "async_set_function",
        "schema": SERVICE_SET_FUNCTION_SCHEMA,
    },
    SERVICE_SET_TARGET_HUMIDITY: {
        "method": "async_set_target_humidity",
        "schema": SERVICE_SET_TARGET_HUMIDITY_SCHEMA,
    },
    SERVICE_SET_LIGHT_BRIGHTNESS: {
        "method": "async_set_light_brightness",
        "schema": SERVICE_SET_LIGHT_BRIGHTNESS_SCHEMA,
    },
    SERVICE_SET_CHILD_LOCK: {
        "method": "async_set_child_lock",
        "schema": SERVICE_SET_CHILD_LOCK_SCHEMA,
    },
    SERVICE_SET_TIMER: {
        "method": "async_set_timer",
        "schema": SERVICE_SET_TIMER_SCHEMA,
    },
    SERVICE_SET_DISPLAY_LIGHT: {
        "method": "async_set_display_light",
        "schema": SERVICE_SET_DISPLAY_LIGHT_SCHEMA,
    },
    SERVICE_SET_USED_INDEX: {
        "method": "async_set_used_index",
        "schema": SERVICE_SET_USED_INDEX_SCHEMA,
    },
}
