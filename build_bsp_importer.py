import os.path
import shutil

# files to include in the output zip file
files = [
    "Q2BSP.py",
    "bsp_importer/__init__.py",
    "bsp_importer/blender_load_bsp.py"
]

# intermediary location for the directory to be zipped
dest = "build/io_import_bsp"

if not os.path.exists(dest):
    os.makedirs(dest)

for file in files:
    shutil.copyfile(file, os.path.join(dest, os.path.basename(file)))

# create zip file
shutil.make_archive("blender-bsp-importer", 'zip', "build")
