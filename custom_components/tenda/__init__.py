import logging
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["device_tracker"]

async def async_setup(hass, config):
    """Set up the Tenda integration."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass, entry):
    from .coordinator import TendaCoordinator

    _LOGGER.debug("Setting up Tenda integration with entry: %s", entry.entry_id)
    
    coordinator = TendaCoordinator(hass, entry)
    _LOGGER.debug("Created TendaCoordinator, starting first refresh...")
    
    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.debug("First refresh complete. Coordinator data: %s", coordinator.data)
    except Exception as e:
        _LOGGER.error("First refresh failed: %s", e, exc_info=True)
        raise

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    _LOGGER.debug("Coordinator stored in hass.data[%s][%s]", DOMAIN, entry.entry_id)
    
    _LOGGER.debug("Data before forward_entry_setups: %s", coordinator.data)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.debug("Forward entry setups completed for platforms: %s", PLATFORMS)
    
    return True

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
