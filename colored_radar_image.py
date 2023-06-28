import copy
import os
import warnings
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np

from Q2BSP import *
from util.bsp_util import get_faces_from_vertices, get_normals, get_unique_texture_names
from util.geometry import normalize_faces
from util.texture_util import get_average_color


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
    # instead of directly reading all information from file, the Q2BSP class is used for reading
    temp_map = Q2BSP(path)

    # get a list of unique texture names (which are stored without an extension -> multiple ones
    # must be tested)
    textures, unique_textures = get_unique_texture_names(temp_map)
    # iterate through texture list, look which one exists, load, rescale to 1×1 pixel = color is
    # mean color
    average_colors = get_average_colors(pball_path, unique_textures)

    # instead of storing face color directly in the Polygon object, store an index so that you
    # can easily change one color for all faces using the same one
    tex_indices = [x.texture_info for x in temp_map.faces]
    tex_ids = [unique_textures.index(textures[tex_index]) for tex_index in tex_indices]

    # each face is a list of vertices stored as Tuples
    faces, skip_surfaces = get_faces_from_vertices(temp_map)

    # get minimal of all x y and z values and move all vertices so they all have coordinate
    # values >= 0
    polys_normalized = normalize_faces(faces)

    normals = get_normals(temp_map)

    # construct polygon list out of the faces, indices into unique textures aka colors (two
    # different textures could have the same mean color), normals
    polygons: List[Polygon] = list()
    for idx, poly in enumerate(polys_normalized):
        polygon = Polygon(poly, tex_ids[idx], point3f(*normals[idx]))
        polygons.append(polygon)

    print(skip_surfaces, "skip")
    for i in skip_surfaces[::-1]:
        polygons.pop(i)

    return polygons, average_colors


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

        color = get_average_color(pball_path + "/textures/" + texture_path)

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


def sort_by_axis(faces: List[Polygon], axis: int) -> List[Polygon]:
    """
    Sorts polygons by depth aka how far away from the camera they are
    depth is resembled by the axis that is not used for pixel position
    :param faces: list of Polygons
    :param axis: axis that defines the depth (one of [0,1,2])
    :return: sorted list of Polygons
    """
    faces = copy.deepcopy(faces)
    order = [
        mean(depth_coordinate)
        for depth_coordinate in [
            [vert[axis] for vert in face] for face in [face.vertices for face in faces]
        ]
    ]
    faces_sorted = [
        x
        for _, x in sorted(zip(order, faces), key=operator.itemgetter(0), reverse=True)
    ]
    return faces_sorted


def get_rot_polys(
    polys: List[Polygon], x_angle: float, y_angle: float, z_angle: float
) -> List[Polygon]:
    """
    Applies matrix rotations by z, y, x axis in this order on vertices and normals
    :param polys: list of Polygons
    :param x_angle: rotation angle in degrees
    :param y_angle: rotation angle in degrees
    :param z_angle: rotation angle in degrees
    :return: rotated Polygon list
    """
    faces = copy.deepcopy(polys)
    if (
        not z_angle == 0
    ):  # should speed things up because vertices would be left unchanged with angle == 0 anyway
        for idx0, face in enumerate(faces):
            # rotate each vertex
            for idx1, vertex in enumerate(face.vertices):
                old_x, old_y, old_z = faces[idx0].vertices[idx1]
                old_normal_x, old_normal_y, old_normal_z = faces[idx0].normal
                faces[idx0].vertices[idx1][0] = (
                    math.cos(math.radians(z_angle)) * old_x
                    - math.sin(math.radians(z_angle)) * old_y
                )
                faces[idx0].vertices[idx1][1] = (
                    math.sin(math.radians(z_angle)) * old_x
                    + math.cos(math.radians(z_angle)) * old_y
                )
            # rotate normals once per face
            faces[idx0].normal.x = (
                math.cos(math.radians(z_angle)) * old_normal_x
                - math.sin(math.radians(z_angle)) * old_normal_y
            )
            faces[idx0].normal.y = (
                math.sin(math.radians(z_angle)) * old_normal_x
                + math.cos(math.radians(z_angle)) * old_normal_y
            )

    if not y_angle == 0:
        for idx0, face in enumerate(faces):
            for idx1, vertex in enumerate(face.vertices):
                old_x, old_y, old_z = faces[idx0].vertices[idx1]
                old_normal_x, old_normal_y, old_normal_z = faces[idx0].normal
                faces[idx0].vertices[idx1][0] = (
                    math.cos(math.radians(y_angle)) * old_x
                    + math.sin(math.radians(y_angle)) * old_z
                )
                faces[idx0].vertices[idx1][2] = (
                    -math.sin(math.radians(y_angle)) * old_x
                    + math.cos(math.radians(y_angle)) * old_z
                )
            faces[idx0].normal.x = (
                math.cos(math.radians(y_angle)) * old_normal_x
                + math.sin(math.radians(y_angle)) * old_normal_z
            )
            faces[idx0].normal.z = (
                -math.sin(math.radians(y_angle)) * old_normal_x
                + math.cos(math.radians(y_angle)) * old_normal_z
            )

    if not x_angle == 0:
        for idx0, face in enumerate(faces):
            for idx1, vertex in enumerate(face.vertices):
                old_x, old_y, old_z = faces[idx0].vertices[idx1]
                old_normal_x, old_normal_y, old_normal_z = faces[idx0].normal
                faces[idx0].vertices[idx1][1] = (
                    math.cos(math.radians(x_angle)) * old_y
                    - math.sin(math.radians(x_angle)) * old_z
                )
                faces[idx0].vertices[idx1][2] = (
                    math.sin(math.radians(x_angle)) * old_y
                    + math.cos(math.radians(x_angle)) * old_z
                )
            faces[idx0].normal.y = (
                math.cos(math.radians(x_angle)) * old_normal_y
                - math.sin(math.radians(x_angle)) * old_normal_z
            )
            faces[idx0].normal.z = (
                math.sin(math.radians(x_angle)) * old_normal_y
                + math.cos(math.radians(x_angle)) * old_normal_z
            )

    # moves all polys so that all coordinate values >= 0
    min_x = min(
        [a for b in [[vert[0] for vert in face.vertices] for face in faces] for a in b]
    )
    min_y = min(
        [a for b in [[vert[1] for vert in face.vertices] for face in faces] for a in b]
    )
    min_z = min(
        [a for b in [[vert[2] for vert in face.vertices] for face in faces] for a in b]
    )

    for idx1, face in enumerate(faces):
        for idx2, vert in enumerate(face.vertices):
            faces[idx1].vertices[idx2][0] = (
                vert[0] - min_x
            )  # so nothing of the map is clipped off
            faces[idx1].vertices[idx2][1] = vert[1] - min_y
            faces[idx1].vertices[idx2][2] = vert[2] - min_z

    return faces


def create_poly_image(
    polys: List[Polygon],
    ax: plt.axes,
    average_colors: List[Tuple[int]],
    perspective: bool,
    max_resolution: int = 2048,
    fov: int = 50,
) -> Optional[Image.Image]:
    """
    Draws radar image and assigns it to axes or returns it
    :param polys:
    :param ax:
    :param average_colors:
    :param max_resolution:
    :param fov:
    :return:
    """
    # y value will be the images x value and (max z value - z) will be images y value
    x = 1
    y = 2
    z = 3 - (x + y)
    # sorted descending because the bigger the x value the further away the polygon is from camera
    polys = sort_by_axis(polys, z)
    # round vertices so they are integers and match pixel positions

    max_x = round(
        max(
            [
                vert[x]
                for vert in [a for b in [face.vertices for face in polys] for a in b]
            ]
        )
    )
    max_y = round(
        max(
            [
                vert[y]
                for vert in [a for b in [face.vertices for face in polys] for a in b]
            ]
        )
    )
    # print("maxs before rescaling", max_x, max_y)

    # the view vector is the direction the camera is looking ... in orthographic projection
    view_vector = [0, 0, 0]
    view_vector[z] = 1  # dynamic in case x y z values get changed again

    # calculates most extreme (highest absolute) value for all vector x and y angles
    all_verts = [
        a for b in [[vert for vert in face.vertices] for face in polys] for a in b
    ]
    shifts = [
        (
            vert[x] / np.tan(math.radians(fov)) - vert[z],
            vert[y] / np.tan(math.radians(fov)) - vert[z],
        )
        for vert in all_verts
    ]
    shift = max([a for b in shifts for a in b])
    shift = shift if shift > 0 else 0
    # print("shift", shift)

    if perspective:
        # applies projection on x and y values
        for idx1, face in enumerate(polys):
            for idx2, vert in enumerate(face.vertices):
                # shifts all vertices on z axis to render all with set fov
                polys[idx1].vertices[idx2][z] += shift
                # for not rendering anything in front of the near clipping plane
                if polys[idx1].vertices[idx2][z] >= 1:
                    polys[idx1].vertices[idx2][x] = (vert[x] - max_x / 2) / vert[
                        z
                    ] * max(max_x, max_y) + max_x / 2
                    polys[idx1].vertices[idx2][y] = (vert[y] - max_y / 2) / vert[
                        z
                    ] * max(max_x, max_y) + max_y / 2
                else:
                    polys[idx1].vertices[idx2][x] = None
                    polys[idx1].vertices[idx2][y] = None

    # min and max x and y values of the projected vertices
    pmin_x = round(
        min(
            [
                vert[x]
                for vert in [a for b in [face.vertices for face in polys] for a in b]
            ]
        )
    )
    pmin_y = round(
        min(
            [
                vert[y]
                for vert in [a for b in [face.vertices for face in polys] for a in b]
            ]
        )
    )
    pmax_x = round(
        max(
            [
                vert[x]
                for vert in [a for b in [face.vertices for face in polys] for a in b]
            ]
        )
    )
    pmax_y = round(
        max(
            [
                vert[y]
                for vert in [a for b in [face.vertices for face in polys] for a in b]
            ]
        )
    )
    # print("mins projected", pmin_x, pmin_y)
    # print("maxs projected", pmax_x, pmax_y)

    # image dimensions are set to these new maximum x and y values ... before perspective projection
    img = Image.new(
        "RGBA",
        (
            int(
                (pmax_x - pmin_x)
                / max((pmax_x - pmin_x, pmax_y - pmin_y))
                * max_resolution
            ),
            int(
                (pmax_y - pmin_y)
                / max((pmax_x - pmin_x, pmax_y - pmin_y))
                * max_resolution
            ),
        ),
        (255, 255, 255, 100),
    )
    draw = ImageDraw.Draw(img, "RGBA")

    for idx, face in enumerate(polys):
        # might be necessary at some point where the near clipping plane is inside of the map
        if any([not vert[x] or not vert[y] for vert in face.vertices]):
            # print("skipped")
            continue
        # calculates center of mass for face, will represent the camera viewing direction to this face
        mean_vertex = [
            mean([vert[0] for vert in face.vertices]),
            mean([vert[1] - max_x / 2 for vert in face.vertices]),
            mean([vert[2] - max_y / 2 for vert in face.vertices]),
        ]

        # angle based on center of mass, otherwise for high fovs, wrong faces would be drawn
        angle = math.degrees(
            np.arccos(
                np.dot(mean_vertex, list(face.normal))
                / (np.linalg.norm(mean_vertex) * np.linalg.norm(list(face.normal)))
            )
        )
        # print("mean view", [vert/np.linalg.norm(mean_vertex) for vert in mean_vertex], view_vector, angle)

        # angle is < 90 when face normal and camera viewing direction are the same -> face showing away from camera
        if angle < 90:
            continue
        # draw polygon upside down with precalculated mean texture color
        if not average_colors[face.tex_id] == (0, 0, 0, 0):
            draw.polygon(
                [
                    (
                        (pmax_x - size[x])
                        / max(pmax_x - pmin_x, pmax_y - pmin_y)
                        * max_resolution,
                        (pmax_y - size[y])
                        / max(pmax_x - pmin_x, pmax_y - pmin_y)
                        * max_resolution,
                    )
                    for size in face.vertices
                ],
                fill=average_colors[face.tex_id],
                outline=(0, 0, 0),
            )

    # if render mode == "all" the image isn't saved but assigned to an axes
    if not ax:
        return img
    else:
        ax.axis("off")
        ax.imshow(img)
