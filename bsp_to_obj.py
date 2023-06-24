import os

from colored_radar_image import get_polygons


def obj_from_bsp(bsp_path='beta/oddball_b1.bsp', pball_path='./pball'):
    (polys, colors) = \
        get_polygons(os.path.join(
            pball_path, 'maps', bsp_path), pball_path)

    obj_file = ''

    faces = []
    vertex_count = 0

    obj_file += "# OBJ file\n"
    for poly in polys:
        tmp_faces = []
        for v in poly.vertices:
            vertex_count += 1
            tmp_faces.append(vertex_count)
            line = f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n'
            obj_file += line

        faces.append(tmp_faces)
    for face in faces:
        line = 'f '
        line += ' '.join([str(x) for x in face])
        line += '\n'
        obj_file += line

    return obj_file
