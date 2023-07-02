from typing import List, Tuple

from Q2BSP import Q2BSP, point3f
import numpy as np

def get_normals(temp_map: Q2BSP) -> List[List[float]]:
    """
    get normals out of the Q2BSP object
    if face.plane_side != 0, flip it (invert signs of coordinates)
    :param temp_map: q Q2BSP object
    :return:List of normals as list of three floats
    """
    normal_list: List[point3f] = [x.normal for x in temp_map.planes]
    normals = []
    for face in temp_map.faces:
        # print(temp_map.tex_infos[face.texture_info].flags)
        if not face.plane_side == 0:
            # -1*0.0 returns -0.0 which is prevented by this expression
            # TODO: Does -0.0 do any harm here?
            normal: List[float, float, float] = [
                -1 * x if not x == 0.0 else x for x in normal_list[face.plane]
            ]
        else:
            normal: List[float, float, float] = list(normal_list[face.plane])
        normals.append(normal)
    return normals


def get_faces_from_vertices(temp_map: Q2BSP):
    """
    BSP files define vertices that make up edges which make up face edges which make up faces.
    This function redefines faces as a list of vertices.
    :param temp_map: a Q2BSP object
    :return: a list of faces as a list of vertices (three floats) and a list of surfaces not
    rendered in-game (hint, nodraw, skip) as well as sky surfaces as they would block vision by
    sealing off the map.
    """
    # faces: List[List[Tuple[float, float, float]]] = []
    skip_surfaces = []
    num_triangles = sum([x.num_edges-2 for x in temp_map.faces])
    faces = np.zeros((num_triangles, 3, 3))
    triangle_counter = 0

    for idx, face in enumerate(temp_map.faces):
        flags = temp_map.tex_infos[face.texture_info].flags
        if flags.hint or flags.nodraw or flags.sky or flags.skip:
            skip_surfaces.append(idx)
        current_face: List[Tuple] = []
        for i in range(face.num_edges):
            face_edge = temp_map.face_edges[face.first_edge + i]
            if face_edge > 0:
                edge = temp_map.edge_list[face_edge]
            else:
                edge = temp_map.edge_list[abs(face_edge)][::-1]
            for vert in edge:
                if not temp_map.vertices[vert] in current_face:
                    current_face.append(temp_map.vertices[vert])
        for i in range(len(current_face) - 2):
            faces[i] = np.asarray([current_face[0], current_face[1], current_face[i+2]])
            triangle_counter += 1
        # faces.append(current_face)
    return faces, skip_surfaces


def get_unique_texture_names(temp_map: Q2BSP) -> Tuple[List[str], List[str]]:
    """
    Get a list of all texture names and a list of unique texture names of a Q2BSP object
    :param temp_map: Q2BSP object
    :return: two lists of strings
    """
    texture_list = [x.get_texture_name() for x in temp_map.tex_infos]
    texture_list_cleaned = list(dict.fromkeys(texture_list))
    return texture_list, texture_list_cleaned
