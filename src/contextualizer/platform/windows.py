"""Windows platform support — not yet implemented."""
from PIL import Image


def check_environment() -> None:
    raise RuntimeError(
        "Windows is not yet supported. "
        "Contributions welcome — see platform/windows.py."
    )


def load_icon() -> Image.Image:
    raise NotImplementedError("Windows support is not yet implemented")
