from __future__ import annotations

import ctypes
import logging
import platform
from pathlib import Path

log = logging.getLogger(__name__)

SPOUT_DLL = "SpoutLibrary.dll"


class SpoutBridge:
    """Thin wrapper around Spout2 for sending textures to Resolume.

    Falls back to a no-op stub if Spout2 is not available.
    """

    def __init__(self, name: str = "XVCpanel") -> None:
        self.name = name
        self._lib = None
        self._sender = None
        self._available = False

        if platform.system() != "Windows":
            log.info("Spout2 only available on Windows — running in stub mode")
            return

        self._try_load()

    def _try_load(self) -> None:
        try:
            dll = ctypes.CDLL(SPOUT_DLL)
            self._lib = dll
            self._available = True
            log.info("Spout2 loaded successfully")
        except OSError:
            log.warning("Spout2 DLL not found — running in stub mode")

    @property
    def available(self) -> bool:
        return self._available

    def create_sender(self, width: int = 1920, height: int = 1080) -> bool:
        if not self._available:
            log.debug("stub: create_sender(%s, %dx%d)", self.name, width, height)
            return True
        # Real Spout2 init would go here
        return True

    def send_texture(self, texture_id: int, width: int, height: int) -> bool:
        if not self._available:
            return True
        # Real Spout2 send would go here
        return True

    def release_sender(self) -> None:
        if not self._available:
            return
        # Real Spout2 release would go here

    def __del__(self) -> None:
        self.release_sender()
