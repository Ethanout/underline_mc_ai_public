---
name: mcf-loot-table
description: Create and modify Minecraft Java Edition loot tables. Use when working with item drops, chest loot, entity drops, fishing loot, bartering, archaeology, or any loot generation. Covers pools, entries, conditions, functions, and loot context.
license: MIT
compatibility: opencode
metadata:
  version: "1.0"
  game-version: "26.1.2"
  category: minecraft-datapack
---

# Minecraft Loot Tables

## File Location
`data/<namespace>/loot_table/<path>.json`

## Root Structure
```json
{
  "type": "minecraft:generic",
  "random_sequence": "namespace:sequence_name",
  "functions": [],
  "pools": []
}
```

Fields:
- **type** (default: `generic`): Loot context parameter set for validation
- **random_sequence**: Named random sequence for deterministic loot generation
- **functions**: Item modifiers applied to ALL generated items
- **pools**: List of random pools, processed in order

## Loot Pools

```json
{
  "rolls": { "type": "minecraft:uniform", "min": 1, "max": 3 },
  "bonus_rolls": { "type": "minecraft:uniform", "min": 0, "max": 1 },
  "conditions": [],
  "functions": [],
  "entries": []
}
```

Fields:
- **rolls** (required): Number provider for base rolls
- **bonus_rolls** (default: 0): Extra rolls based on luck (player luck attribute + fishing_luck_bonus)
- **conditions**: Predicate list - ALL must pass for pool to be used
- **functions**: Item modifiers applied to every item from this pool
- **entries** (required): Loot entries to draw from

### Number Providers
```json
// Constant
{ "type": "minecraft:constant", "value": 5 }

// Uniform distribution
{ "type": "minecraft:uniform", "min": 1, "max": 3 }

// Binomial distribution
{ "type": "minecraft:binomial", "n": 5, "p": 0.5 }

// Storage-based (from command storage)
{ "type": "minecraft:storage", "storage": "namespace:key", "path": "value" }

// Score-based (from scoreboard)
{ "type": "minecraft:score", "target": { "type": "minecraft:fixed", "name": "player" }, "score": "objective" }
```

## Entry Types

### Single Entries (Singleton)

**item** - Generate a single item stack:
```json
{ "type": "minecraft:item", "name": "minecraft:diamond", "weight": 1, "functions": [] }
```

**loot_table** - Reference another loot table:
```json
{ "type": "minecraft:loot_table", "value": "minecraft:chests/simple_dungeon", "weight": 1 }
```

**dynamic** - Context-dependent generation:
```json
{ "type": "minecraft:dynamic", "name": "contents" }
// "sherds" - for decorated pots
// "contents" - for shulker boxes (drop contents to world)
```

**empty** - Generate nothing:
```json
{ "type": "minecraft:empty", "weight": 5 }
```

**slots** - Generate from item slot:
```json
{ "type": "minecraft:slots", "slot_source": { "type": "..." } }
```

**tag** - Generate items from a tag:
```json
{ "type": "minecraft:tag", "name": "minecraft:arrows", "expand": false }
// expand=false: single entry, generates one item from tag
// expand=true: composite entry, expands to one entry per tag item
```

### Composite Entries

**alternatives** - First passing child:
```json
{
  "type": "minecraft:alternatives",
  "children": [
    { "type": "minecraft:item", "name": "minecraft:diamond", "conditions": [...] },
    { "type": "minecraft:item", "name": "minecraft:iron_ingot" }
  ]
}
```

**group** - All children:
```json
{ "type": "minecraft:group", "children": [...] }
```

**sequence** - Children until one fails:
```json
{ "type": "minecraft:sequence", "children": [...] }
```

### Common Entry Fields
- **weight** (default: 1): Relative weight for random selection
- **quality** (default: 0): Luck-based weight modifier: `max(⌊weight + quality × luck⌋, 0)`
- **conditions**: Predicates - all must pass for entry to be in pool
- **functions**: Item modifiers applied to this entry's items

## Loot Context Parameters
Used for predicate validation. Common types:
- `generic` - No special parameters
- `block` - Has `origin`, `block_state`, `tool`, `explosion_radius`
- `entity` - Has `origin`, `this_entity`, `attacker`, `direct_attacker`, `attacking_player`, `damage_source`
- `chest` - Has `origin`
- `fishing` - Has `origin`, `tool`
- `gift` - Has `origin`, `this_entity`

## Custom Loot Table Assignment

### Container/Chest
```mcfunction
data merge block <pos> {LootTable: "namespace:path", LootTableSeed: 12345L}
```

### Entity Death Drops
```mcfunction
data merge entity @e[type=zombie,limit=1] {DeathLootTable: "namespace:path"}
```

### Via Command
```
loot spawn ~ ~ ~ loot namespace:path
loot give @p loot namespace:path
loot insert ~ ~ ~ loot namespace:path
```

## Built-in Loot Table Categories
- `archaeology/` - Suspicious block brushing
- `blocks/` - Block drops
- `brush/` - Brushing drops (armadillo)
- `carve/` - Carving drops (pumpkin)
- `charged_creeper/` - Charged creeper kills
- `chests/` - Structure chest loot
- `dispensers/` - Trial chamber dispensers
- `entities/` - Mob death drops
- `equipment/` - Trial spawner mob equipment
- `gameplay/` - Fishing, bartering, hero gifts, etc.
- `harvest/` - Harvest drops (beehive, berries, cave vines)
- `pots/` - Decorated pot contents
- `shearing/` - Shearing drops
- `spawners/` - Trial spawner rewards
