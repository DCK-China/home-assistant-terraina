"""Config flow for TERRAINA integration."""

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, GLOBAL_DOMAIN, SERVER_DOMAIN_NAME
from .httpClient import TerrainaHttpClient
from .oauth2Client import create_auth_implementation


class TerrainaConfigFlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow for TERRAINA."""

    VERSION = 1
    MINOR_VERSION = 1
    DOMAIN = DOMAIN

    def __init__(self) -> None:
        """Initialize."""
        super().__init__()
        self.data: object | None = None
        self._http_client: TerrainaHttpClient | None = None
        self._user_data: dict | None = None
        self._my_reauth_entry_id: str | None = None

    @property
    def logger(self):
        """Return logger."""
        return logging.getLogger(__name__)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """First step: select region."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured(error="Only one TERRAINA account allowed.")
        http_client = TerrainaHttpClient(
            hass=self.hass,
            base_url=GLOBAL_DOMAIN,
            session=async_get_clientsession(self.hass),
            region="",  # 这个是请求region的接口，不需要region参数
        )
        countries = await http_client.get_countries()
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {vol.Required("country"): vol.In(countries.keys())}
                ),
            )

        # 获取区域信息
        region = countries[user_input["country"]]
        self._user_data = {"region": region}
        # 直接使用区域信息创建 OAuth2 实现
        config_entry_oauth2_flow.async_register_implementation(
            self.hass,
            DOMAIN,
            create_auth_implementation(
                self.hass,
                authorize_url=f"{SERVER_DOMAIN_NAME[region]}/user-center/oauth2/auth",
                token_url=f"{SERVER_DOMAIN_NAME[region]}/user-center/oauth2/token",
            ),
        )

        return await self.async_step_pick_implementation()

    async def async_oauth_create_entry(self, data: dict):
        """Create config entry after OAuth."""
        if self._user_data:
            data.update(self._user_data)

        # 处理重新认证的情况
        if self._my_reauth_entry_id:
            return self.async_update_reload_and_abort(
                self.hass.config_entries.async_get_entry(self._my_reauth_entry_id),
                data_updates=data,
                reason="reauth successful",
            )

        return self.async_create_entry(
            title=DOMAIN,
            data=data,
        )

    async def async_step_reauth(
        self, user_input: Mapping[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Handle re-authentication."""
        # 从已保存的数据中获取区域信息
        self._my_reauth_entry_id = self.context.get("entry_id")
        region = user_input["region"]
        self._user_data = {"region": region}
        if region:
            config_entry_oauth2_flow.async_register_implementation(
                self.hass,
                DOMAIN,
                create_auth_implementation(
                    self.hass,
                    authorize_url=f"{SERVER_DOMAIN_NAME[region]}/user-center/oauth2/auth",
                    token_url=f"{SERVER_DOMAIN_NAME[region]}/user-center/oauth2/token",
                ),
            )

        return await self.async_step_pick_implementation()
