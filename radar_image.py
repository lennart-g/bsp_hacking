import wireframe_radar_image as wf
import heatmap_radar_image as hm
import colored_radar_image as cl

def create_image(path_to_pball: str, map_path:str, image_type: str, mode: int, image_path: str, dpi: int= 1700, x_an: float = None, z_an: float = None) -> None:
    """
    root function for creating radar images
    :param path_to_pball: path to pball directory / root directory for game media
    :param map_path: local path to map file including .bsp extension
    :param image_type: says if front side top or rotated view is to be rendered
    :param solid: solid or wireframe mode
    :param image_path: path to store image to
    :param dpi: image resolution, only relevant for image_type "all"
    :return: None, images created here are stored to drive
    """
    # values are x,y values defining which coordinates PIL uses for drawing and in which order
    image_types_axes = {"front": [1, 2],
                   "side": [0, 1],
                   "top": [0, 2],
                   "rotated": [0, 2],
                   "all": []}
    # checks if image_type is valid
    if image_type not in image_types_axes.keys():
        print("Error: No such image type", image_type, "\n pick one of ", *image_types_axes.keys())
        return
    if mode == 0:  # true color solid
        polys, mean_colors = cl.get_polygons(path_to_pball + map_path, path_to_pball)
        # get angles with maximum information aka faces are least stacked
        # approach: for z rotation, get diagonal on xy plane and take its angle, for x rotation accordingly
        if not x_an and not z_an:
            max_x = max([a for b in [x.vertices for x in polys] for a in b], key=lambda x: x[0])
            max_y = max([a for b in [x.vertices for x in polys] for a in b], key=lambda x: x[1])
            max_z = max([a for b in [x.vertices for x in polys] for a in b], key=lambda x: x[2])
            maxs = [max_x[0], max_y[1], max_z[2]]
            z_an = cl.math.degrees(cl.arctan(maxs[1] / maxs[0]))
            x_an = 90 - cl.math.degrees(cl.arctan(maxs[1] / maxs[2]))
        poly_rot = cl.get_rot_polys(polys, x_an, 0, z_an)  # x rot, roll/y rot, z rot
        if image_type == "all":
            return
            # fig_solid, ((s_ax1, s_ax2), (s_ax3, s_ax4)) = cl.plt.subplots(nrows=2, ncols=2)
            # fig_solid.suptitle(map_path.replace(".bsp", "").split("/")[len(map_path.split("/")) - 1] + " solid")
            #
            # cl.create_poly_image(polys, s_ax1, opacity=50, x=1, y=2, title="front view")
            # cl.create_poly_image(polys, s_ax2, opacity=50, title="top view")
            # cl.create_poly_image(polys, s_ax3, opacity=50, x=0, y=2, title="side view")
            # fig_solid.show()
            # fig_solid.savefig(image_path, dpi=dpi)
            # return
            # create_poly_image(poly_rot, s_ax4, x=0, y=2, title="rotated view \n (orthographic)",
            #                   average_colors=mean_colors, opacity=255)
            #
            # fig_solid.show()
            # fig_solid.savefig(image_path, dpi=dpi)
            # # print(texture_ids)
        elif image_type == "rotated":
            cl.create_poly_image(poly_rot, None, opacity=255, x=0, y=2, title="rotated view \n (orthographic)",
                              average_colors=mean_colors).save(image_path)
        else:
            return
            # cl.create_poly_image(polys, None, opacity=50, x=image_types_axes[image_type][0],
            #                   y=image_types_axes[image_type][1]).save(image_path)

    elif mode==1:  # heatmap solid
        polys, texture_ids, mean_colors = hm.get_polys(path_to_pball+map_path, path_to_pball)
        poly_rot = hm.get_rot_polys(polys, 10, 0, 70)
        polys = hm.sort_by_z(polys)
        if image_type == "all":
            fig_solid, ((s_ax1, s_ax2), (s_ax3, s_ax4)) = hm.plt.subplots(nrows=2, ncols=2)
            fig_solid.suptitle(map_path.replace(".bsp", "").split("/")[len(map_path.split("/")) - 1] + " solid")

            hm.create_poly_image(polys, s_ax1, opacity=50, x=1, y=2, title="front view")
            hm.create_poly_image(polys, s_ax2, opacity=50, title="top view")
            hm.create_poly_image(polys, s_ax3, opacity=50, x=0, y=2, title="side view")
            hm.create_poly_image(poly_rot, s_ax4, x=0, y=2, title="rotated view \n (orthographic)", ids=texture_ids, average_colors=mean_colors)

            fig_solid.show()
            fig_solid.savefig(image_path, dpi=dpi)
            print(texture_ids)
        elif image_type == "rotated":
            hm.create_poly_image(poly_rot, None, x=0, y=2, title="rotated view \n (orthographic)", ids=texture_ids, average_colors=mean_colors).save(image_path)
        else:
            hm.create_poly_image(polys, None, opacity=50, x=image_types_axes[image_type][0], y=image_types_axes[image_type][1]).save(image_path)
    elif mode == 2:  # heatmap wireframe
        lines = wf.get_line_coords(path_to_pball+map_path)
        lines_rot=wf.get_rot_polys(lines, 10, 0, 70)
        if image_type == "all":
            fig_wireframe, ((s_ax1, s_ax2), (s_ax3, s_ax4)) = wf.plt.subplots(nrows=2, ncols=2)
            fig_wireframe.suptitle(map_path.replace(".bsp", "").split("/")[len(map_path.split("/")) - 1] + " wireframe")

            wf.create_line_image(lines, s_ax1, x=1, y=2, title="front view")
            wf.create_line_image(lines, s_ax2, title="top view")
            wf.create_line_image(lines, s_ax3, x=0, y=2, title="side view")
            wf.create_line_image(lines_rot, s_ax4, x=0, y=2, title="rotated view \n (orthographic)")

            fig_wireframe.show()
            fig_wireframe.savefig(image_path, dpi=dpi)
        elif image_type == "rotated":
            wf.create_line_image(lines_rot, None, x=0, y=2, title="rotated view \n (orthographic)").save(image_path)
        else:
            wf.create_line_image(lines, None, x=image_types_axes[image_type][0], y=image_types_axes[image_type][1]).save(image_path)
