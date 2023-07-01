import math

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from plots.plot_poly_image import cl_create_poly_image, cl_get_rot_polys
import colored_radar_image as cl
import heatmap_radar_image as hm
import wireframe_radar_image as wf


def get_optimal_angle(polys):
    # get angles with maximum information aka faces are least stacked
    # approach: for z rotation, get diagonal on xy plane and take its angle, for x rotation accordingly
    # not working well yet, best for this would be a real 3d angle
    max_x = max([a for b in [x.vertices for x in polys] for a in b], key=lambda x: x[0])
    max_y = max([a for b in [x.vertices for x in polys] for a in b], key=lambda x: x[1])
    max_z = max([a for b in [x.vertices for x in polys] for a in b], key=lambda x: x[2])
    maxs = [max_x[0], max_y[1], max_z[2]]

    z_angle = -math.degrees(np.arctan(maxs[0] / maxs[1]))
    y_angle = -math.degrees(np.arctan(maxs[0] / maxs[2]))
    x_angle = 0.0

    return x_angle, y_angle, z_angle


def create_image(
    path_to_pball: str,
    map_path: str,
    image_type: str,
    mode: int,
    image_path: str,
    dpi: int = 1700,
    x_an: float = None,
    y_an: float = None,
    z_an: float = None,
    max_resolution: int = 2048,
    fov: int = 50,
) -> None:
    """
    root function for creating radar images
    :param mode: 0: colored solid, 1: heatmap solid, 2: heatmap wireframe
    :param path_to_pball: path to pball directory / root directory for game media
    :param map_path: local path to map file including .bsp extension
    :param image_type: says if front side top or rotated view is to be rendered
    :param image_path: path to store image to
    :param dpi: image resolution, only relevant for image_type "all"
    :param x_an: rotation angle in degrees
    :param y_an: rotation angle in degrees
    :param z_an: rotation angle in degrees
    :return: None, images created here are stored to drive
    """
    # values are x,y values defining which coordinates PIL uses for drawing and in which order
    image_types_axes = {
        "front": [1, 2],
        "side": [0, 1],
        "top": [0, 2],
        "rotated": [0, 2],
        "all": [],
    }
    # previous system caused mirroring, this one is based of front view (z vs x with depth=y)
    view_rotations = {
        "front": [0, 0, 0],
        "right": [0, 0, -90],
        "back": [0, 0, 180],
        "left": [0, 0, -270],
        "top": [0, -90, -90],
        "bottom": [0, -270, -90],
        "rotated": [x_an, y_an, z_an],
    }
    # checks if image_type is valid
    if (
        image_type not in image_types_axes.keys()
        and image_type not in view_rotations.keys()
    ):
        print(
            "Error: No such image type",
            image_type,
            "\n pick one of ",
            *image_types_axes.keys(),
        )
        return
    if mode == 0 or mode == 1:  # true color solid
        # load geometry and color information from bsp file
        polys, mean_colors = cl.get_polygons(path_to_pball + map_path, path_to_pball)
        if (image_type == "rotated" or image_type == "all") and (
            x_an is None or y_an is None or z_an is None
        ):
            view_rotations["rotated"] = get_optimal_angle(polys)
        if image_type == "all":
            # render images and assign to a matplotlib axes, then save whole plot
            fig_solid, ((s_ax1, s_ax2), (s_ax3, s_ax4)) = plt.subplots(nrows=2, ncols=2)
            fig_solid.suptitle(
                map_path.replace(".bsp", "").split("/")[len(map_path.split("/")) - 1]
                + f"\n({'orthographic' if mode==1 else 'perspective'} projection)"
            )

            poly_list = cl_get_rot_polys(
                polys, *view_rotations["front"]
            )  # x rot, roll/y rot, z rot
            cl_create_poly_image(
                poly_list, s_ax1, mean_colors, mode == 0, max_resolution, fov
            )
            poly_list = cl_get_rot_polys(
                polys, *view_rotations["top"]
            )  # x rot, roll/y rot, z rot
            cl_create_poly_image(
                poly_list, s_ax2, mean_colors, mode == 0, max_resolution, fov
            )
            poly_list = cl_get_rot_polys(
                polys, *view_rotations["right"]
            )  # x rot, roll/y rot, z rot
            cl_create_poly_image(
                poly_list, s_ax3, mean_colors, mode == 0, max_resolution, fov
            )
            poly_list = cl_get_rot_polys(
                polys, *view_rotations["rotated"]
            )  # x rot, roll/y rot, z rot
            cl_create_poly_image(
                poly_list, s_ax4, mean_colors, mode == 0, max_resolution, fov
            )
            s_ax1.set_title("front view")
            s_ax2.set_title("top view")
            s_ax3.set_title("side view")
            s_ax4.set_title(f"rotated view")
            fig_solid.show()
            fig_solid.savefig(image_path, dpi=dpi)
        else:
            # rotate polys and draw
            poly_rot = cl_get_rot_polys(polys, *view_rotations[image_type])

            img = cl_create_poly_image(
                poly_rot, None, mean_colors, mode == 0, max_resolution, fov
            )
            img.save(image_path)
    elif mode == 2:  # heatmap solid
        polys, texture_ids, mean_colors = hm.get_polys(
            path_to_pball + map_path, path_to_pball
        )
        poly_rot = hm.get_rot_polys(polys, 45, 0, 0)  # fixed value rotation
        polys = hm.sort_by_z(polys)
        if image_type == "all":
            fig_solid, ((s_ax1, s_ax2), (s_ax3, s_ax4)) = hm.plt.subplots(
                nrows=2, ncols=2
            )
            fig_solid.suptitle(
                map_path.replace(".bsp", "").split("/")[len(map_path.split("/")) - 1]
                + " solid"
            )

            # predefined opacity to also display underground ways (plus no proper depth testing here)
            hm.create_poly_image(polys, s_ax1, opacity=50, x=1, y=2, title="front view")
            hm.create_poly_image(polys, s_ax2, opacity=50, title="top view")
            hm.create_poly_image(polys, s_ax3, opacity=50, x=0, y=2, title="side view")

            # opacity is calculated based on distance to 'camera'
            hm.create_poly_image(
                poly_rot,
                s_ax4,
                x=0,
                y=2,
                title="rotated view \n (orthographic)",
                ids=texture_ids,
                average_colors=mean_colors,
            )

            fig_solid.show()
            fig_solid.savefig(image_path, dpi=dpi)
        # only difference here is that rotated polys are used
        # while for the rest just the coordinate positions are swapped
        elif image_type == "rotated":
            hm.create_poly_image(
                poly_rot,
                None,
                x=0,
                y=2,
                title="rotated view \n (orthographic)",
                ids=texture_ids,
                average_colors=mean_colors,
            ).save(image_path)
        else:
            hm.create_poly_image(
                polys,
                None,
                opacity=50,
                x=image_types_axes[image_type][0],
                y=image_types_axes[image_type][1],
            ).save(image_path)

    elif mode == 3:  # heatmap wireframe
        lines = wf.get_line_coords(path_to_pball + map_path)
        lines_rot = wf.get_rot_polys(lines, 10, 0, 70)
        if image_type == "all":
            fig_wireframe, ((s_ax1, s_ax2), (s_ax3, s_ax4)) = wf.plt.subplots(
                nrows=2, ncols=2
            )
            fig_wireframe.suptitle(
                map_path.replace(".bsp", "").split("/")[len(map_path.split("/")) - 1]
                + " wireframe"
            )

            wf.create_line_image(lines, s_ax1, x=1, y=2, title="front view")
            wf.create_line_image(lines, s_ax2, title="top view")
            wf.create_line_image(lines, s_ax3, x=0, y=2, title="side view")
            wf.create_line_image(
                lines_rot, s_ax4, x=0, y=2, title="rotated view \n (orthographic)"
            )

            fig_wireframe.show()
            fig_wireframe.savefig(image_path, dpi=dpi)
        elif image_type == "rotated":
            wf.create_line_image(
                lines_rot, None, x=0, y=2, title="rotated view \n (orthographic)"
            ).save(image_path)
        else:
            wf.create_line_image(
                lines,
                None,
                x=image_types_axes[image_type][0],
                y=image_types_axes[image_type][1],
            ).save(image_path)
