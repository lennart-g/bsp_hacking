import struct
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
import math
from statistics import mean
import copy
import os
from PIL import Image
from PIL import WalImageFile


def sort_by_z(faces):
    order = [mean(b) for b in [[c[2] for c in b] for b in faces]]
    faces = [x for _, x in sorted(zip(order, faces))]
    return faces


def get_rot_polys(param_faces, x_angle, y_angle, z_angle):
    faces=copy.deepcopy(param_faces)
    if not y_angle == 0:
        for idx0, face in enumerate(faces):
            for idx1, vertex in enumerate(face):
                old_x, old_y, old_z=faces[idx0][idx1]
                faces[idx0][idx1][0]=math.cos(math.radians(y_angle))*old_x+math.sin(math.radians(y_angle))*old_z
                faces[idx0][idx1][2]=-math.sin(math.radians(y_angle))*old_x+math.cos(math.radians(y_angle))*old_z
    if not z_angle == 0:
        for idx0, face in enumerate(faces):
            for idx1, vertex in enumerate(face):
                old_x, old_y, old_z=faces[idx0][idx1]
                faces[idx0][idx1][0]=math.cos(math.radians(z_angle))*old_x-math.sin(math.radians(z_angle))*old_y
                faces[idx0][idx1][1]=math.sin(math.radians(z_angle))*old_x+math.cos(math.radians(z_angle))*old_y
    if not x_angle == 0:
        for idx0, face in enumerate(faces):
            for idx1, vertex in enumerate(face):
                old_x, old_y, old_z=faces[idx0][idx1]
                faces[idx0][idx1][1]=math.cos(math.radians(x_angle))*old_y-math.sin(math.radians(x_angle))*old_z
                faces[idx0][idx1][2]=math.sin(math.radians(x_angle))*old_y+math.cos(math.radians(x_angle))*old_z

    min_x = min([p for i in [[vertex[0] for vertex in edge] for edge in faces] for p in i])
    #print(min_x)
    #print(max([p for i in [[vertex[0] for vertex in edge] for edge in faces] for p in i]))
    min_y = min([p for i in [[vertex[1] for vertex in edge] for edge in faces] for p in i])
    min_z = min([p for i in [[vertex[2] for vertex in edge] for edge in faces] for p in i])

    return [[[round(vertex[0] - min_x), round(vertex[1] - min_y), round(vertex[2] - min_z)] for vertex in edge] for edge
            in faces]


def get_line_coords(path):
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
            vert_1 = int.from_bytes(bytes1[offset_edges + 4 * i + 0:offset_edges + 4 * i + 2], byteorder='little', signed=False)
            vert_2 = int.from_bytes(bytes1[offset_edges + 4 * i + 2:offset_edges + 4 * i + 4], byteorder='little', signed=False)
            edges.append([vertices[vert_1], vertices[vert_2]])
        min_x = min([p for i in [[vertex[0] for vertex in edge] for edge in edges] for p in i])
        print(min_x)
        print(max([p for i in [[vertex[0] for vertex in edge] for edge in edges] for p in i]))
        min_y = min([p for i in [[vertex[1] for vertex in edge] for edge in edges] for p in i])
        min_z = min([p for i in [[vertex[2] for vertex in edge] for edge in edges] for p in i])

        print(edges[:10])
        return [[[round(vertex[0]-min_x), round(vertex[1]-min_y), round(vertex[2]-min_z)] for vertex in edge] for edge in edges]


def create_line_image(edges, ax, x=0, y=1, title="", thickness=14):
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
    z=3-(x+y)
    print(max([p for i in [[vertex[0] for vertex in edge] for edge in edges] for p in i]))
    max_y = round(max([p for i in [[vertex[y] for vertex in edge] for edge in edges] for p in i]))
    img = Image.new("RGB",
                    (round(max([p for i in [[vertex[x] for vertex in edge] for edge in edges] for p in i])),
                     round(max([p for i in [[vertex[y] for vertex in edge] for edge in edges] for p in i]))),
                    "white")
    draw = ImageDraw.Draw(img)
    max_z = max([p for i in [[vertex[z] for vertex in edge] for edge in edges] for p in i])
    for edge in edges:
        mean_z = (edge[0][z]+edge[1][z])/2.0
        col = int(510 * mean_z / max_z)
        draw.line((edge[0][x], max_y-edge[0][y], edge[1][x], max_y-edge[1][y]), fill=(max(0,col-255),0,max(0,255-col)), width=thickness)
    if not ax:
        return img
    else:
        ax.axis("off")
        ax.imshow(img)
        ax.set_title(title)
