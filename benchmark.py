import os
import timeit
from radar_image import create_image


pball_path = os.path.abspath('./pball')


def render_solid_perspective():
    create_image(pball_path, "/maps/beta/oddball_b1.bsp", "all", 0, "mode0.png", max_resolution=1024)


time_perspective = timeit.timeit("render_solid_perspective()", globals=locals(), number=1)

print(f'solid_perspective {time_perspective}s')