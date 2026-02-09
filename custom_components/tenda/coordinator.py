from datetime import timedelta, datetime
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TendaApi
from .const import (
    DOMAIN,
    CONF_SCAN_INTERVAL,
    CONF_GRACE_PERIOD,
    CONF_KEEP_DEVICES,
    DEFAULT_GRACE_PERIOD,
    DEFAULT_KEEP_DEVICES,
)
from .storage import TendaStorage

_LOGGER = logging.getLogger(__name__)


class TendaCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry

        self.api = TendaApi(
            entry.data["host"],
            entry.data["password"],
            async_get_clientsession(hass),
        )

        self.grace_period = entry.data.get(
            CONF_GRACE_PERIOD, DEFAULT_GRACE_PERIOD
        )
        self.keep_devices = entry.data.get(
            CONF_KEEP_DEVICES, DEFAULT_KEEP_DEVICES
        )

        self.storage = TendaStorage(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=entry.data.get(CONF_SCAN_INTERVAL, 30)
            ),
        )

    async def async_config_entry_first_refresh(self):
        await self.storage.async_load()
        await super().async_config_entry_first_refresh()

    async def _async_update_data(self):
        try:
            _LOGGER.debug("Starting update: fetching devices from API...")
            seen = await self.api.get_devices()
            _LOGGER.debug("API returned %d devices: %s", len(seen), list(seen.keys()))
            
            devices = self.storage.data.setdefault("devices", {})
            now = datetime.utcnow().isoformat()

            for mac, info in seen.items():
                if isinstance(info, dict):
                    name = info.get("name")
                    ip = info.get("ip")
                else:
                    name = info
                    ip = None

                dev = devices.setdefault(mac, {
                    "name": name,
                    "ip": ip,
                    "misses": 0,
                    "last_seen": None,
                })

                dev["name"] = name
                dev["ip"] = ip
                dev["misses"] = 0
                dev["last_seen"] = now
                _LOGGER.debug("Device %s (%s) - seen, misses=0, ip=%s", mac, name, ip)

            for mac, dev in list(devices.items()):
                if mac not in seen:
                    dev["misses"] += 1
                    _LOGGER.debug("Device %s - not seen, misses now=%d", mac, dev["misses"])

                    if not self.keep_devices and dev["misses"] >= self.grace_period:
                        _LOGGER.debug("Removing device %s (keep_devices=false)", mac)
                        devices.pop(mac)

            _LOGGER.debug("Update complete. Total devices: %d", len(devices))
            await self.storage.async_save()
            return devices

        except Exception as err:
            _LOGGER.exception("Failed to update devices: %s", err)
            fallback = self.storage.data.get("devices", {})
            _LOGGER.debug("Returning fallback data with %d devices", len(fallback))
            return fallback