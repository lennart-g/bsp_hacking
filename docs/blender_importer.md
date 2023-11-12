# Blender BSP Importer
## [Releases](https://github.com/lennart-g/bsp_hacking/releases)

## Installation
Simply install the .zip file as an add-on, 
e.g. via Edit > Preferences > Add-ons > Install...

## Usage
The add-on will show up in File > Import > WIP Quake 2 Level Import (.bsp).

The created object will likely need to be scaled down by a factor of 0.1
or more.

## Development
Create a module like the following, e.g. in `bsp_importer/dev_register.py`.
Open it in the blender script editor. Adjust `package_path` to
the local path to this repository and run whenever changes were made to
local dependencies of the add-on.

```python
package_path = "/path/to/project"

import sys
if not package_path in sys.path:
    sys.path.append(package_path)

import importlib
import bsp_importer

# unregister add-on first so it no longer shows when subsequent code fails
try:
    bsp_importer.unregister()
except RuntimeError:
    pass

# force reload all custom modules to apply potential changes
importlib.reload(bsp_importer)

# will be called by the if __name__ == '__main__' in the released zip
bsp_importer.register()
```