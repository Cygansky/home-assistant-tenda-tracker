import hashlib
import json
import time
import logging

_LOGGER = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

class TendaAuthError(Exception):
    pass

class TendaApi:
    def __init__(self, host, password, session):
        self._host = host
        self._password = password
        self._session = session
        self._cookies = None

    async def _login(self):
        _LOGGER.debug("Logging in to Tenda router at %s", self._host)
        pwd_hash = hashlib.md5(self._password.encode()).hexdigest()
        data = f"username=admin&password={pwd_hash}"

        async with self._session.post(
            f"http://{self._host}/login/Auth",
            data=data,
            headers=HEADERS,
            allow_redirects=False,
        ) as resp:
            if resp.status != 302:
                _LOGGER.error("Login failed! Status: %d", resp.status)
                raise TendaAuthError(resp.status)
            self._cookies = resp.cookies
            _LOGGER.debug("Login successful, cookies obtained")

    async def get_devices(self, retry_count=0, max_retries=1):
        if self._cookies is None:
            _LOGGER.debug("No cookies, need to login first")
            await self._login()

        url = f"http://{self._host}/goform/getOnlineList?{time.time()}"
        _LOGGER.debug("Fetching device list from: %s", url)

        async with self._session.get(
            url,
            cookies=self._cookies,
            headers=HEADERS,
            allow_redirects=False,
        ) as resp:
            _LOGGER.debug("Device list response status: %d", resp.status)
            text = await resp.text()
            _LOGGER.debug("Response text (first 500 chars): %s", text[:500])

        try:
            payload = json.loads(text)
            _LOGGER.debug("Parsed JSON, got %d items", len(payload) if isinstance(payload, list) else 0)
        except json.JSONDecodeError as e:
            if retry_count >= max_retries:
                _LOGGER.error(
                    "Failed to decode devices JSON after %d retries. Response: %s",
                    retry_count,
                    text[:200] if text else "<empty>"
                )
                raise ValueError(f"Invalid JSON response from device list: {e}") from e
            
            _LOGGER.warning(
                "Failed to decode JSON (attempt %d/%d), clearing cookies and retrying",
                retry_count + 1,
                max_retries + 1
            )
            self._cookies = None
            return await self.get_devices(retry_count=retry_count + 1, max_retries=max_retries)

        devices = {}
        for d in payload:
            mac = d.get("deviceId") or d.get("localhostMac")
            name = d.get("devName") or d.get("localhostName")
            if mac and name:
                devices[mac] = name
                _LOGGER.debug("Found device: %s -> %s", mac, name)
            else:
                _LOGGER.debug("Skipped device (missing mac or name): %s", d)

        _LOGGER.debug("Total devices found: %d", len(devices))
        return devices
