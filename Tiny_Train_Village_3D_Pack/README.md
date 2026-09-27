# Tiny Train Village — 3D model pack

Thirty editable, character-free objects based on the supplied object catalog.
Created and rendered in Blender 4.5.3 LTS.

## Start here

1. Open `Tiny_Train_Village.blend` in Blender 4.5 or newer.
2. Each numbered collection contains one catalog object and a named root empty.
3. Select a collection in the Outliner to inspect its parts. The collection names
   match the original catalog numbers. Collections are also marked as assets.
4. To use an individual model elsewhere, import its `.glb` file from `models/`.

The Blender file arranges the objects in a gallery. Individual GLB exports have
their root at the origin and their lowest geometry on the ground. Dimensions are
in meters. Blender uses Z up; the glTF exports use the standard Y-up convention.
Rail vehicles face negative X. The studio collection contains only presentation
lighting, a ground plane and a camera; it is excluded from the individual GLBs.

## What is included

- `Tiny_Train_Village.blend`: editable geometry, named parts, materials and studio.
- `models/`: 30 self-contained GLB files with materials.
- `Catalog_3D_Preview.png`: a contact sheet of renders of the actual meshes.
- `previews/`: one actual Blender render per object.
- `catalog_manifest.json`: names, dimensions, categories and mesh statistics.
- `validation_report.json`: export checks performed on this pack.
- `build_catalog.py`: procedural source for the models.
- `render_catalog.py`: script for rendering the exported Blender scene.
- `reference/Selected_Object_Catalog.png`: the exact supplied reference image.

## Objects

| # | Object | # | Object |
|---|---|---|---|
| 01 | Steam locomotive | 16 | Wood stove |
| 02 | Greenhouse carriage | 17 | Dining table |
| 03 | Kitchen carriage | 18 | Wooden chair |
| 04 | Workshop carriage | 19 | Workbench |
| 05 | Railway track | 20 | Tool rack |
| 06 | Station building | 21 | Cooking utensils |
| 07 | Stone bridge | 22 | Bowls and plates |
| 08 | Village cottage | 23 | Planter box |
| 09 | Wooden fence | 24 | Flower pot |
| 10 | Signboard | 25 | Vegetable crops |
| 11 | Lamp post | 26 | Pine tree |
| 12 | Station bench | 27 | Leafy tree |
| 13 | Station clock | 28 | Bushes and flowers |
| 14 | Wooden crate | 29 | Boulders |
| 15 | Barrel | 30 | River and waterfall |

## Intended level of detail

These are stylized starter meshes interpreted from one image. Hidden sides,
depth and construction are approximated. They preserve the catalog's subjects
and broad color palette, with simpler surfaces and geometry than the illustration.
The preview sheet shows the actual delivered geometry, not an AI-rendered promise.

The models have editable material colors and bevels in the Blender file. The GLB
exports contain evaluated geometry. There are no external texture dependencies.
Meshes are static and unrigged. Final game work may include combining parts,
reducing draw calls, adding collisions, UVs, baked textures, LODs or animations
according to the target engine. Architectural and botanical objects use multiple
intersecting meshes; this pack is not prepared as watertight 3D-printing geometry.

## Rebuild or customize

The existing Blender file is ready to open; rebuilding is optional. Save any
unrelated Blender work before running the generator: it resets the current scene.

From a terminal with Blender available:

```sh
blender --background --python build_catalog.py
blender --background --python render_catalog.py
```

Alternatively, open `build_catalog.py` in Blender's Scripting workspace and run
it. Outputs are written beside the script. Materials, dimensions and individual
object-building functions are grouped near the top and middle of the script.
The generator uses a fixed random seed so its output is reproducible.

To render only selected objects, set the `TINY_TRAIN_RENDER_ONLY` environment
variable to comma-separated catalog numbers, for example `1,2,3,4`.

