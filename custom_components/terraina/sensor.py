"""TERRAINA sensor."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    # SensorDeviceClass,
    SensorEntity,
    # SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    # CHARGING,
    DOMAIN,
    NAME,
    # EMERGENCY_STOP,
    # LOCKED,
    # RAINED,
    SERVER_DOMAIN_NAME,
    # WORKING_STATUS,
)
from .httpClient import RefreshFailedException, TerrainaHttpClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up TERRAINA sensors."""

    region = entry.data.get("region")
    httpClient = TerrainaHttpClient(
        hass=hass,
        base_url=SERVER_DOMAIN_NAME[region],
        session=async_get_clientsession(hass),
        region=region,
    )
    # 获取全部序列号
    devices = await httpClient.get_serial_numbers(config_entry=entry)
    # 注册工作服务
    sensors = []
    sensor_map = {}
    service_map = {}
    registered_services = []

    for device in devices:
        sn = str(device["sn"])
        device_name = device["deviceName"]
        model_name = device["modelName"]
        back_service_name = f"back_{model_name}_{sn[-6:]}"
        sensor = LawnmowerSensor(hass=hass, entry=entry, sn=sn, device_name=device_name)
        sensors.append(sensor)
        sensor_map[sn] = sensor
        service_map[sn] = back_service_name

        async def handle_back(call: ServiceCall, *, serial: str = sn) -> None:
            """Send mower back to dock."""

            await httpClient.go_home(config_entry=entry, serial_number=serial)

        hass.services.async_register(DOMAIN, back_service_name, handle_back)
        registered_services.append(back_service_name)

    # Store registered services in hass.data for cleanup during unload
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}
    hass.data[DOMAIN][entry.entry_id]["services"] = registered_services

    sensors.append(
        LawnmowerControllerSensor(hass, entry, httpClient, sensor_map, service_map)
    )
    async_add_entities(sensors)


class LawnmowerSensor(SensorEntity):
    """LawnmowerSensor for lawnmower."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, sn: str, device_name: str
    ) -> None:
        """Init function."""
        self._hass = hass
        self._entry = entry
        self._attr_has_entity_name = True
        self._sn = str(sn)
        self._device_name = device_name
        self._attr_name = f"{self._device_name} ({self._sn})"
        self._attr_unique_id = f"{entry.entry_id}_{self._sn}_binding"
        self._attr_native_value = "binding"

    @property
    def should_poll(self) -> bool:
        """Enable polling."""
        return False

    @property
    def device_info(self) -> DeviceInfo:
        """Device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},  # 同一个 serial_number 表示同一设备
            name=NAME,
        )


class LawnmowerControllerSensor(SensorEntity):
    """Display all devices under the account."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        http_client: TerrainaHttpClient,
        sensor_map: dict[str, LawnmowerSensor],
        service_map: dict[str, str],
    ) -> None:
        """Initialize the devices sensor."""
        self._attr_unique_id = f"{entry.data['region']}_devices"
        self._hass = hass
        self._attr_has_entity_name = True
        self._entry = entry
        self._disabled = False
        self._http_client = http_client
        self._attr_available = True
        self._attr_native_value = "Connected"
        self._sensor_map = sensor_map
        self._service_map = service_map
        self._attr_name = "Controller"

    @property
    def should_poll(self) -> bool:
        """Enable polling."""
        return True

    @property
    def device_info(self) -> DeviceInfo:
        """Device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},  # 同一个 serial_number 表示同一设备
            name=NAME,
        )

    def reset_client(self) -> None:
        """Reset the HTTP client in case of previous failures."""
        self._disabled = False

    async def async_update(self) -> None:
        """Fetch latest device list."""
        if not self._disabled:
            try:
                # 获取新的设备列表
                new_devices = await self._http_client.get_serial_numbers(
                    config_entry=self._entry
                )
                self._attr_available = True
                current_serials = set(self._sensor_map.keys())
                new_serials = {str(device["sn"]) for device in new_devices}

                added_serials = new_serials - current_serials
                removed_serials = current_serials - new_serials
                for sn in removed_serials:
                    service_name = self._service_map.pop(sn)
                    if self.hass.services.has_service(DOMAIN, service_name):
                        self.hass.services.async_remove(DOMAIN, service_name)
                if len(added_serials) > 0 or len(removed_serials) > 0:
                    _LOGGER.info(
                        "Device list changed. Added: %s, Removed: %s",
                        added_serials,
                        removed_serials,
                    )
                    # Avoid mutating entities during iteration; reload after yielding.
                    self._hass.async_create_task(
                        self._hass.config_entries.async_reload(self._entry.entry_id)
                    )
                    return

            except RefreshFailedException:
                _LOGGER.warning("Failed to refresh device list")
                self._attr_available = False
                self._disabled = True
                self._attr_native_value = "Disconnected"
            except Exception:
                _LOGGER.exception("Failed to update device list")
                self._attr_available = False
