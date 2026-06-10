---
name: mcf-predicate
description: Create and modify Minecraft Java Edition predicate files and inline predicates. Use when building condition checks for loot tables, advancements, target selectors, or execute commands. Covers all 20+ predicate types with complete field reference.
license: MIT
compatibility: opencode
metadata:
  version: "1.0"
  game-version: "26.1.2"
  category: minecraft-datapack
---

# Minecraft Predicates (Loot Conditions)

## File Location
`data/<namespace>/predicate/<path>.json`

## Usage
- **Target selectors**: `@a[predicate=namespace:path]`
- **Execute command**: `execute if predicate namespace:path`
- **Inline predicate** (SNBT in commands):
```
execute if predicate {condition:"minecraft:location_check",predicate:{biome:"minecraft:plains"}}
```
- **Loot tables**: in `conditions` arrays within pools/entries
- **Advancements**: in trigger conditions and player predicates

## File Format
Object form (single predicate):
```json
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": { ... }
}
```

Array form (multiple = all_of):
```json
[
  { "condition": "minecraft:location_check", ... },
  { "condition": "minecraft:weather_check", ... }
]
```

## Predicate Types Reference

### Logical Predicates

**all_of** - Logical AND:
```json
{ "condition": "minecraft:all_of", "terms": [...] }
```

**any_of** - Logical OR:
```json
{ "condition": "minecraft:any_of", "terms": [...] }
```

**inverted** - Logical NOT:
```json
{ "condition": "minecraft:inverted", "term": { ... } }
```

**reference** - Reference another predicate file:
```json
{ "condition": "minecraft:reference", "name": "namespace:path" }
```

### Entity Predicates

**entity_properties** - Test entity properties:
```json
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "type": "minecraft:zombie",
    "location": { "biome": "minecraft:desert" },
    "flags": { "is_on_fire": true },
    "nbt": "{Health:20.0f}"
  }
}
```
Entity targets: `this`, `attacker`, `direct_attacker`, `attacking_player`, `target_entity`, `interacting_entity`

**entity_scores** - Test scoreboard scores:
```json
{
  "condition": "minecraft:entity_scores",
  "entity": "this",
  "scores": {
    "my_objective": { "min": 1, "max": 10 }
  }
}
```

### Location & Block Predicates

**location_check** - Test location with offset:
```json
{
  "condition": "minecraft:location_check",
  "offsetX": 0, "offsetY": 1, "offsetZ": 0,
  "predicate": {
    "block": { "blocks": ["minecraft:stone"] },
    "biome": "minecraft:plains",
    "dimension": "minecraft:overworld",
    "light": { "light": { "min": 7 } }
  }
}
```
Requires loot context `origin`.

**block_state_property** - Test block state:
```json
{
  "condition": "minecraft:block_state_property",
  "block": "minecraft:oak_door",
  "properties": { "half": "upper", "open": "true" }
}
```
Requires loot context `block_state`.

### Item Predicates

**match_tool** - Test the used tool/item:
```json
{
  "condition": "minecraft:match_tool",
  "predicate": {
    "items": ["minecraft:diamond_pickaxe"],
    "enchantments": [{ "enchantment": "minecraft:silk_touch", "levels": { "min": 1 } }]
  }
}
```
Requires loot context `tool`.

### Damage & Combat Predicates

**damage_source_properties** - Test damage source:
```json
{
  "condition": "minecraft:damage_source_properties",
  "predicate": {
    "tags": [{ "id": "minecraft:is_fire", "expected": true }],
    "is_direct": true
  }
}
```
Requires loot context `origin` and `damage_source`.

**killed_by_player** - Entity killed by player:
```json
{ "condition": "minecraft:killed_by_player" }
```

**survives_explosion** - 1/explosion_radius probability:
```json
{ "condition": "minecraft:survives_explosion" }
```
Passes automatically if no `explosion_radius` context.

### Random Predicates

**random_chance** - Random probability (0.0-1.0):
```json
{
  "condition": "minecraft:random_chance",
  "chance": { "type": "minecraft:constant", "value": 0.5 }
}
```

**random_chance_with_enchanted_bonus** - Enchantment-affected probability:
```json
{
  "condition": "minecraft:random_chance_with_enchanted_bonus",
  "enchantment": "minecraft:looting",
  "enchanted_chance": {
    "type": "minecraft:linear",
    "base": 0.025,
    "per_level_above_first": 0.01
  },
  "unenchanted_chance": 0.025
}
```
Requires `attacking_entity` context.

**table_bonus** - Enchantment-level-indexed probability table:
```json
{
  "condition": "minecraft:table_bonus",
  "enchantment": "minecraft:fortune",
  "chances": [0.0, 0.33, 0.5, 0.66, 1.0]
}
```
Requires `tool` context.

### Environment Predicates

**weather_check** - Test weather:
```json
{
  "condition": "minecraft:weather_check",
  "raining": true,
  "thundering": false
}
```

**time_check** - Test game time:
```json
{
  "condition": "minecraft:time_check",
  "clock": "minecraft:overworld",
  "value": { "min": 0, "max": 13000 },
  "period": 24000
}
```
With `period`, time is modulo'd first (e.g., period=24000 checks day time only).

**environment_attribute_check** (v26.1) - Test environment attribute:
```json
{
  "condition": "minecraft:environment_attribute_check",
  "attribute": "minecraft:temperature",
  "value": 0.8
}
```
Requires `origin` if attribute varies by location.

**enchantment_active_check** - Test if enchantment is active:
```json
{
  "condition": "minecraft:enchantment_active_check",
  "active": true
}
```
Requires `enchantment_active` context.

### Value Predicates

**value_check** - Compare a number provider against a range:
```json
{
  "condition": "minecraft:value_check",
  "value": { "type": "minecraft:score", "target": "this", "score": "my_obj" },
  "range": { "min": 0, "max": 100 }
}
```

## Common Patterns

### Check if player is in a specific biome
```json
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "location": { "biome": "minecraft:desert" }
  }
}
```

### Check if block below player is grass
```json
{
  "condition": "minecraft:location_check",
  "offsetY": -1,
  "predicate": {
    "block": { "blocks": ["minecraft:grass_block"] }
  }
}
```

### 50% chance
```json
{ "condition": "minecraft:random_chance", "chance": 0.5 }
```
