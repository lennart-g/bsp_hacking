# BSP-Hacking
Multiple Algorithms to change Quake 2 BSP files

1. Q2BSP class
2. Radar Image Generator

## Radar Image Generator
The original purpose of this project was automatically generating a top view shot of maps that gives all
the characteristic information an in-game screenshot would also provide (mostly surfaces colors and the
map layout). In addition it now also supports rendering orthographic images at any given camera angle.

The Radar Image Generator so far consists of four files: radar_image.py serves as the root file that will be called by
the user. Colored_radar_image.py, wireframe_radar_image.py and heatmap_radar_image.py contain the functions required 
to generate radar images. 
 
These three files will now be explained more in detail.
 
 ### colored_radar_image.py
 This file contains the most recent functionality.
 
 From a Q2BSP object it takes not only geometry information but also normal and texture information.
 The normal is used to determine if a face faces the camera or not. If it doesn't face the camera but
 still is rendered, it would block vision. The texture information is used by loading each texture and
 determining its mean intensity. The image module used for drawing polygons (PIL) does not support textures.
 After sorting all polygons by their depth / distance to camera, they are drawn:
 
 ![Image of colored 3D view](https://github.com/lennart-g/BSP-Hacking/blob/radar_image/imgs/pp1_3d.png)