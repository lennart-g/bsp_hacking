import struct
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
from statistics import mean
import copy
import os
from PIL import WalImageFile
from numpy import arctan
import math
from typing import List, Tuple, Optional
from Q2BSP import *
from dataclasses import dataclass
import numpy as np
import operator


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
    for texture in texture_list_cleaned:
        color = (0, 0, 0)
        if os.path.isfile(pball_path + "/textures/" + texture + ".png"):
            img = Image.open((pball_path + "/textures/" + texture + ".png"))
            img2 = img.resize((1, 1))
            img2 = img2.convert("RGBA")
            img2 = img2.load()
            color = img2[0, 0]
            # color = img2.getpixel((0, 0))

        elif os.path.isfile(pball_path + "/textures/" + texture + ".jpg"):
            img = Image.open((pball_path + "/textures/" + texture + ".jpg"))
            img2 = img.resize((1, 1))

            img2 = img2.convert("RGBA")
            img2 = img2.load()
            color = img2[0, 0]

        elif os.path.isfile(pball_path + "/textures/" + texture + ".tga"):
            img = Image.open((pball_path + "/textures/" + texture + ".tga"))
            img2 = img.resize((1, 1))

            img2 = img2.convert("RGBA")
            img2 = img2.load()
            color = img2[0, 0]

        elif os.path.isfile(pball_path + "/textures/" + texture + ".wal"):
            with open("pb2e.pal", "r") as pal:
                conts = (pal.read().split("\n")[3:])
                conts = [b.split(" ") for b in conts]
                conts = [c for b in conts for c in b]
                conts.pop(len(conts) - 1)
                conts = list(map(int, conts))
                img3 = WalImageFile.open((pball_path + "/textures/" + texture + ".wal"))
                img3.putpalette(conts)
                img3 = img3.convert("RGBA")
                # print("mode",img3.mode)

                img2 = img3.resize((1, 1))

                color = img2.getpixel((0, 0))
        # print(f"texture: {texture} - color: {color} - type: {type(color)}")
        color_rgb = color[:3]
        if color_rgb == (0, 0, 0):
            print(texture)
        average_colors.append(color_rgb)

    # instead of storing face color directly in the Polygon object, store an index so that you can easily change one
    # color for all faces using the same one
    tex_indices = [x.texture_info for x in temp_map.faces]
    tex_ids = [texture_list_cleaned.index(texture_list[tex_index]) for tex_index in tex_indices]

    # each face is a list of vertices stored as Tuples
    faces: List[List[Tuple]] = list()
    for face in temp_map.faces:
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

    # TODO: rounding here and after rotating increases error
    # polys_normalized = [[[round(vertex[0] - min_x),
    #                       round(vertex[1] - min_y),
    #                       round(vertex[2] - min_z)] for vertex in edge] for edge in faces]
    polys_normalized = [[[vertex[0] - min_x,
                          vertex[1] - min_y,
                          vertex[2] - min_z] for vertex in edge] for edge in faces]

    # get normals out of the Q2BSP object, if face.plane_side != 0, flip it (invert signs of coordinates)
    normal_list = [x.normal for x in temp_map.planes]
    normals = list()
    for face in temp_map.faces:
        if not face.plane_side == 0:
            # -1*0.0 returns -0.0 which is prevented by this expression
            # TODO: Does -0.0 do any harm here?
            normal = [-1*x if not x == 0.0 else x for x in normal_list[face.plane]]
        else:
            normal = list(normal_list[face.plane])
        normals.append(normal)

    # construct polygon list out of the faces, indices into unique textures aka colors (two different textures could
    # have the same mean color), normals
    polygons: List[Polygon] = list()
    for idx, poly in enumerate(polys_normalized):
        polygon = Polygon(poly, tex_ids[idx], point3f(*normals[idx]))
        polygons.append(polygon)
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
    order = [mean(depth_coordinate) for depth_coordinate in [[vert[axis] for vert in face] for face in [face.vertices for face in faces]]]
    faces_sorted = [x for _, x in sorted(zip(order, faces), key=operator.itemgetter(0), reverse=True)]
    return faces_sorted


def get_rot_polys(polys: List[Polygon], x_angle: float, y_angle: float, z_angle: float) -> List[Polygon]:
    faces = copy.deepcopy(polys)
    # if not z_angle == 0:
    for idx0, face in enumerate(faces):
        for idx1, vertex in enumerate(face.vertices):
            old_x, old_y, old_z = faces[idx0].vertices[idx1]
            old_normal_x, old_normal_y, old_normal_z = faces[idx0].normal
            faces[idx0].vertices[idx1][0] = math.cos(math.radians(z_angle)) * old_x - math.sin(
                math.radians(z_angle)) * old_y
            faces[idx0].vertices[idx1][1] = math.sin(math.radians(z_angle)) * old_x + math.cos(
                math.radians(z_angle)) * old_y
            faces[idx0].normal.x = math.cos(math.radians(z_angle)) * old_normal_x - math.sin(
                math.radians(z_angle)) * old_normal_y
            faces[idx0].normal.y = math.sin(math.radians(z_angle)) * old_normal_x + math.cos(
                math.radians(z_angle)) * old_normal_y
    # if not x_angle == 0:
    for idx0, face in enumerate(faces):
        for idx1, vertex in enumerate(face.vertices):
            old_x, old_y, old_z = faces[idx0].vertices[idx1]
            old_normal_x, old_normal_y, old_normal_z = faces[idx0].normal
            faces[idx0].vertices[idx1][1] = math.cos(math.radians(x_angle)) * old_y - math.sin(
                math.radians(x_angle)) * old_z
            faces[idx0].vertices[idx1][2] = math.sin(math.radians(x_angle)) * old_y + math.cos(
                math.radians(x_angle)) * old_z
            faces[idx0].normal.y = math.cos(math.radians(x_angle)) * old_normal_y - math.sin(
                math.radians(x_angle)) * old_normal_z
            faces[idx0].normal.z = math.sin(math.radians(x_angle)) * old_normal_y + math.cos(
                math.radians(x_angle)) * old_normal_z
    # if not y_angle == 0:
    for idx0, face in enumerate(faces):
        for idx1, vertex in enumerate(face.vertices):
            old_x, old_y, old_z = faces[idx0].vertices[idx1]
            old_normal_x, old_normal_y, old_normal_z = faces[idx0].normal
            faces[idx0].vertices[idx1][0] = math.cos(math.radians(y_angle)) * old_x + math.sin(
                math.radians(y_angle)) * old_z
            faces[idx0].vertices[idx1][2] = -math.sin(math.radians(y_angle)) * old_x + math.cos(
                math.radians(y_angle)) * old_z
            faces[idx0].normal.x = math.cos(math.radians(y_angle)) * old_normal_x + math.sin(
                math.radians(y_angle)) * old_normal_z
            faces[idx0].normal.z = -math.sin(math.radians(y_angle)) * old_normal_x + math.cos(
                math.radians(y_angle)) * old_normal_z

    # print(faces)
    # print([[vert[0] for vert in face.vertices] for face in faces])
    min_x = min([a for b in [[vert[0] for vert in face.vertices] for face in faces] for a in b])
    min_y = min([a for b in [[vert[1] for vert in face.vertices] for face in faces] for a in b])
    min_z = min([a for b in [[vert[2] for vert in face.vertices] for face in faces] for a in b])
    # polys_normalized = [[[round(vertex[0] - min_x),
    #                       round(vertex[1] - min_y),
    #                       round(vertex[2] - min_z)] for vertex in face.vertices] for face in faces]
    # for idx1, face in enumerate(faces):
    #     for idx2, vert in enumerate(face.vertices):
    #         faces[idx1].vertices[idx2][0] = round(vert[0] - min_x)
    #         faces[idx1].vertices[idx2][1] = round(vert[1] - min_y)
    #         faces[idx1].vertices[idx2][2] = round(vert[2] - min_z)
    for idx1, face in enumerate(faces):
        for idx2, vert in enumerate(face.vertices):
            faces[idx1].vertices[idx2][0] = vert[0] - min_x
            faces[idx1].vertices[idx2][1] = vert[1] - min_y
            faces[idx1].vertices[idx2][2] = vert[2] - min_z
    # print([x.normal for x in faces])
    return faces


def get_line_coords(path: str) -> List[List[List[int]]]:
    with open(path, "rb") as f:  # bsps are binary files
        bytes1 = f.read()  # stores all bytes in bytes1 variable (named like that to not interfere with builtin names
        offset_verts = int.from_bytes(bytes1[24:28], byteorder='little', signed=False)
        length_verts = int.from_bytes(bytes1[28:32], byteorder='little', signed=False)
        offset_edges = int.from_bytes(bytes1[96:100], byteorder='little', signed=False)
        length_edges = int.from_bytes(bytes1[100:104], byteorder='little', signed=False)
        vertices = list()
        for i in range(int(length_verts / 12)):
            (vert_x,) = struct.unpack('<f', (bytes1[offset_verts + 12 * i + 0:offset_verts + 12 * i + 4]))
            (vert_y,) = struct.unpack('<f', (bytes1[offset_verts + 12 * i + 4:offset_verts + 12 * i + 8]))
            (vert_z,) = struct.unpack('<f', (bytes1[offset_verts + 12 * i + 8:offset_verts + 12 * i + 12]))
            vertices.append([vert_x, vert_y, vert_z])
        edges = list()
        for i in range(int(length_edges / 4)):  # texture information lump is 76 bytes large
            vert_1 = int.from_bytes(bytes1[offset_edges + 4 * i + 0:offset_edges + 4 * i + 2], byteorder='little',
                                    signed=False)
            vert_2 = int.from_bytes(bytes1[offset_edges + 4 * i + 2:offset_edges + 4 * i + 4], byteorder='little',
                                    signed=False)
            edges.append([vertices[vert_1], vertices[vert_2]])
        min_x = min([p for i in [[vertex[0] for vertex in edge] for edge in edges] for p in i])
        # print(min_x)
        # print(max([p for i in [[vertex[0] for vertex in edge] for edge in edges] for p in i]))
        min_y = min([p for i in [[vertex[1] for vertex in edge] for edge in edges] for p in i])
        min_z = min([p for i in [[vertex[2] for vertex in edge] for edge in edges] for p in i])

        return [[[round(vertex[0] - min_x), round(vertex[1] - min_y), round(vertex[2] - min_z)] for vertex in edge] for
                edge in edges]


def create_line_image(edges: List[List[List[int]]], ax: plt.axes, x: int = 0, y: int = 1, title: str = "",
                      thickness: int = 14) -> Optional[Image.Image]:
    """
    creates wireframe PIL image and assigns it to axes or returns it
    :param edges:
    :param ax:
    :param x:
    :param y:
    :param title:
    :param thickness:
    :return:
    """
    z = 3 - (x + y)
    # print(max([p for i in [[vertex[0] for vertex in edge] for edge in edges] for p in i]))
    max_y = round(max([p for i in [[vertex[y] for vertex in edge] for edge in edges] for p in i]))
    img = Image.new("RGB",
                    (round(max([p for i in [[vertex[x] for vertex in edge] for edge in edges] for p in i])),
                     round(max([p for i in [[vertex[y] for vertex in edge] for edge in edges] for p in i]))),
                    "black")
    draw = ImageDraw.Draw(img)
    max_z = max([p for i in [[vertex[z] for vertex in edge] for edge in edges] for p in i])
    for edge in edges:
        mean_z = (edge[0][z] + edge[1][z]) / 2.0
        col = int(510 * mean_z / max_z)
        draw.line((edge[0][x], max_y - edge[0][y], edge[1][x], max_y - edge[1][y]),
                  fill=(max(0, col - 255), 0, max(0, 255 - col)), width=thickness)
    if not ax:
        return img
    else:
        ax.axis("off")
        ax.imshow(img)
        ax.set_title(title)


def create_poly_image(polys: List[Polygon], ax, opacity=-1, x=0, y=1, title="", average_colors=None) -> Optional[
    Image.Image]:
    """
    Draws radar image and assigns it to axis or returns it
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
    z = 3 - (x + y)
    polys = sort_by_axis(polys, z)
    # round vertices so they are integers and match pixel positions
    for idx1, face in enumerate(polys):
        for idx2, vert in enumerate(face.vertices):
            polys[idx1].vertices[idx2][0] = round(polys[idx1].vertices[idx2][0])
            polys[idx1].vertices[idx2][1] = round(polys[idx1].vertices[idx2][1])
            polys[idx1].vertices[idx2][2] = round(polys[idx1].vertices[idx2][2])

    # extract normals, ids, polys from the Polygon list
    # TODO: modify code so it doesnt need following extraction
    normals = [x.normal for x in polys]
    ids = [x.tex_id for x in polys]
    polys = [x.vertices for x in polys]
    max_y = round(max([p for i in [[vertex[y] for vertex in edge] for edge in polys] for p in i]))
    img = Image.new("RGBA",
                    (round(max([p for i in [[vertex[x] for vertex in edge] for edge in polys] for p in i])),
                     round(max([p for i in [[vertex[y] for vertex in edge] for edge in polys] for p in i]))),
                    (255, 255, 255, 100))
    draw = ImageDraw.Draw(img, "RGBA")
    max_z = max([p for i in [[vertex[z] for vertex in edge] for edge in polys] for p in i])
    # num_polys = 2000
    # for i in range(num_polys):
    #     col_a, col_b, col_c = average_colors[ids[i]]
    #     colors = (col_a, col_b, col_c, opacity)
    #     draw.polygon([(vert[x], max_y - vert[y]) for vert in polys[i]], fill=colors, outline=(255, 255, 255, 10))
    view_vector = [0, 0, 0]
    view_vector[z] = -1
    for idx, face in enumerate(polys):
        angle = math.degrees(np.arccos(np.dot(view_vector, list(normals[idx])) / (
                    np.linalg.norm(view_vector) * np.linalg.norm(list(normals[idx])))))
        # print(angle)
        # if angle < 90:
        #     # print(angle)
        #     continue
        # if average_colors[ids[idx]] == (0,0,0):
        #     continue
        mean_z = mean([x[z] for x in face])
        # print("normal:", normals[idx])
        # print("angle to 0 0 -1:", angle)
        if opacity == -1:
            opacity = min(255, int(180 * (1 - mean_z / max_z)))
        col = int(510 * mean_z / max_z)
        colors = (max(0, col - 255), 0, max(0, 255 - col), opacity)
        if ids and average_colors:
            print("hi")
            col_a, col_b, col_c = average_colors[ids[idx]]
            print(average_colors[ids[idx]])
            colors = (col_a, col_b, col_c, opacity)
        draw.polygon([(vert[x], max_y - vert[y]) for vert in face], fill=colors, outline=(0, 0, 0))
    print(average_colors)
    # print(ids)
    if not ax:
        return img
    else:
        ax.axis("off")
        ax.imshow(img)
        ax.set_title(title)


def create_image(path_to_pball: str, map_path: str, image_type: str, solid: bool, image_path: str,
                 dpi: int = 1700, x_an: float = 0, z_an: float = 0) -> None:
    """
    root function for creating radar images
    :param path_to_pball: path to pball directory / root directory for game media
    :param map_path: local path to map file including .bsp extension
    :param image_type: says if front side top or rotated view is to be rendered
    :param solid: solid or wireframe mode
    :param image_path: path to store image to
    :param dpi: image resolution, only relevant for image_type "all"
    :return: None, images created here are stored to drive
    """
    # values are x,y values defining which coordinates PIL uses for drawing and in which order
    image_types_axes = {"front": [1, 2],
                        "side": [0, 2],
                        "top": [0, 1],
                        "rotated": [0, 2],
                        "all": []}
    # checks if image_type is valid
    if image_type not in image_types_axes.keys():
        print("Error: No such image type", image_type, "\n pick one of ", *image_types_axes.keys())
        return
    if solid:
        polys, mean_colors = get_polygons(path_to_pball + map_path, path_to_pball)
        # get angles with maximum information aka faces are least stacked
        # approach: for z rotation, get diagonal on xy plane and take its angle, for x rotation accordingly
        if not x_an and not z_an:
            max_x = max([a for b in [x.vertices for x in polys] for a in b], key=lambda x: x[0])
            max_y = max([a for b in [x.vertices for x in polys] for a in b], key=lambda x: x[1])
            max_z = max([a for b in [x.vertices for x in polys] for a in b], key=lambda x: x[2])
            maxs = [max_x[0], max_y[1], max_z[2]]
            z_angle = math.degrees(arctan(maxs[1] / maxs[0]))
            x_angle = 90 - math.degrees(arctan(maxs[1] / maxs[2]))
            poly_rot = get_rot_polys(polys, x_angle, 0, z_angle)  # x rot, roll/y rot, z rot
        else:
            poly_rot = get_rot_polys(polys, x_an, 0, z_an)  # x rot, roll/y rot, z rot
        if image_type == "all":
            fig_solid, ((s_ax1, s_ax2), (s_ax3, s_ax4)) = plt.subplots(nrows=2, ncols=2)
            fig_solid.suptitle(map_path.replace(".bsp", "").split("/")[len(map_path.split("/")) - 1] + " solid")

            create_poly_image(polys, s_ax1, opacity=50, x=1, y=2, title="front view")
            create_poly_image(polys, s_ax2, opacity=50, title="top view")
            create_poly_image(polys, s_ax3, opacity=50, x=0, y=2, title="side view")
            fig_solid.show()
            fig_solid.savefig(image_path, dpi=dpi)
            return
            create_poly_image(poly_rot, s_ax4, x=0, y=2, title="rotated view \n (orthographic)",
                              average_colors=mean_colors, opacity=255)

            fig_solid.show()
            fig_solid.savefig(image_path, dpi=dpi)
            # print(texture_ids)
        elif image_type == "rotated":
            create_poly_image(poly_rot, None, opacity=255, x=0, y=2, title="rotated view \n (orthographic)",
                              average_colors=mean_colors).save(image_path)
        else:
            create_poly_image(polys, None, opacity=50, x=image_types_axes[image_type][0],
                              y=image_types_axes[image_type][1]).save(image_path)
    else:
        lines = get_line_coords(path_to_pball + map_path)
        print(lines)
        lines_rot = get_rot_polys(lines, 10, 0, 70)
        if image_type == "all":
            fig_wireframe, ((s_ax1, s_ax2), (s_ax3, s_ax4)) = plt.subplots(nrows=2, ncols=2)
            fig_wireframe.suptitle(map_path.replace(".bsp", "").split("/")[len(map_path.split("/")) - 1] + " wireframe")

            create_line_image(lines, s_ax1, x=1, y=2, title="front view")
            create_line_image(lines, s_ax2, title="top view")
            create_line_image(lines, s_ax3, x=0, y=2, title="side view")
            create_line_image(lines_rot, s_ax4, x=0, y=2, title="rotated view \n (orthographic)")

            fig_wireframe.show()
            fig_wireframe.savefig(image_path, dpi=dpi)
        elif image_type == "rotated":
            create_line_image(lines_rot, None, x=0, y=2, title="rotated view \n (orthographic)").save(image_path)
        else:
            create_line_image(lines, None, x=image_types_axes[image_type][0], y=image_types_axes[image_type][1]).save(
                image_path)
