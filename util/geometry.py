from typing import List, Tuple


def normalize_faces(
    faces: List[List[Tuple[float, float, float]]]
) -> List[List[Tuple[float, float, float]]]:
    """
    move min XYZ to origin
    :param faces: list of faces defined by XYZ vertices
    :return: list of faces defined by shifted vertices
    """
    min_x = min([a[0] for b in faces for a in b])
    min_y = min([a[1] for b in faces for a in b])
    min_z = min([a[2] for b in faces for a in b])
    polys_normalized = [
        [(vertex[0] - min_x, vertex[1] - min_y, vertex[2] - min_z) for vertex in edge]
        for edge in faces
    ]
    return polys_normalized
