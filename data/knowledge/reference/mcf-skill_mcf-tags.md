---
name: mcf-tags
description: Create and modify Minecraft Java Edition tag definitions. Use when grouping game elements (blocks, items, entities, functions, biomes, etc.) for use in recipes, loot tables, predicates, commands, and world generation. Covers tag file format, loading behavior, and all available tag types for version 26.1.2.
license: MIT
compatibility: opencode
metadata:
  version: "1.0"
  game-version: "26.1.2"
  category: minecraft-datapack
---

# Minecraft Tags (Data Pack Tags)

## File Location
`data/<namespace>/tags/<registry_path>/<tag_name>.json`

For functions (not a registry): `data/<namespace>/tags/function/<tag_name>.json`

## Tag File Format
```json
{
  "replace": false,
  "values": [
    "minecraft:oak_log",
    "minecraft:birch_log",
    "#namespace:other_tag",
    { "id": "optional:item", "required": false }
  ]
}
```

Fields:
- **replace** (default: false): `true` = completely override lower-priority tags; `false` = merge
- **values** (required): Array of entries
- **required** (default: true): `false` = silently ignore missing entries

### Entry Types
Each entry can be:
```json
// Simple ID
"namespace:value"

// Tag reference (with # prefix)
"#namespace:other_tag"

// Object with optional flag
{ "id": "namespace:value", "required": false }
```

### Tag ID Format
When referencing tags in commands, recipes, etc., prefix with `#`:
```
#minecraft:logs          # Block tag
#namespace:my_functions   # Function tag
#minecraft:skeletons      # Entity type tag
```

## Loading & Priority
- Load bottom-up (higher data pack priority overrides lower)
- If upper `replace: true`, lower data is completely discarded
- If upper `replace: false`, values are merged
- Invalid lower tag (missing entries) makes upper tag invalid too
- Circular tag references cause load failure

### Extension vs Replacement Example
```json
// Extend (append to existing):
// data/minecraft/tags/block/sword_efficient.json
{ "values": ["#minecraft:wool"] }

// Replace (override completely):
// data/minecraft/tags/block/beacon_base_blocks.json
{ "replace": true, "values": ["minecraft:lodestone"] }
```

## Available Tag Types (v26.1.2)

### Game Element Tags
| Registry Path | Description |
|---|---|
| `block` | Block tags |
| `item` | Item tags |
| `entity_type` | Entity type tags |
| `fluid` | Fluid tags |
| `game_event` | Game event tags |

### Definition Tags
| Registry Path | Description |
|---|---|
| `banner_pattern` | Banner pattern tags |
| `chat_type` | Chat type tags |
| `damage_type` | Damage type tags |
| `dialog` | Dialog tags |
| `enchantment` | Enchantment tags |
| `instrument` | Goat horn instrument tags |
| `painting_variant` | Painting variant tags |
| `point_of_interest_type` | Point of interest type tags |
| `potion` | Potion effect tags |
| `timeline` | Timeline tags |
| `villager_trade` | Villager trade tags |

### World Generation Tags
| Registry Path | Description |
|---|---|
| `worldgen/biome` | Biome tags |
| `worldgen/configured_feature` | Configured feature tags |
| `worldgen/flat_level_generator_preset` | Superflat preset tags |
| `worldgen/structure` | Structure tags |
| `worldgen/world_preset` | World preset tags |

### Function Tags
| Registry Path | Description |
|---|---|
| `function` | Function tags (not a registry) |

No tags exist for: advancements, recipes, structure templates.

## Special Function Tags

### `#minecraft:load`
```json
// data/minecraft/tags/function/load.json
{
  "values": ["mypack:init", "mypack:setup"]
}
```
- Executed on world load, server start, and `/reload`
- Runs BEFORE players join - cannot target players
- Cannot use `/tellraw`, `/title`, etc. (no players online)

### `#minecraft:tick`
```json
// data/minecraft/tags/function/tick.json
{
  "values": ["mypack:tick_handler"]
}
```
- Executed at the start of EVERY game tick
- Use for continuous game loops
- Be careful with performance - minimize heavy operations

## Common Tag Usage Examples

### In Recipe (item tag)
```json
{
  "type": "minecraft:crafting_shaped",
  "key": { "#": { "tag": "minecraft:logs" } },
  "pattern": ["##", "##"],
  "result": { "id": "minecraft:crafting_table" }
}
```

### In Loot Table (entry with tag)
```json
{
  "type": "minecraft:tag",
  "name": "minecraft:arrows",
  "expand": false
}
```

### In Predicate
```json
{
  "condition": "minecraft:location_check",
  "predicate": {
    "biome": "#minecraft:is_forest"
  }
}
```

### In Command
```
execute if block ~ ~-1 ~ #minecraft:dirt run say Standing on dirt-type block
execute if entity @e[type=#minecraft:skeletons] run say Skeleton nearby
function #mypack:daily_tasks
```

### In World Generation (biome tag)
```json
// Referenced in multi_noise_biome_source_parameter_list
{
  "biome": "#minecraft:is_overworld"
}
```

### In Enchantment Definition
```json
{
  "supported_items": "#minecraft:enchantable/sword",
  "exclusive_set": "#minecraft:exclusive_set/damage"
}
```

## Important Tag Directories (v26.1.2)
Note: Tag directories use **singular** forms since 1.21:
- `tags/block` (NOT `tags/blocks`)
- `tags/item` (NOT `tags/items`)
- `tags/entity_type` (NOT `tags/entity_types`)
- `tags/fluid` (NOT `tags/fluids`)
- `tags/game_event` (NOT `tags/game_events`)
- `tags/function` (NOT `tags/functions`)
