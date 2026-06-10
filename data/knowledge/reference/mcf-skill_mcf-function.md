---
name: mcf-function
description: Create and modify Minecraft Java Edition .mcfunction files, function macros, function tags (#load, #tick), scheduling, and function execution. Use when writing command sequences, creating game loops, or implementing data pack logic.
license: MIT
compatibility: opencode
metadata:
  version: "1.0"
  game-version: "26.1.2"
  category: minecraft-datapack
---

# Minecraft Function (MCFunction)

## File Location
`data/<namespace>/function/<path>.mcfunction`

## File Format

### Basic Commands
Each line is a command **without** a leading `/`:
```mcfunction
say Hello World
give @a minecraft:diamond 1
teleport @p ~ ~10 ~
```

### Line Continuation
Use `\` at end of line to continue on next line:
```mcfunction
say 你\
    好
```

### Comments
Use `#` at the start of a line for comments:
```mcfunction
# This is a comment
say Hello  # This is NOT a comment - would cause error
```

## Macros

Macros delay command parsing to runtime and allow dynamic substitution.

### Macro Syntax
- Line starts with `$` (first non-whitespace character)
- Uses `$(key)` for substitution variables
- Key characters: `a-z`, `A-Z`, `0-9`, `_`

```mcfunction
$give @s $(id) $(count)
```

### Calling Macro Functions
```mcfunction
function test:macro_func with entity @p SelectedItem
# or with explicit NBT:
function test:macro_func with {id: "minecraft:stick", count: 64}
```

### Value Conversion Rules
When NBT values are substituted:
- Numbers: converted to text without type suffixes (float decimals up to 15 places)
- Strings: extracted value (no quotes)
- Lists/Compounds/Arrays: converted to SNBT format

### Performance
- Non-macro lines: parsed at load time
- Macro lines: parsed at each call (with caching for repeated parameters)
- Max command length (including macro expansion): 2,000,000 characters

## Calling Functions

### Via Command
```
function <namespace>:<path>
function #<namespace>:<tag>           # Call all functions in a tag
execute if function <namespace>:<path>  # Conditional execution
```

### Via Function Tags
```json
// data/<namespace>/tags/function/load.json
{
  "values": ["my_pack:init"]
}
```

#### Special Built-in Tags
- **`#minecraft:load`** - Functions run on world load / server start / `/reload`. Executes before players join. Cannot target players.
- **`#minecraft:tick`** - Functions run every game tick. Used for game loops.

### Via Advancements
```json
{
  "rewards": {
    "function": "namespace:path/to/function"
  }
}
```
Executor is the player who earned the advancement.

### Via Schedule
```
schedule function <namespace>:<path> <time>
schedule clear <namespace>:<path>
```
Delays function execution by specified time (in ticks). Time: `1d` (day), `1s` (second), `1t` (tick), or raw ticks.

### Via Enchantment Effects
```json
{
  "type": "run_function",
  "function": "test:test"
}
```

## Execution Behavior

### Execution Context
- Functions store caller's context: executing entity, position, rotation, dimension
- `execute` subcommands change context only for the current command, not subsequent ones
- If executor is server ("Server"), position is world spawn

### Command Limits
- All commands (including sub-function calls) execute within **one game tick**
- Limited by game rule `max_command_sequence_length` (default: 65536)
- Max command characters (including macros): 2,000,000

### Execution Example
```mcfunction
# Calling function:
execute as @a at @s run function foo:bar

# foo:bar contents:
teleport @s ~ ~5 ~
execute at @s run setblock ~ ~-1 ~ minecraft:diamond_block
setblock ~ ~-1 ~ minecraft:emerald_block
```
Result: All players teleported up 5 blocks, emerald placed at original position, diamond placed at new position.

## Return Values
Use the `/return` command to set function return values:
```
return <value>    # Set success=true, result=<value>
return fail       # Set success=false
return run ...    # Run command and use its result
```

- Functions without `return` are **Void functions** (no return value)
- `execute if function` checks for non-zero return value
- `execute store ... run function` stores the function's result

## Recursion
Functions can call themselves:
```mcfunction
say 1
function test:test
say 2
```
Beware: no termination condition = infinite loop until `maxCommandChainLength` limit.

## Permission Levels
- Singleplayer/LAN: commands up to permission level 2
- Multiplayer server: controlled by `function-permission-level` in `server.properties`
- Default: level 2

## Best Practices (from MCBookshelf patterns)

### I/O Convention: Storage `bs:in` / `bs:out`
Use a consistent storage namespace for function inputs and outputs:
```mcfunction
# Input pattern
data modify storage bs:in my_module.my_function set value {field1: "value", count: 5}
function #mypack:my_function

# Output pattern
data get storage bs:out my_module
```

Each function should clearly document its inputs (`bs:in`) and outputs (`bs:out`).

### Scoreboard Conventions
Use dedicated objectives for data passing:
```
bs.in    - Input scores (shifted for fixed-point: ×1000 for 3 decimal places)
bs.out   - Output/return values
bs.lambda - Callback context (temporary, per-invocation)
bs.data  - Persistent or temporary data
bs.ctx   - Context for macro calls (storage-based)
```

### Fixed-Point Arithmetic
Since scores only store integers, use digit shifting for decimals:
```mcfunction
# Store 42.5 (shifted by 3 digits = 42500)
scoreboard players set $value bs.in 42500

# In macros, scale back:
$tp @s ~ ~ ~$(value)

# Macro parameter from storage:
# Storage: {x: 42.5}
function mypack:action with storage bs:ctx x
# Inside the macro:
$tp @s ~ ~$(x) ~
```

### Public API via Function Tags
```mcfunction
# Public API (function tag - callers use this)
function #mypack:module_name  -- help/discovery
function #mypack:do_something -- public function

# Private implementation (direct function - internal use only)
function mypack:internal/_helper  -- underscore prefix = private
```

### Multi-tick Processing
To avoid lag, spread heavy operations across ticks:
```mcfunction
# Use /schedule for delayed execution
schedule function mypack:process_next 1t

# Or store progress in storage/scoreboard
# mypack:process_batch
execute store result score $remaining bs.data run ...
execute if score $remaining bs.data matches 1.. run schedule function mypack:process_batch 1t
```

### Help / Discovery Function
```mcfunction
# data/mypack/function/help.mcfunction
tellraw @a [{"text":"=== MyPack v1.0 ===","color":"gold"}]
tellraw @a [{"text":"  #mypack:do_thing - Description of what it does","color":"gray"}]
```

### Callback Pattern
```mcfunction
# Accept a command string as callback
# Storage: {run: "say Hello", on_finished: "say Done"}
function #mypack:iterate with storage bs:in my_module

# Execute the callback command directly:
$execute $(run)

# Inside iteration macros:
# The $(run) gets replaced with the callback command string
```

### Lambda Scores in Callbacks
Provide context to callbacks via scoreboard:
```
$generation.i bs.lambda   - First dimension index (0 to size-1)
$generation.j bs.lambda   - Second dimension index
$raycast.entry_distance bs.lambda - Distance from origin (×1000)
$raycast.hit_face bs.lambda - Hit face (0=bottom,1=top,2=north,3=south,4=west,5=east)
```

### Macro Functions as Typed Arguments
Use macro functions to pass typed parameters:
```mcfunction
# Call with typed arguments:
function #mypack:set_block {type:"minecraft:oak_stairs", mode:"replace"}

# Inside the macro:
$setblock ~ ~ ~ $(type)[$(state)]
```

### Documenting Function I/O
Always document functions with clear Input/Output sections:
```mcfunction
# ============================================
# mypack:teleport_above
# Teleports the executor N blocks above their current position
#
# Inputs:
#   Storage bs:in mypack.teleport_above:
#     height: Number of blocks to go up
#
#   Execution: at <entity> (position reference)
#
# Outputs:
#   State: Entity teleported
# ============================================
$tp @s ~ ~$(height) ~
```

### Entity Safety
When using persistent entities:
```mcfunction
# NEVER do this - it kills library entities:
kill @e

# Instead, use tags to protect system entities:
kill @e[tag=!mypack.persistent]
# Or target specifically:
kill @e[type=minecraft:item,tag=!mypack.protected]
```

### Pre-compute / Constant Storage
Store lookup tables in `bs:const` storage for performance:
```mcfunction
# Pre-compute once (in #load function):
data modify storage bs:const mypack.colors set value [
  {name: "red", rgb: 16711680},
  {name: "green", rgb: 65280},
  {name: "blue", rgb: 255}
]

# Use during runtime:
data modify storage bs:ctx mypack selected_color set from storage bs:const mypack.colors[0]

## Entity Access Patterns (Avoiding @e Scans)

Scanning all entities with `@e` is the #1 performance killer in datapacks. These patterns avoid it.

### World Entity Pattern (Fixed UUID, Zero Scans)

The ultimate entity access optimization: spawn an **item entity** with a **fixed, known UUID** in `#load`. Access it by UUID directly — no `@e` scan of any kind.

```mcfunction
# In #minecraft:load function:
# Spawn with a PREDETERMINED UUID — never scan to find it again
summon minecraft:item ~ ~ ~ {Item:{id:"minecraft:stone",Count:1b},UUID:[I;0,0,0,1],Tags:["mypack.world","mypack.persistent"],PickupDelay:32767,Age:-32768}

# Later, access directly by UUID — ZERO entity iteration:
execute as 00000000-0000-0000-0000-000000000001 run function mypack:tick
data get entity 00000000-0000-0000-0000-000000000001
data modify entity 00000000-0000-0000-0000-000000000001 data.something set value ...
```

**Why item entity specifically?**
- Has `Owner`/`Thrower` NBT to enable `on origin` tracing
- `PickupDelay:32767` = can never be picked up
- `Age:-32768` = never despawns
- Can hold item NBT as additional data storage
- Cheaper than marker for some operations

**Why UUID-based access is fastest?**
- Minecraft internally hashes entities by UUID
- `execute as <uuid> run ...` = O(1) direct lookup
- `@e[tag=...,limit=1]` = O(n) entity scan
- The difference: 1 microsecond vs scanning potentially thousands of entities

### `on origin` Pattern with UUID World Entity
```mcfunction
# When you need to trace back to a player without @a scan:
# 1. Players throw items or interact → Minecraft auto-sets Thrower/Owner NBT
# 2. Read the Owner UUID from the item's NBT
# 3. Access the player directly by UUID

# Example: player right-clicks → detect interaction → get player UUID from Thrower
execute as @e[type=item,tag=mypack.interaction] run data modify storage mypack:temp owner set from entity @s Item.tag.Owner
# Now access player directly:
execute as $(owner_UUID) run say I was the one who clicked!
```

### Complete UUID-Based Architecture
```mcfunction
# #load - spawn world entity with FIXED UUID
summon minecraft:item 0 0 0 {Item:{id:"minecraft:stone",Count:1b},UUID:[I;0,0,0,1],Tags:["world"],PickupDelay:32767,Age:-32768}
# Store the known UUID string in storage for macro use:
data modify storage mypack:const world_uuid set value "00000000-0000-0000-0000-000000000001"

# #tick - execute from world entity by UUID (zero scan):
execute as 00000000-0000-0000-0000-000000000001 run function mypack:tick

# Anywhere — access world entity data by UUID:
data get entity 00000000-0000-0000-0000-000000000001
```

> **UUID 技巧** 在 NBT 中使用 `uuid("hex-string")` 自动转换：`{UUID:uuid("dab4d1cd-223b-41bd-8084-59d890d935e4")}` → `{UUID:[I;...]}`

> **世界实体安全性**：全局共享对象，接口实现需确保维度/区块/实体安全，调用完毕后放回安全位置。

## Stack-based Function Context (from VanillaLibrary Feature #4)

Use command storage as a call stack — proper scoping, recursive algorithms, variable isolation.

```mcfunction
# Push new frame:
data modify storage example:0 stack append value {}
# Current frame = stack[-1] (LIFO)
data modify storage example:0 stack[-1].CONTEXT.input set value [1,2,3]
# Pop frame:
data remove storage example:0 stack[-1]
```

Each function pushes a frame, writes params to `CONTEXT`, reads results from `return`, and pops on exit. Avoids global variable pollution. Faster than macros for non-iterative data ops.

## Entity Tree (OOP via Passengers + Origin)

From VanillaLibrary Feature #3 — build object graphs using entity passenger trees:
```mcfunction
# Root = item_display (interpolatable for smooth motion)
# Leaf = item (entity pointer via Thrower→on origin)
summon item_display ~ ~ ~ {Tags:["Camera"],teleport_duration:5,Passengers:[
  {id:"item",PickupDelay:32767,Age:-32768,Item:{id:"music_disc_11",count:1,components:{"item_model":"air"}},Tags:["Ptr","CameraEntity"]}
]}

# Navigate tree: execute on passengers → access pointer → on origin → get target
execute on passengers if entity @s[tag=Ptr] on origin run say Found target!

# Key: NEVER use @e[nbt={}] on root entities — it serializes ALL passengers!
```

## Entity Selector Performance (Source-Code Level)

From VanillaLibrary Feature 2025.07#2 (创小业) — reading Minecraft source code for truth.

### Performance Hierarchy
```
UUID access:                                     O(1) - direct hash lookup
Player name:                                     O(1) - direct hash lookup  
@s:                                              instant
@a / @p / @r:                                    only scans players
@e with type=:                                   type-indexed, fast
@e without type=:                                scans ALL entities
```

### Critical Optimizations
```mcfunction
# 1. ALWAYS use type= on @e - Minecraft indexes entities by type
# BAD:  @e[tag=target]
# GOOD: @e[type=zombie,tag=target]  -- type check is near-instant

# 2. ALWAYS use distance= to limit dimension (even without range)
# @e without distance= scans ALL dimensions; with distance= scans current only
# BAD:  @e[type=item,tag=target]
# GOOD: @e[type=item,tag=target,distance=0..]  -- distance=0.. is a valid no-op!

# 3. Actual parameter execution order (NOT your written order):
#    type → level → gamemode → team → scores → tag → name → nbt (LAST!)
#    x_rotation → y_rotation → Box → distance → sort → limit (ALWAYS at end)
# Non-order-dependent params: x,y,z,dx,dy,dz,distance,level,x_rot,y_rot,limit,sort

# 4. limit= only helps when sort is NOT specified (sort=arbitrary)
# With sort=nearest/random/furthest, the game must scan ALL entities first
# @e[limit=1] : stops after first match → good
# @e[sort=nearest,limit=1] : scans ALL, then sorts, then picks 1 → bad

# 5. NEVER use nbt={} as a first-line filter — it copies ALL entity NBT
# nbt= should ALWAYS be the LAST parameter (written last = checked last)
# WRONG: @e[nbt={Sheared:1b},scores={temp=88}]
# RIGHT: @e[scores={temp=88},nbt={Sheared:1b}]  -- only 2 pass scores, then NBT check

# 6. dx,dy,dz create a Box for pre-filtering (only @e)
# @e[dx=10,dy=5,dz=10] first checks chunk intersection, then tests predicates
# A well-sized Box can eliminate 90%+ entities before any predicate runs

# Golden example:
# Known: sheep near (0,0), only 2 have temp=88, one is sheared
execute as @e[type=sheep,distance=..10,scores={temp=88},nbt={Sheared:1b},limit=1]
# type= first (fast), distance= limits chunks, scores= (2 pass), nbt= last (1 check)
```

### Common Pitfalls
```
@s with sort=nearest → degenerates to @a behavior (Mojang doesn't prevent this)
scores={} with duplicate keys → HashMap overwrites, last one wins
tag= with contradictions → @e[tag=a,tag=!a] → always empty (Mojang doesn't catch)
```

## Half-Reduction State Machine (Single-Variable Debounce)

From VanillaLibrary Feature 2026.01#f (伊桑) — one-scoreboard edge detection with built-in debounce.

```mcfunction
# The formula: state = (state + 4) / 2 every tick
# When an event fires: scoreboard players add @s state 4
# State transitions:
#   0 → event → 2 (rising) → 3 (active) → 3 → 3 ...
#   ...event stops → 3 → 1 (falling) → 0 (idle)
#   2 = "just pressed", 3 = "holding", 1 = "just released", 0 = "idle"

# Implementation:
scoreboard objectives add state dummy
scoreboard players set 2 const 2  # divisor constant

# In tick:
scoreboard players operation @s state /= 2 const
execute if score @s state matches 2 run say Just pressed!
execute if score @s state matches 3 run say Holding...
execute if score @s state matches 1 run say Just released!

# In event handler (e.g., right-click progress):
scoreboard players add @s state 4

# +6 variant for debounce protection (survives intermittent trigger loss):
# +6 gives: 3=press, 4-5=hold, 1=release, 2=transition state
scoreboard players add @s state 6
```

Works because: integer division by 2 creates a decay chain where only 3 and 2 map to 1. Any other number, divided repeatedly, eventually hits 2 then 1. Adding 4 or 6 creates a ramp that the decay turns into a clean rising/falling edge.

## OhMyDat: Entity-Private Storage (O(1) Hash)

From VanillaLibrary Feature 2026.01#a (伶) — 8-dimensional array for per-entity data.

```
Core idea: entity ID → 4-digit base-4 number → 8D array index
Max entities: 4^8 = 65,536

ID allocation: (array[0] + array[-1]) / 2, binary subdivision
Garbage collection: manipulate all scores to detect vanished entities
Data access: arr[-4][-4][-4][-4][-4][-4][-4][-4] = entity's private space
```

```mcfunction
# Usage:
function #oh_my_dat:please   # Register entity, get private space
data modify storage oh_my_dat: _[-4][-4][-4][-4][-4][-4][-4][-4].hp set value 20

# Empty-element padding trick for index access:
# To access index 3 in a 4-element array: pad with 3 empties, then [-4] = index 3
data modify storage arr:data _ append value [] # pad
data modify storage arr:data _[-4] set value "arr[3]"
# Cleanup: remove indices 4,5,6 (keep 0-3)
```

## Queue & Stack Data Structures

From VanillaLibrary Feature 2025.11#3 (洪旗) — FIFO/LIFO in pure mcfunction.

```mcfunction
# Queue (FIFO):
# Enqueue:
$data modify storage queue:data $(name) append value $(value)
# Dequeue:
$data modify storage queue:data de_queue set from storage queue:data $(name)[0]
$data remove storage queue:data $(name)[0]
# Length:
$return run data get storage queue:data $(name)

# Stack (LIFO):
# Push:
$data modify storage stack:data $(name) prepend value $(value)
# Pop (via [-1]):
$data modify storage stack:data pop set from storage stack:data $(name)[-1]
$data remove storage stack:data $(name)[-1]

# Queue traversal without changing original:
$data modify set storage queue:data back set from storage queue:data $(name)
# Process back[0], remove back[0], recurse

# In-place traversal (process all, return to original order):
# Dequeue → process → enqueue, repeat queue.length times
# After N iterations, first dequeued item returns to index 0

# Real application: auto-loading crossbow magazine
# Store preloaded arrows in item's custom_data as queue
# On fire: dequeue first arrow → set as charged_projectile
# On reload: enqueue new arrow to custom_data queue
```

## Data Pack Optimization Principles

From VanillaLibrary Feature 2025.04#3 (Dahesor).

### Cost Hierarchy (per single operation)
```
scoreboard add/remove:     1 scb (baseline unit)
storage modify:            2-10 scb
entity data modify:        30-60 scb
block entity data:         40-80 scb
player data modify:        100-200 scb (SLOWEST NBT source)
nbt={} in selector:        copies ALL entity NBT recursively → AVOID
```

### NBT Cache Pattern
```mcfunction
# BAD — reads player NBT 3 times:
execute if data entity @s SelectedItem{id:"minecraft:stone"} run ...
execute if data entity @s SelectedItem{id:"minecraft:dirt"} run ...

# GOOD — read once into storage, check storage:
data modify storage tmp:cache item set from entity @s SelectedItem
execute if data storage tmp:cache item{id:"minecraft:stone"} run ...
execute if data storage tmp:cache item{id:"minecraft:dirt"} run ...
```

### Frequency Tuning
```
#tick function:    optimize AGGRESSIVELY — runs every tick
schedule loops:    moderate optimization — runs periodically  
event handlers:    minimal optimization needed — rare triggers
visual updates:    can drop to 1/2/5 Hz — players won't notice
```

### Profiling with F3+L / /perf
Generate a 10-second profile, find the zip in `.minecraft/debug/profiling/`.
Look for `commandFunctions` in `server/profiling.txt`:
```
function mypack:tick(201/1) - 69.88%/0.46%
# 201 executions / avg 1 per tick / 69.88% of parent / 0.46% of total tick time
```
Upload to https://misode.github.io/report/ for visual analysis.

### `/return` for Early Exit
```mcfunction
# BAD — all conditions evaluated even if case 1 matches:
execute if score @s foo matches 1 run say case1
execute if score @s foo matches 2 run say case2

# GOOD — return run stops function after first match:
execute if score @s foo matches 1 run return run say case1
execute if score @s foo matches 2 run return run say case2
```

### Dev Toolchain (from Rainbow_'s guide)
```
Editor:   VSCode + Datapack Helper Plus (Spyglass/"大憨批")
Build:    Beet (Python) or MCFPP (dedicated lang)
Models:   Blockbench + Animated Java plugin
Mods:     Axiom (building), Datamancer (debugging), Sniffer (breakpoints)
Analysis: F3+L profiling → https://misode.github.io/report/
```

## Data Pack → Shader Communication (Particle Channel)

From VanillaLibrary Feature 2025.09#7 (MC作死狼王) — the ONLY proven way to send data from data packs to shaders without mods.

### Core Principle
```
Data Pack:  /particle entity_effect{color:[R,G,B,A]} ~ ~ ~ (special alpha = marker)
    ↓
Vertex Shader: detect Color.a in range → redirect to screen corner (fixed NDC position)
    ↓
Post Shader:   texture(ParticlesSampler, vec2(1.0,1.0)) → read the RGB values
    ↓
Result:        Data pack can pass arbitrary float3 data to post-processing shader!
```

### Vertex Shader Pattern
```glsl
#version 150
#moj_import <minecraft:globals.glsl>

#define RESOLUTION_FACTOR 2  // 2x2 pixels in corner is enough

void main() {
    if (baseColor.a > 0.113 && baseColor.a < 0.115) {
        // Detected: this is our data particle. Redirect to screen corner.
        vec4 clipSpacePos = vec4(0.0, 0.0, -0.05, 1.0);
        vec2 cornerOffset = quadCorners[gl_VertexID % 4];
        clipSpacePos.xy += cornerOffset;
        vec2 ndcCornerOffset = -cornerOffset - 0.5;
        vec2 screenOffset = ndcCornerOffset / ScreenSize;
        gl_Position = ProjMat * clipSpacePos;
        gl_Position.xy = gl_Position.w * (vec2(1.0) - screenOffset * vec2(RESOLUTION_FACTOR));
    } else {
        gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);
    }
}
```

### Fragment Shader (particle.fsh)
```glsl
void main() {
    if (baseColor.a > 0.113 && baseColor.a < 0.115) {
        fragColor = vec4(baseColor.rgb, 1.0);  // Pure color, no fog/lighting
    } else {
        // Normal particle rendering...
    }
}
```

### Post Shader (transparency.fsh)
```glsl
// Read data from the particle channel in screen corner:
vec4 particleInput = texture(ParticlesSampler, vec2(1.0, 1.0));
// particleInput.rgb now contains the values from the datapack!
// Use it to control shader parameters dynamically.
fragColor = mix(originalColor, particleInput, 0.5);  // Example: screen tint
```

### Data Pack Side
```mcfunction
# Send RGB values to shader via particle (A=0.114 is the marker):
execute as @a at @s run particle entity_effect{color:[1.0,0.5,0.0,0.114]} ~ ~ ~

# With dialog UI for user control (1.21.6+):
# dialog → macro → scoreboard → storage → particle with values
```

### Critical Details
- Alpha range check: `Color.a > 0.113 && Color.a < 0.115` (float precision)
- Tinted_leaves particle A is ALWAYS 1.0 (bug) — use entity_effect only
- RESOLUTION_FACTOR=2 for 2×2 pixel area is enough for transmission
- View bobbing fix: use `-cornerOffset-0.5` for ndcCornerOffset calculation
- Requires "Fabulous" graphics (transparency.json is the active post pipeline)

## Shader Key Data Extraction (轩宇1725 series)

From `ModelViewMat` and `ProjMat`, extract game state without any data pack input:
```glsl
// Player yaw (rotation):
float yaw = atan(ModelViewMat[2][0] / ModelViewMat[0][0]);

// Player pitch:
float pitch = atan(ModelViewMat[1][2] / ModelViewMat[1][1]);

// Field of view (degrees):
float fov = degrees(atan(1.0 / ProjMat[1][1]) * 2.0);

// Aspect ratio:
float aspect = ProjMat[1][1] / ProjMat[0][0];

// Near plane distance:
float near = ProjMat[3][2] / (1.0 - ProjMat[2][2]);

// Far plane distance:
float far = -ProjMat[3][2] / (1.0 + ProjMat[2][2]);

// Is GUI (orthographic projection)?
bool isGui = (ProjMat[2][3] == 0.0);

// Camera block position (1.21.11+): CameraBlockPos (ivec3)
// Camera sub-block offset (1.21.11+): CameraOffset (vec3)

// Game time [0,1] cycling every 20min: GameTime (float)

// Screen dimensions: ScreenSize (vec2, pixels)

// Enchantment glint intensity: GlintAlpha (float)
```

### Shader Uniform Blocks (1.21.6+)
```
globals.glsl:        Globals { CameraBlockPos, CameraOffset, ScreenSize, GlintAlpha, GameTime, MenuBlurRadius, UseRgss }
fog.glsl:            Fog { FogColor, FogEnvironmentalStart/End, FogRenderDistanceStart/End, FogSkyEnd, FogCloudsEnd }
dynamictransforms.glsl: DynamicTransforms { ModelViewMat, ColorModulator, ModelOffset, TextureMat }
projection.glsl:     Projection { ProjMat }
lightmap.fsh:        LightmapInfo { AmbientLightFactor, SkyFactor, BlockFactor, NightVisionFactor, DarknessScale, DarkenWorldFactor, BrightnessFactor, SkyLightColor, AmbientColor }
```

### GLSL Column-Major Trap
GLSL stores matrices column-major. When constructing matrices in code:
```glsl
// Written in code as rows → interpreted as COLUMNS:
mat4 m = mat4(
    1.0, 2.0, 3.0, 4.0,   // COLUMN 0
    5.0, 6.0, 7.0, 8.0,   // COLUMN 1
    ...                    // etc.
);
// Always TRANSPOSE your math-on-paper matrices before coding!
```
```
