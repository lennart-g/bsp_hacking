import os

from colored_radar_image import get_polygons


def obj_from_bsp(bsp_path='beta/oddball_b1.bsp', pball_path='./pball'):
    (polys, colors) = \
        get_polygons(os.path.join(
            pball_path, 'maps', bsp_path), pball_path)

    obj_file = ''

    faces = []
    # vertex_count = 0

    vertex_lines = []
    face_lines = []
    color_lines = []

    obj_file += "# OBJ file\n"

    flattened_verts = [v for poly in polys for v in poly.vertices]
    flattened_verts = tuple(map(tuple, flattened_verts))
    unique_verts = tuple(set(flattened_verts))
    # tuple(unique_verts).index(tuple(flattened_verts[5]))
    # save each vertex making up a polygon
    for vert in unique_verts:
        v = [x / 1000 for x in vert]
        line = f'v {v[0]:.4f} {v[2]:.4f} {v[1]:.4f}\n'
        vertex_lines.append(line)

    for poly in polys:
        tmp_faces = []
        for v in poly.vertices:
            # vertex_count += 1
            tmp_faces.append(unique_verts.index(tuple(v)) + 1)
            # v = [x/1000 for x in v]
            # line = f'v {v[0]:.4f} {v[2]:.4f} {v[1]:.4f}\n'
            # vertex_lines.append(line)

        faces.append({'verts': tmp_faces, 'tex_id': poly.tex_id})
    # save each face as indices to the vertices
    for face in faces:
        verts = face['verts']
        for i in range(len(verts) - 2):
            line = 'f '
            line += f'{verts[0]} {verts[i+1]} {verts[i+2]}'
            line += '\n'
            face_lines.append(line)

            line = '# '
            line += ' '.join([str(x) for x in colors[face['tex_id']]])
            line += '\n'
            color_lines.append(line)

    obj_file += ''.join(vertex_lines)
    obj_file += ''.join(face_lines)
    obj_file += ''.join(color_lines)

    print(f'vertex lines: {len(vertex_lines)}')
    print(f'face lines: {len(face_lines)}')
    print(f'color lines: {len(color_lines)}')
    return obj_file

out = obj_from_bsp()

with open('/home/lennart/Downloads/test6.obj', 'w') as f:
    f.write(out)
