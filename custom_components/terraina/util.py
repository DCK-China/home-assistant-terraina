"""Util code."""

import collections
from datetime import UTC, datetime
import hashlib
import hmac
import random
import string
import time
import uuid


def hmac_sha256_hex(message: str, key: str) -> str:
    """使用 HMAC-SHA256 计算消息摘要并返回16进制字符串."""
    key_bytes = key.encode("utf-8")
    message_bytes = message.encode("utf-8")
    hmac_obj = hmac.new(key_bytes, message_bytes, hashlib.sha256)
    return hmac_obj.hexdigest()


def generate_uuid() -> str:
    """生成一个随机 UUID 字符串."""
    return str(uuid.uuid4())


def current_timestamp_seconds() -> str:
    """返回当前时间的时间戳，单位为秒（整数）."""
    return str(int(time.time()))


def signature(
    params: dict[str, str], func: collections.abc.Callable[[str, str], str], key: str
) -> str:
    """对字典参数进行签名."""
    sorted_items = sorted(params.items())
    message = "&".join(f"{k}={v}" for k, v in sorted_items)
    return func(message, key)


def get_standard_headers(client_id: str, client_secret: str) -> dict:
    """Get standard header for api request."""
    timestamp = current_timestamp_seconds()
    nonce = generate_uuid()
    headers = {
        "x-platform-client-id": client_id,
        "x-platform-timestamp": timestamp,
        "x-platform-nonce": nonce,
    }
    header_param = {
        "client_id": client_id,
        "timestamp": timestamp,
        "nonce": nonce,
    }
    param_signature = signature(header_param, hmac_sha256_hex, client_secret)
    if not signature:
        return None
    headers["x-platform-signature"] = param_signature
    return headers


def from_dict_2_metadata(header: dict[str, str]) -> list[tuple[str, str]]:
    """Convert a dictionary to gRPC metadata format (list of tuples)."""
    return [(str(k), str(v)) for k, v in header.items()]


def utc_now_str() -> str:
    """返回当前UTC时间的格式化字符串，精确到毫秒."""
    now = datetime.now(UTC)
    return now.strftime("%Y-%m-%d %H:%M:%S.") + f"{int(now.microsecond / 1000):03d}"


def random_code(length: int = 8) -> str:
    """生成指定长度的随机字符串，包含大小写字母和数字."""
    chars = string.ascii_letters + string.digits  # a-zA-Z0-9
    return "".join(random.choices(chars, k=length))
