import copy
import os
import warnings
from typing import Optional
import logging

from Q2BSP import *
from util.bsp_util import get_faces_from_vertices, get_normals, get_unique_texture_names
from util.geometry import normalize_faces
from util.texture_util import get_average_color
import numpy as np

@dataclass
class Polygon:
    vertices: List[List[int]]
    tex_id: int
    normal: point3f

    def __iter__(self):
        return iter(astuple(self))


def get_polygons(path: str, pball_path: str) -> Tuple[List[Polygon], List[Tuple[int]]]:
    """
    Converts information from Q2BSP object into List of Polygon objects Calculates mean color of
    all used textures and builds list of all unique colors
    :param path: full path to map
    :param pball_path: path to pball / game media directory, needed to get full texture path
    :return: list of Polygon objects, list of RGB colors (in the case of a face normally not
    rendered in the game, e.g. a clip brush, the color is (0,0,0,0))
    """
    # from Q2BSP object, this uses attributes .faces, tex_infos, face_edges, edge_list, vertices, .planes

    # instead of directly reading all information from file, the Q2BSP class is used for reading
    temp_map = Q2BSP(path, load_textures=True, load_geometry=True)

    # get a list of unique texture names (which are stored without an extension -> multiple ones
    # must be tested)
    textures, unique_textures = get_unique_texture_names(temp_map)
    # iterate through texture list, look which one exists, load, rescale to 1×1 pixel = color is
    # mean color
    average_colors = get_average_colors(pball_path, unique_textures)

    # instead of storing face color directly in the Polygon object, store an index so that you
    # can easily change one color for all faces using the same one
    # tex_indices = [x.texture_info for x in temp_map.faces]
    tex_indices = [x.texture_info for x in temp_map.faces for y in range(x.num_edges-2)]
    tex_ids = [unique_textures.index(textures[tex_index]) for tex_index in tex_indices]

    # each face is a list of vertices stored as Tuples
    # faces, skip_surfaces = get_faces_from_vertices(temp_map)
    faces, skip_surfaces = get_faces_from_vertices(temp_map)

    # get minimal of all x y and z values and move all vertices so they all have coordinate
    # values >= 0
    polys_normalized = normalize_faces(faces)
    # polys_normalized = faces

    # construct polygon list out of the faces, indices into unique textures aka colors (two
    # different textures could have the same mean color), normals
    # polygons: List[Polygon] = list()
    # for idx, poly in enumerate(polys_normalized):
    #     polygon = Polygon(poly, tex_ids[idx], point3f(0.0, 0.0, 0.0))
    #     polygons.append(polygon)
    #
    # print(skip_surfaces, "skip")
    # for i in skip_surfaces[::-1]:
    #     polygons.pop(i)

    polys_normalized = np.delete(polys_normalized, skip_surfaces, axis=0)
    tex_ids = [x for i, x in enumerate(tex_ids) if i not in skip_surfaces]

    return polys_normalized, tex_ids, average_colors


def get_average_colors(pball_path, texture_list_cleaned):
    average_colors = list()
    for texture in texture_list_cleaned:
        color = (0, 0, 0)
        if not os.path.exists(
            pball_path + "/textures/" + "/".join(texture.lower().split("/")[:-1])
        ):
            warnings.warn(
                f"No such path {pball_path + '/textures/' + '/'.join(texture.lower().split('/')[:-1])}. Defaulting average color to {color} "
            )

            # set default color for missing textures
            average_colors.append(color)
            continue

        # list of all files in stored subdirectory
        texture_options = os.listdir(
            pball_path + "/textures/" + "/".join(texture.lower().split("/")[:-1])
        )
        texture_options = [x for x in texture_options if os.path.splitext(x)[-1] in ('.jpg', '.png', '.tga', '.wal')]

        texture_path = ""
        # iterate through texture options until one name matches stored texture name
        for idx, tex_option in enumerate(texture_options):
            if texture.split("/")[-1].lower() == os.path.splitext(tex_option)[0]:
                texture_path = (
                    "/".join(texture.lower().split("/")[:-1]) + "/" + tex_option
                )
                break

        # texture was not found in specified subdirectory
        if not texture_path:
            print("Missing texture: ", texture)
            average_colors.append((0, 0, 0))
            continue

        try:
            color = get_average_color(pball_path + "/textures/" + texture_path)
        except ValueError as e:
            logging.warning('Captured exception in get_average_color: ' + str(e))
        except Exception as e:
            logging.error('Unexpected error in get_average_color: ' + str(e))

        color_rgb = color[:3]
        if color_rgb == (0, 0, 0):
            print(texture)
        if True in [
            x in texture.lower() for x in ["origin", "clip", "skip", "hint", "trigger"]
        ]:
            print(texture)
            color_rgb = (0, 0, 0, 0)  # actually rgba
        average_colors.append(color_rgb)
    return average_colors


if __name__ == '__main__':
    import time
    start_time = time.time()
    get_polygons("/home/lennart/Downloads/pball/maps/bankrob.bsp", "/home/lennart/Downloads/pball")
    print(f'Time for get_polygons: {time.time() - start_time} seconds')
