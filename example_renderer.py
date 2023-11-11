import os

from radar_image import create_image

from inspect import getsourcefile
from os.path import dirname, abspath
current_path = dirname(abspath(getsourcefile(lambda:0)))

# pball_path = os.path.abspath("./pball")
pball_path = os.path.join(current_path, 'pball')
create_image(
    pball_path,
    "/maps/beta/oddball_b1.bsp",
    "all",
    3,
    "mode3.png",
    max_resolution=1024,
    x_an=0.0,
    y_an=0.0,
    z_an=0.0,
)

# create_image(
#     pball_path,
#     "/maps/beta/oddball_b1.bsp",
#     "all",
#     2,
#     "mode2.png",
#     max_resolution=1024,
#     x_an=0.0,
#     y_an=0.0,
#     z_an=0.0,
# )
#
# create_image(
#     pball_path,
#     "/maps/beta/oddball_b1.bsp",
#     "all",
#     1,
#     "mode1.png",
#     max_resolution=1024,
#     x_an=0.0,
#     y_an=0.0,
#     z_an=0.0,
# )
#
# create_image(
#     pball_path,
#     "/maps/beta/oddball_b1.bsp",
#     "all",
#     0,
#     "mode0.png",
#     max_resolution=1024,
#     x_an=0.0,
#     y_an=0.0,
#     z_an=0.0,
# )
