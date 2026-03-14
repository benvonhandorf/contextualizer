"""
Linux-specific system tray icon creation.

pystray on Linux uses the StatusNotifierItem (SNI) protocol or libappindicator.
Requirements:
  - KDE Plasma: works out of the box.
  - GNOME Shell: requires the "AppIndicator and KStatusNotifierItem Support" extension.
  - Other desktops: any panel implementing the SNI spec should work.
"""
import os

from PIL import Image, ImageDraw


def check_environment() -> None:
    """
    Verify that a graphical display environment is available.

    Raises RuntimeError with a descriptive message if the environment is
    unlikely to support a system tray icon.
    """
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        raise RuntimeError(
            "No graphical display detected (DISPLAY and WAYLAND_DISPLAY are both unset).\n"
            "Contextualizer requires a running desktop environment with system tray support.\n"
            "On GNOME Shell, also ensure the 'AppIndicator and KStatusNotifierItem Support' "
            "extension is enabled."
        )


def load_icon() -> Image.Image:
    """
    Create the system tray icon as a PIL Image.

    Returns a 64x64 RGBA image. Replace with a proper asset once one is available
    by loading it from the package data directory instead.
    """
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Steel-blue circle as a placeholder icon
    draw.ellipse([8, 8, 56, 56], fill=(70, 130, 180, 255))
    return img
