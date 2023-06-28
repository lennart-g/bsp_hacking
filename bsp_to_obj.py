import os

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
    (polys, colors) = get_polygons(
        os.path.join(pball_path, "maps", bsp_path), pball_path
    )

    obj_file = ""

    faces = []

    vertex_lines = []
    face_lines = []
    color_lines = []

    obj_file += "# OBJ file\n"

    tmp_flattened_verts = [v for poly in polys for v in poly.vertices]
    flattened_verts = tuple(map(tuple, tmp_flattened_verts))
    unique_verts = tuple(set(flattened_verts))
    # save each unique vertex
    for vert in unique_verts:
        v = [x / 1000 for x in vert]
        line = f"v {v[0]:.4f} {v[2]:.4f} {v[1]:.4f}\n"
        vertex_lines.append(line)

    # define each face as 1-based indices to the vertices
    for poly in polys:
        tmp_faces = []
        for v in poly.vertices:
            tmp_faces.append(unique_verts.index(tuple(v)) + 1)

        faces.append({"verts": tmp_faces, "tex_id": poly.tex_id})

    # break down each polygon into triangles by fan triangulation
    # save each triangle as 1-based indices to the vertices
    # define color indices as
    color_indices = []

    for face in faces:
        verts = face["verts"]
        for i in range(len(verts) - 2):
            line = "f "
            line += f"{verts[0]} {verts[i+1]} {verts[i+2]}"
            line += "\n"
            face_lines.append(line)
            color_indices.append(face["tex_id"])

    # save each unique color as 0-255 RGB values or RGBA for faces not rendered in-game
    for color in colors:
        line = "# "
        line += " ".join([str(x) for x in color])
        line += "\n"
        color_lines.append(line)

    # save all color indices in one commented line
    color_index_line = "# "
    color_index_line += " ".join([str(x) for x in color_indices])
    color_index_line += "\n"

    obj_file += "".join(vertex_lines)
    obj_file += "".join(face_lines)
    obj_file += "".join(color_lines)
    obj_file += color_index_line

    print(f"vertex lines: {len(vertex_lines)}")
    print(f"face lines: {len(face_lines)}")
    print(f"color lines: {len(color_indices)}")
    print(f"color indices: {len(color_indices)}")
    return obj_file
