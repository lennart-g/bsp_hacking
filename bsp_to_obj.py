import os

import numpy as np
import logging
from colored_radar_image import get_polygons


def obj_from_bsp(
    bsp_path: str = "beta/oddball_b1.bsp", pball_path: str = "./pball"
) -> str:
    """
    converts a bsp file alongside with mean color per face to a .obj standard string
    First line is a comment describing the file
    Next lines are a variably sized block defining vertex positions
    Next lines are a variably sized block defining faces as 1-based indices to the vertices
    Next lines are a variably sized block of comments defining colors as 0-255 RGB values or RGBA
    for faces not
     rendered in-game. These lines are ignored by regular .obj parsers
    Last line is a comment defining the color index for each face
    :param bsp_path: path to bsp file relative to pball/maps
    :param pball_path: path to pball directory
    :return: .obj file as string
    """
    (polys, tex_ids, colors) = get_polygons(
        os.path.join(pball_path, "maps", bsp_path), pball_path
    )

    obj_file = ""

    faces = []

    vertex_lines = []
    face_lines = []
    color_lines = []

    obj_file += "# OBJ file\n"

    # tmp_flattened_verts = [v for poly in polys for v in poly.vertices]
    # flattened_verts = tuple(map(tuple, tmp_flattened_verts))
    # unique_verts = tuple(set(flattened_verts))

    polys = polys / 1000

    flattened_verts = polys.reshape(-1, 3)
    _, idx = np.unique(flattened_verts, axis=0, return_index=True)
    unique_verts, vertex_positions = np.unique(flattened_verts, axis=0, return_inverse=True)
    # unique_verts = flattened_verts[np.sort(idx)]

    logging.debug(f'Starting obj_from_bsp')

    # save each unique vertex
    for v in unique_verts:
        line = f"v {v[0]:.4f} {v[2]:.4f} {v[1]:.4f}\n"
        vertex_lines.append(line)

    logging.debug(f'Done vertex lines obj_from_bsp')

    # define each face as 1-based indices to the vertices
    # for poly in polys:
    #     tmp_faces = []
    #     for v in poly.vertices:
    #         tmp_faces.append(unique_verts.index(tuple(v)) + 1)
    #
    #     faces.append({"verts": tmp_faces, "tex_id": poly.tex_id})


    # for idx,poly in enumerate(polys):
    #     tmp_faces = []
    #     for vert in poly:
    #         index = np.where((unique_verts==vert).all(axis=1))[0][0] + 1
    #         tmp_faces.append(index)
    #     faces.append({"verts": tmp_faces, "tex_id": tex_ids[idx]})

    faces = [{'verts': vertex_positions[3 * i:3 * i + 3] + 1, 'tex_id': tex_ids[i]} for i in range(len(polys))]

    logging.debug(f'Done faces preparation obj_from_bsp')


    # break down each polygon into triangles by fan triangulation
    # save each triangle as 1-based indices to the vertices
    # define color indices as
    color_indices = []

    for face in faces:
        verts = face["verts"]
        line = "f "
        line += f"{verts[0]} {verts[1]} {verts[2]}"
        line += "\n"
        face_lines.append(line)
        color_indices.append(face["tex_id"])

    logging.debug(f'Done generating face lines obj_from_bsp')

    # save each unique color as 0-255 RGB values or RGBA for faces not rendered in-game
    for color in colors:
        line = "# "
        line += " ".join([str(x) for x in color])
        line += "\n"
        color_lines.append(line)

    logging.debug(f'Done generating color lines obj_from_bsp')

    # save all color indices in one commented line
    color_index_line = "# "
    color_index_line += " ".join([str(x) for x in color_indices])
    color_index_line += "\n"

    obj_file += "".join(vertex_lines)
    obj_file += "".join(face_lines)
    obj_file += "".join(color_lines)
    obj_file += color_index_line

    logging.debug(f"vertex lines: {len(vertex_lines)}")
    logging.debug(f"face lines: {len(face_lines)}")
    logging.debug(f"color lines: {len(color_indices)}")
    logging.debug(f"color indices: {len(color_indices)}")
    return obj_file


if __name__ == '__main__':
    # before: Time for obj_from_bsp: 11.885419607162476 seconds
    import sys
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    import time
    start_time = time.time()
    out = obj_from_bsp(bsp_path='bankrob.bsp', pball_path='/home/lennart/Downloads/pball')
    print(f'Time for obj_from_bsp: {time.time() - start_time} seconds')
    with open('output/bankrob_new.obj', 'w') as f:
        f.write(out)
