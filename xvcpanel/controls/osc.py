from __future__ import annotations

import socket
import struct


def _osc_string(value: str) -> bytes:
    encoded = value.encode("utf-8") + b"\0"
    return encoded + b"\0" * (-len(encoded) % 4)


def send_float(host: str, port: int, address: str, value: float) -> None:
    """Send one OSC float without requiring a third-party OSC package."""
    if not address.startswith("/"):
        raise ValueError("OSC addresses must start with /")
    if not 1 <= port <= 65535:
        raise ValueError("OSC port must be between 1 and 65535")
    packet = _osc_string(address) + _osc_string(",f") + struct.pack(">f", value)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(packet, (host, port))
