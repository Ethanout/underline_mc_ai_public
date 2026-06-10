---
name: mcf-enchantment
description: Create and modify Minecraft Java Edition enchantment definitions. Use when adding custom enchantments, configuring enchantment effects (value effects, entity effects, location-based effects), component-based effects, or enchantment properties. Covers the full enchantment data-driven system for version 26.1.2.
license: MIT
compatibility: opencode
metadata:
  version: "1.0"
  game-version: "26.1.2"
  category: minecraft-datapack
---

# Minecraft Enchantment Definitions

## File Location
`data/<namespace>/enchantment/<path>.json`

Note: Enchantment definitions are **NOT hot-reloadable** (`/reload` won't work). Must restart the server.

## Root Structure
```json
{
  "description": { "translate": "enchantment.minecraft.sharpness" },
  "anvil_cost": 1,
  "max_level": 5,
  "weight": 10,
  "min_cost": { "base": 1, "per_level_above_first": 11 },
  "max_cost": { "base": 21, "per_level_above_first": 11 },
  "supported_items": "#minecraft:enchantable/sword",
  "primary_items": "#minecraft:enchantable/sword",
  "slots": ["mainhand"],
  "exclusive_set": "#minecraft:exclusive_set/damage",
  "effects": { ... }
}
```

### Field Descriptions
- **description** (required): Text component for tooltip display
- **anvil_cost** (required, ≥0): XP cost per level when combining. Halved for books.
- **max_level** (required, 1-255): Maximum enchantment level
- **weight** (required, 1-1024): Selection weight for random enchantment
- **min_cost** (required): Minimum enchantment power level
- **max_cost** (required): Maximum enchantment power level
- **supported_items**: Items that can receive this via anvil (item ID, tag, or array)
- **primary_items**: Items that can receive this via enchanting table (subset of supported_items)
- **slots** (required): Equipment slot groups where enchantment is active
- **exclusive_set**: Incompatible enchantments (ID, tag, or array)
- **effects**: Enchantment effect components (see below)

### Cost Calculation
For level `n`, the power level is:
```
min_cost.base + min_cost.per_level_above_first * (n - 1)
```
to
```
max_cost.base + max_cost.per_level_above_first * (n - 1)
```

## Enchantment Effect Components

### Value Effect Components (modify numeric values)

**Plain value effects** (set with value effect):
```json
{
  "effects": {
    "minecraft:crossbow_charge_time": {
      "type": "minecraft:add",
      "value": { "type": "minecraft:linear", "base": -0.25, "per_level_above_first": -0.25 }
    }
  }
}
```

Available plain value components:
| Component ID | Modifies | Base Input |
|---|---|---|
| `crossbow_charge_time` | Charge time (seconds) | 1.25 |
| `trident_spin_attack_strength` | Riptide movement speed | 0 |

**Conditional value effects** (value effects with predicates):
```json
{
  "effects": {
    "minecraft:damage": [
      {
        "effect": {
          "type": "minecraft:add",
          "value": { "type": "minecraft:linear", "base": 1.5, "per_level_above_first": 0.5 }
        },
        "requirements": {
          "condition": "minecraft:entity_properties",
          "entity": "direct_attacking_entity",
          "predicate": { "type": "minecraft:player" }
        }
      }
    ]
  }
}
```

Conditional value components:
| Component ID | Modifies | Loot Context |
|---|---|---|
| `ammo_use` | Ammo consumption | `enchanted_item` |
| `block_experience` | Block XP drops | Based on block |
| `item_damage` | Durability loss | Based on action |
| `projectile_piercing` | Arrow piercing count | 0 |
| `repair_with_xp` | Mending repair amount | XP orb value |
| `armor_effectiveness` | Damage reduction ratio | Armor base |
| `damage` | Attack damage (enchantment attack power) | Base attack |
| `damage_protection` | Protection coefficient | 0 |
| `knockback` | Extra knockback | Base knockback |
| `smash_damage_per_fallen_block` | Mace smash damage/block | 0 |
| `mob_experience` | Mob XP when killed | Mob base XP |
| `fishing_luck_bonus` | Fishing luck | 0 |
| `fishing_time_reduction` | Fishing wait time reduction | 0 |
| `projectile_count` | Multishot projectile count | 1 |
| `projectile_spread` | Multishot spread angle | 0 |
| `trident_return_acceleration` | Loyalty acceleration | 0 |

**Targeted value effect** (attacker/victim):
```json
{
  "effects": {
    "minecraft:equipment_drops": [
      {
        "enchanted": "attacker",
        "effect": { "type": "minecraft:set", "value": 0.0 },
        "requirements": {}
      }
    ]
  }
}
```

### Entity Effect Components (trigger actions on entities)

**Conditional entity effects**:
| Component ID | Trigger | Affected Entity | Position |
|---|---|---|---|
| `tick` | Every game tick | This entity | Entity position |
| `post_piercing_attack` | After piercing attack | This entity | Entity position |
| `projectile_spawned` | Projectile fired | Projectile | Projectile position |
| `hit_block` | Mining/arrow hits block | Player/arrow | Block center |

**Targeted entity effects** (`post_attack`):
```json
{
  "effects": {
    "minecraft:post_attack": [
      {
        "enchanted": "attacker",
        "affected": "victim",
        "effect": {
          "type": "minecraft:apply_mob_effect",
          "to_apply": { "id": "minecraft:slowness", "duration": 100, "amplifier": 0 }
        },
        "requirements": {}
      }
    ]
  }
}
```

### Location-Based Effects
```json
{
  "effects": {
    "minecraft:location_changed": [
      {
        "effect": {
          "type": "minecraft:apply_mob_effect",
          "to_apply": { "id": "minecraft:speed", "duration": 20, "amplifier": 0 }
        },
        "requirements": {}
      }
    ]
  }
}
```
Triggers when block position changes, landing, or equipment change. Requires item in valid slot.

### Damage Immunity
```json
{
  "effects": {
    "minecraft:damage_immunity": [
      {
        "effect": {},
        "requirements": {
          "condition": "minecraft:damage_source_properties",
          "predicate": { "tags": [{ "id": "minecraft:is_fire", "expected": true }] }
        }
      }
    ]
  }
}
```

### Attribute Effects
```json
{
  "effects": {
    "minecraft:attributes": [
      {
        "type": "minecraft:add",
        "attribute": "minecraft:generic.max_health",
        "operation": "add_value",
        "amount": { "type": "minecraft:linear", "base": 2.0, "per_level_above_first": 2.0 },
        "id": "minecraft:enchantment.health_boost",
        "slot": "any"
      }
    ]
  }
}
```

### Unit Components (no data needed)
- `minecraft:prevent_armor_change` - `{}` - Prevents armor removal
- `minecraft:prevent_equipment_drop` - `{}` - Prevents death drop

### Crossbow Sound Component
```json
{
  "effects": {
    "minecraft:crossbow_charging_sounds": [
      {
        "start": "minecraft:item.crossbow.loading_start",
        "mid": "minecraft:item.crossbow.loading_middle",
        "end": "minecraft:item.crossbow.loading_end"
      }
    ]
  }
}
```

### Trident Sound Component
```json
{
  "effects": {
    "minecraft:trident_sound": ["minecraft:item.trident.throw"]
  }
}
```

## Value Effect Types

**all_of** - Sequential composition:
```json
{ "type": "minecraft:all_of", "effects": [...] }
```

**add** - valueEffectOutput(x) = x + levelFunction(level):
```json
{ "type": "minecraft:add", "value": { "type": "minecraft:linear", "base": 1.0, "per_level_above_first": 1.0 } }
```

**multiply** - valueEffectOutput(x) = x × levelFunction(level):
```json
{ "type": "minecraft:multiply", "factor": { "type": "minecraft:linear", "base": 1.5, "per_level_above_first": 0.5 } }
```

**set** - valueEffectOutput(x) = levelFunction(level):
```json
{ "type": "minecraft:set", "value": { "type": "minecraft:linear", "base": 3.0, "per_level_above_first": 0.0 } }
```

**remove_binomial** - Binomial reduction:
```json
{ "type": "minecraft:remove_binomial", "chance": { "type": "minecraft:linear", "base": 0.5, "per_level_above_first": 0.0 } }
```

**exponential** - valueEffectOutput(x) = x × base^exponent:
```json
{
  "type": "minecraft:exponential",
  "base": { "type": "minecraft:linear", "base": 1.1, "per_level_above_first": 0.0 },
  "exponent": { "type": "minecraft:linear", "base": 1.0, "per_level_above_first": 1.0 }
}
```

### Level-Dependent Value Types
```json
// Linear: base + per_level_above_first * (level - 1)
{ "type": "minecraft:linear", "base": 1.0, "per_level_above_first": 1.0 }

// Clamped linear: same but clamped to [min, max]
{ "type": "minecraft:clamped", "value": {...}, "min": 0.0, "max": 10.0 }

// Fraction: numerator / denominator
{ "type": "minecraft:fraction", "numerator": {...}, "denominator": {...} }

// Levels squared: level^2 + constant
{ "type": "minecraft:levels_squared", "added": 0.0 }

// Lookup table by level index:
{ "type": "minecraft:lookup", "values": [1.0, 2.5, 5.0], "fallback": 1.0 }
```

## Entity Effect Types
```json
{ "type": "minecraft:all_of", "effects": [...] }
{ "type": "minecraft:apply_exhaustion", "amount": {...} }
{ "type": "minecraft:apply_impulse", "direction": [0.0, 0.5, 1.0], "coordinate_scale": [0.0, 0.0, 1.0], "magnitude": {...} }
{ "type": "minecraft:apply_mob_effect", "to_apply": { "id": "minecraft:speed", "duration": 200, "amplifier": 1, "ambient": false, "show_particles": true, "show_icon": true } }
{ "type": "minecraft:change_item_damage", "amount": {...} }  # Negative = repair
{ "type": "minecraft:damage_entity", "damage_type": "minecraft:magic", "amount": {...} }
{ "type": "minecraft:explode", "attribute_to_user": false, "damage_type": "minecraft:explosion", "knockback_multiplier": 1.0, "immune_blocks": "#minecraft:incorrect_for_wooden_tool", "radius": {...}, "create_fire": false, "block_interaction": "none", "small_particles": {...}, "large_particles": {...}, "sound": "minecraft:entity.generic.explode" }
{ "type": "minecraft:ignite", "duration": {...} }
{ "type": "minecraft:play_sound", "sound": "minecraft:entity.player.levelup", "volume": 1.0, "pitch": 1.0 }
{ "type": "minecraft:replace_block", "block_state": { "Name": "minecraft:air" }, "offset": [0, 0, 0], "predicate": {...} }
{ "type": "minecraft:replace_disk", "radius": {...}, "height": 1, "block_state": { "Name": "minecraft:air" }, "predicate": {...} }
{ "type": "minecraft:run_function", "function": "namespace:path" }
{ "type": "minecraft:set_block_properties", "properties": { "lit": "true" }, "offset": [0, 0, 0] }
{ "type": "minecraft:spawn_particles", "particle": { "type": "minecraft:flame" }, "horizontal_position": {...}, "vertical_position": {...}, "horizontal_velocity": {...}, "vertical_velocity": {...}, "speed": 0.0 }
{ "type": "minecraft:summon_entity", "entity": "minecraft:lightning_bolt", "join_team": false }
```

## Complete Example (Custom Enchantment)
```json
{
  "description": { "text": "Life Steal", "color": "red" },
  "anvil_cost": 4,
  "max_level": 3,
  "weight": 5,
  "min_cost": { "base": 10, "per_level_above_first": 10 },
  "max_cost": { "base": 50, "per_level_above_first": 10 },
  "supported_items": "#minecraft:enchantable/sword",
  "slots": ["mainhand"],
  "exclusive_set": "#minecraft:exclusive_set/damage",
  "effects": {
    "minecraft:post_attack": [
      {
        "enchanted": "attacker",
        "affected": "attacker",
        "effect": {
          "type": "minecraft:apply_mob_effect",
          "to_apply": {
            "id": "minecraft:regeneration",
            "duration": 60,
            "amplifier": { "type": "minecraft:linear", "base": 0, "per_level_above_first": 0 }
          }
        }
      }
    ],
    "minecraft:damage": [
      {
        "effect": {
          "type": "minecraft:add",
          "value": { "type": "minecraft:linear", "base": 1.0, "per_level_above_first": 0.5 }
        }
      }
    ]
  }
}
```
