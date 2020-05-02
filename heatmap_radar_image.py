import struct
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
import math
from statistics import mean
import copy
import os
from PIL import Image
from PIL import WalImageFile


def get_polys(path, pball_path):
    with open(path, "rb") as f:  # bsps are binary files
        bytes1 = f.read()  # stores all bytes in bytes1 variable (named like that to not interfere with builtin names
        # get offset (position of entity block begin) and length of entity block -> see bsp quake 2 format documentation
        offset_faces = int.from_bytes(bytes1[56:60], byteorder='little', signed=False)
        length_faces = int.from_bytes(bytes1[60:64], byteorder='little', signed=False)

        offset_verts = int.from_bytes(bytes1[24:28], byteorder='little', signed=False)
        length_verts = int.from_bytes(bytes1[28:32], byteorder='little', signed=False)
        vertices = list()
        for i in range(int(length_verts / 12)):
            (vert_x,) = struct.unpack('<f', (bytes1[offset_verts + 12 * i + 0:offset_verts + 12 * i + 4]))
            (vert_y,) = struct.unpack('<f', (bytes1[offset_verts + 12 * i + 4:offset_verts + 12 * i + 8]))
            (vert_z,) = struct.unpack('<f', (bytes1[offset_verts + 12 * i + 8:offset_verts + 12 * i + 12]))
            vertices.append([vert_x, vert_y, vert_z])
            # print(f"{vert_x} - {vert_y} - {vert_z}")

        offset_edges = int.from_bytes(bytes1[96:100], byteorder='little', signed=False)
        length_edges = int.from_bytes(bytes1[100:104], byteorder='little', signed=False)
        edges = list()
        for i in range(int(length_edges / 4)):  # texture information lump is 76 bytes large
            vert_1 = int.from_bytes(bytes1[offset_edges + 4 * i + 0:offset_edges + 4 * i + 2], byteorder='little', signed=False)
            vert_2 = int.from_bytes(bytes1[offset_edges + 4 * i + 2:offset_edges + 4 * i + 4], byteorder='little', signed=False)
            edges.append([vertices[vert_1], vertices[vert_2]])

        offset_face_edges = int.from_bytes(bytes1[104:108], byteorder='little', signed=False)
        length_face_edges = int.from_bytes(bytes1[108:112], byteorder='little', signed=False)
        face_edges = list()
        for i in range(int(length_face_edges / 4)):  # texture information lump is 76 bytes large
            edge_index = int.from_bytes(bytes1[offset_face_edges + 4 * i + 0:offset_face_edges + 4 * i + 4], byteorder='little', signed=True)
            if edge_index > 0:
                face_edges.append([edges[abs(edge_index)][0], edges[abs(edge_index)][1]])
            elif edge_index < 0:
                face_edges.append([edges[abs(edge_index)][1], edges[abs(edge_index)][0]])

        offset_textures = int.from_bytes(bytes1[48:52], byteorder='little', signed=False)
        length_textures = int.from_bytes(bytes1[52:56], byteorder='little', signed=False)
        texture_list = list()
        for i in range(int(length_textures/76)):
            tex = (bytes1[offset_textures+76*i+40:offset_textures+76*i+72])
            tex = [x for x in tex if x]
            tex_name = struct.pack("b" * len(tex), *tex).decode('ascii', "ignore")
            print(tex_name)
            texture_list.append(tex_name)

        faces = list()
        tex_ids = list()
        texture_list_cleaned=list(dict.fromkeys(texture_list))

        average_colors=list()
        for texture in texture_list_cleaned:
            color = (0, 0, 0)
            if os.path.isfile(pball_path+"/textures/"+texture+".png"):
                img = Image.open((pball_path+"/textures/"+texture+".png"))
                img2 = img.resize((1, 1))

                color = img2.getpixel((0, 0))

            elif os.path.isfile(pball_path+"/textures/"+texture+".jpg"):
                img = Image.open((pball_path+"/textures/"+texture+".jpg"))
                img.save("1.png")
                img2 = img.resize((1, 1))
                # break

                color = img2.getpixel((0, 0))
                # print(f"texture: {texture} - color: {color}")

            elif os.path.isfile(pball_path + "/textures/" + texture + ".tga"):
                img = Image.open((pball_path + "/textures/" + texture + ".tga"))
                img2 = img.resize((1, 1))

                color = img2.getpixel((0, 0))
                # print(f"texture: {texture} - color: {color}")

            elif os.path.isfile(pball_path+"/textures/"+texture+".wal"):
                with open("pb2e.pal", "r") as pal:
                    conts = (pal.read().split("\n")[3:])
                    conts = [b.split(" ") for b in conts]
                    conts = [c for b in conts for c in b]
                    conts.pop(len(conts)-1)
                    conts=list(map(int, conts))
                    img3 = WalImageFile.open((pball_path+"/textures/"+texture+".wal"))
                    img3.putpalette(conts)
                    img3=img3.convert("RGBA")
                    print(img3.mode)

                    img2 = img3.resize((1, 1))

                    color = img2.getpixel((0, 0))
            print(f"texture: {texture} - color: {color}")
            color_rgb = color[:3]
            average_colors.append(color_rgb)

        for i in range(int(length_faces / 20)):  # texture information lump is 76 bytes large
            # get sum of flags / transform flag bit field to uint32
            first_edge = (bytes1[offset_faces + 20 * i + 4:offset_faces + 20 * i + 8])
            (num_edges,) = struct.unpack('<H', (bytes1[offset_faces + 20 * i + 8:offset_faces + 20 * i + 10]))
            (tex_index,) = struct.unpack('<H', (bytes1[offset_faces + 20 * i + 10:offset_faces + 20 * i + 12]))
            print(tex_index)
            tex_ids.append(texture_list_cleaned.index(texture_list[tex_index]))
            print(tex_ids[len(tex_ids)-1])
            first_edge = int.from_bytes(first_edge, byteorder='little', signed=True)
            next_edges = list()
            for j in range(num_edges):
                if face_edges[first_edge+j][0] not in next_edges:
                    next_edges.append(face_edges[first_edge+j][0])

                if face_edges[first_edge + j][1] not in next_edges:
                    next_edges.append(face_edges[first_edge + j][1])
            faces.append(next_edges)

        print(texture_list_cleaned)
        print(tex_ids)
        print(average_colors)

        min_x = min([p for i in [[vertex[0] for vertex in edge] for edge in faces] for p in i])
        min_y = min([p for i in [[vertex[1] for vertex in edge] for edge in faces] for p in i])
        min_z = min([p for i in [[vertex[2] for vertex in edge] for edge in faces] for p in i])

        return [[[round(vertex[0]-min_x), round(vertex[1]-min_y), round(vertex[2]-min_z)] for vertex in edge] for edge in faces], tex_ids, average_colors


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


def create_poly_image(polys, ax, opacity=-1, x=0, y=1, title="", ids=None, average_colors=None):
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
    z = 3-(x+y)
    max_y = round(max([p for i in [[vertex[y] for vertex in edge] for edge in polys] for p in i]))
    img = Image.new("RGB",
                    (round(max([p for i in [[vertex[x] for vertex in edge] for edge in polys] for p in i])),
                     round(max([p for i in [[vertex[y] for vertex in edge] for edge in polys] for p in i]))),
                    "white")
    draw = ImageDraw.Draw(img, "RGBA")
    max_z = max([p for i in [[vertex[z] for vertex in edge] for edge in polys] for p in i])

    for idx, edge in enumerate(polys):
        mean_z = sum([x[z] for x in edge])/len(edge)
        if opacity == -1:
            opacity = min(255, int(180*(1-mean_z/max_z)))
        col = int(510 * mean_z / max_z)
        colors = (max(0, col-255), 0, max(0, 255-col), opacity)
        if ids and average_colors:
            col_a, col_b, col_c = average_colors[ids[idx]]
            print(average_colors[ids[idx]])
            colors = (col_a, col_b, col_c,opacity)
        draw.polygon([(vert[x], max_y-vert[y]) for vert in edge], fill=colors, outline=(255,255,255,10))
    if not ax:
        return img
    else:
        ax.axis("off")
        ax.imshow(img)
        ax.set_title(title)
