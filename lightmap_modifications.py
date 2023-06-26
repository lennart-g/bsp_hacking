import os

from Q2BSP import *


def make_lightmap_grayscale(map_path: str, affix: str) -> None:
    """
    Turns each lightmap texel into grayscale
    :param map_path: absolute path to map
    :return: None
    """
    temp_map = Q2BSP(map_path)
    for idx, color in enumerate(temp_map.lightmaps):
        temp_map.lightmaps[idx] = RGBColor(
            *[int(0.2989 * color.r + 0.5870 * color.g + 0.1140 * color.b)] * 3
        )
    temp_map.worldspawn["message"] = (
        map_path.split("/")[-1] + "\ngrayscale lightmap version"
    )
    temp_map.save_lightmaps(temp_map.lightmaps)
    temp_map.update_lump_sizes()
    temp_map.save_map(map_path, "_" + affix)
