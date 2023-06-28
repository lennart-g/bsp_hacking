import os
from typing import Tuple

from PIL import Image, WalImageFile

palette_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pb2e.pal")


def get_average_color(texture_path: str) -> Tuple[int, int, int, int]:
    """
    Opens file if in supported format (png, jpg, tga or wal), resizes to 1x1 and returns the color
    :param texture_path: path to texture
    :return: tuple containing RGBA color
    """
    if os.path.splitext(texture_path)[1] in [".png", ".jpg", ".tga"]:
        img = Image.open(texture_path)
        img2 = img.resize((1, 1))
        img2 = img2.convert("RGBA")
        img2 = img2.load()
        color = img2[0, 0]

    elif os.path.splitext(texture_path)[1] == ".wal":
        # wal files are 8 bit and require a palette
        with open(palette_path, "r") as pal:
            conts = pal.read().split("\n")[3:]
            conts = [b.split(" ") for b in conts]
            conts = [c for b in conts for c in b]
            conts.pop(len(conts) - 1)
            conts = list(map(int, conts))
            img3 = WalImageFile.open(texture_path)
            img3.putpalette(conts)
            img3 = img3.convert("RGBA")

            img2 = img3.resize((1, 1))

            color = img2.getpixel((0, 0))
    else:
        raise ValueError(
            f"Unsupported format {os.path.splitext(texture_path)[1]} in {texture_path}"
            f"\nsupported formats are .png, .jpg, .tga, .wal"
        )
    return color
