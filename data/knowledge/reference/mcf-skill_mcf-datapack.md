---
name: mcf-datapack
description: Create and modify Minecraft Java Edition data packs (version 26.1.2). Use when working with pack.mcmeta, data pack structure, loading order, overlays, or experimental features. Covers directory structure and metadata format.
license: MIT
compatibility: opencode
metadata:
  version: "1.0"
  game-version: "26.1.2"
  category: minecraft-datapack
---

# Minecraft Data Pack Structure

## Target Version
This skill targets Minecraft Java Edition **26.1.2** (data pack version `[101, 1]`). Excludes snapshot 26.2 features (e.g., `sulfur_cube_archetype`).

## When to Use
- Creating a new data pack
- Modifying `pack.mcmeta`
- Setting up data pack directory structure
- Configuring experimental features
- Using overlay directories for multi-version support
- Understanding data pack loading and priority

## Data Pack Root Structure

```
<datapack-name>/
├── pack.mcmeta          # REQUIRED: metadata
├── pack.png             # Optional: icon (PNG)
└── data/
    └── <namespace>/
        ├── function/           # .mcfunction files
        ├── structure/          # .nbt structure templates
        ├── advancement/        # JSON advancement definitions
        ├── banner_pattern/     # JSON banner pattern definitions
        ├── cat_variant/        # JSON cat variant definitions
        ├── chat_type/          # JSON chat type definitions
        ├── chicken_variant/    # JSON chicken variant definitions
        ├── cow_variant/        # JSON cow variant definitions
        ├── damage_type/        # JSON damage type definitions
        ├── dialog/             # JSON dialog definitions
        ├── dimension/          # JSON dimension definitions
        ├── dimension_type/     # JSON dimension type definitions
        ├── enchantment/        # JSON enchantment definitions
        ├── enchantment_provider/ # JSON enchantment provider defs
        ├── frog_variant/       # JSON frog variant definitions
        ├── instrument/         # JSON goat horn instrument defs
        ├── item_modifier/      # JSON item modifier definitions
        ├── jukebox_song/       # JSON jukebox song definitions
        ├── loot_table/         # JSON loot table definitions
        ├── painting_variant/   # JSON painting variant definitions
        ├── pig_variant/        # JSON pig variant definitions
        ├── predicate/          # JSON predicate definitions
        ├── recipe/             # JSON recipe definitions
        ├── tags/               # Tag definitions (function, block, item, etc.)
        ├── timeline/           # JSON timeline definitions
        ├── trade_set/          # JSON trade set definitions
        ├── trial_spawner/      # JSON trial spawner config
        ├── trim_material/      # JSON armor trim material
        ├── trim_pattern/       # JSON armor trim pattern
        ├── villager_trade/     # JSON villager trade definitions
        ├── wolf_sound_variant/ # JSON wolf sound variant
        ├── wolf_variant/       # JSON wolf variant definitions
        ├── world_clock/        # JSON world clock definitions
        ├── worldgen/           # World generation
        │   ├── biome/
        │   ├── configured_carver/
        │   ├── configured_feature/
        │   ├── density_function/
        │   ├── flat_level_generator_preset/
        │   ├── multi_noise_biome_source_parameter_list/
        │   ├── noise/
        │   ├── noise_settings/
        │   ├── placed_feature/
        │   ├── processor_list/
        │   ├── structure/
        │   ├── structure_set/
        │   ├── template_pool/
        │   └── world_preset/
        └── zombie_nautilus_variant/
```

### Note on Directory Names (v26.1.2)
All directories use **singular** forms:
- `function` (NOT `functions`)
- `loot_table` (NOT `loot_tables`)
- `predicate` (NOT `predicates`)
- `item_modifier` (NOT `item_modifiers`)
- `advancement` (NOT `advancements`)
- `recipe` (NOT `recipes`)
- Tag directories: `tags/block`, `tags/item`, `tags/entity_type`, `tags/function` etc.

## pack.mcmeta Format

### Modern Format (v26.1.2, preferred)
```json
{
  "pack": {
    "description": "Example Data Pack",
    "min_format": [101, 1],
    "max_format": [101, 1]
  }
}
```

Fields:
- **description** (required): Text component describing the pack
- **min_format** (required): `[major, minor]` - minimum compatible version. `[101, 1]` for 26.1.2
- **max_format** (required): `[major, minor]` - maximum compatible version. Single int = minor defaults to `0x7fffffff`
- **pack_format** (deprecated): Single integer, kept for compatibility
- **supported_formats** (deprecated): Integer range, kept for compatibility

### Features (Experimental Content)
```json
{
  "pack": {
    "description": "Experimental Pack",
    "min_format": [101, 1],
    "max_format": [101, 1]
  },
  "features": {
    "enabled": ["minecraft:update_1_21"]
  }
}
```
Note: Packs with `features` field must be added when creating a new world.

### Filter (Block Specific Content)
```json
{
  "pack": { ... },
  "filter": {
    "block": [
      { "namespace": "minecraft", "path": "recipes/.*" }
    ]
  }
}
```
Uses regex patterns to ignore matching files from lower-priority data packs.

### Overlays (Multi-Version Support)
```json
{
  "pack": { ... },
  "overlays": {
    "entries": [
      {
        "directory": "overlay_1",
        "min_format": [101, 0],
        "max_format": [101, 1]
      }
    ]
  }
}
```
Overlay directories contain their own `data/` and `assets/` subdirectories.

## Data Pack Loading & Priority

### Load Order
- Data packs load from **bottom to top** (higher priority overrides lower)
- Order configured in world creation screen or via `/datapack` commands
- Stored in `level.dat` → `DataPacks`

### Hot Reload
- `/reload` reloads: functions, advancements, recipes, loot tables, predicates, item modifiers
- `/reload` does NOT reload: worldgen, enchantments, armor trims, jukebox songs, dimension types
- Worldgen changes require re-entering the world

### Data Pack Commands
```
/datapack list                    # List loaded packs
/datapack enable <name>           # Enable a pack
/datapack disable <name>          # Disable a pack
/reload                           # Reload data packs
```

## Data Pack Version History (Key Milestones for v26.1.2)

Version 101.1 (26.1):
- World clocks and mob sound variant definitions
- Item component `dye`
- `crafting_dye` and `crafting_imbue` recipe types
- Removed `crafting_special_armordye`, `crafting_special_mapcloning`, `crafting_special_tippedarrow`
- Custom recipes can control input/output more flexibly
- Changed save format and basic data storage
- Piglin/villager inventories use `mob.inventory.*`, removed `villager.*`

Version 94.1 (1.21.11):
- Item components: `use_effect`, `minimum_attack_charge`, `damage_type`, `kinetic_weapon`, `piercing_weapon`, `swing_animation`, `attack_range`
- Support testing if item has a specific component

## Data Pack Architecture Patterns (from MCBookshelf)

### Modular Library Design
Organize data packs as reusable modules with clear API boundaries:
```
mypack/
├── pack.mcmeta
├── pack.png
└── data/
    └── mypack/
        ├── function/
        │   ├── load.mcfunction        # Init on world load
        │   ├── tick.mcfunction        # Per-tick logic
        │   ├── help.mcfunction        # Self-documentation
        │   ├── api/                   # PUBLIC API
        │   │   ├── module_a.mcfunction
        │   │   └── module_b.mcfunction
        │   └── internal/              # PRIVATE implementation
        │       ├── _core.mcfunction   # Underscore = private
        │       └── _helpers.mcfunction
        ├── function/tags/
        │   ├── load.json             # #minecraft:load entry
        │   └── tick.json             # #minecraft:tick entry
        ├── item_modifier/
        ├── loot_table/
        ├── predicate/
        └── tags/
```

### Storage Namespace Convention
Use consistent storage namespaces for data flow:
```
bs:in     - Function inputs (write before calling)
bs:out    - Function outputs (read after calling)
bs:const  - Pre-computed constants (write once in #load)
bs:ctx    - Temporary context for macro calls
bs.data   - Module persistent data
```

### Scoreboard Convention
```
bs.in     - Input scores (shifted for fixed-point)
bs.out    - Output/return values from functions
bs.lambda - Callback context scores (temporary)
bs.data   - Persistent runtime data
```

### Function Naming Conventions
```
mypack:api/module_name     - Public API (callers depend on this)
mypack:internal/_helper    - Private implementation (may change)
#mypack:help               - Function tag for self-documentation
#mypack:module_name        - Function tag exposing module entry points
```

### Using Function Tags as Module API
```json
// data/mypack/tags/function/my_module.json
{
  "values": [
    "mypack:api/my_module",
    "mypack:internal/_setup"  // Runs once on first call
  ]
}
```

Callers use: `function #mypack:my_module`

### Self-Documenting Help System
```mcfunction
# data/mypack/function/help.mcfunction
tellraw @a [{"text":"=== MyPack v1.0 ===","color":"gold"}]
tellraw @a [{"text":"  Modules:","color":"yellow"}]
tellraw @a [{"text":"  #mypack:block    - Get/set blocks with state preservation","color":"gray"}]
tellraw @a [{"text":"  #mypack:raycast  - Ray collision detection","color":"gray"}]
tellraw @a [{"text":"  #mypack:math     - Trigonometry and math functions","color":"gray"}]
tellraw @a [{"text":"Status:","color":"yellow"}]
tellraw @a [{"text":"  Use /function #mypack:status for module status","color":"gray"}]
```

Run with: `function #mypack:help`

### I/O Contract Pattern
Every public function should document:
```mcfunction
# ============================================
# mypack:api/my_function
# Brief description of what this does.
#
# Inputs:
#   Storage bs:in mypack.my_function:
#     field (type): Description
#   Execution: at <entity> (position reference)
#   Score $score_name bs.in: Description
#
# Outputs:
#   Return: 1=success, 0=failure
#   Storage bs:out mypack:
#     result (type): Description
#   Score $score_name bs.out: Description
#
# Example:
#   data modify storage bs:in ... set value {...}
#   execute positioned ~ ~ ~ run function #mypack:my_function
#   data get storage bs:out mypack
# ============================================
```

### Entity Safety & Persistent Entities
```mcfunction
# NEVER kill all entities - it destroys library entities
# BAD:  kill @e
# GOOD: kill @e[tag=!mypack.persistent]

# Tag persistent entities on creation:
summon minecraft:marker ~ ~ ~ {Tags:["mypack.persistent","mypack.system"]}

# Clean up only your own entities:
kill @e[type=minecraft:marker,tag=mypack.system]
```

### Multi-Tick Processing (Anti-Lag)
```mcfunction
# Process large operations across ticks
# mypack:api/process_batch
execute if score $remaining bs.data matches 1.. run function mypack:internal/_do_batch
execute if score $remaining bs.data matches 1.. run schedule function mypack:api/process_batch 1t

# Or use limit-based iteration:
# mypack:api/iterate_cuboid
# with: {width:100,height:100,depth:100,limit:256}
# limit: max steps per tick
```

### Dependency Management
```mcfunction
# Check dependencies in #load function:
execute unless function #dependency_pack:status run tellraw @a [{"text":"ERROR: Missing dependency pack!","color":"red"}]
```

### Beet Integration (Python Build Pipeline)
```yaml
# beet.yml
require:
  - mypack.module.block
  - mypack.module.raycast
pipeline:
  - mecha           # Command preprocessor
  - beet.contrib.auto_yaml
output: build
```

## MCBookshelf Module Reference (Design Patterns)

MCBookshelf is the premier modular datapack library. Studying its architecture reveals production-proven patterns.

### Module Catalog & Key Functions

| Module | Help Tag | Core Capability |
|--------|----------|-----------------|
| **Block** | `#bs.block:help` | Get/set blocks with state preservation, fill, match, sound playback |
| **Raycast** | `#bs.raycast:help` | Voxel traversal ray casting with block/entity collision, callbacks, piercing |
| **Math** | `#bs.math:help` | Trig (sin/cos/tan/atan2), log/exp, pow, sqrt, GCD, factorial |
| **Generation** | `#bs.generation:help` | Multi-tick world iteration (cuboid/rectangle), noise callbacks |
| **Random** | `#bs.random:help` | 6 distributions, weighted choice, 2D noise matrices |
| **Health** | `#bs.health:help` | Player HP management, entity lifetime (TTL) with on_death callbacks |
| **Hitbox** | `#bs.hitbox:help` | Block shape/collision, entity dynamic/baked/custom hitboxes, providers |
| **View** | `#bs.view:help` | Aimed block/entity/point, block placement, visibility checks (can_see, in_view) |
| **Move** | `#bs.move:help` | Velocity-based entity movement with collision resolution callbacks |
| **Tree** | `#bs.tree:help` | Bank of pre-built tree structures (10 types × 5 variants each) |
| **Scheduler** | `#bs.scheduler:help` | Advanced scheduling beyond vanilla `/schedule` |

### Block Module Deep Dive
```mcfunction
# Get block at position (stores virtual format in bs:out block)
execute positioned ~ ~-.5 ~ run function #bs.block:get_block

# Virtual block format output:
# bs:out block {group:"stairs", block:"oak_stairs[facing=north,shape=straight]", 
#               type:"minecraft:oak_stairs", state:"[facing=north,shape=straight]", ...}

# State manipulation (acts on bs:out block virtual format):
function #bs.block:replace_properties {properties:[{name:"facing",value:"east"}]}
function #bs.block:replace_type {type:"minecraft:spruce_stairs"}
function #bs.block:map_type {type:"minecraft:spruce_planks",mapping_registry:"bs.shapes"}
function #bs.block:mix_type {type:"minecraft:bricks",mapping_registry:"bs.shapes"}

# Place blocks:
function #bs.block:set_block -- from bs:in block.set_block.block
function #bs.block:set_type  -- preserves state, from bs:in block.set_type.type

# Fill region:
function #bs.block:fill_block -- from bs:in block.fill_block {block,from,to,mode,filter}
function #bs.block:fill_type  -- preserves states, from bs:in block.fill_type {type,from,to,...}

# Lookup block properties by type (no position needed):
function #bs.block:lookup_type {type:"minecraft:stone"}
# Returns: hardness, blast_resistance, friction, instrument, sounds, can_occlude, etc.
```

### Raycast Module Deep Dive
```mcfunction
# Basic raycast (returns 1=hit, 0=miss)
execute anchored eyes positioned ^ ^ ^ run function #bs.raycast:run {with:{max_distance:10}}

# With callbacks:
execute anchored eyes positioned ^ ^ ^ run function #bs.raycast:run {with:{
  entities:true,
  on_targeted_block:"setblock ~ ~ ~ stone",
  on_targeted_entity:"say Hit!",
  on_entry_point:"particle flame ~ ~ ~",
  on_exit_point:"particle smoke ~ ~ ~"
}}

# Lambda scores available inside callbacks:
# $raycast.entry_distance bs.lambda (×1000)
# $raycast.hit_face bs.lambda (0=bottom,1=top,2=north,3=south,4=west,5=east)
# $raycast.hit_flag bs.lambda (-1=entity, else block hitbox flag)
# $raycast.entry_point.[x,y,z] bs.lambda (×1000, relative to target)

# Piercing (pass through N targets):
function #bs.raycast:run {with:{piercing:{blocks:2,entities:0}}}
```

### Hitbox Module Deep Dive
```mcfunction
# Block hitboxes (coords 0-16 within block space):
function #bs.hitbox:get_block_shape       # Default (interaction) shape
function #bs.hitbox:get_block_collision   # Physical collision shape

# Entity hitboxes:
function #bs.hitbox:get_entity            # Get width/height/depth
function #bs.hitbox:bake_entity           # Freeze hitbox (faster, no updates)
function #bs.hitbox:set_entity {with:{width:1.0,height:2.0,centered:false}}
function #bs.hitbox:reset_entity          # Back to dynamic

# Hitbox Providers (used by raycast/move):
# function #bs.hitbox:callback/get_block_shape             (flag 1 = solid)
# function #bs.hitbox:callback/get_block_shape_with_fluid  (flag 1=solid, 2=fluid)
# function #bs.hitbox:callback/get_block_collision
# function #bs.hitbox:callback/get_block_placement         (flag 4 = placement)
```

### Move Module Deep Dive
```mcfunction
# Set velocity scores on entity, then apply:
scoreboard players set @s bs.vel.x 120
scoreboard players set @s bs.vel.y 30
scoreboard players set @s bs.vel.z 80
function #bs.move:apply_vel {scale:0.001,with:{}}

# Collision behaviors:
function #bs.move:apply_vel {...,with:{on_collision:"function #bs.move:callback/bounce"}}
function #bs.move:apply_vel {...,with:{on_collision:"function #bs.move:callback/slide"}}
function #bs.move:apply_vel {...,with:{on_collision:"function #bs.move:callback/stick"}}
function #bs.move:apply_vel {...,with:{on_collision:"function #bs.move:callback/damped_bounce"}}

# Reference frame conversion:
function #bs.move:local_to_canonical  # ^-based velocity → world velocity
function #bs.move:canonical_to_local  # World velocity → ^-based velocity

# Lambda scores during collision callback:
# $move.hit_face bs.lambda    -- which face was hit
# $move.hit_flag bs.lambda    -- hitbox flag (-1=entity)
# $move.vel.[x,y,z] bs.lambda -- remaining velocity after rollback

# Custom collision: cancel velocity on hit axis
execute if score $move.hit_face bs.lambda matches 4..5 store result score $move.vel.x bs.lambda run scoreboard players set @s bs.vel.x 0
```

### Health / TimeToLive
```mcfunction
# Player health (uses instant_health effect, bypasses NBT limits)
function #bs.health:set_health {points:20.0}
function #bs.health:add_health {points:5.0}
function #bs.health:get_health {scale:1000}  # Returns scaled int

# Entity lifetime:
execute as @e[type=creeper] run function #bs.health:time_to_live {with:{
  time:10, unit:"s",
  on_death:"execute at @s run particle explosion_emitter ~ ~ ~"
}}
```

### View Module Wrappers (simplified raycast)
```mcfunction
# What entity is looking at (simplified):
function #bs.view:at_aimed_block {run:"setblock ~ ~ ~ sponge",with:{}}
function #bs.view:as_aimed_entity {run:"say I see you!",with:{}}
function #bs.view:at_aimed_point {run:"particle flame ~ ~ ~",with:{}}
function #bs.view:at_block_placement {run:"setblock ~ ~ ~ stone",with:{}}

# Predicate-based entity lookup (high performance, player only):
tag @e[type=armor_stand] add bs.view.is_lookable
function #bs.view:as_looked_entity {run:"effect give @s glowing 1 0 true"}

# Visibility checks:
execute as @e at @s if function #bs.view:can_see_ata {with:{}}
function #bs.view:in_view_ata {angle:90}
```

### Random Distributions Deep Dive
```mcfunction
# 6 probability distributions:
function #bs.random:uniform {min:1,max:100}              # Equal probability
function #bs.random:binomial {trials:10,probability:0.2}  # N trials, P(success)
function #bs.random:geometric {probability:0.02}          # Tries until first success
function #bs.random:normal {mean:10,spread:3}             # Bell curve
function #bs.random:poisson {lambda:5}                    # Event rate model

# Noise (scaled by 1000):
function #bs.random:simplex_noise_2d        # Gradient noise
function #bs.random:fractal_noise_2d        # Multi-octave noise

# Noise matrices (storage arrays):
function #bs.random:white_noise_mat_2d {width:16,height:16,with:{scale:1}}
function #bs.random:simplex_noise_mat_2d {width:16,height:16,with:{size:8,seed:42}}
function #bs.random:fractal_noise_mat_2d {width:16,height:16,with:{size:8,octaves:4,persistence:0.5}}

# Weighted random choice:
data modify storage bs:in random.weighted_choice.options set value ["A","B","C"]
data modify storage bs:in random.weighted_choice.weights set value [5,3,2]
function #bs.random:weighted_choice
```

### Generation Module Patterns
```mcfunction
# Iterate a 2D rectangle (multi-tick):
data modify storage bs:in generation.on_rectangle set value {
  width:64, depth:64, limit:64,
  direction:"es",
  run:'function #bs.generation:callback/set_block {block:"stone",with:{masks:[{block:"air"}]}}',
  on_finished:"say Done"
}
function #bs.generation:on_rectangle

# Procedural terrain with noise:
data modify storage bs:in generation.on_rectangle set value {
  width:64, depth:64, limit:64,
  run:'function #bs.generation:callback/fractal_noise_2d {
    run:"function mypack:place_block",
    with:{size:32,octaves:4,persistence:0.5}
  }'
}
function #bs.generation:on_rectangle
# mypack:place_block uses $generation.noise bs.lambda value [-1000,1000]
```

### Key Design Patterns Summary

| Pattern | Implementation | Why |
|---------|---------------|-----|
| Virtual format | `bs:out block {type,state,properties,...}` | In-memory block manipulation without placing |
| Help discovery | `#bs.module:help` function tag | Self-documenting modules |
| I/O contract | `bs:in`/`bs:out` storage + `bs.in`/`bs.out` scores | Predictable data flow |
| Lambda scores | `$module.var bs.lambda` | Context for callbacks without global storage |
| Callback commands | `{run:"command string",on_*:"command"}` | Execute arbitrary commands as callbacks |
| Typed macros | `{type:"value",mode:"value"}` | Strong typing for function parameters |
| Providers | `function #bs.hitbox:callback/get_*` | Strategy pattern for swappable behavior |
| Read-only output | `[readonly]` marked storage | Prevent mutation bugs |
| Multi-tick | `limit:N` parameter | Avoid lag from large operations |
| Entity safety | `kill @e[tag=!bs.persistent]` | Protect library entities |
| Bake/Reset | `bake_entity`/`reset_entity` | Performance optimization |
| Flag system | Numeric flags (1,2,4,8) on hitboxes | Categorize collisions (solid/fluid/placement) |

## Smithed Compatibility Conventions

The Smithed ecosystem defines standards for pack interoperability in a multi-pack world.

### Namespacing Convention
Prefix ALL pack-specific identifiers to prevent collisions:
```
# Scoreboard objectives:  pack_prefix.objective_name
scoreboard objectives add tcc.dummy dummy      # NOT: dummy

# Storage:  pack_prefix:path
data merge storage tcc:data {foo: "bar"}       # NOT: storage data {foo: "bar"}

# Entity tags:  pack_prefix.tag_name
tag @s add tcc.custom_entity                   # NOT: custom_entity

# File paths (inherent to data pack structure):
function tcc:path/to/function                  # Already namespaced by nature
```

### Pack ID Convention (pack.mcmeta)
Add an `id` field to `pack.mcmeta` for tooling to identify your pack:
```json
{
  "id": "my-pack",
  "pack": {
    "description": "My Cool Pack",
    "min_format": [101, 1],
    "max_format": [101, 1]
  }
}
```
The `id` must be stable across versions and match the Smithed upload ID.

### CMD (Custom Model Data) Prefixing
Since 1.20.5, prefer `item_model` component. If using `custom_model_data`, use `strings` subcomponent with namespace prefix:
```json
{
  "components": {
    "minecraft:custom_model_data": {
      "strings": ["mypack:cool_sword"]
    }
  }
}
```

### Smithed Tag Specification for Entity/Item/Block Interop

**Custom Entity Tags:**
```
# Mark custom mobs so other packs don't modify them:
summon zombie ~ ~ ~ {Tags:["smithed.entity"], CustomName:'"Custom Zombie"'}

# Respecting: exclude custom entities from vanilla modifications:
execute as @e[type=zombie, tag=!smithed.entity] run ...

# Boss / technical entities:
summon marker ~ ~ ~ {Tags:["smithed.entity","smithed.strict","smithed.block"]}
# smithed.strict: exempt from position/rotation changes, almost everything
```

**Custom Block Tags:**
```
# Place marker inside custom blocks:
setblock ~ ~ ~ obsidian
summon marker ~ ~ ~ {Tags:["smithed.block","smithed.entity","smithed.strict"]}

# Respecting: check for marker before modifying blocks:
execute if block ~ ~ ~ obsidian unless entity @e[tag=smithed.block,distance=..0.5] run ...
```

**Custom Item Tags (in custom_data component):**
```
# Mark items that shouldn't act like the base item:
give @s coal[custom_data={smithed:{ignore:{functionality:1b}}}]

# Mark items that shouldn't be crafting ingredients:
give @s chestplate[custom_data={smithed:{ignore:{crafting:1b}}}]

# Mark purely technical items (should be ignored by everything):
give @s paper[custom_data={smithed:{ignore:{everything:1b}}}]

# Check for custom items in selectors:
execute as @a if items entity @s weapon.mainhand *[custom_data~{smithed:{ignore:{functionality:1b}}}] run ...
```

### Vanilla Overrides (for Weld compatibility)
When overriding vanilla assets, use Weld merging rules to avoid conflicts:
- Use proper merge strategies for tag files (append, not replace)
- Prefix custom data within vanilla-format files

## Beet - Python Data Pack Development Kit

Beet is a build system that treats data packs and resource packs as Python objects.

### Core Concepts
```python
from beet import DataPack, Function, Context

# Plugin pattern: function that takes Context
def my_plugin(ctx: Context):
    # ctx.data = DataPack (programmatic access)
    # ctx.assets = ResourcePack
    # ctx.meta = Pipeline metadata (configurable)

    # Generate a function programmatically:
    ctx.data["demo:hello"] = Function(
        ["say hello world"] * 5,
        tags=["minecraft:load"]
    )

# beet.json configuration:
# {
#   "name": "my-project",
#   "output": "out",
#   "pipeline": ["my_plugins.my_plugin"],
#   "meta": {"custom_param": 42}
# }
```

### Key Beet Features
- **Lazy loading**: Files stay unloaded until accessed, instant load for thousands of files
- **Merging**: Tags auto-merge, languages auto-merge, smart conflict resolution
- **Plugin system**: `ctx.require(other_plugin)` for dependencies
- **File handles**: Unloaded → Serialized → Deserialized states, transparent conversion
- **Namespace proxies**: `pack.functions["demo:foo"]` direct access
- **Watch mode**: `beet watch --reload` for live data pack reloading during development

### Beet Ecosystem
| Tool | Description |
|------|-------------|
| `mecha` | Command pre-processor (extends .mcfunction syntax) |
| `lectern` | Document-based authoring format |
| `sandstone` | TypeScript framework for writing commands |
| `mcbookshelf` | PyPI package for Bookshelf library integration |

### Beet Pipeline Analogy
```
Sources → [Plugin 1] → [Plugin 2] → [... ] → Output Data Pack + Resource Pack
```
Like webpack for Minecraft: process and bundle separate sources into production pack.

## Community Resources Summary

| Resource | URL | Purpose |
|----------|-----|---------|
| Datapack Wiki | https://datapack.wiki/ | Community-built guides, getting started tutorials |
| Smithed Conventions | https://wiki.smithed.dev/conventions/ | Interoperability standards for pack ecosystem |
| Weld (Smithed) | https://weld.smithed.dev | Smart pack merging for resource pack compatibility |
| MCC FAQ | https://minecraftcommands.github.io/wiki/questions | Common questions with solutions (items, scores, entities, raycasting, etc.) |
| Beet | https://mcbeet.dev/ | Python build system / dev kit for data packs |
| MCStacker | https://mcstacker.net | Command generator for complex commands |
| Misode | https://misode.github.io/ | Generators for all JSON datapack types |
| Animated Java | https://animated-java.dev/ | Blockbench plugin for custom animations |
| Spyglass | https://marketplace.visualstudio.com/items?itemName=SPGoding.datapack-language-server | VSCode datapack language server |

## Smithed Library Ecosystem
| Library | Version | Purpose |
|---------|---------|---------|
| Actionbar | v0.4.1 | Show actionbar messages to players |
| Crafter | v0.2.0 | Custom crafting mechanics |
| Custom Block | v0.2.0 | Data-driven custom blocks |
| Damage | v0.2.0 | Custom damage handling |
| Prevent Aggression | v0.2.0 | Control mob aggression |
| Item | v0.2.1 | Item manipulation utilities |
| Title | v0.0.1 | Title display management |

## Recommended Tools for Pack Development
| Tool | Type | Why |
|------|------|-----|
| VSCode + Spyglass | Editor | Syntax highlighting, autocomplete, jump to definition |
| Beet | Build system | Plugin pipeline, programmatic pack generation |
| Misode | Generator | Online generators for every JSON format |
| MCStacker | Generator | Complex command generation (give, summon, tellraw) |
| Datamancer (mod) | Debugging | Auto-reload, profiling, benchmarking |
| CommandCrafter (mod) | Debugging | Breakpoints, step-through for functions |
| Component Viewer (mod) | Inspection | View and copy item components |
| Worldgen Devtools (mod) | Development | World generation development aids |

## MCC FAQ - Production-Grade Tricks & Patterns

These are "wiki can't teach you" techniques from the community knowledge base (https://minecraftcommands.github.io/wiki/questions).

### Custom Item Identification (1.20.5+)
```mcfunction
# ALWAYS use custom_data for item identification, NEVER rely on item name
give @s stick[ custom_data={my_tag:true}, item_name='"My Stick"' ]

# Detect in inventory:
@a[nbt={Inventory:[{components:{"minecraft:custom_data":{my_tag:true}}}]}]

# Detect with execute if items (sub-predicate ~):
execute as @a if items entity @s container.* *[custom_data~{my_tag:true}]

# Detect on ground:
execute if entity @e[type=item,nbt={Item:{components:{"minecraft:custom_data":{my_tag:true}}}}]
```

### "Run Once" Pattern (edge detection without comparators)
```mcfunction
# Scoreboard method (best for Java):
scoreboard objectives add matched dummy
execute as @a[scores={matched=0},x=73,y=10,z=3,distance=..1] run say Entered area!
execute as @a store success score @s matched if entity @s[x=73,y=10,z=3,distance=..1]

# Tag method (works in Bedrock too):
execute as @a[x=73,y=10,z=3,distance=..1,tag=!alreadyMatched] run say Entered area!
tag @a[tag=alreadyMatched] remove alreadyMatched
tag @a[x=73,y=10,z=3,distance=..1] add alreadyMatched
```

### Player Join Detection
```mcfunction
# First time join (tag method):
execute as @a[tag=!init] run say Welcome, new player!
tag @a[tag=!init] add init

# Consecutive join (leave_game objective):
scoreboard objectives add leave custom:leave_game
execute as @a[scores={leave=1..}] run say Welcome back!
scoreboard players reset @a[scores={leave=1..}] leave

# Combined (2 commands, handles both first and rejoins):
scoreboard objectives add leave custom:leave_game
execute as @a unless score @s leave = @s leave store success score @s leave run tellraw @a [{"selector":"@s"}," just logged in for the first time!"]
execute as @a unless score @s leave matches 1 store success score @s leave run tellraw @a [{"selector":"@s"}," just came back!"]
```

### Scoreboard ID System (Entity Linking)
```mcfunction
scoreboard objectives add ID dummy

# Assign unique IDs to new players:
execute as @a unless score @s ID = @s ID store result score @s ID run scoreboard players add #new ID 1

# Link entity to player:
scoreboard players operation @e[tag=my_entity] ID = @p ID

# Find linked entity:
execute as @e[tag=my_entity] if score @s ID = @p ID run say Found!
```

### Client-Side Entityless Raycasting
```mcfunction
# Single-tick, entity-free raycast. Step=0.1, max=50 steps=5 blocks
# Start:
execute as @p at @s anchored eyes positioned ^ ^ ^ anchored feet run function mypack:ray_start

# mypack:ray_start
scoreboard players set @s ray_steps 50
function mypack:ray

# mypack:ray
execute unless block ~ ~ ~ #minecraft:air run return run function mypack:ray_hit
scoreboard players remove @s ray_steps 1
execute if score @s ray_steps matches 1.. positioned ^ ^ ^0.1 run function mypack:ray

# mypack:ray_hit
setblock ~ ~ ~ minecraft:stone
```

### Single-Command "Looking At" Check
```mcfunction
# Check if player looks at entity/position (one command, no raycast needed):
execute as @a at @s anchored eyes facing entity @e[type=cow,limit=1,sort=nearest] eyes feet positioned ^ ^ ^1 rotated as @s positioned ^ ^ ^-1 if entity @s[distance=..0.1] run say Looking at cow!

# Check if looking at coordinates:
execute as @a at @s anchored eyes facing 10 20 30 feet positioned ^ ^ ^1 rotated as @s positioned ^ ^ ^-1 if entity @s[distance=..0.1] run say Looking at position!

# Viewing angle formula:  distance(d) → angle(α)
# α = 2 × arcsin(d/2),  d = 2 × sin(α/2)
# d=0.1 → ~5.7° cone,  d=0.2 → ~11.5° cone
```

### Floor Crafting (Custom NBT Crafting)
```mcfunction
# 1.20.5+ floor crafting: items on ground → custom result
# Uses store success entity Age short 6000 to instantly despawn consumed ingredients
execute at @a as @e[type=item,distance=..6,nbt={OnGround:true,Item:{id:"minecraft:emerald",count:2,components:{"minecraft:custom_data":{some:true}}}}] at @s \
  if block ~ ~ ~ air \
  store success entity @s Age short 6000 \
  store success entity @e[type=item,distance=..0.5,limit=1,nbt={OnGround:true,Item:{id:"minecraft:diamond",count:1,components:{"minecraft:custom_data":{custom:true}}}}] Age short 6000 \
  store success entity @e[type=item,distance=..0.5,limit=1,nbt={OnGround:true,Item:{id:"minecraft:redstone",count:5,components:{"minecraft:custom_data":{data:true}}}}] Age short 6000 \
  run summon item ~ ~ ~ {Item:{id:"minecraft:ender_eye",count:1,components:{"minecraft:custom_data":{custom_result:true}}}}

# With animation (shulker box burst):
# ... summon area_effect_cloud store success score @s craft_anim
# ... run summon item ~ ~ ~ {Fire:20s,Item:{id:"minecraft:shulker_box",...,components:{"minecraft:container":[...]}}}
```

### Knowledge Book Crafting (1.20+)
Using `recipe_crafted` trigger to check ingredient NBT:
```json
{
  "criteria": {
    "requirement": {
      "trigger": "minecraft:recipe_crafted",
      "conditions": {
        "recipe_id": "example:my_recipe",
        "ingredients": [
          { "items": ["minecraft:emerald"], "nbt": "{some:true}" },
          { "items": ["minecraft:emerald"], "nbt": "{some:true}" }
        ]
      }
    }
  },
  "rewards": {
    "function": "example:recipe_reset",
    "loot": ["example:my_result"]
  }
}
```
Reset function: `advancement revoke @s from example:recipe/root` + `clear @s knowledge_book`

### Inventory Store & Restore (Storage + Macros)
```mcfunction
# Store player inventory to storage (1.20.2+):
execute store result storage example:inv this.ID int 1 run scoreboard players get @s ID
data modify storage example:inv this.Inventory set from entity @s Inventory
function example:storing/update with storage example:inv this

# Restore with inline loot table macro (1.20.5+):
$loot replace entity @s container.$(Slot) loot {pools:[{rolls:1,entries:[{type:"minecraft:item",name:"$(id)",functions:[{function:"minecraft:set_count",count:$(count)},{function:"minecraft:set_components",components:$(components)}]}]}]}

# Slots need special handling:
# Inventory: container.0-26
# Hotbar: container.0-8 (same as container.0-8, which ARE hotbar slots)
# Armor: armor.head, armor.chest, armor.legs, armor.feet
# Offhand: weapon.offhand (=-106)
```

### Yellow Shulker Box Trick (Bulk Item Give)
Place items into a yellow shulker box, use `/loot` to give contents:
```mcfunction
data merge block <pos> {Items:[]}
data modify block <pos> Items append from ...
loot give @a mine <pos> minecraft:air{drop_contents:1b}
```
Key: Must remove `Slot` data before `data modify` append, or items get overwritten.

### XP Orb Raycast (Bedrock Single-Tick)
```mcfunction
# Summon XP orb per player, then 2^9=512 iterations in one tick:
execute as @a at @s run summon xp_orb
execute as @e[type=xp_orb] at @s at @p rotated as @p anchored eyes run tp @s ~~~ ~ ~
execute as @e[c=2] as @e[c=2] ... (8 more x2) as @e[type=xp_orb] at @s run tp @s ^^^0.1 true
execute at @e[type=xp_orb] run particle minecraft:basic_crit_particle ~~~
kill @e[type=xp_orb]
```
Each `as @e[c=2]` doubles execution count. 9 doublings = 512 iterations.

### Value Comparison Without Scoreboards (1.20.5+)
```json
{
  "condition": "minecraft:value_check",
  "value": { "type": "minecraft:storage", "storage": "example:data", "path": "value" },
  "range": {
    "min": { "type": "minecraft:storage", "storage": "example:data", "path": "min" },
    "max": { "type": "minecraft:storage", "storage": "example:data", "path": "max" }
  }
}
```

### execute if items Sub-Predicate (~) vs Exact (=)
```mcfunction
# Exact match: item must have EXACTLY this component (fails if any other enchantments exist)
execute if items entity @s weapon *[minecraft:enchantments={levels:{"minecraft:unbreaking":1}}]

# Sub-predicate: item just needs to CONTAIN matching part (more flexible)
execute if items entity @s weapon *[minecraft:enchantments~[{enchantment:"minecraft:unbreaking",levels:{min:1}}]]

# OR conditions:
execute if items entity @s weapon *[minecraft:damage~{damage:{max:5}}|minecraft:damage~{damage:{min:40}}]
```

### Entity_Scores Predicate (Ranged Comparison)
```json
// kills >= deaths
{ "min": { "type": "minecraft:score", "target": "this", "score": "deaths" } }
// kills > deaths (need inverted + all_of):
[{ "min": { "target":"this","score":"deaths" } }, { "condition":"inverted", "term":{ "max": { "target":"this","score":"deaths" } } }]
// kills = deaths:
{ "min": { "target":"this","score":"deaths" }, "max": { "target":"this","score":"deaths" } }
```

### Random Number Production Patterns
```mcfunction
# Modern (best): /random command
execute store result score #rnd random run random value 1..100

# Range shift: to get [5,15] from [0,10]:
# generate [0,10], then add 5 → [5,15]

# Random chance without numbers:
{ "condition": "minecraft:random_chance", "chance": 0.3 }
```

### Item Loot Table JSON→NBT Conversion Gotcha
When using `set_components` in loot tables/recipes, JSON values auto-convert to NBT:
```json
"components": { "minecraft:custom_data": {"my_tag": 1} }
// Result: {my_tag: 1b}  NOT {my_tag: 1}
// Ints become smallest fitting byte/short/int/long
// Always check with /data get entity @s SelectedItem
```
- **Smithed**: https://smithed.dev/ - Pack distribution platform
- **Misode**: https://misode.github.io/ - Online generators for all datapack types
- **MCStacker**: https://mcstacker.net - Command generator
- **Beet**: https://mcbeet.dev/ - Python datapack development toolkit
- **Smithed Conventions**: https://wiki.smithed.dev/conventions/ - Compatibility standards
- **Datapack Wiki**: https://datapack.wiki/ - Guides and tutorials
- **MCC FAQ**: https://minecraftcommands.github.io/wiki/questions - Common questions answered
- **Official wiki**: https://zh.minecraft.wiki/w/数据包
- **pack.mcmeta generator**: https://misode.github.io/pack-mcmeta/
