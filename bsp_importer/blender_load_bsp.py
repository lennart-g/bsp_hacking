try:
    # same directory import in released version
    from . import Q2BSP
except ImportError:
    # absolute import for development
    import Q2BSP
import os
import bpy


def blender_load_bsp(object_path, displayed_name):
    """ Create Q2BSP dataclass object """
    # A class containing (most) information stored in a .bsp file
    my_map = Q2BSP.Q2BSP(object_path)

    if not displayed_name:
        path = os.path.normpath(object_path)
        path.split(os.sep)

        object_name = "/".join(path.split(os.sep)[-2:])
        print(object_name)
    else:
        print(displayed_name)
        object_name = displayed_name

    """ Lots of code (copy and pasted) that creates a mesh and adds it to the scene collection/outlines """
    mesh = bpy.data.meshes.new(object_name)  # add the new mesh, * extracts string from list
    obj = bpy.data.objects.new(mesh.name, mesh)
    col = bpy.data.collections.get("Collection")
    col.objects.link(obj)
    bpy.context.view_layer.objects.active = obj

    edges = [my_map.edge_list[x] if x >= 0 else my_map.edge_list[-x][::-1] for x in my_map.face_edges]

    faces_verts = []
    for face in my_map.faces:
        face_verts = []
        face_verts.append(edges[face.first_edge][0])
        for offset in range(1, face.num_edges):
            face_verts.append(edges[face.first_edge + offset][0])
        faces_verts.append(face_verts)

    mesh.from_pydata(my_map.vertices, [], faces_verts)
    return {'FINISHED'}  # no idea, seems to be necessary for the UI


