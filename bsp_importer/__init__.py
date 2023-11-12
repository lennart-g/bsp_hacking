bl_info = {
    "name": "Experimental BSP Importer",
    "author": "Lennart G",
    "location": "File > Import > Quake 2 BSP (.bsp)",
    "version": (0, 2, 0),
    "blender": (2, 80, 0),
    "category": "Import-Export"
}

# To support reload properly, try to access a package var,
# if it's there, reload everything
if "bpy" in locals():
    import importlib
    try:
        # relative import in release
        importlib.reload(Q2BSP)
    except NameError:
        # absolute import in development
        import Q2BSP
        importlib.reload(Q2BSP)
    importlib.reload(blender_load_bsp)
    print("Reloaded multifiles")
else:
    from . import blender_load_bsp
    print("Imported multifiles")

"""
This part is required for the UI, to make the Addon appear under File > Import once it's
activated and to have additional input fields in the file picking menu
Code is taken from Templates > Python > Operator File Import in Text Editor
The code here calls blender_load_bsp
"""

# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ImportSomeData(Operator, ImportHelper):
    """Loads a Quake 2 BSP File"""
    bl_idname = "import_bsp.some_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import BSP"

    ## ImportHelper mixin class uses this
    # filename_ext = ".bsp"

    filter_glob: StringProperty(
        default="*.*",  # only shows bsp files in opening screen
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    displayed_name: StringProperty(name="Displayed name",
                                             description="What this model should be named in the outliner\ngood for default file names like tris.md2",
                                             default="",
                                             maxlen=1024)

    def execute(self, context):
        return blender_load_bsp.blender_load_bsp(self.filepath, self.displayed_name)


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportSomeData.bl_idname, text="WIP Quake 2 Level Import (.bsp)")


# called when addon is activated (adds script to File > Import
def register():
    bpy.utils.register_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


# called when addon is deactivated (removed script from menu)
def unregister():
    bpy.utils.unregister_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
