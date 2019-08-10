# Hestalon's Filter Tool in Python (HEFTY)
HEFTY is a Python3 (>= 3.5) tool to generate loot filter for [Path of Exile](https://www.pathofexile.com).
The intention is to change only parts of the filter without changing affecting other values, which are defined in JSON files.
While it can be quite difficult sometimes of foreground and background colors are easy to see, this tool contains a small functionality for it.
Text and border colors are handled as foreground and checked against the background color, only when these colors are defined.
An warning will be shown if the contrast ratio is too low.

## Run

```text
# creates the default filter
./hefty.py
# print help
./hefty.py --help
```

## Configuration
The valid values of the configuration can be found on the [PoE-Wiki](https://pathofexile.gamepedia.com/Item_filter).

### Folder: configs
This folder contains the definition of the filter itself. All folders are different types of filter, while each containing file is a different strictness.
Currently the best approach is to create one filter and copy it and modify desired sections.
The top level object is the filter and all containing ones are *chapter*. Each *chapter* can contain multiple *section*, with a different name.
The *section* can be either an object or a list of objects. All objects in a section can contain configuration values for:
* show
* theme
* condition

### Folder: conditions:
This folder contains the definition for the filtering, the conditions to apply a rule.
Each file within a folder is going to be read and can contain any object in any order.
Every object name is also the identifier, which is used in the `configs` and for extending another condition.

The following values are valid:
* extends
* itemLevel
* dropLevel
* quality
* rarity
* class
* type
* prophecy
* sockets
* links
* socketColors
* height
* width
* mod
* enchanted
* enchantment
* stackSize
* gemLevel
* identified
* corrupted
* elder
* shaper
* fractured
* synthesised
* shaped
* tier

### Folder: themes
This folder contains just like the `conditions` the configuration used in the `configs`, but in this case the visuals.
Values set in these files are referencing the values in the `styles` folder.

Valid configuration values:
* extends
* border
* text
* background
* size
* sound
* dropSound
* icon
* beam

### Folder: styles
Styling and keeping the same color in the whole filter can be hard, so this file contains all definitions.

The file can contain the following objects:
* color
* size
* sound
* dropSound
* icon
* beam


## TODO
* Validation of input
* Chapter/Section generation maybe recursive
* missing items with special mods like merciless
