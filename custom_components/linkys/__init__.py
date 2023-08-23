"""Example Load Platform integration."""
from __future__ import annotations
import asyncio
from datetime import timedelta, datetime
import json
import logging
import traceback
import requests

_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.event import track_time_interval, call_later


DOMAIN = "linky"
HA_LAST_ENERGY_KWH = "Linky energy"
HA_MONTH_ENERGY_KWH = "Linky energy month"
HA_HOURS_ENERGY_KWH = "Linky energy hours"

DEFAULT_SCAN_INTERVAL = timedelta(hours=8)
CONF_API_KEY = "api_key"
CONF_POINT_ID = "point_id"
CONF_EMAIL = "email"


class Linky_Account:
    def __init__(self, api_key, point_id, email) -> None:
        self.api_key = api_key
        self.point_id = point_id
        self.email = email

    def __getitem__(self, key):
        return getattr(self, key)


SCAN_INTERVAL = timedelta(hours=8)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Your controller/hub specific code."""
    sensors = [
        {
            "name": HA_LAST_ENERGY_KWH,
            "unit": "kWh",
            "value": "0",
            "timestamp": None,
        },
        {
            "name": HA_MONTH_ENERGY_KWH,
            "unit": "kWh",
            "value": "0",
            "timestamp": None,
        },
        {
            "name": HA_HOURS_ENERGY_KWH,
            "unit": None,
            "value": [],
            "timestamp": None,
        },
    ]
    # Initialize the 'linky' key in hass.data dictionary
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # Store the sensors list in the 'linky' key
    hass.data[DOMAIN]["sensors"] = sensors
    # Data that you want to share with your platforms
    try:
        hass.data[DOMAIN]["account"] = Linky_Account(
            config[DOMAIN][CONF_API_KEY],
            config[DOMAIN][CONF_POINT_ID],
            config[DOMAIN][CONF_EMAIL],
        )
        await LinkyAccount(hass)
        await load_sensor_platform(config, hass)

        _LOGGER.debug("Linky platform initialization has completed successfully")
    except BaseException:
        _LOGGER.error(
            "Linky platform initialization has failed with exception : {0}".format(
                traceback.format_exc()
            )
        )

    return True


async def load_sensor_platform(config, hass: HomeAssistant):
    await hass.helpers.discovery.async_load_platform("sensor", DOMAIN, {}, config)


async def async_update(hass: HomeAssistant, config_entry):
    return await LinkyAccount(hass)


async def LinkyAccount(hass: HomeAssistant):
    sensors_data = hass.data[DOMAIN]["sensors"]

    def update_sensors(hass: HomeAssistant, sensors_data, daily, hours):
        for sensor in sensors_data:
            if sensor["name"] == HA_HOURS_ENERGY_KWH:
                sensor["value"] = hours["hours"]
                sensor["timestamp"] = hours["timestamp"]

            else:
                sensor["value"] = daily[sensor["name"]]["value"]
                sensor["timestamp"] = daily[sensor["name"]]["timestamp"]
        hass.helpers.dispatcher.async_dispatcher_send("linky_update")
        return sensors_data

    daily = await hass.async_run_job(fetch_daily_consumption, hass)
    hours = await hass.async_run_job(fetch_hours_consumption, hass)
    try:
        sensors_data = update_sensors(hass, sensors_data, daily, hours)
        hass.data[DOMAIN]["sensors"] = sensors_data
        _LOGGER.debug("Linky sensors update has completed successfully")
    except BaseException:
        _LOGGER.error(
            "Linky sensors update has failed with exception : {0}".format(
                traceback.format_exc()
            )
        )


def fetch_daily_consumption(hass: HomeAssistant):
    api_key = hass.data[DOMAIN]["account"]["api_key"]
    pmr = hass.data[DOMAIN]["account"]["point_id"]
    email = hass.data[DOMAIN]["account"]["email"]

    url = "https://conso.boris.sh/api/daily_consumption?"
    start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    end = datetime.now().strftime("%Y-%m-%d")

    try:
        # Get full month data
        payload = {"prm": pmr, "start": start, "end": end}
        data = requests.get(
            url,
            params=payload,
            headers={
                "Authorization": "Bearer " + api_key,
                "User-Agent": "Home Assistant",
                "From": email if email else "exemple@email.com",
            },
            timeout=10,
        ).json()
        _LOGGER.debug("data={0}".format(json.dumps(data, indent=2)))
        data = data["interval_reading"]
        last_kwh = float(data[-1]["value"]) / 1000
        month_kwh = sum([float(d["value"]) / 1000 for d in data])
        timestamp = datetime.strptime(data[-1]["date"], "%Y-%m-%d")
        return {
            HA_LAST_ENERGY_KWH: {
                "value": last_kwh,
                "timestamp": timestamp,
            },
            HA_MONTH_ENERGY_KWH: {
                "value": month_kwh,
                "timestamp": timestamp,
            },
        }

    except BaseException:
        _LOGGER.error(
            "Failed to query Linky library with exception : {0}".format(
                traceback.format_exc()
            )
        )
        return {
            HA_LAST_ENERGY_KWH: {
                "value": 0,
                "timestamp": None,
            },
            HA_MONTH_ENERGY_KWH: {
                "value": 0,
                "timestamp": None,
            },
        }


def fetch_hours_consumption(hass: HomeAssistant):
    api_key = hass.data[DOMAIN]["account"]["api_key"]
    pmr = hass.data[DOMAIN]["account"]["point_id"]
    email = hass.data[DOMAIN]["account"]["email"]
    url = "https://conso.boris.sh/api/consumption_load_curve?"

    start = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    end = datetime.now().strftime("%Y-%m-%d")
    try:
        # Get full month data
        payload = {"prm": pmr, "start": start, "end": end}
        data = requests.get(
            url,
            params=payload,
            headers={
                "Authorization": "Bearer " + api_key,
                "User-Agent": "Home Assistant",
                "From": email if email else "exemple@email.com",
            },
            timeout=10,
        ).json()
        _LOGGER.debug("data={0}".format(json.dumps(data, indent=2)))
        data = data["interval_reading"]
        return {"hours": data, "timestamp": datetime.now()}

    except BaseException:
        _LOGGER.error(
            "Failed to query Linky library with exception : {0}".format(
                traceback.format_exc()
            )
        )
