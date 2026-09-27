# Tiny Train Village — Meadowvale

A playable, editable Godot 4.6 scene built with the existing Tiny Train Village GLB models. The supplied `train.png` guided the arrangement: a locomotive followed by greenhouse, kitchen and workshop carriages; a station behind the train; and a river, waterfall, stone bridge, cottages and trees in the background.

## Open and play

Import `project.godot` in Godot 4.6 or newer, then press **F5**. The main scene is `scenes/meadowvale.tscn`.

The project opens directly behind the gold capsule, ready to walk. Click inside the game window to focus it, then use WASD or the arrow keys. Press **Tab** for the village overview.

The game starts in fullscreen. **F11** toggles fullscreen and windowed mode (use **Fn + F11** if your Mac assigns F11 to a system shortcut). Godot's embedded Game view does not support fullscreen: in the Game view's top-right options menu, turn off **Embed Game on Next Play**, then stop and run the project again.

Use **Run Project (F5)**, not **Run Current Scene (F6)**: individual scenery scenes such as `landscape.tscn` do not contain the player. On Mac keyboards, you may need **Fn + F5**, or use the top-right **Run Project** button.

| Control | Action |
| --- | --- |
| WASD / arrow keys | Walk |
| Shift | Run |
| Space | Jump |
| Mouse | Look around while captured |
| Mouse wheel | Adjust following-camera distance |
| Tab / V / Enter | Switch between overview and exploration |
| Esc | Release the mouse |
| Left click | Capture the mouse again |
| R | Return to the starting position |
| F11 | Toggle fullscreen / windowed mode |
| F12 | Save a screenshot to Godot's user-data folder as `meadowvale.png` |

Walk around the train, reach the station platform using the steps at its right end, or follow the lane behind the station to the village and bridge. Jump to get onto the open carriages. The camera uses a spring arm to shorten its distance near solid objects.

## Edit the scene

All world geometry, model placements, lights, cameras, UI nodes and collision shapes are serialized in the `.tscn` files. Nothing generates or scatters the scene at runtime. The only gameplay script, `scripts/player.gd`, controls the capsule, camera switching, mouse capture and screenshot shortcut.

- `meadowvale.tscn`: complete scene, lighting, overview camera and interface.
- `railway.tscn`: track sections, four train vehicles, collisions and static steam puffs.
- `station.tscn`: station, platform, steps, furniture, storage and garden.
- `landscape.tscn`: river bridge, waterfall, village and placed landscaping.
- `terrain.tscn`: meadow, riverbed, lanes, hills and distant mountains.
- `player.tscn`: capsule body, collision shape and following camera.
- `grove.tscn`, `pine.tscn`, `leafy_tree.tscn`, `boulders.tscn`, `fence.tscn`, `cottage.tscn`: reusable scene pieces.

Open a component scene to edit it, or enable **Editable Children** on its instance in the main scene. All 30 original model files are included under `assets/models/`; the original Blender files and source asset pack are untouched.

The existing models use a simpler low-poly style than the painted reference. Buildings remain exterior models, the train is stationary, and there are no economy, carriage-purchase or NPC systems. Collision shapes are simplified for exploration; small plants are decorative.

## Validation

`verification.txt` records runtime checks performed in Godot 4.6. `screenshots/overview.png` and `screenshots/exploration.png` are actual Godot viewport captures.
