"""Windows platform support — not yet implemented."""
from PIL import Image


def load_icon() -> Image.Image:
    raise NotImplementedError("Windows support is not yet implemented")
