from __future__ import annotations
import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from datetime import timedelta
import async_timeout

from . import ZhihuifangdongApi, ZhihuifangdongConfigEntry

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=15)  # Metrics update interval


async def async_setup_entry(hass: HomeAssistant, entry: ZhihuifangdongConfigEntry, async_add_entities):
    api: ZhihuifangdongApi = entry.runtime_data

    coordinator = ZhihuifangdongDataUpdateCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        ZhihuifangdongMeterSensor(coordinator, "residualElectricity", "kWh", "剩余电量"),
        # Cumulative energy sensor for Home Assistant Energy dashboard
        ZhihuifangdongMeterSensor(
            coordinator,
            "electricEnergy",
            "kWh",
            "用电量",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        ZhihuifangdongMeterSensor(coordinator, "voltage", "V", "电压"),
        ZhihuifangdongMeterSensor(coordinator, "electricity", "A", "电流"),
        ZhihuifangdongMeterSensor(coordinator, "power", "W", "功率", is_calculated=True)
    ], True)


class ZhihuifangdongDataUpdateCoordinator(DataUpdateCoordinator):

    USER_AGENT = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
        "Html5Plus/1.0 (Immersed/20) uni-app"
    )

    def __init__(self, hass: HomeAssistant, api: ZhihuifangdongApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Zhihuifangdong Meter Data",
            update_interval=SCAN_INTERVAL,
        )
        self.api = api
        self.data = {}
        self.meter_id = None

    async def _async_update_data(self):
        try:
            headers = await self.api.async_get_headers()

            headers.update({
                "User-Agent": self.USER_AGENT,
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "Connection": "keep-alive",
                "Accept-Language": "zh-CN,zh-Hans;q=0.9",
            })

            # Step one: get house info to find meter ID
            house_info_url = "https://api.zhihuifangdong.net/core/app/rentExt/rentHouseInfoHb?current=1&size=1"
            async with async_timeout.timeout(10):
                resp = await self.api._session.get(house_info_url, headers=headers)
                resp.raise_for_status()
                house_info = await resp.json()

            records = house_info.get("data", {}).get("records", [])
            if not records:
                raise UpdateFailed("No house records found")

            meter_add_forms = records[0].get("meterAddForms", [])
            if not meter_add_forms:
                raise UpdateFailed("No meter info found")

            self.meter_id = meter_add_forms[0].get("meterId")
            if not self.meter_id:
                raise UpdateFailed("Meter ID not found")

            # Step two: get meter details using meter ID
            meter_detail_url = f"https://api.zhihuifangdong.net/netty/app/meter/getDeviceDetail?id={self.meter_id}&type=1"
            async with async_timeout.timeout(10):
                resp = await self.api._session.get(meter_detail_url, headers=headers)
                resp.raise_for_status()
                meter_data = await resp.json()

            if meter_data.get("success") and "data" in meter_data:
                self.data = meter_data["data"]
                return self.data

            raise UpdateFailed("Invalid meter detail response")

        except Exception as err:
            raise UpdateFailed(f"Error fetching Zhihuifangdong data: {err}") from err


class ZhihuifangdongMeterSensor(SensorEntity):
    def __init__(
        self,
        coordinator: ZhihuifangdongDataUpdateCoordinator,
        field: str,
        unit: str,
        name: str,
        is_calculated: bool = False,
        device_class: SensorDeviceClass | None = None,
        state_class: SensorStateClass | None = None,
    ) -> None:
        self.coordinator = coordinator
        self.field = field
        self.unit = unit
        self._name = name
        self.is_calculated = is_calculated
        self._attr_unique_id = f"zhihuifangdong_{field}_sensor"
        # optional attributes for energy sensors
        if device_class is not None:
            self._attr_device_class = device_class
        if state_class is not None:
            self._attr_state_class = state_class

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        if self.is_calculated:
            try:
                voltage = float(self.coordinator.data.get("voltage", 0))
                current = float(self.coordinator.data.get("electricity", 0))
                return round(voltage * current, 2)  # Power Calculation: P = U * I
            except Exception:
                return None
        val = self.coordinator.data.get(self.field)
        # Ensure numeric values are returned for energy sensors
        try:
            if val is None:
                return None
            return float(val)
        except (TypeError, ValueError):
            return val

    @property
    def unit_of_measurement(self):
        return self.unit

    @property
    def icon(self):
        icons = {
            "voltage": "mdi:flash",
            "electricity": "mdi:current-ac",
            "power": "mdi:power-plug",
            "residualElectricity": "mdi:gauge",
            "electricEnergy": "mdi:flash-circle",
        }
        return icons.get(self.field, "mdi:meter")


    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        return {
            "on": data.get("on", False),
            "open": data.get("open", False),
            "controllable": data.get("controllable", False),
            "status": data.get("status", "unknown"),
            "type": data.get("type", "unknown"),
            "ble_no": data.get("bleNo", ""),
            "community": data.get("communityName", ""),
            "house": data.get("houseName", ""),
            "sn": data.get("sn", ""),
            }

    @property
    def available(self):
        return bool(self.coordinator.data)

    async def async_update(self):
        await self.coordinator.async_request_refresh()
