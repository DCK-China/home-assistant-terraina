"""gRPC util for requesting data."""

import logging

from . import platform_iot_streams_pb2
from .const import (
    BINDING,
    CHARGING,
    DOMAIN,
    EMERGENCY_STOP,
    LOCKED,
    LOG,
    OTA,
    RAINED,
    TASK,
    VERSION,
    WORKING_MODE,
    WORKING_STATUS,
)
from .payload import DeviceMessageWrapper
from .util import random_code, utc_now_str

CLOCK_OUT_OF_SYNC_MAX_SEC = 20
HEARTBEAT_TIME_INTERVAL = 30
_LOGGER = logging.getLogger(__name__)


class MessageBuilder:
    """Build gRPC message."""

    _HA_PREFIX = "ha-"
    _VERSION = VERSION

    def __init__(self) -> None:
        """Init."""
        return

    def build_heartbeat(self, serial_number: str) -> platform_iot_streams_pb2.In:
        """Produce heartbeat message."""
        return platform_iot_streams_pb2.In(
            type="heartbeat",
            sn=serial_number,
            payload="",
        )

    def build_query_state_message(
        self, serial_number: str
    ) -> tuple[platform_iot_streams_pb2.In, str]:
        """Produce query_state message."""
        msg_id = self._HA_PREFIX + random_code()
        service_id = self._HA_PREFIX + random_code()
        msg = DeviceMessageWrapper()
        msg.set_info(
            self._VERSION,
            msg_id,
            serial_number,
            utc_now_str(),
        ).set_service(service_id, "get", {"getDeviceDetail": None})
        return platform_iot_streams_pb2.In(
            type="device",
            sn=serial_number,
            payload=msg.to_base64(),
        ), msg_id

    def build_change_status_message(
        self, serial_number: str, status: int
    ) -> tuple[platform_iot_streams_pb2.In, str]:
        """Produce query_state message."""
        msg_id = self._HA_PREFIX + random_code()
        service_id = self._HA_PREFIX + random_code()
        msg = DeviceMessageWrapper()
        msg.set_info(
            self._VERSION,
            msg_id,
            serial_number,
            utc_now_str(),
        ).set_service(
            service_id,
            "set",
            {"setWorkStatus": {"status": status}},
        )
        return platform_iot_streams_pb2.In(
            type="device",
            sn=serial_number,
            payload=msg.to_base64(),
        ), msg_id

    def build_change_status_message_payload(
        self, serial_number: str, status: int
    ) -> str:
        """Produce query_state message."""
        msg_id = self._HA_PREFIX + random_code()
        service_id = self._HA_PREFIX + random_code()
        msg = DeviceMessageWrapper()
        msg.set_info(
            self._VERSION,
            msg_id,
            serial_number,
            utc_now_str(),
        ).set_service(
            service_id,
            "set",
            {"setWorkStatus": {"status": status}},
        )
        return msg.to_base64()


def split_bits(self, value: int) -> dict:
    """Split an integer into specific bit fields."""
    return {
        "locked": LOCKED[(value >> 0) & 0b1],
        "emergency_stop": EMERGENCY_STOP[(value >> 1) & 0b1],
        "charging": CHARGING[(value >> 2) & 0b11],
        "rained": RAINED[(value >> 4) & 0b11],
        "working_status": WORKING_STATUS[(value >> 6) & 0b1111],
        "ota": OTA[(value >> 10) & 0b1],
        "log": LOG[(value >> 11) & 0b1],
        "task": TASK[(value >> 12) & 0b1],
        "working_mode": WORKING_MODE[(value >> 13) & 0b1],
        "binding": BINDING[(value >> 14) & 0b1],
        "end": (value >> 15) & 0b1,
        "reserve": (value >> 16) & 0b1,
    }
