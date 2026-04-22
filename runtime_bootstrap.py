from __future__ import annotations

import os
import platform as _platform


def patch_windows_platform() -> None:
    """Avoid slow WMI-based Windows probes during scientific imports."""
    if os.name != "nt" or getattr(_platform, "_newsprop_platform_patched", False):
        return

    _platform.machine = lambda: "AMD64"  # type: ignore[assignment]
    _platform.processor = lambda: "AMD64"  # type: ignore[assignment]
    _platform.win32_ver = lambda: ("10", "10.0.0", "", "Multiprocessor Free")  # type: ignore[assignment]
    _platform._newsprop_platform_patched = True
