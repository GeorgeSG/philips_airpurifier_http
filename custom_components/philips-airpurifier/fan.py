"""Support for Phillips Air Purifiers and Humidifiers."""

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import urllib.request
import base64
import binascii
import json
import random

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

from .crypto import *
from .const import *

__version__ = '0.3.5'

DEFAULT_NAME = 'Philips AirPurifier'
ICON = 'mdi:air-purifier'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

### Setup Platform ###

def setup_platform(hass, config, add_devices, discovery_info=None):
    add_devices([PhilipsAirPurifierFan(hass, config)])


class PhilipsAirPurifierFan(FanEntity):
    def __init__(self, hass, config):
        self.hass = hass
        self._host = config[CONF_HOST]
        self._name = config[CONF_NAME]
        self._state = None
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
        self._used_index = None
        self._water_level = None
        self._child_lock = None
        self._timer = None

        self.update()

    ### Update Fan attributes ###

    def update(self):
        self._update_filters()
        url = 'http://{}/di/v1/products/1/air'.format(self._host)
        status = self._get(url)
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
            om = status[PHILIPS_SPEED]
            om = SPEED_MAP.get(om, om)
            if om != SPEED_SILENT and self._fan_speed == MODE_MANUAL:
                self._fan_speed = om
        if PHILIPS_BRIGHTNESS in status:
            self._light_brightness = status[PHILIPS_BRIGHTNESS]
        if 'ddp' in status:
            ddp = status['ddp']
            ddp_str = {'1': 'PM2.5', '0': 'IAI'}
            self._used_index = ddp_str.get(ddp, ddp)
        if PHILIPS_WATER_LEVEL in status:
            self._water_level = status[PHILIPS_WATER_LEVEL]
        if PHILIPS_CHILD_LOCK in status:
            self._child_lock = status[PHILIPS_CHILD_LOCK]
        if PHILIPS_TIMER in status:
            self._timer = status[PHILIPS_TIMER]

    def _update_filters(self):
        url = 'http://{}/di/v1/products/1/fltsts'.format(self._host)
        filters = self._get(url)
        self._pre_filter = filters['fltsts0']
        if 'wicksts' in filters:
            self._wick_filter = filters['wicksts']
        self._carbon_filter = filters['fltsts2']
        self._hepa_filter = filters['fltsts1']

    ### Properties ###

    @property
    def state(self):
        return self._state

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return ICON

    @property
    def speed_list(self) -> list:
        return SPEED_AND_MODE_LIST

    @property
    def speed(self) -> str:
        return self._fan_speed

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_SET_SPEED

    def turn_on(self, speed: str = None, **kwargs) -> None:
        if speed is None:
            values = { PHILIPS_POWER: '1' }
            self.set_values(values)
        else:
            self.set_speed(speed)

    def turn_off(self, **kwargs) -> None:
        values = { PHILIPS_POWER: '0' }
        self.set_values(values)

    def set_speed(self, speed: str):
        values = {}
        if speed == SPEED_TURBO:
            values[PHILIPS_SPEED] = PHILIPS_SPEED_TURBO
        elif speed == SPEED_1:
            values[PHILIPS_SPEED] = '1'
        elif speed == SPEED_2:
            values[PHILIPS_SPEED] = '2'
        elif speed == SPEED_3:
            values[PHILIPS_SPEED] = '3'
        elif speed == MODE_AUTO:
            values[PHILIPS_MODE] = PHILIPS_MODE_AUTO
        elif speed == MODE_ALLERGEN:
            values[PHILIPS_MODE] = PHILIPS_MODE_ALLERGEN
        elif speed == MODE_SLEEP:
            values[PHILIPS_MODE] = PHILIPS_MODE_SLEEP
        self.set_values(values)

    @property
    def device_state_attributes(self):
        return {
            ATTR_FUNCTION: self._function,
            ATTR_USED_INDEX: self._used_index,
            ATTR_PM25: self._pm25,
            ATTR_ALLERGEN_INDEX: self._allergen_index,
            ATTR_TEMPERATURE: self._temperature,
            ATTR_HUMIDITY: self._humidity,
            ATTR_TARGET_HUMIDITY: self._target_humidity,
            ATTR_WATER_LEVEL: self._water_level,
            ATTR_LIGHT_BRIGHTNESS: self._light_brightness,
            ATTR_CHILD_LOCK: self._child_lock,
            ATTR_TIMER: self._timer,
            ATTR_PRE_FILTER: self._pre_filter,
            ATTR_WICK_FILTER: self._wick_filter,
            ATTR_CARBON_FILTER: self._carbon_filter,
            ATTR_HEPA_FILTER: self._hepa_filter,
        }


    ### Other methods ###

    def set_values(self, values):
        body = encrypt(values, self._session_key)
        url = 'http://{}/di/v1/products/1/air'.format(self._host)
        req = urllib.request.Request(url=url, data=body, method='PUT')
        with urllib.request.urlopen(req) as response:
            resp = response.read()

    def _get_key(self):
        url = 'http://{}/di/v1/products/0/security'.format(self._host)
        a = random.getrandbits(256)
        A = pow(G, a, P)
        data = json.dumps({'diffie': format(A, 'x')})
        data_enc = data.encode('ascii')
        req = urllib.request.Request(url=url, data=data_enc, method='PUT')
        with urllib.request.urlopen(req) as response:
            resp = response.read().decode('ascii')
            dh = json.loads(resp)
        key = dh['key']
        B = int(dh['hellman'], 16)
        s = pow(B, a, P)
        s_bytes = s.to_bytes(128, byteorder='big')[:16]
        session_key = aes_decrypt(bytes.fromhex(key), s_bytes)
        self._session_key = session_key[:16]

    def _get_once(self, url):
        with urllib.request.urlopen(url) as response:
            resp = response.read()
            resp = decrypt(resp.decode('ascii'), self._session_key)
            return json.loads(resp)

    def _get(self, url):
        try:
            return self._get_once(url)
        except Exception as e:
            self._get_key()
            return self._get_once(url)
