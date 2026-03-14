"""
Platform dispatch module. Imports the correct platform-specific implementation
based on the current OS and re-exports its public API.

Adding support for a new platform means creating a new module (e.g. platform/freebsd.py)
and adding a branch here.
"""
import sys

from PIL.Image import Image  # noqa: F401 — re-exported for type checking

if sys.platform == "linux":
    from contextualizer.platform.linux import check_environment as check_environment
    from contextualizer.platform.linux import load_icon as load_icon
elif sys.platform == "darwin":
    from contextualizer.platform.macos import check_environment as check_environment
    from contextualizer.platform.macos import load_icon as load_icon
elif sys.platform == "win32":
    from contextualizer.platform.windows import check_environment as check_environment
    from contextualizer.platform.windows import load_icon as load_icon
else:
    raise RuntimeError(f"Unsupported platform: {sys.platform}")
