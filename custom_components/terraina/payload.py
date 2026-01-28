"""Encapsule of original proto payload object."""

import base64
from collections.abc import Iterable
from typing import Any

from .terraina_pb2 import DeviceEvent, DeviceMessage, DeviceService, Params, Property


class ParamsWrapper:
    """Wrap the Prarams object in gRPC."""

    def __init__(self, proto: Params | None = None) -> None:
        """Init."""
        self._proto = proto or Params()

    def set_value(self, key: str, value: Any) -> "ParamsWrapper":
        """Set value."""
        self._proto.key = key
        if isinstance(value, str):
            self._proto.stringValue = value
        elif isinstance(value, int):
            self._proto.intValue = value
        elif isinstance(value, bool):
            self._proto.boolValue = value
        elif isinstance(value, float):
            self._proto.doubleValue = value
        elif isinstance(value, dict):
            for k, v in value.items():
                p = ParamsWrapper(self._proto.params.add())
                p.set_value(k, v)
        return self

    def get_proto(self) -> Params:
        """Get proto object."""
        return self._proto


class PropertyWrapper:
    """Property wrapper."""

    def __init__(self, proto: Property | None = None) -> None:
        """Init."""
        self._proto = proto or Property()

    def set_value(self, name: str, value: Any) -> "PropertyWrapper":
        """Set value."""
        self._proto.name = name
        if isinstance(value, str):
            self._proto.stringValue = value
        elif isinstance(value, int):
            self._proto.intValue = value
        elif isinstance(value, bool):
            self._proto.boolValue = value
        elif isinstance(value, float):
            self._proto.doubleValue = value
        return self

    def get_proto(self) -> Property:
        """Get proto."""
        return self._proto


class DeviceEventWrapper:
    """DeviceEvent wrapper."""

    def __init__(self, proto: DeviceEvent | None = None) -> None:
        """Init."""
        self._proto = proto or DeviceEvent()

    def set_name(self, name: str) -> "DeviceEventWrapper":
        """Set name."""
        self._proto.name = name
        return self

    def add_param(self, key: str, value: Any) -> "DeviceEventWrapper":
        """Add param."""
        p = ParamsWrapper(self._proto.params.add())
        p.set_value(key, value)
        return self

    def get_proto(self) -> DeviceEvent:
        """Get proto."""
        return self._proto


class DeviceServiceWrapper:
    """Device Service Wrapper."""

    def __init__(self, proto: DeviceService | None = None) -> None:
        """Init."""
        self._proto = proto or DeviceService()

    def set_info(self, service_id: str, name: str) -> "DeviceServiceWrapper":
        """Set info."""
        self._proto.id = service_id
        self._proto.name = name
        return self

    def add_param(self, key: str, value: Any) -> "DeviceServiceWrapper":
        """Add param."""
        p = ParamsWrapper(self._proto.params.add())
        p.set_value(key, value)
        return self

    def get_proto(self) -> DeviceService:
        """Get proto."""
        return self._proto


class DeviceMessageWrapper:
    """Device message Wrapper."""

    def __init__(self, proto: DeviceMessage | None = None) -> None:
        """Init."""
        self._proto = proto or DeviceMessage()

    def set_info(
        self, version: str, msg_id: str, sn: str, time: str
    ) -> "DeviceMessageWrapper":
        """Set info."""
        self._proto.version = version
        self._proto.id = msg_id
        self._proto.sn = sn
        self._proto.time = time
        return self

    def add_property(self, name: str, value: Any) -> PropertyWrapper:
        """Add propterty."""
        wrapper = PropertyWrapper(self._proto.properties.add())
        wrapper.set_value(name, value)
        return wrapper

    def add_event(self, name: str, params: dict[str, Any]) -> DeviceEventWrapper:
        """Add event."""
        wrapper = DeviceEventWrapper(self._proto.events.add())
        wrapper.set_name(name)
        for k, v in params.items():
            wrapper.add_param(k, v)
        return wrapper

    def set_service(
        self, service_id: str, name: str, params: dict[str, Any]
    ) -> DeviceServiceWrapper:
        """Set service."""
        wrapper = DeviceServiceWrapper(self._proto.services)
        wrapper.set_info(service_id, name)
        for k, v in params.items():
            wrapper.add_param(k, v)
        return wrapper

    def to_base64(self) -> str:
        """Transfer the proto object to base 64 string."""
        return base64.b64encode(self._proto.SerializeToString()).decode()

    @classmethod
    def from_base64(cls, b64_str: str) -> "DeviceMessageWrapper":
        """Parse object from base 64 string."""
        try:
            proto = DeviceMessage()
            proto.ParseFromString(base64.b64decode(b64_str))
            return cls(proto)
        except:
            return DeviceMessageWrapper()

    def get_proto(self) -> DeviceMessage:
        """Get proto."""
        return self._proto

    def __repr__(self) -> str:
        """Repr."""
        return str(self._proto)


def _params_to_dict(params: Iterable[Params]) -> dict[str, Any]:
    """Convert a repeated Params (or any iterable of Params) into a nested dict.
    - If the same key appears multiple times, values are combined into a list.
    - Leaves without a set oneof value become None.
    """
    result: dict[str, Any] = {}
    for p in params:
        key = p.key

        # If this param has nested params, recurse
        if len(p.params) > 0:
            value = _params_to_dict(p.params)
        else:
            # Determine which oneof is set (value is the oneof group name)
            oneof_name = p.WhichOneof("value")
            if oneof_name is None:
                value = None
            else:
                value = getattr(p, oneof_name)

        # Merge duplicate keys into a list
        if key in result:
            if isinstance(result[key], list):
                result[key].append(value)
            else:
                result[key] = [result[key], value]
        else:
            result[key] = value

    return result


class PayLoadExtractor:
    """A class to extract data in the payload (expects DeviceMessage proto wrapper)."""

    def __init__(self, device_message_wrapper) -> None:
        """Init."""
        # device_message_wrapper: your DeviceMessageWrapper instance
        self._device_message_wrapper = device_message_wrapper

    def extract(self) -> dict[str, Any]:
        """Extract useful structured dict from the protobuffer DeviceMessage."""
        proto: DeviceMessage = self._device_message_wrapper.get_proto()

        # services is a singular message in your proto (DeviceService)
        if proto.services is None:
            return {}

        svc = proto.services
        # svc.params is a repeated Params -> convert to dict
        return _params_to_dict(svc.params)
