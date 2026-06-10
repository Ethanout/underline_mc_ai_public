---
name: mcf-item-modifier
description: Create and modify Minecraft Java Edition item modifier definitions. Use when working with item modification functions in loot tables or via /item modify command. Covers all 40+ modifier types with complete field reference for version 26.1.2.
license: MIT
compatibility: opencode
metadata:
  version: "1.0"
  game-version: "26.1.2"
  category: minecraft-datapack
---

# Minecraft Item Modifiers

## File Location
`data/<namespace>/item_modifier/<path>.json`

## Usage
```
item modify entity @s weapon.mainhand namespace:modifier_name
item replace block ~ ~ ~ container.0 from entity @s weapon.mainhand namespace:modifier_name
```

## Basic Format
Single modifier:
```json
{
  "function": "minecraft:set_count",
  "count": 1
}
```

Multiple modifiers (array):
```json
[
  { "function": "minecraft:set_count", "count": 1 },
  { "function": "minecraft:set_name", "name": "My Item" }
]
```

With conditions:
```json
{
  "conditions": [
    { "condition": "minecraft:random_chance", "chance": 0.5 }
  ],
  "function": "minecraft:set_count",
  "count": 64
}
```

## Modifier Types Reference

### Count & Quantity

**set_count** - Set or modify item count:
```json
{
  "function": "minecraft:set_count",
  "count": { "type": "minecraft:uniform", "min": 1, "max": 3 },
  "add": false
}
```

**limit_count** - Clamp item count:
```json
{
  "function": "minecraft:limit_count",
  "limit": { "min": 1, "max": 64 }
}
```

**enchanted_count_increase** - Enchantment-based count:
```json
{
  "function": "minecraft:enchanted_count_increase",
  "enchantment": "minecraft:fortune",
  "count": 1,
  "limit": 64
}
```

### Enchantment

**enchant_randomly** - Random enchantment:
```json
{
  "function": "minecraft:enchant_randomly",
  "only_compatible": true,
  "options": ["minecraft:sharpness", "minecraft:smite"]
}
```
Options can be a tag: `"#minecraft:on_random_loot"`

**enchant_with_levels** - Enchant at specific level:
```json
{
  "function": "minecraft:enchant_with_levels",
  "levels": { "type": "minecraft:uniform", "min": 5, "max": 30 },
  "options": "#minecraft:on_random_loot"
}
```

**set_enchantments** - Set specific enchantments:
```json
{
  "function": "minecraft:set_enchantments",
  "enchantments": {
    "minecraft:sharpness": 5,
    "minecraft:unbreaking": 3
  },
  "add": false
}
```

### Item Name & Lore

**set_name** - Set custom name (text component):
```json
{
  "function": "minecraft:set_name",
  "name": { "text": "Sword of Destiny", "color": "gold", "italic": false },
  "entity": "this"
}
```

**set_lore** - Set lore lines:
```json
{
  "function": "minecraft:set_lore",
  "lore": [
    { "text": "A legendary weapon", "color": "gray" }
  ],
  "mode": "replace_all"
}
```
Modes: `replace_all`, `append`, `insert`, `replace_section`

**copy_name** - Copy entity name to item:
```json
{
  "function": "minecraft:copy_name",
  "source": "block_entity"
}
```
Sources: `this`, `attacker`, `last_damage_player`, `block_entity`, `direct_attacker`

### Components & Data

**set_components** - Set item stack components:
```json
{
  "function": "minecraft:set_components",
  "components": {
    "minecraft:custom_name": "{\"text\":\"Custom\"}",
    "minecraft:enchantment_glint_override": true,
    "!minecraft:unbreakable": {}
  }
}
```
Use `!component_name` to remove a component.

**copy_components** - Copy components from source:
```json
{
  "function": "minecraft:copy_components",
  "source": "block_entity",
  "include": ["minecraft:custom_name"],
  "exclude": []
}
```

**set_custom_data** - Set custom_data component:
```json
{
  "function": "minecraft:set_custom_data",
  "tag": "{my_key: 123, my_string: \"hello\"}"
}
```
String or object format. Merges into existing `custom_data`.

**copy_custom_data** - Copy NBT to custom_data:
```json
{
  "function": "minecraft:copy_custom_data",
  "source": { "type": "context", "target": "block_entity" },
  "ops": [
    { "op": "replace", "source": "Items", "target": "stored_items" }
  ]
}
```
Ops: `replace`, `append`, `merge`. Source: `context` or `storage`.

### Damage & Durability

**set_damage** - Set durability ratio:
```json
{
  "function": "minecraft:set_damage",
  "damage": 0.5,
  "add": false
}
```
`damage` is a ratio (0.0-1.0). `add=true` makes it additive.

### Contents & Container

**set_contents** - Set container-like contents:
```json
{
  "function": "minecraft:set_contents",
  "component": "container",
  "entries": []
}
```
Component types: `container`, `bundle_contents`, `charged_projectiles`

**modify_contents** - Modify item contents:
```json
{
  "function": "minecraft:modify_contents",
  "component": "container",
  "modifier": { "function": "minecraft:set_count", "count": 1 }
}
```

### Books

**set_book_cover** - Set written book metadata:
```json
{
  "function": "minecraft:set_book_cover",
  "title": { "raw": "My Story", "filtered": "My Story" },
  "author": "PlayerName",
  "generation": 1
}
```

**set_writable_book_pages** - Set book & quill pages:
```json
{
  "function": "minecraft:set_writable_book_pages",
  "pages": ["Page 1", "Page 2"],
  "mode": "replace_all"
}
```

**set_written_book_pages** - Set signed book pages:
```json
{
  "function": "minecraft:set_written_book_pages",
  "pages": [{ "raw": "Content", "filtered": "Content" }],
  "mode": "replace_all"
}
```

### Fireworks

**set_fireworks** - Set firework rocket data:
```json
{
  "function": "minecraft:set_fireworks",
  "flight_duration": 3,
  "explosions": {
    "values": [{
      "shape": "large_ball",
      "colors": [16711680, 65280],
      "fade_colors": [255],
      "trail": true,
      "twinkle": false
    }],
    "mode": "replace_all"
  }
}
```

**set_firework_explosion** - Set firework star data (same fields as above, single explosion).

### Special Items

**set_potion** - Set potion type:
```json
{ "function": "minecraft:set_potion", "id": "minecraft:long_swiftness" }
```

**set_random_potion** - Random potion from options:
```json
{
  "function": "minecraft:set_random_potion",
  "options": [
    { "type": "minecraft:uniform", "min": 0, "max": 5 }
  ]
}
```

**set_ominous_bottle_amplifier** - Set ominous bottle level:
```json
{
  "function": "minecraft:set_ominous_bottle_amplifier",
  "amplifier": { "type": "minecraft:uniform", "min": 0, "max": 4 }
}
```

**set_stew_effect** - Set suspicious stew effects:
```json
{
  "function": "minecraft:set_stew_effect",
  "effects": [
    { "type": "minecraft:night_vision", "duration": 100 }
  ]
}
```

**set_instrument** - Set goat horn instrument:
```json
{ "function": "minecraft:set_instrument", "options": "#minecraft:goat_horns" }
```

**set_random_dyes** - Set random dye on dyeable item:
```json
{
  "function": "minecraft:set_random_dyes",
  "from_options": false
}
```

**exploration_map** - Convert to explorer map:
```json
{
  "function": "minecraft:exploration_map",
  "destination": "on_treasure_maps",
  "decoration": "target_point",
  "zoom": 2,
  "search_radius": 50,
  "skip_existing_chunks": true
}
```

**fill_player_head** - Set player head owner:
```json
{
  "function": "minecraft:fill_player_head",
  "entity": "this"
}
```

### Attributes & Banners

**set_attributes** - Set attribute modifiers:
```json
{
  "function": "minecraft:set_attributes",
  "modifiers": [{
    "attribute": "minecraft:generic.attack_damage",
    "operation": "add_value",
    "amount": 5,
    "id": "namespace:custom_bonus",
    "slot": "mainhand"
  }],
  "replace": true
}
```
Operations: `add_value` (Op0), `add_multiplied_base` (Op1), `add_multiplied_total` (Op2)

**set_banner_pattern** - Set banner patterns:
```json
{
  "function": "minecraft:set_banner_pattern",
  "patterns": [
    { "pattern": "minecraft:stripe_top", "color": "red" },
    { "pattern": "minecraft:stripe_bottom", "color": "blue" }
  ],
  "append": false
}
```

### Custom Model Data

**set_custom_model_data** - Set model override data:
```json
{
  "function": "minecraft:set_custom_model_data",
  "floats": { "values": [1.0, 2.5], "mode": "replace_all" },
  "flags": { "values": [true, false], "mode": "replace_all" },
  "strings": { "values": ["variant_a"], "mode": "append" },
  "colors": { "values": [16711680], "mode": "replace_all" }
}
```
Modes: `replace_all`, `replace_section`, `append`, `insert`

### Utility

**apply_bonus** - Enchantment-based bonus count:
```json
{
  "function": "minecraft:apply_bonus",
  "enchantment": "minecraft:fortune",
  "formula": "uniform_bonus_count",
  "parameters": { "bonusMultiplier": 1 }
}
```
Formulas: `uniform_bonus_count`, `ore_drops`, `binomial_with_bonus_count`

**copy_state** - Copy block state to item:
```json
{
  "function": "minecraft:copy_state",
  "block": "minecraft:oak_log",
  "properties": ["axis"]
}
```

**set_item** - Replace with different item:
```json
{
  "function": "minecraft:set_item",
  "item": "minecraft:stone"
}
```

**set_loot_table** - Set loot table on container item:
```json
{
  "function": "minecraft:set_loot_table",
  "name": "minecraft:chests/simple_dungeon",
  "seed": 12345
}
```

**furnace_smelt** - Convert to smelting result:
```json
{ "function": "minecraft:furnace_smelt" }
```

**explosion_decay** - Apply explosion decay (1/radius chance to vanish):
```json
{ "function": "minecraft:explosion_decay" }
```

**discard** - Remove the item stack:
```json
{ "function": "minecraft:discard" }
```

**toggle_tooltips** - Toggle tooltip visibility:
```json
{
  "function": "minecraft:toggle_tooltips",
  "toggles": {
    "minecraft:enchantments": false,
    "minecraft:stored_enchantments": true
  }
}
```

### Flow Control

**filtered** - Conditional modifier application:
```json
{
  "function": "minecraft:filtered",
  "item_filter": { "items": ["minecraft:diamond"] },
  "on_pass": { "function": "minecraft:set_count", "count": 64 },
  "on_fail": { "function": "minecraft:discard" }
}
```

**sequence** - Apply modifiers sequentially:
```json
{
  "function": "minecraft:sequence",
  "functions": [
    { "function": "minecraft:set_count", "count": 3 },
    { "function": "minecraft:enchant_randomly" }
  ]
}
```

**reference** - Reference another modifier file:
```json
{ "function": "minecraft:reference", "name": "namespace:other_modifier" }
```
