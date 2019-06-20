# Hestalon's Filter Tool in Python (HEFTY)
HEFTY is a Python3 (>= 3.5) tool to generate loot filter for [Path of Exile](https://www.pathofexile.com).
The intention is to change only parts of the filter without changing affecting other values, which are defined in JSON files.

## Run

```text
# creates the default theme
./hefty.py
# print help
./hefty.py --help
```

## Configuration
The valid values of the configuration can be found on the [PoE-Wiki](https://pathofexile.gamepedia.com/Item_filter).

### Folder: configs
This folder contains the definition for the filtering.
Each file is one *chapter* and contains a dedicated header in the resulting Filter later.
Each chapter must contain a *section*, which has a name and the definition. 

An simple example is the following: 
```json
{
  "Chapter name": {
    "priority": 900,
    "section": {
      "Section name": {
        "theme": "fallback"
      }
    }
  }
}
```

All configuration done on *chapter*-level affecting all containing elements on *section*-level, but a *section* is overriding the *chapter*.
The priority of the chapter configures the ordering in the filter.

Valid configuration in *chapter*:
* priority

The following configuration can be set in both level:
* theme (*mandatory*)
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

## Folder: styles/themes
Both folders are using the same configuration but the idea is to define e.g. the colors in the style folder, while the theme is using these configurations.

Valid style and theme configuration values:
* extends
* border
* text
* background
* size
* sound
* dropSound
* icon
* beam

An example for the theme example above could be defined like this:
````json
{
  "text-white": {
    "text": "255 255 255 255"
  },
  "background-pink": {
    "background": "255 0 255"
  },
  "fallback": {
    "extends": ["text-white", "background-pink"]    
  }
}
````

The *extends* value can be either a string or a list of strings, which inheriting all values of the other styles.
Ordering can be important, the last values can override the values before, while the highest priority still is on the style itself.
