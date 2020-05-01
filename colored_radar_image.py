
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
    faces_sorted = [x for _, x in sorted(zip(order, faces), key=operator.itemgetter(0), reverse=True)]
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
                old_normal_x, old_normal_y, old_normal_z = faces[idx0].normal
                faces[idx0].vertices[idx1][0] = math.cos(math.radians(z_angle)) * old_x - math.sin(
                    math.radians(z_angle)) * old_y
                faces[idx0].vertices[idx1][1] = math.sin(math.radians(z_angle)) * old_x + math.cos(
                    math.radians(z_angle)) * old_y
            # rotate normals once per face
            faces[idx0].normal.x = math.cos(math.radians(z_angle)) * old_normal_x - math.sin(
                math.radians(z_angle)) * old_normal_y
            faces[idx0].normal.y = math.sin(math.radians(z_angle)) * old_normal_x + math.cos(
                math.radians(z_angle)) * old_normal_y

    if not y_angle == 0:
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

    if not x_angle == 0:
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

    # moves all polys so that all coordinate values >= 0
    min_x = min([a for b in [[vert[0] for vert in face.vertices] for face in faces] for a in b])
    min_y = min([a for b in [[vert[1] for vert in face.vertices] for face in faces] for a in b])
    min_z = min([a for b in [[vert[2] for vert in face.vertices] for face in faces] for a in b])

    for idx1, face in enumerate(faces):
        for idx2, vert in enumerate(face.vertices):
            faces[idx1].vertices[idx2][0] = vert[0] - min_x  # so nothing of the map is clipped off
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
    print("maxs before rescaling", max_x, max_y)

    # highest visible angle between camera / near plane normal and vertex
    fov = 85

    # scales all polys so that min values stay 0,0,0 amd max values <= max_resolution
    for idx1, face in enumerate(polys):
        for idx2, vert in enumerate(face.vertices):
            polys[idx1].vertices[idx2][0] = round(polys[idx1].vertices[idx2][0] / max(max_x, max_y) * max_resolution)
            polys[idx1].vertices[idx2][1] = round(polys[idx1].vertices[idx2][1] / max(max_x, max_y) * max_resolution)
            polys[idx1].vertices[idx2][2] = round(polys[idx1].vertices[idx2][2] / max(max_x, max_y) * max_resolution)

    # new max x and y values, one should be max_resolution, other one smaller or equal
    max_x = round(max([vert[x] for vert in [a for b in [face.vertices for face in polys] for a in b]]))
    max_y = round(max([vert[y] for vert in [a for b in [face.vertices for face in polys] for a in b]]))
    print("maxs after rescaling", max_x, max_y)

    # # image dimensions are set to these new maximum x and y values ... before perspective projection
    # img = Image.new("RGBA",
    #                 (max_resolution,
    #                  max_resolution),
    #                 (255, 255, 255, 100))
    # draw = ImageDraw.Draw(img, "RGBA")

    # the view vector is the direction the camera is looking ... in orthographic projection
    view_vector = [0, 0, 0]
    view_vector[z] = 1  # dynamic in case x y z values get changed again

    # calculates most extreme (highest absolute) value for all vector x and y angles
    all_verts = [a for b in [[vert for vert in face.vertices] for face in polys] for a in b]
    angles_x = [[np.arctan((vert[x] - max_x/2) / vert[z]), idex, x] for vert, idex in zip(all_verts, list(range(len(all_verts))))if vert[z] >= 1]
    angles_y = [[np.arctan((vert[y] - max_y/2) / vert[z]), idex, y] for vert, idex in zip(all_verts, list(range(len(all_verts))))if vert[z] >= 1]
    min_an_x = min(angles_x, key=operator.itemgetter(0))
    # min_an_x[0] = abs(min_an_x[0])
    max_an_x = max(angles_x, key=operator.itemgetter(0))
    min_an_y = min(angles_y, key=operator.itemgetter(0))
    # min_an_y[0] = abs(min_an_y[0])
    max_an_y = max(angles_y, key=operator.itemgetter(0))
    print(f"fov: {fov} - minx: {math.degrees(min_an_x[0])} - miny: {math.degrees(min_an_y[0])} - maxx: {math.degrees(max_an_x[0])} - maxy: {math.degrees(max_an_y[0])}")

    # determines shift required to display all projected vertices on image
    max_idex =max((max_an_x, max_an_y, min_an_x, min_an_y), key=lambda x:abs(x[0]))
    print("midex", max_idex, math.degrees(max_idex[0]))
    shift = all_verts[max_idex[1]][max_idex[2]] / np.tan(math.radians(fov)) - all_verts[max_idex[1]][z]
    shifts = [(vert[x] / np.tan(math.radians(fov)) - vert[z],vert[y] / np.tan(math.radians(fov)) - vert[z]) for vert in all_verts]
    shift = max([a for b in shifts for a in b])
    shift = shift if shift > 0 else 0
    print("shift", shift)
    print("test", math.degrees(np.arctan(all_verts[min_an_x[1]][min_an_x[2]]/all_verts[min_an_x[1]][z])),
          math.degrees(np.arctan(all_verts[min_an_x[1]][min_an_x[2]]/(all_verts[min_an_x[1]][z]+shift))),
          all_verts[min_an_x[1]])
    print("test2", math.degrees(np.arctan(all_verts[max_an_x[1]][max_an_x[2]]/all_verts[max_an_x[1]][z])),
          math.degrees(np.arctan(all_verts[max_an_x[1]][max_an_x[2]]/(all_verts[max_an_x[1]][z]+shift))),
          all_verts[max_an_x[1]])
    print("test3", math.degrees(np.arctan(all_verts[min_an_y[1]][min_an_y[2]]/all_verts[min_an_y[1]][z])),
          math.degrees(np.arctan(all_verts[min_an_y[1]][min_an_y[2]]/(all_verts[min_an_y[1]][z]+shift))),
          all_verts[min_an_y[1]])
    print("test4", math.degrees(np.arctan(all_verts[max_an_y[1]][max_an_y[2]]/all_verts[max_an_y[1]][z])),
          math.degrees(np.arctan(all_verts[max_an_y[1]][max_an_y[2]]/(all_verts[max_an_y[1]][z]+shift))),
          all_verts[max_an_y[1]])

    # shifts map far enough backward or forward to fill whole image ... doesnt work well yet
    # applies projection on x and y values
    for idx1, face in enumerate(polys):
        for idx2, vert in enumerate(face.vertices):
            polys[idx1].vertices[idx2][z] += shift
            # polys[idx1].vertices[idx2][z] -= 3200
            # polys[idx1].vertices[idx2][y] += 920
            # polys[idx1].vertices[idx2][x] += 100
            if polys[idx1].vertices[idx2][z] >= 1:
                polys[idx1].vertices[idx2][x] = (vert[x]-max_x/2)/vert[z]*max(max_x, max_y) + max_x/2
                polys[idx1].vertices[idx2][y] = (vert[y]-max_y/2)/vert[z]*max(max_x, max_y) + max_y/2
            else:
                polys[idx1].vertices[idx2][x] = None
                polys[idx1].vertices[idx2][y] = None

    pmin_x = round(min([vert[x] for vert in [a for b in [face.vertices for face in polys] for a in b]]))
    pmin_y = round(min([vert[y] for vert in [a for b in [face.vertices for face in polys] for a in b]]))
    pmin_z = round(min([vert[z] for vert in [a for b in [face.vertices for face in polys] for a in b]]))
    pmax_x = round(max([vert[x] for vert in [a for b in [face.vertices for face in polys] for a in b]]))
    pmax_y = round(max([vert[y] for vert in [a for b in [face.vertices for face in polys] for a in b]]))
    pmax_z = round(max([vert[z] for vert in [a for b in [face.vertices for face in polys] for a in b]]))
    print("mins projected", pmin_x, pmin_y, pmin_z)
    print("maxs projected", pmax_x, pmax_y, pmax_z)

    # for idx1, face in enumerate(polys):
    #     for idx2, vert in enumerate(face.vertices):
    #         polys[idx1].vertices[idx2][x] = polys[idx1].vertices[idx2][x] / max(pmax_x-pmin_x, pmax_y-pmin_y) * max_resolution
    #         polys[idx1].vertices[idx2][y] = polys[idx1].vertices[idx2][y] / max(pmax_x-pmin_x, pmax_y-pmin_y) * max_resolution
    #         polys[idx1].vertices[idx2][z] = polys[idx1].vertices[idx2][z] -=

    # image dimensions are set to these new maximum x and y values ... before perspective projection
    img = Image.new("RGBA",
                    (int((pmax_x-pmin_x)/max((pmax_x-pmin_x, pmax_y-pmin_y))*max_resolution),
                     int((pmax_y-pmin_y)/max((pmax_x-pmin_x, pmax_y-pmin_y))*max_resolution)),
                    (255, 255, 255, 100))
    draw = ImageDraw.Draw(img, "RGBA")


    for idx, face in enumerate(polys):
        # might be necessary at some point where the near clipping plane is inside of the map
        if any([not vert[x] or not vert[y] for vert in face.vertices]):
            print("skipped")
            continue
        # calculates center of mass for face, will represent the camera viewing direction to this face
        mean_vertex = [mean([vert[0] for vert in face.vertices]), mean([vert[1]-max_x/2 for vert in face.vertices]), mean([vert[2]-max_y/2 for vert in face.vertices])]

        # angle based on center of mass, otherwise for high fovs, wrong faces would be drawn
        angle = math.degrees(np.arccos(np.dot(mean_vertex, list(face.normal)) / (
                np.linalg.norm(mean_vertex) * np.linalg.norm(list(face.normal)))))
        # print("mean view", [vert/np.linalg.norm(mean_vertex) for vert in mean_vertex], view_vector, angle)

        # angle is < 90 when face normal and camera viewing direction are the same -> face showing away from camera
        if angle < 90:
            continue
        # draw polygon upside down with precalculated mean texture color
        if not average_colors[face.tex_id] == (0,0,0,0):
            draw.polygon([((pmax_x - size[x])/max(pmax_x-pmin_x, pmax_y-pmin_y)*max_resolution, (pmax_y - size[y])/max(pmax_x-pmin_x, pmax_y-pmin_y)*max_resolution) for size in face.vertices], fill=average_colors[face.tex_id], outline=(0,0,0))

    # if render mode == "all" the image isn't saved but assigned to an axes
    if not ax:
        return img
    else:
        ax.axis("off")
        ax.imshow(img)