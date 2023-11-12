from . import Q2BSP
import os
import bpy


def blender_load_bsp(md2_path, displayed_name):
    """
    This function uses the information from a md2 dataclass into a blender object.
    This will consist of an animated mesh and its material (which is not much more than the texture.
    For better understanding, steps are:
        - Create the MD2 object containing all information that's inside the loaded md2
        - Get the absolute path of the UV map / skin to load
        - Get necessary information about the mesh (vertices, tris, uv coordinates)
        - Create the scene structure and create the mesh for the first frame
        - Assign UV coordinates to each triangle
        - Create shape animation (Add keyframe to each vertex)
        - Assign skin to mesh
    """
    """ Create Q2BSP dataclass object """
    object_path = md2_path  # Kept for testing purposes
    # A dataclass containing all information stored in a .md2 file
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


