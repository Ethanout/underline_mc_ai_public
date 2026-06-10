---
name: mcf-recipe
description: Create and modify Minecraft Java Edition recipe definitions. Use when adding custom crafting recipes, smelting, blasting, smoking, campfire cooking, stonecutting, smithing, or the new dye/imbue recipe types. Covers all recipe types with complete field reference for version 26.1.2.
license: MIT
compatibility: opencode
metadata:
  version: "1.0"
  game-version: "26.1.2"
  category: minecraft-datapack
---

# Minecraft Recipes

## File Location
`data/<namespace>/recipe/<path>.json`

Note: Recipes have **no tags** - game does not load `data/<namespace>/tags/recipe/`.

## Recipe Types (v26.1.2)

| Type | Description |
|------|-------------|
| `crafting_shaped` | Shaped crafting (symmetric ok) |
| `crafting_shapeless` | Shapeless crafting |
| `crafting_transmute` | Type conversion (preserves components) |
| `crafting_dye` | Dyeing items |
| `crafting_imbue` | Imbuing (tipped arrows) |
| `smelting` | Furnace |
| `blasting` | Blast furnace |
| `smoking` | Smoker |
| `campfire_cooking` | Campfire |
| `stonecutting` | Stonecutter |
| `smithing_transform` | Smithing upgrade |
| `smithing_trim` | Armor trim |

### Removed in v26.1
- `crafting_special_armordye` (replaced by `crafting_dye`)
- `crafting_special_mapcloning`
- `crafting_special_tippedarrow` (replaced by `crafting_imbue`)

## Common Fields
```json
{
  "type": "minecraft:crafting_shaped",
  "group": "wooden_stairs",
  "category": "building",
  "show_notification": true,
  "result": {
    "id": "minecraft:oak_planks",
    "count": 4
  }
}
```

Category values: `building`, `redstone`, `equipment`, `misc`

## Shaped Recipe
```json
{
  "type": "minecraft:crafting_shaped",
  "category": "equipment",
  "key": {
    "#": "minecraft:stick",
    "X": "#minecraft:planks"
  },
  "pattern": [
    "X",
    "#",
    "#"
  ],
  "result": { "id": "minecraft:wooden_sword", "count": 1 }
}
```
- Pattern rows: max 3 strings, each max 3 chars
- Keys: single chars (not space)
- Ingredient format: single item ID, list of IDs, or tag `#namespace:tag`
- Auto-symmetry: mirror patterns work automatically

## Shapeless Recipe
```json
{
  "type": "minecraft:crafting_shapeless",
  "category": "equipment",
  "ingredients": [
    "minecraft:iron_ingot",
    "minecraft:flint"
  ],
  "result": { "id": "minecraft:flint_and_steel", "count": 1 }
}
```
- 1-9 ingredients
- Each can be: single item ID, list of IDs, or tag

## Transmute Recipe (Type Conversion)
```json
{
  "type": "minecraft:crafting_transmute",
  "category": "misc",
  "input": "minecraft:glass_bottle",
  "material": "minecraft:honey_bottle",
  "material_count": { "min": 1, "max": 4 },
  "result": { "id": "minecraft:honey_bottle" },
  "add_material_to_result_count": false
}
```
- Preserves item components from input
- `material_count`: must be `[1,8]` sub-interval
- Does not work when input and result are the same item

## Dye Recipe (v26.1)
```json
{
  "type": "minecraft:crafting_dye",
  "category": "misc",
  "target": "#minecraft:dyeable",
  "dye": "#minecraft:dyes",
  "result": { "id": "minecraft:leather_chestplate" }
}
```
- At least 2 items in crafting grid
- First `target` item = input (multiple targets = no output)
- Other items must match `dye` and have `dye` component
- Preserves existing `dyed_color`, blends with input dyes

## Imbue Recipe (v26.1)
```json
{
  "type": "minecraft:crafting_imbue",
  "category": "misc",
  "input": "minecraft:arrow",
  "ingredient": {
    "item": "minecraft:lingering_potion"
  },
  "result": { "id": "minecraft:tipped_arrow", "count": 8 }
}
```
- Used for tipped arrows from lingering potions
- Transfers potion effects from ingredient to result

## Smelting/Blasting/Smoking/Campfire
```json
{
  "type": "minecraft:smelting",
  "category": "food",
  "ingredient": { "item": "minecraft:beef" },
  "result": { "id": "minecraft:cooked_beef" },
  "experience": 0.35,
  "cookingtime": 200
}
```
- `cookingtime`: 200 (furnace), 100 (blast/smoker), 600 (campfire)
- `experience`: XP reward

## Stonecutting
```json
{
  "type": "minecraft:stonecutting",
  "ingredient": { "item": "minecraft:stone" },
  "result": { "id": "minecraft:stone_slab", "count": 2 }
}
```

## Smithing Transform (Upgrade)
```json
{
  "type": "minecraft:smithing_transform",
  "template": { "item": "minecraft:netherite_upgrade_smithing_template" },
  "base": { "item": "minecraft:diamond_sword" },
  "addition": { "item": "minecraft:netherite_ingot" },
  "result": { "id": "minecraft:netherite_sword" }
}
```

## Smithing Trim
```json
{
  "type": "minecraft:smithing_trim",
  "template": { "tag": "minecraft:trim_templates" },
  "base": { "tag": "minecraft:trimmable_armor" },
  "addition": { "tag": "minecraft:trim_materials" }
}
```

## Special/Custom Recipes
Custom recipes (like book cloning, map copying, firework star fading, shield decoration, banner duplication, repair) use fixed types:
- `crafting_special_shielddecoration`
- `crafting_special_bannerduplicate`
- `crafting_special_bookcloning`
- `crafting_special_firework_rocket`
- `crafting_special_firework_star`
- `crafting_special_firework_star_fade`
- `crafting_special_mapcloning` (still exists for non-Java)
- `crafting_special_repairitem`
- `crafting_special_suspiciousstew`
- `crafting_special_tippedarrow` (replaced by imbue in 26.1)

## Item Result with Components (v26.1)
```json
{
  "result": {
    "id": "minecraft:diamond_sword",
    "count": 1,
    "components": {
      "minecraft:enchantments": {
        "levels": { "minecraft:sharpness": 5 }
      },
      "minecraft:custom_name": "{\"text\":\"Legendary Sword\"}"
    }
  }
}
```

## Ingredient Formats
```json
// Single item
{ "item": "minecraft:stick" }

// Tag
{ "tag": "minecraft:planks" }

// Multiple options (any of)
[
  "minecraft:oak_planks",
  "minecraft:birch_planks"
]

// With count (some recipe types)
{ "item": "minecraft:stick", "count": 2 }
```
