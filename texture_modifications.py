import os
from typing import Optional
from PIL import WalImageFile, ImageOps
from Q2BSP import *


def load_texture(pball_path: str, texture: str) -> Optional[Image.Image]:
    """
    Loads Image object based on texture name and subdir
    :param pball_path: path to game media folder
    :param texture: texture name the way it is stored in the bsp file (relative to pball/textures and without extension)
    :return: RGBA Image object
    """
    if not os.path.exists(pball_path + "/textures/" + "/".join(texture.lower().split("/")[:-1])):
        print(f"Info: no such path {pball_path + '/textures/' + '/'.join(texture.lower().split('/')[:-1])}")
        return
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
    :param map_path: absolute path to bsp file
    :param tex_dir: subdirectory of modified texture copies
    :param affix: prefix of new texture path
    :return: yields all texture paths stored in the bsp file
    """
    temp_map = Q2BSP(map_path)
    for idx, tex_info in enumerate(temp_map.tex_infos):
        tex_name = tex_info.get_texture_name()
        temp_map.tex_infos[idx].set_texture_name(tex_dir + affix + "_" + tex_name.split("/")[-1])
        yield tex_name
    temp_map.update_lump_sizes()
    temp_map.save_map(map_path, "_" + affix)


def create_inverted_textures(pball_path: str, map_path: str, new_dir: str, affix: str):
    """
    creates color inverted copy of all textures linked in the bsp file and creates map copy with edited texture links
    :param pball_path: path to game media folder
    :param map_path: relative to pball path, includes .bsp extension
    :param new_dir: subdirectory for white texture in /textures/
    :param affix: name for color inverted texture and for texture stored
    :return: None
    """
    textures = change_texture_paths(pball_path+map_path, new_dir, affix)
    for texture in textures:
        image = load_texture(pball_path, texture)
        if not image:
            continue
        # don't invert alpha channel
        r, g, b, a = image.split()
        rgb_image = Image.merge('RGB', (r, g, b))

        inverted_image = ImageOps.invert(rgb_image)

        r2, g2, b2 = inverted_image.split()

        final_transparent_image = Image.merge('RGBA', (r2, g2, b2, a))

        final_transparent_image.save(
            pball_path +"/textures/"+ new_dir + affix + "_" + texture.split("/")[len(texture.split("/")) - 1] + ".png", "PNG")


def create_monochrome_textures(pball_path: str, map_path: str, new_dir: str, affix: str) -> None:
    """
    creates monochrome 1×1 pixel copy of all textures linked in bsp and creates map copy with edited texture links
    :param pball_path: path to game media folder
    :param map_path: relative to pball path, includes .bsp extension
    :param new_dir: subdirectory for white texture in /textures/
    :param affix: name for monochrome texture and for texture stored
    :return: None
    """
    textures = change_texture_paths(pball_path+map_path, new_dir, affix)
    for texture in textures:
        image = load_texture(pball_path, texture)
        if not image:
            continue
        image = image.resize((1, 1))
        image.save(
            pball_path +"/textures/"+ new_dir + affix + "_" + texture.split("/")[len(texture.split("/")) - 1] + ".png", "PNG")


def create_grayscale_textures(pball_path: str, map_path: str, new_dir: str, affix: str) -> None:
    """
    creates grayscale versions of all textures linked in the bsp and creates map copy with edited texture links
    :param pball_path: path to game media folder
    :param map_path: relative to pball path, includes .bsp extension
    :param new_dir: subdirectory for white texture in /textures/
    :param affix: prefix for grayscale texture and for texture name stored in the bsp
    :return: None
    """
    textures = change_texture_paths(pball_path+map_path, new_dir, affix)
    for texture in textures:
        image = load_texture(pball_path, texture)
        if not image:
            continue
        image = image.convert('LA')
        image.save(
            pball_path +"/textures/"+ new_dir + affix + "_" + texture.split("/")[len(texture.split("/")) - 1] + ".png", "PNG")


def bsp_lightmap_only(pball_path: str, map_path: str, new_dir: str, affix: str) -> None:
    """
    Assigns white texture to all faces so that face color solely depends on the lightmap
    :param pball_path: path to game media folder
    :param map_path: relative to pball path, includes .bsp extension
    :param new_dir: subdirectory for white texture in /textures/
    :param affix: name for white texture and for texture stored
    :return: None
    """
    temp_map = Q2BSP(pball_path+map_path)
    # set all stored texture names to white texture path
    for idx, tex_info in enumerate(temp_map.tex_infos):
        temp_map.tex_infos[idx].set_texture_name(new_dir + affix)
    # save new bsp
    temp_map.update_lump_sizes()
    temp_map.save_map(pball_path+map_path, "_" + affix)
    # create white texture if it doesnt exist yet
    create_white_texture(pball_path + "/textures/" + new_dir, affix + ".png", 1)


def create_white_texture(path: str, name: str, size: int) -> None:
    """
    Creates white texture + specified subdirectory if they don't exist
    :param path: absolute path
    :param name: should start with "/" and contain file extension
    :param size: width and height of square-shaped white texture
    :return: None
    """
    # create subdirectory(/ies) if it doesn't exist
    if not os.path.exists(path):
        os.makedirs(path)
    # create white image if no image with the specified path exists
    if not os.path.exists(path+name):
        img = Image.new('RGB', (size, size), (255, 255, 255))
        img.save(path+name, "PNG")
        print(f"Created white texture of size {size}×{size}")
