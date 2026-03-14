"""macOS platform support — not yet implemented."""
from PIL import Image


def check_environment() -> None:
    raise RuntimeError(
        "macOS is not yet supported. "
        "Contributions welcome — see platform/macos.py."
    )


def load_icon() -> Image.Image:
    raise NotImplementedError("macOS support is not yet implemented")
