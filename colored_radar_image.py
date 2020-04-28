import copy
import os
from typing import Optional

import numpy as np
from PIL import WalImageFile

from Q2BSP import *


@dataclass
class Polygon:
    vertices: List[List[int]]
    tex_id: int
    normal: point3f

    def __iter__(self):
        return iter(astuple(self))


def get_polygons(path: str, pball_path: str) -> Tuple[List[Polygon], List[Tuple[int]]]:
    """
    Converts information from Q2BSP object into List of Polygon objects
    Calculates mean color of all used textures and builds list of all unique colors
    :param path: full path to map
    :param pball_path: path to pball / game media directory, needed to get full texture path
    :return: list of Polygon objects, list of RGB colors
    """
    # instead of directly reading all information from file, the Q2BSP class is used for reading
    temp_map = Q2BSP(path)


    # get a list of unique texture names (which are stored without an extension -> multiple ones must be tested)
    texture_list = [x.get_texture_name() for x in temp_map.tex_infos]
    texture_list_cleaned = list(dict.fromkeys(texture_list))
    # iterate through texture list, look which one exists, load, rescale to 1×1 pixel = color is mean color
    average_colors = list()
    skip_faces = list()

    for texture in texture_list_cleaned:
        color = (0, 0, 0)
        # list of all files in stored subdirectory
        texture_options = os.listdir(pball_path+"/textures/"+"/".join(texture.lower().split("/")[:-1]))
        texture_path = ""
        # iterate through texture options until one name matches stored texture name
        for idx, tex_option in enumerate(texture_options):
            if texture.split("/")[-1].lower() == os.path.splitext(tex_option)[0]:
                texture_path = "/".join(texture.lower().split("/")[:-1]) + "/" + tex_option
                break

        # texture was not found in specified subdirectory
        if not texture_path:
            print("Missing texture: ", texture)
            average_colors.append((0, 0, 0))
            continue

        if os.path.splitext(texture_path)[1] in [".png", ".jpg", ".tga"]:
            img = Image.open(pball_path + "/textures/" + texture_path)
            img2 = img.resize((1, 1))
            img2 = img2.convert("RGBA")
            img2 = img2.load()
            color = img2[0, 0]

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

                img2 = img3.resize((1, 1))

                color = img2.getpixel((0, 0))
        else:
            print(f"Error: unsupported format {os.path.splitext(texture_path)[1]} in {texture_path}"
                  f"\nsupported formats are .png, .jpg, .tga, .wal")

        color_rgb = color[:3]
        if color_rgb == (0, 0, 0):
            print(texture)
        # print(texture)
        if True in [x in texture.lower() for x in ["origin", "clip", "skip", "hint", "trigger"]]:
            print(texture)
            color_rgb = (0,0,0,0)  # actually rgba
        average_colors.append(color_rgb)

    # instead of storing face color directly in the Polygon object, store an index so that you can easily change one
    # color for all faces using the same one
    tex_indices = [x.texture_info for x in temp_map.faces]
    tex_ids = [texture_list_cleaned.index(texture_list[tex_index]) for tex_index in tex_indices]

    # each face is a list of vertices stored as Tuples
    faces: List[List[Tuple]] = list()
    skip_surfaces = []
    for idx, face in enumerate(temp_map.faces):
        flags = temp_map.tex_infos[face.texture_info].flags
        if flags.hint or flags.nodraw or flags.sky or flags.skip:
            skip_surfaces.append(idx)
        current_face: List[Tuple] = list()
        for i in range(face.num_edges):
            face_edge = temp_map.face_edges[face.first_edge + i]
            if face_edge > 0:
                edge = temp_map.edge_list[face_edge]
            else:
                edge = temp_map.edge_list[abs(face_edge)][::-1]
            for vert in edge:
                if not temp_map.vertices[vert] in current_face:
                    current_face.append(temp_map.vertices[vert])
        faces.append(current_face)

    # get minimal of all x y and z values and move all vertices so they all have coordinate values >= 0
    min_x = min([a[0] for b in faces for a in b])
    min_y = min([a[1] for b in faces for a in b])
    min_z = min([a[2] for b in faces for a in b])

    polys_normalized = [[[vertex[0] - min_x,
                          vertex[1] - min_y,
                          vertex[2] - min_z] for vertex in edge] for edge in faces]

    # get normals out of the Q2BSP object, if face.plane_side != 0, flip it (invert signs of coordinates)
    normal_list = [x.normal for x in temp_map.planes]
    normals = list()
    for face in temp_map.faces:
        # print(temp_map.tex_infos[face.texture_info].flags)
        if not face.plane_side == 0:
            # -1*0.0 returns -0.0 which is prevented by this expression
            # TODO: Does -0.0 do any harm here?
            normal = [-1 * x if not x == 0.0 else x for x in normal_list[face.plane]]
        else:
            normal = list(normal_list[face.plane])
        normals.append(normal)

    # construct polygon list out of the faces, indices into unique textures aka colors (two different textures could
    # have the same mean color), normals
    polygons: List[Polygon] = list()
    for idx, poly in enumerate(polys_normalized):
        polygon = Polygon(poly, tex_ids[idx], point3f(*normals[idx]))
        polygons.append(polygon)

    print(skip_surfaces, "skip")
    for i in skip_surfaces[::-1]:
        polygons.pop(i)

    # for idx, poly in enumerate(polygons):
    #     print(average_colors[poly.tex_id])
    #     if average_colors[poly.tex_id] == (0,0,0,0):
    #         print("here")
    #         polygons.pop(len(polygons)-1-idx)

    return polygons, average_colors


def sort_by_axis(faces: List[Polygon], axis: int) -> List[Polygon]:
    """
    Sorts polygons by depth aka how far away from the camera they are
    depth is resembled by the axis that is not used for pixel position
    :param faces: list of Polygons
    :param axis: axis that defines the depth (one of [0,1,2])
    :return: sorted list of Polygons
    """
    faces = copy.deepcopy(faces)
    order = [mean(depth_coordinate) for depth_coordinate in
             [[vert[axis] for vert in face] for face in [face.vertices for face in faces]]]
    faces_sorted = [x for _, x in sorted(zip(order, faces), key=operator.itemgetter(0), reverse=False)]
    return faces_sorted


def get_rot_polys(polys: List[Polygon], x_angle: float, y_angle: float, z_angle: float) -> List[Polygon]:
    """
    Applies matrix rotations by z, y, x axis in this order on vertices and normals
    :param polys: list of Polygons
    :param x_angle: rotation angle in degrees
    :param y_angle: rotation angle in degrees
    :param z_angle: rotation angle in degrees
    :return: rotated Polygon list
    """
    faces = copy.deepcopy(polys)
    if not z_angle == 0:  # should speed things up because vertices would be left unchanged with angle == 0 anyway
        for idx0, face in enumerate(faces):
            # rotate each vertex
            for idx1, vertex in enumerate(face.vertices):
                old_x, old_y, old_z = faces[idx0].vertices[idx1]
                faces[idx0].vertices[idx1][0] = math.cos(math.radians(z_angle)) * old_x - math.sin(
                    math.radians(z_angle)) * old_y
                faces[idx0].vertices[idx1][1] = math.sin(math.radians(z_angle)) * old_x + math.cos(
                    math.radians(z_angle)) * old_y
            # rotate normals once per face
            old_normal_x, old_normal_y, old_normal_z = faces[idx0].normal
            faces[idx0].normal.x = math.cos(math.radians(z_angle)) * old_normal_x - math.sin(
                math.radians(z_angle)) * old_normal_y
            faces[idx0].normal.y = math.sin(math.radians(z_angle)) * old_normal_x + math.cos(
                math.radians(z_angle)) * old_normal_y

    if not y_angle == 0:
        for idx0, face in enumerate(faces):
            for idx1, vertex in enumerate(face.vertices):
                old_x, old_y, old_z = faces[idx0].vertices[idx1]
                faces[idx0].vertices[idx1][0] = math.cos(math.radians(y_angle)) * old_x + math.sin(
                    math.radians(y_angle)) * old_z
                faces[idx0].vertices[idx1][2] = -math.sin(math.radians(y_angle)) * old_x + math.cos(
                    math.radians(y_angle)) * old_z

            old_normal_x, old_normal_y, old_normal_z = faces[idx0].normal
            faces[idx0].normal.x = math.cos(math.radians(y_angle)) * old_normal_x + math.sin(
                math.radians(y_angle)) * old_normal_z
            faces[idx0].normal.z = -math.sin(math.radians(y_angle)) * old_normal_x + math.cos(
                math.radians(y_angle)) * old_normal_z

    if not x_angle == 0:
        for idx0, face in enumerate(faces):
            for idx1, vertex in enumerate(face.vertices):
                old_x, old_y, old_z = faces[idx0].vertices[idx1]
                faces[idx0].vertices[idx1][1] = math.cos(math.radians(x_angle)) * old_y - math.sin(
                    math.radians(x_angle)) * old_z
                faces[idx0].vertices[idx1][2] = math.sin(math.radians(x_angle)) * old_y + math.cos(
                    math.radians(x_angle)) * old_z
            old_normal_x, old_normal_y, old_normal_z = faces[idx0].normal
            faces[idx0].normal.y = math.cos(math.radians(x_angle)) * old_normal_y - math.sin(
                math.radians(x_angle)) * old_normal_z
            faces[idx0].normal.z = math.sin(math.radians(x_angle)) * old_normal_y + math.cos(
                math.radians(x_angle)) * old_normal_z

    # moves all polys so that all coordinate values >= 0
    min_x = min([a for b in [[vert[0] for vert in face.vertices] for face in faces] for a in b])
    min_y = min([a for b in [[vert[1] for vert in face.vertices] for face in faces] for a in b])
    min_z = min([a for b in [[vert[2] for vert in face.vertices] for face in faces] for a in b])

    for idx1, face in enumerate(faces):
        for idx2, vert in enumerate(face.vertices):
            faces[idx1].vertices[idx2][0] = vert[0] - min_x
            faces[idx1].vertices[idx2][1] = vert[1] - min_y
            faces[idx1].vertices[idx2][2] = vert[2] - min_z

    return faces


def create_poly_image(polys: List[Polygon], ax, average_colors, max_resolution: int = 2048) -> Optional[
    Image.Image]:
    """
    Draws radar image and assigns it to axes or returns it
    :param polys: faces of the bsp
    :param ax: axes to draw to
    :param opacity: opacity of individual faces
    :param x: coordinate that will be drawn as x value
    :param y: coordinate that will be drawn as y value
    :param title: only relevant when image is drawn on axes
    :param ids:
    :param average_colors:
    :return:
    """
    # y value will be the images x value and (max z value - z) will be images y value
    x = 1
    y = 2
    z = 3 - (x + y)
    # sorted descending because the bigger the x value the further away the polygon is from camera
    polys = sort_by_axis(polys, z)
    # round vertices so they are integers and match pixel positions

    max_x = round(max([vert[x] for vert in [a for b in [face.vertices for face in polys] for a in b]]))
    max_y = round(max([vert[y] for vert in [a for b in [face.vertices for face in polys] for a in b]]))

    for idx1, face in enumerate(polys):
        for idx2, vert in enumerate(face.vertices):
            polys[idx1].vertices[idx2][0] = round(polys[idx1].vertices[idx2][0] / max(max_x, max_y) * max_resolution)
            polys[idx1].vertices[idx2][1] = round(polys[idx1].vertices[idx2][1] / max(max_x, max_y) * max_resolution)
            polys[idx1].vertices[idx2][2] = round(polys[idx1].vertices[idx2][2] / max(max_x, max_y) * max_resolution)

    max_x = round(max([vert[x] for vert in [a for b in [face.vertices for face in polys] for a in b]]))
    max_y = round(max([vert[y] for vert in [a for b in [face.vertices for face in polys] for a in b]]))

    img = Image.new("RGBA",
                    (max_x,
                     max_y),
                    (255, 255, 255, 100))
    draw = ImageDraw.Draw(img, "RGBA")

    # the view vector is the direction the camera is looking
    view_vector = [0, 0, 0]
    view_vector[z] = -1  # dynamic in case x y z values get changed again
    for idx, face in enumerate(polys):
        angle = math.degrees(np.arccos(np.dot(view_vector, list(face.normal)) / (
                np.linalg.norm(view_vector) * np.linalg.norm(list(face.normal)))))
        # only render faces facing in camera direction
        if angle < 90:
            continue
        # draw polygon upside down with precalculated mean texture color
        if not average_colors[face.tex_id] == (0,0,0,0):
            draw.polygon([(vert[x], max_y - vert[y]) for vert in face.vertices], fill=average_colors[face.tex_id])

    # if render mode == "all" the image isn't saved but assigned to an axes
    if not ax:
        return img
    else:
        ax.axis("off")
        ax.imshow(img)