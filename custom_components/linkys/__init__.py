from __future__ import annotations
import asyncio
from datetime import timedelta, datetime
import json
import logging
import traceback
import requests

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.event import track_time_interval, call_later
from homeassistant.helpers import discovery
from homeassistant.helpers.dispatcher import async_dispatcher_send

_LOGGER = logging.getLogger(__name__)

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


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    sensors = [
        {"name": HA_LAST_ENERGY_KWH, "unit": "kWh", "value": "0", "timestamp": None},
        {"name": HA_MONTH_ENERGY_KWH, "unit": "kWh", "value": "0", "timestamp": None},
        {"name": HA_HOURS_ENERGY_KWH, "unit": None, "value": [], "timestamp": None},
    ]

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    hass.data[DOMAIN]["sensors"] = sensors

    try:
        hass.data[DOMAIN]["account"] = Linky_Account(
            config[DOMAIN][CONF_API_KEY],
            config[DOMAIN][CONF_POINT_ID],
            config[DOMAIN][CONF_EMAIL],
        )

        await LinkyAccount(hass)
        await discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
        _LOGGER.debug("Linky platform initialization OK")

    except Exception:
        _LOGGER.error(
            "Linky platform initialization failed:\n%s", traceback.format_exc()
        )

    return True


async def LinkyAccount(hass: HomeAssistant):
    sensors_data = hass.data[DOMAIN]["sensors"]

    def update_sensors(sensors_data, daily, hours):
        for sensor in sensors_data:
            if sensor["name"] == HA_HOURS_ENERGY_KWH:
                sensor["value"] = hours["hours"]
                sensor["timestamp"] = hours["timestamp"]
            else:
                sensor["value"] = daily[sensor["name"]]["value"]
                sensor["timestamp"] = daily[sensor["name"]]["timestamp"]

        async_dispatcher_send(hass, "linky_update")
        return sensors_data

    daily = await hass.async_add_executor_job(fetch_daily_consumption, hass)
    hours = await hass.async_add_executor_job(fetch_hours_consumption, hass)

    if daily is None or hours is None:
        _LOGGER.error("Données Linky indisponibles, mise à jour annulée")
        return

    try:
        hass.data[DOMAIN]["sensors"] = update_sensors(sensors_data, daily, hours)
        _LOGGER.debug("Linky sensors updated")

    except Exception:
        _LOGGER.error("Linky sensors update failed:\n%s", traceback.format_exc())


def fetch_daily_consumption(hass: HomeAssistant):
    api_key = hass.data[DOMAIN]["account"]["api_key"]
    prm = hass.data[DOMAIN]["account"]["point_id"]
    email = hass.data[DOMAIN]["account"]["email"]

    url = "https://conso.boris.sh/api/daily_consumption?"
    start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    end = datetime.now().strftime("%Y-%m-%d")

    try:
        payload = {"prm": prm, "start": start, "end": end}
        data = requests.get(
            url,
            params=payload,
            headers={
                "Authorization": "Bearer " + api_key,
                "User-Agent": "Home Assistant",
                "From": email or "exemple@email.com",
            },
            timeout=10,
        ).json()

        _LOGGER.debug("daily data=%s", json.dumps(data, indent=2))

        if "interval_reading" not in data:
            _LOGGER.error("Réponse Linky invalide (daily): %s", data)
            return None

        data = data["interval_reading"]
        if not data:
            return None

        last_kwh = float(data[-1]["value"]) / 1000
        month_kwh = sum(float(d["value"]) / 1000 for d in data)
        timestamp = datetime.strptime(data[-1]["date"], "%Y-%m-%d")

        return {
            HA_LAST_ENERGY_KWH: {"value": last_kwh, "timestamp": timestamp},
            HA_MONTH_ENERGY_KWH: {"value": month_kwh, "timestamp": timestamp},
        }

    except Exception:
        _LOGGER.error("Daily fetch error:\n%s", traceback.format_exc())
        return None


def fetch_hours_consumption(hass: HomeAssistant):
    api_key = hass.data[DOMAIN]["account"]["api_key"]
    prm = hass.data[DOMAIN]["account"]["point_id"]
    email = hass.data[DOMAIN]["account"]["email"]

    url = "https://conso.boris.sh/api/consumption_load_curve?"
    start = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    end = datetime.now().strftime("%Y-%m-%d")

    try:
        payload = {"prm": prm, "start": start, "end": end}
        data = requests.get(
            url,
            params=payload,
            headers={
                "Authorization": "Bearer " + api_key,
                "User-Agent": "Home Assistant",
                "From": email or "exemple@email.com",
            },
            timeout=10,
        ).json()

        _LOGGER.debug("hours data=%s", json.dumps(data, indent=2))

        if "interval_reading" not in data:
            _LOGGER.error("Réponse Linky invalide (hours): %s", data)
            return None

        data = data["interval_reading"]
        if not data:
            return None

        return {"hours": data, "timestamp": datetime.now()}

    except Exception:
        _LOGGER.error("Hours fetch error:\n%s", traceback.format_exc())
        return None
