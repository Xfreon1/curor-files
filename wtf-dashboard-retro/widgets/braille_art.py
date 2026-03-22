"""Convert image bytes to Unicode braille art for terminal display."""
import io

# Braille dot mapping for a 2x4 pixel cell
# Each braille char (U+2800-U+28FF) encodes 8 dots in a 2-wide, 4-tall grid
_DOT_MAP = [
    (0, 0, 0x01), (1, 0, 0x08),
    (0, 1, 0x02), (1, 1, 0x10),
    (0, 2, 0x04), (1, 2, 0x20),
    (0, 3, 0x40), (1, 3, 0x80),
]


def image_to_braille(image_bytes: bytes, width: int = 16, height: int = 8) -> list[str]:
    """Convert image bytes to braille art.

    Args:
        image_bytes: Raw image data (JPEG/PNG).
        width: Output width in braille characters (each = 2 px wide).
        height: Output height in braille characters (each = 4 px tall).

    Returns:
        List of strings, one per row. Empty list on failure.
    """
    try:
        from PIL import Image
    except ImportError:
        return []

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert("L")  # grayscale
        img = img.resize((width * 2, height * 4), Image.LANCZOS)
        img = img.convert("1")  # 1-bit with Floyd-Steinberg dithering
        pixels = img.load()

        rows = []
        for cy in range(height):
            row = ""
            for cx in range(width):
                bits = 0
                for dx, dy, mask in _DOT_MAP:
                    px = cx * 2 + dx
                    py = cy * 4 + dy
                    if pixels[px, py]:  # white/bright = dot on
                        bits |= mask
                row += chr(0x2800 + bits)
            rows.append(row)
        return rows
    except Exception:
        return []
