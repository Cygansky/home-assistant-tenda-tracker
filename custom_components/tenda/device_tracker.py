import logging

from homeassistant.components.device_tracker import TrackerEntity, SourceType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up device_tracker platform (minimal, coordinator-backed)."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for mac, dev in (coordinator.data or {}).items():
        name = dev.get("name") if isinstance(dev, dict) else str(mac)
        entities.append(TendaDevice(coordinator, mac, name))

    async_add_entities(entities, update_before_add=True)


class TendaDevice(CoordinatorEntity, TrackerEntity):
    """Coordinator-backed device tracker that exposes state as 'home'/'not_home'."""

    def __init__(self, coordinator, mac, name):
        super().__init__(coordinator)
        self._mac = mac
        self._attr_unique_id = f"{mac}"
        self._attr_name = name
        self._attr_source_type = SourceType.ROUTER
        self._connected = False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updates from the coordinator and schedule HA state update."""
        data = self.coordinator.data or {}
        dev = data.get(self._mac)

        if dev and isinstance(dev, dict):
            self._connected = dev.get("misses", 0) < getattr(self.coordinator, "grace_period", 1)
        else:
            self._connected = False

        # parent will schedule update in HA
        super()._handle_coordinator_update()

    @property
    def state(self):
        """Return 'home' when connected, otherwise 'not_home'."""
        return "home" if self._connected else "not_home"

    @property
    def extra_state_attributes(self):
        """Return additional state attributes for the entity (ip)."""
        data = self.coordinator.data or {}
        dev = data.get(self._mac)

        if dev and isinstance(dev, dict):
            ip = dev.get("ip")
            return {"ip": ip} if ip is not None else {}

        return {}

