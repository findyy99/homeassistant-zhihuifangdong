"""The Zhihuifangdong Apartment integration."""
from __future__ import annotations

import logging
from typing import Any
import hashlib

import async_timeout
from aiohttp import ClientResponseError
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

# Platforms supported by this integration
_PLATFORMS: list[Platform] = [Platform.SENSOR]

class ZhihuifangdongApi:
    """Simple async client for Zhihuifangdong API."""

    LOGIN_URL = "https://api.zhihuifangdong.net/auth/auth/apploginMultipleRole"

    def __init__(self, hass: HomeAssistant, username: str, password: str) -> None:
        """Initialize the API client."""
        self.hass = hass
        self._session = async_get_clientsession(hass)
        self.username = username
        self.password = password
        self.token: str | None = None

    async def async_login(self) -> None:
        """Perform login and store token.

        Raise ConfigEntryAuthFailed on auth errors.
        Raise ConfigEntryNotReady on temporary errors.
        """
        headers = {
            "Host": "api.zhihuifangdong.net",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Accept": "*/*",
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 "
                "(Immersed/44) uni-app"
            ),
            "Authorization": "",
            "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        }

        data = {
            "username": self.username,
            "password": self.encrypt_passwd(self.password),
            "edition": "1",
        }

        try:
            async with async_timeout.timeout(10):
                resp = await self._session.post(self.LOGIN_URL, headers=headers, data=data)
                resp.raise_for_status()
                json_data: Any = await resp.json()
        except ClientResponseError as err:
            status = getattr(err, "status", None)
            if status in (401, 403):
                raise ConfigEntryAuthFailed("Invalid Zhihuifangdong credentials") from err
            raise ConfigEntryNotReady("Error logging in to Zhihuifangdong") from err
        except Exception as err:
            raise ConfigEntryNotReady("Unable to reach Zhihuifangdong API") from err

        if isinstance(json_data, dict):
            code = json_data.get("code")
            if code == "PASSWORD_ERROR":
                raise ConfigEntryAuthFailed("Invalid Zhihuifangdong credentials")
            elif not json_data.get("success", False):
                raise ConfigEntryNotReady(f"Login failed: {json_data.get('message')}")

        token = (
            (json_data.get("data") or {}).get("token")
            or json_data.get("token")
            or json_data.get("access_token")
        )

        if not token:
            raise ConfigEntryNotReady("Login succeeded but no token returned")

        self.token = token

    async def async_get_headers(self) -> dict[str, str]:
        """Return headers including authorization for subsequent requests."""
        if not self.token:
            raise ConfigEntryAuthFailed("Not authenticated")
        return {"Authorization": f"Bearer {self.token}"}

    def encrypt_passwd(self, input_password: str) -> str:
        """
        Generates the MD5 hash of a given password.

        Args:
            input_password: The password to be hashed.

        Returns:
            The 32-character hexadecimal MD5 hash of the input string.
        """
        # MD5 expects byte-like objects, so encode the string
        md5_hash_object = hashlib.md5(input_password.encode('utf-8'))
        # Get the hexadecimal representation of the hash
        hex_digest = md5_hash_object.hexdigest()
        return hex_digest 

# Custom ConfigEntry type alias holding the API client at runtime
ZhihuifangdongConfigEntry = ConfigEntry[ZhihuifangdongApi]  # type: ignore[misc]


async def async_setup_entry(hass: HomeAssistant, entry: ZhihuifangdongConfigEntry) -> bool:
    """Set up Zhihuifangdong from a config entry."""
    username = entry.data.get("username")
    password = entry.data.get("password")

    if not username or not password:
        raise ConfigEntryAuthFailed("Missing username or password in config entry")

    api = ZhihuifangdongApi(hass, username, password)

    try:
        await api.async_login()
    except ConfigEntryAuthFailed:
        _LOGGER.warning("Authentication failed for Zhihuifangdong entry")
        raise
    except ConfigEntryNotReady:
        _LOGGER.error("Zhihuifangdong API not ready")
        raise

    # Store API client for platforms to use (runtime only)
    entry.runtime_data = api

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ZhihuifangdongConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    if unload_ok:
        # Clean up runtime data
        entry.runtime_data = None
    return unload_ok