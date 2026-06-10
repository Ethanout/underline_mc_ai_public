---
name: mcf-advancement
description: Create and modify Minecraft Java Edition advancement definitions. Use when building custom advancement trees, defining triggers, rewards, display settings, or unlocking recipes. Covers all 57+ trigger types with complete field reference.
license: MIT
compatibility: opencode
metadata:
  version: "1.0"
  game-version: "26.1.2"
  category: minecraft-datapack
---

# Minecraft Advancements

## File Location
`data/<namespace>/advancement/<path>.json`

## Root Structure
```json
{
  "criteria": { ... },
  "display": { ... },
  "parent": "namespace:parent_advancement",
  "requirements": [["criterion1"], ["criterion2"]],
  "rewards": { ... },
  "sends_telemetry_event": false
}
```

Fields:
- **criteria** (required): Map of criterion definitions
- **display**: Display info (optional for logic-only advancements)
- **parent**: Parent advancement namespace ID (omit for root)
- **requirements**: Logical OR-of-ANDs for criteria completion. Default: all criteria must complete
- **rewards**: Experience, functions, loot tables, recipes
- **sends_telemetry_event** (default: false): Only effective for `minecraft` namespace

## Display Settings
```json
{
  "display": {
    "title": { "translate": "advancements.story.root.title" },
    "description": { "translate": "advancements.story.root.description" },
    "icon": { "id": "minecraft:grass_block", "count": 1 },
    "background": "minecraft:textures/gui/advancements/backgrounds/stone.png",
    "frame": "task",
    "show_toast": true,
    "announce_to_chat": true,
    "hidden": false
  }
}
```

Frame types:
- `task` - Normal (rounded square, yellow text)
- `goal` - Goal (rounded, yellow text)
- `challenge` - Challenge (spiky, pink text)

### Background Texture
- Only for root advancements
- Path: `assets/<namespace>/textures/<path>.png`
- Reference in data pack: `<namespace>:<path>` (omit `textures/` and `.png`)

### Tab Creation
- Root advancements (no `parent`) with `display` create tabs
- Tab icon = root advancement icon
- Tab appears when any advancement in tree is earned

### Visibility Rules
An advancement shows in the menu if:
1. It is a root advancement, OR
2. Its parent is visible, AND it has `display` defined, AND `hidden` is `false`

Hidden advancements only appear after completion.

## Criteria Structure
```json
{
  "criteria": {
    "criterion_name": {
      "trigger": "minecraft:inventory_changed",
      "conditions": {
        "player": [{ "condition": "minecraft:entity_properties", "entity": "this", "predicate": {...} }],
        "items": [{ "items": ["minecraft:crafting_table"] }]
      }
    }
  }
}
```

## Trigger Types Reference

### Inventory & Items
| Trigger | Description |
|---------|-------------|
| `inventory_changed` | Player inventory changes |
| `item_durability_changed` | Any item damaged |
| `consume_item` | Item with `consumable` component consumed |
| `filled_bucket` | Bucket filled |
| `using_item` | Using an item (per tick) |
| `enchanted_item` | Item enchanted at table |
| `recipe_crafted` | Recipe used to craft |
| `recipe_unlocked` | Recipe unlocked |
| `pickup_item` | *(via thrown_item_picked_up_by_player)* |

### Blocks
| Trigger | Description |
|---------|-------------|
| `placed_block` | Block placed |
| `enter_block` | Entity collides with block (per tick) |
| `any_block_use` | Any block interaction |
| `default_block_use` | Empty-hand block interaction |
| `item_used_on_block` | Item used on block |
| `bee_nest_destroyed` | Beehive/bee nest destroyed |
| `slide_down_block` | Sliding down honey block |

### Combat & Damage
| Trigger | Description |
|---------|-------------|
| `player_hurt_entity` | Player damages entity |
| `player_killed_entity` | Player kills entity |
| `entity_hurt_player` | Player damaged |
| `entity_killed_player` | Entity kills player |
| `killed_by_arrow` | Arrow kills entity |
| `shot_crossbow` | Crossbow fired |
| `target_hit` | Projectile hits target block |
| `spear_mobs` | Spear charge attack |
| `player_sheared_equipment` | Sheared mob equipment |

### Movement & Dimension
| Trigger | Description |
|---------|-------------|
| `changed_dimension` | Player changes dimension |
| `fall_from_height` | Fall to ground |
| `fall_after_explosion` | Fall after explosion/knockback |
| `levitation` | Under levitation (per tick) |
| `nether_travel` | Return from Nether to Overworld |
| `started_riding` | Entity mounted |
| `ride_entity_in_lava` | Riding entity on lava (per tick) |
| `location` | Every 20 ticks (1 second) |

### Status Effects & Brewing
| Trigger | Description |
|---------|-------------|
| `effects_changed` | Status effect gained/removed |
| `brewed_potion` | Potion taken from brewing stand |
| `used_totem` | Totem of Undying used |
| `cured_zombie_villager` | Zombie villager cured |
| `construct_beacon` | Beacon structure changed |

### Entities & Interactions
| Trigger | Description |
|---------|-------------|
| `bred_animals` | Two animals breed |
| `tame_animal` | Animal tamed |
| `summoned_entity` | Iron golem/snow golem/wither/dragon summoned |
| `player_interacted_with_entity` | Player interacts with entity |
| `villager_trade` | Trade completed |
| `thrown_item_picked_up_by_entity` | Entity picks up thrown item |
| `thrown_item_picked_up_by_player` | Player picks up thrown item |
| `fishing_rod_hooked` | Fish caught or entity hooked |
| `allay_drop_item_on_block` | Allay drops item on block |

### Events & Special
| Trigger | Description |
|---------|-------------|
| `channeled_lightning` | Channeling trident spawns lightning |
| `lightning_strike` | Lightning bolt disappears |
| `slept_in_bed` | Player sleeps |
| `used_ender_eye` | Eye of Ender used |
| `voluntary_exile` | Raid triggered |
| `hero_of_the_village` | Raid victory |
| `impossible` | Cannot trigger naturally; use `/advancement grant` |
| `tick` | Every game tick |
| `player_generates_container_loot` | Container/suspicious block loot generated |
| `kill_mob_near_sculk_catalyst` | Sculk catalyst spreads |
| `avoid_vibration` | Vibration avoided by sneaking |
| `crafter_recipe_crafted` | Crafter ejects item |

### Common Condition Fields
Most triggers support:
```json
{
  "conditions": {
    "player": {
      "location": { "biome": "minecraft:desert" }
    }
  }
}
```

## Requirements Logic
```json
{
  "criteria": {
    "a": { "trigger": "minecraft:inventory_changed", "conditions": {"items":[{"items":["minecraft:diamond"]}]} },
    "b": { "trigger": "minecraft:inventory_changed", "conditions": {"items":[{"items":["minecraft:iron_ingot"]}]} }
  },
  "requirements": [
    ["a", "b"]  // Both must be true (AND)
  ]
}
```

OR logic:
```json
"requirements": [
  ["a"],  // a OR b
  ["b"]
]
```

## Rewards
```json
{
  "rewards": {
    "experience": 100,
    "function": "namespace:reward_function",
    "loot": ["namespace:reward_loot_table"],
    "recipes": ["namespace:unlocked_recipe"]
  }
}
```
- **experience**: XP directly added (not orbs)
- **function**: Executed as the player
- **loot**: Loot table given to player (uses `this_entity`=player context)
- **recipes**: Recipes unlocked

## Complete Example
```json
{
  "display": {
    "icon": { "id": "minecraft:diamond" },
    "title": "Diamond Get!",
    "description": "Obtain a diamond",
    "frame": "task",
    "show_toast": true,
    "announce_to_chat": true
  },
  "parent": "minecraft:story/iron_tools",
  "criteria": {
    "has_diamond": {
      "trigger": "minecraft:inventory_changed",
      "conditions": {
        "items": [{ "items": ["minecraft:diamond"] }]
      }
    }
  },
  "rewards": {
    "experience": 50
  }
}
```
