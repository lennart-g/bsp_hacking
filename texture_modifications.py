from PIL import Image, WalImageFile, ImageOps
import os
from typing import Optional
from Q2BSP import *


def load_texture(pball_path: str, texture: str) -> Optional[Image.Image]:
    """
    Loads Image object based on texture name and subdir
    :param pball_path:
    :param texture:
    :return: RGBA Image object
    """
    # list of all files in stored subdirectory
    texture_options = os.listdir(pball_path + "/textures/" + "/".join(texture.lower().split("/")[:-1]))
    texture_path = ""
    # iterate through texture options until one name matches stored texture name
    for idx, tex_option in enumerate(texture_options):
        if texture.split("/")[-1].lower() == os.path.splitext(tex_option)[0]:
            texture_path = "/".join(texture.lower().split("/")[:-1]) + "/" + tex_option
            break

    # texture was not found in specified subdirectory
    if not texture_path:
        print("Missing texture: ", texture)
        return

    if os.path.splitext(texture_path)[1] in [".png", ".jpg", ".tga"]:
        img = Image.open(pball_path + "/textures/" + texture_path)
        img2 = img.convert("RGBA")
        return img2

    elif os.path.splitext(texture_path)[1] == ".wal":
        # wal files are 8 bit and require a palette
        with open("pb2e.pal", "r") as pal:
            conts = (pal.read().split("\n")[3:])
            conts = [b.split(" ") for b in conts]
            conts = [c for b in conts for c in b]
            conts.pop(len(conts) - 1)
            conts = list(map(int, conts))
            img3 = WalImageFile.open(pball_path + "/textures/" + texture_path)
            img3.putpalette(conts)
            img3 = img3.convert("RGBA")
            return img3
    else:
        print(f"Error: unsupported format {os.path.splitext(texture_path)[1]} in {texture_path}"
              f"\nsupported formats are .png, .jpg, .tga, .wal")
        return


def change_texture_paths(map_path: str, tex_dir: str, affix: str) -> List[str]:
    """
    changes stored image directory and adds prefix to stored texture name
    :param map_path:
    :param tex_dir:
    :param affix:
    :return:
    """
    temp_map = Q2BSP(map_path)
    for idx, tex_info in enumerate(temp_map.tex_infos):
        tex_name = tex_info.get_texture_name()
        temp_map.tex_infos[idx].set_texture_name(tex_dir + affix + "_" + tex_name.split("/")[-1])
        yield tex_name
    print("test")
    temp_map.update_lump_sizes()
    temp_map.save_map(map_path, "_" + affix)


def create_inverted_textures(pball_path, map_path, new_dir, affix):
    textures = change_texture_paths(pball_path+map_path, new_dir, affix)
    for texture in textures:
        image = load_texture(pball_path, texture)
        if not image:
            continue
        r, g, b, a = image.split()
        rgb_image = Image.merge('RGB', (r, g, b))

        inverted_image = ImageOps.invert(rgb_image)

        r2, g2, b2 = inverted_image.split()

        final_transparent_image = Image.merge('RGBA', (r2, g2, b2, a))

        final_transparent_image.save(
            pball_path +"/textures/"+ new_dir + affix + "_" + texture.split("/")[len(texture.split("/")) - 1] + ".png", "PNG")


def create_uni_textures(pball_path, map_path, new_dir, affix):
    textures = change_texture_paths(pball_path+map_path, new_dir, affix)
    for texture in textures:
        image = load_texture(pball_path, texture)
        if not image:
            continue
        image = image.resize((1, 1))
        image.save(
            pball_path +"/textures/"+ new_dir + affix + "_" + texture.split("/")[len(texture.split("/")) - 1] + ".png", "PNG")


def create_grayscale_textures(pball_path, map_path, new_dir, affix):
    textures = change_texture_paths(pball_path+map_path, new_dir, affix)
    for texture in textures:
        image = load_texture(pball_path, texture)
        if not image:
            continue
        image = image.convert('LA')
        image.save(
            pball_path +"/textures/"+ new_dir + affix + "_" + texture.split("/")[len(texture.split("/")) - 1] + ".png", "PNG")


def bsp_lightmap_only(pball_path, map_path, new_dir, affix):
    temp_map = Q2BSP(pball_path+map_path)
    for idx, tex_info in enumerate(temp_map.tex_infos):
        temp_map.tex_infos[idx].set_texture_name(new_dir + "white")
    temp_map.update_lump_sizes()
    temp_map.save_map(pball_path+map_path, "_" + affix)
    create_white_texture(pball_path + "/textures/" + new_dir, "white.png", 1)


def create_white_texture(path, name, size) -> None:
    if not os.path.exists(path):
        os.makedirs(path)
    img = Image.new('RGB', (size, size), (255, 255, 255))
    img.save(path+name, "PNG")
    print(f"Created white texture of size {size}×{size}")
