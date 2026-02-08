from homeassistant.helpers.storage import Store

STORAGE_VERSION = 1
STORAGE_KEY = "tenda_devices"

class TendaStorage:
    def __init__(self, hass):
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data = {"devices": {}}

    async def async_load(self):
        stored = await self._store.async_load()
        if stored:
            self.data = stored

    async def async_save(self):
        await self._store.async_save(self.data)
