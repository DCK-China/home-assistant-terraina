"""httpclient for TERRAINA integration."""

import logging
from typing import Any

import aiohttp
from aiohttp import ClientError, ClientTimeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import CLIENT_ID, CLIENT_SECRET, DOMAIN, SERVER_DOMAIN_NAME, WORKING_STATUS
from .grpc_util import MessageBuilder

_LOGGER = logging.getLogger(__name__)


class RefreshFailedException(HomeAssistantError):
    """Raised when token refresh fails."""


def isValidToken(token: dict[str, Any]) -> bool:
    """Check if the token is valid."""
    return "access_token" in token and "refresh_token" in token


class TerrainaHttpClient:
    """HttpClient for TERRAINA integration."""

    def __init__(
        self,
        hass: HomeAssistant,
        base_url: str,
        session: aiohttp.ClientSession,
        region="cn",
    ) -> None:
        """Initialize the HttpClient."""
        self._base_url = base_url
        self._region = region
        if region in SERVER_DOMAIN_NAME:
            self._token_url = f"{SERVER_DOMAIN_NAME[region]}/user-center/oauth2/token"
        self._session = session
        self._hass = hass

    async def get_countries(self) -> dict[str, Any]:
        """Get countries from TERRAINA API."""
        headers = {"Accept-Language": "en"}
        url = f"{self._base_url}/iot-provision/app/getRegionInfo"

        try:
            async with self._session.get(
                url,
                headers=headers,
                timeout=ClientTimeout(total=10),
            ) as response:
                response.raise_for_status()
                result = await response.json()
                return {item["name"]: item["serRegion"] for item in result["data"]}
        except ClientError as err:
            raise HomeAssistantError(
                f"Failed to get countries from {url}: {err}"
            ) from err
        except TimeoutError as err:
            raise HomeAssistantError(f"Timeout connecting to {url}") from err

    async def get_serial_numbers(self, config_entry: ConfigEntry) -> list[str]:
        """Get serial numbers associated with the account."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config_entry.data['token']['access_token']}",
        }
        url = f"{self._base_url}/smarthome/device/getUserBindDevices"
        async with self._session.post(
            url,
            headers=headers,
            timeout=ClientTimeout(total=10),
        ) as response:
            response.raise_for_status()
            resp_json = await response.json()
            if resp_json.get("code") == 401:
                tokens = await self._refresh_token(config_entry)
                if isValidToken(tokens):
                    return await self.get_serial_numbers(config_entry)
            if resp_json.get("code") != 200:
                raise HomeAssistantError(
                    f"Failed to get serial numbers: {resp_json.get('message')}"
                )

            return resp_json["data"]["deviceList"]

    async def go_home(self, config_entry: ConfigEntry, serial_number: str) -> None:
        """Send the lawnmower back to its charging station."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config_entry.data['token']['access_token']}",
        }
        messageBuilder = MessageBuilder()
        data = {
            "sn": serial_number,
            "payload": messageBuilder.build_change_status_message_payload(
                serial_number=serial_number, status=WORKING_STATUS.index("backing")
            ),
        }
        url = f"{self._base_url}/smarthome/message/send"
        async with self._session.post(
            url,
            json=data,
            headers=headers,
            timeout=ClientTimeout(total=10),
        ) as response:
            response.raise_for_status()
            resp_json = await response.json()
            if resp_json.get("code") == 401:
                tokens = await self._refresh_token(config_entry)
                if isValidToken(tokens):
                    return await self.go_home(config_entry, serial_number)
            if resp_json.get("code") != 200:
                raise HomeAssistantError(
                    f"Failed to send go home command: {resp_json.get('message')}"
                )
        return None

    async def _refresh_token(self, config_entry: ConfigEntry) -> dict[str, Any]:
        """Refresh the access token using the refresh token."""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "refresh_token",
            "refresh_token": config_entry.data["token"]["refresh_token"],
        }
        url = self._token_url

        auth = aiohttp.BasicAuth(CLIENT_ID, CLIENT_SECRET)
        try:
            async with self._session.post(
                url,
                data=data,
                headers=headers,
                timeout=ClientTimeout(total=10),
                auth=auth,
            ) as response:
                response.raise_for_status()
                resp_json = await response.json()
        except (ClientError, TimeoutError) as err:
            self._handle_reauth(config_entry)
            raise RefreshFailedException(
                f"Failed to refresh token from {url}: {err}"
            ) from err
        else:
            if response.status != 200:
                self._handle_reauth(config_entry)
                raise RefreshFailedException("Refresh token is invalid or expired.")

        self._hass.config_entries.async_update_entry(
            config_entry,
            data={**config_entry.data, "token": resp_json},
        )
        return resp_json

    def _handle_reauth(self, config_entry: ConfigEntry) -> None:
        """Trigger reauthentication flow."""
        try:
            self._hass.async_create_task(
                self._hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "TERRAINA authentication expired",
                        "message": "Please re-authenticate your TERRAINA account.",
                    },
                )
            )
        except Exception:
            _LOGGER.exception("Failed to create reauth notification")

        self._hass.async_create_task(
            self._hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "reauth", "entry_id": config_entry.entry_id},
                data=config_entry.data,
            )
        )
