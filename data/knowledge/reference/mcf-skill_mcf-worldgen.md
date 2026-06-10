---
name: mcf-worldgen
description: Create and modify Minecraft Java Edition world generation definitions. Use when working with custom dimensions, biomes, configured/placed features, structures, template pools, noise settings, density functions, carvers, or world presets. Covers all worldgen JSON formats for version 26.1.2.
license: MIT
compatibility: opencode
metadata:
  version: "1.0"
  game-version: "26.1.2"
  category: minecraft-datapack
---

# Minecraft Custom World Generation

## File Location
World generation files are under: `data/<namespace>/worldgen/`

```
worldgen/
├── biome/                          # Biome definitions
├── configured_carver/              # Cave/canyon carvers
├── configured_feature/             # Configured features
├── density_function/               # Density functions
├── flat_level_generator_preset/    # Superflat presets
├── multi_noise_biome_source_parameter_list/ # Biome distribution
├── noise/                          # Noise definitions
├── noise_settings/                 # Noise settings (terrain shape)
├── placed_feature/                 # Placed features
├── processor_list/                 # Structure processors
├── structure/                      # Structure definitions
├── structure_set/                  # Structure sets (placement)
├── template_pool/                  # Jigsaw template pools
└── world_preset/                   # World presets
```

Note: Worldgen definitions are **NOT hot-reloadable** - must re-enter world.

## Dimension Definition
`data/<namespace>/dimension/<name>.json`

```json
{
  "type": "minecraft:overworld",
  "generator": {
    "type": "minecraft:noise",
    "settings": "minecraft:overworld",
    "biome_source": {
      "type": "minecraft:multi_noise",
      "preset": "minecraft:overworld"
    }
  }
}
```

Generator types: `minecraft:noise`, `minecraft:flat`, `minecraft:debug`

### Dimension Type
`data/<namespace>/dimension_type/<name>.json`

```json
{
  "ultrawarm": false,
  "natural": true,
  "coordinate_scale": 1.0,
  "has_skylight": true,
  "has_ceiling": false,
  "ambient_light": 0.0,
  "monster_spawn_light_level": { "type": "minecraft:uniform", "min_inclusive": 0, "max_inclusive": 7 },
  "monster_spawn_block_light_limit": 0,
  "piglin_safe": false,
  "bed_works": true,
  "respawn_anchor_works": false,
  "has_raids": true,
  "logical_height": 384,
  "min_y": -64,
  "height": 384,
  "infiniburn": "#minecraft:infiniburn_overworld",
  "effects": "minecraft:overworld",
  "cloud_height": 192  # New in v26.1
}
```

## Biome Definition
`data/<namespace>/worldgen/biome/<name>.json`

```json
{
  "temperature": 0.8,
  "downfall": 0.4,
  "has_precipitation": true,
  "temperature_modifier": "none",
  "effects": {
    "sky_color": 7972607,
    "water_fog_color": 329011,
    "fog_color": 12638463,
    "water_color": 4159204,
    "foliage_color": 5877296,
    "grass_color": 8431444,
    "grass_color_modifier": "none",
    "music": {
      "sound": "minecraft:music.overworld.desert",
      "min_delay": 12000,
      "max_delay": 24000,
      "replace_current_music": false
    },
    "ambient_sound": "minecraft:ambient.cave",
    "additions_sound": {
      "sound": "minecraft:ambient.cave",
      "tick_chance": 0.001
    },
    "mood_sound": {
      "sound": "minecraft:ambient.cave",
      "tick_delay": 6000,
      "block_search_extent": 8,
      "offset": 2.0
    },
    "particle": {
      "options": { "type": "minecraft:ash" },
      "probability": 0.05
    }
  },
  "carvers": [
    "minecraft:cave",
    "minecraft:cave_extra_underground",
    "minecraft:canyon"
  ],
  "features": [
    ["minecraft:lake_lava_underground"],
    ["minecraft:forest_rock"],
    [],
    [],
    [],
    [],
    ["minecraft:ore_dirt"],
    ["minecraft:ore_gravel"],
    ["minecraft:ore_coal_upper"],
    ["minecraft:ore_iron_upper"],
    ["minecraft:ore_gold"]
  ],
  "creature_spawn_probability": 0.1,
  "spawners": {
    "monster": [
      {
        "type": "minecraft:zombie",
        "weight": 100,
        "minCount": 4,
        "maxCount": 4
      }
    ],
    "creature": [...],
    "ambient": [...],
    "underground_water_creature": [...],
    "water_creature": [...],
    "water_ambient": [...],
    "misc": [...]
  }
}
```

### Features Array Index
Each index represents a generation step:
- 0: Raw generation
- 1: Lakes
- 2: Local modifications
- 3: Underground structures
- 4: Surface structures
- 5: Strongholds
- 6: Underground ores
- 7: Underground ores (less common)
- 8: Underground ores (rare)
- 9: Vegetal decoration
- 10: Top layer modification

## Configured Feature
`data/<namespace>/worldgen/configured_feature/<name>.json`

```json
{
  "type": "minecraft:ore",
  "config": {
    "targets": [
      {
        "target": {
          "predicate_type": "minecraft:tag_match",
          "tag": "minecraft:stone_ore_replaceables"
        },
        "state": { "Name": "minecraft:iron_ore" }
      }
    ],
    "size": 9,
    "discard_chance_on_air_exposure": 0.5
  }
}
```

Common feature types: `ore`, `tree`, `flower`, `block_pile`, `lake`, `spring`, `random_patch`, `simple_block`, `vegetation_patch`, `glow_lichen`, `sculk_patch`, `netherrack_replace_blobs`, `basalt_pillar`, `delta_feature`, `geode`, `fossil`, `root_system`, `bamboo`, `huge_fungus`, `twisting_vines`, `weeping_vines`, `coral`, `sea_pickle`, `kelp`, `seagrass`, `dripstone_cluster`, `pointed_dripstone`, `large_dripstone`, `underwater_magma`, `multiface_growth`, `forest_rock`, `ice_spike`, `iceberg`, `blue_ice`, `end_island`, `end_spike`, `end_gateway`, `chorus_plant`

## Placed Feature
`data/<namespace>/worldgen/placed_feature/<name>.json`

```json
{
  "feature": "minecraft:ore_iron",
  "placement": [
    {
      "type": "minecraft:count",
      "count": 20
    },
    {
      "type": "minecraft:in_square"
    },
    {
      "type": "minecraft:height_range",
      "height": {
        "type": "minecraft:trapezoid",
        "min_inclusive": { "absolute": -24 },
        "max_inclusive": { "absolute": 56 }
      }
    },
    {
      "type": "minecraft:biome"
    }
  ]
}
```

Placement types: `count`, `in_square`, `height_range`, `heightmap`, `biome`, `block_predicate_filter`, `surface_water_depth_filter`, `surface_relative_threshold_filter`, `rarity_filter`, `random_offset`, `noise_based_count`, `noise_threshold_count`, `count_on_every_layer`, `environment_scan`, `random_spread`, `cave_surface`, `rigid_body`

## Structure Definition
`data/<namespace>/worldgen/structure/<name>.json`

Types: `minecraft:jigsaw`, `minecraft:structure_template`, `minecraft:buried_treasure`, `minecraft:ruined_portal`, `minecraft:ocean_ruin`, `minecraft:shipwreck`, `minecraft:end_city`, `minecraft:woodland_mansion`, `minecraft:fortress`, `minecraft:swamp_hut`, `minecraft:igloo`, `minecraft:desert_pyramid`, `minecraft:jungle_temple`

### Jigsaw Structure
```json
{
  "type": "minecraft:jigsaw",
  "biomes": "#minecraft:has_structure/village_plains",
  "step": "surface_structures",
  "spawn_overrides": {},
  "terrain_adaptation": "beard_thin",
  "start_pool": "minecraft:village/plains/town_centers",
  "size": 6,
  "start_height": {
    "absolute": 0
  },
  "project_start_to_heightmap": "WORLD_SURFACE_WG",
  "max_distance_from_center": 80,
  "use_expansion_hack": true
}
```

## Template Pool (Jigsaw)
`data/<namespace>/worldgen/template_pool/<name>.json`

```json
{
  "fallback": "minecraft:village/plains/terminators",
  "elements": [
    {
      "weight": 1,
      "element": {
        "element_type": "minecraft:legacy_single_pool_element",
        "location": "minecraft:village/plains/houses/plains_small_house_1",
        "processors": "minecraft:mossify_10_percent",
        "projection": "rigid"
      }
    }
  ]
}
```

Element types: `minecraft:single_pool_element`, `minecraft:list_pool_element`, `minecraft:legacy_single_pool_element`, `minecraft:empty_pool_element`
Projections: `rigid`, `terrain_matching`, `terrain_adaptive`

## Processor List
`data/<namespace>/worldgen/processor_list/<name>.json`

```json
{
  "processors": [
    {
      "processor_type": "minecraft:rule",
      "rules": [
        {
          "input_predicate": {
            "predicate_type": "minecraft:random_block_match",
            "block": "minecraft:cobblestone",
            "probability": 0.1
          },
          "location_predicate": { "predicate_type": "minecraft:always_true" },
          "output_state": { "Name": "minecraft:mossy_cobblestone" }
        }
      ]
    }
  ]
}
```

Processor types: `minecraft:rule`, `minecraft:block_rot`, `minecraft:block_age`, `minecraft:protected_blocks`, `minecraft:capped`, `minecraft:blackstone_replace`

## Structure Set
`data/<namespace>/worldgen/structure_set/<name>.json`

```json
{
  "structures": [
    {
      "structure": "minecraft:village_plains",
      "weight": 1
    }
  ],
  "placement": {
    "type": "minecraft:random_spread",
    "salt": 10387312,
    "spacing": 34,
    "separation": 8,
    "spread_type": "triangular"
  }
}
```

Placement types: `minecraft:random_spread`, `minecraft:concentric_rings`

## Noise Settings
`data/<namespace>/worldgen/noise_settings/<name>.json`

Controls terrain shape:
```json
{
  "sea_level": 63,
  "disable_mob_generation": false,
  "aquifers_enabled": true,
  "ore_veins_enabled": true,
  "legacy_random_source": false,
  "default_block": { "Name": "minecraft:stone" },
  "default_fluid": { "Name": "minecraft:water", "Properties": { "level": "0" } },
  "noise": {
    "min_y": -64,
    "height": 384,
    "size_horizontal": 1,
    "size_vertical": 2
  },
  "noise_router": {
    "barrier": 0,
    "fluid_level_floodedness": "minecraft:overworld/floodedness",
    "fluid_level_spread": 0,
    "lava": "minecraft:overworld/lava",
    "temperature": "minecraft:overworld/temperature",
    "vegetation": "minecraft:overworld/vegetation",
    "continents": "minecraft:overworld/continents",
    "erosion": "minecraft:overworld/erosion",
    "depth": "minecraft:overworld/depth",
    "ridges": "minecraft:overworld/ridges",
    "initial_density_without_jaggedness": "minecraft:overworld/base_3d_noise",
    "final_density": "minecraft:overworld/base_3d_noise",
    "vein_toggle": 0,
    "vein_ridged": 0,
    "vein_gap": 0
  },
  "spawn_target": [],
  "surface_rule": {
    "type": "minecraft:sequence",
    "sequence": [
      {
        "type": "minecraft:condition",
        "if_true": {
          "type": "minecraft:stone_depth",
          "offset": 0,
          "surface_type": "ceiling",
          "add_surface_depth": false,
          "secondary_depth_range": 0
        },
        "then_run": {
          "type": "minecraft:block",
          "result_state": { "Name": "minecraft:stone" }
        }
      }
    ]
  }
}
```

## Density Function
`data/<namespace>/worldgen/density_function/<name>.json`

```json
{
  "type": "minecraft:add",
  "argument1": "minecraft:overworld/base_3d_noise",
  "argument2": 0.05
}
```

Types: `add`, `multiply`, `min`, `max`, `abs`, `square`, `cube`, `half_negative`, `quarter_negative`, `squeeze`, `noise`, `shifted_noise`, `range_choice`, `constant`, `flat_cache`, `cache_2d`, `cache_once`, `interpolated`, `blend_alpha`, `blend_offset`, `beardifier`, `old_blend_noise`, `y_clamped_gradient`, `surface_depth`, `weird_scaled_sampler`, `shift_a`, `shift_b`, `shift`, `slide`, `spline`

## World Preset
`data/<namespace>/worldgen/world_preset/<name>.json`

```json
{
  "dimensions": {
    "minecraft:overworld": {
      "type": "minecraft:overworld",
      "generator": {
        "type": "minecraft:noise",
        "settings": "minecraft:overworld",
        "biome_source": {
          "type": "minecraft:multi_noise",
          "preset": "minecraft:overworld"
        }
      }
    },
    "minecraft:the_nether": {
      "type": "minecraft:the_nether",
      "generator": {
        "type": "minecraft:noise",
        "settings": "minecraft:nether",
        "biome_source": {
          "type": "minecraft:multi_noise",
          "preset": "minecraft:nether"
        }
      }
    },
    "minecraft:the_end": {
      "type": "minecraft:the_end",
      "generator": {
        "type": "minecraft:noise",
        "settings": "minecraft:end",
        "biome_source": {
          "type": "minecraft:the_end"
        }
      }
    }
  }
}
```

## Multi-Noise Biome Source Parameter List
`data/<namespace>/worldgen/multi_noise_biome_source_parameter_list/<name>.json`

```json
{
  "preset": "minecraft:overworld",
  "biomes": [
    {
      "biome": "minecraft:plains",
      "parameters": {
        "temperature": [-0.45, 0.55],
        "humidity": [-0.35, 0.35],
        "continentalness": [-0.19, 0.5],
        "erosion": [-1.0, 1.0],
        "weirdness": [-1.0, -0.3],
        "depth": 0,
        "offset": 0
      }
    }
  ]
}
```

## Noise
`data/<namespace>/worldgen/noise/<name>.json`

```json
{
  "firstOctave": -7,
  "amplitudes": [1.0, 1.0]
}
```

## Carver
`data/<namespace>/worldgen/configured_carver/<name>.json`

```json
{
  "type": "minecraft:cave",
  "config": {
    "probability": 0.14285715,
    "y": {
      "type": "minecraft:uniform",
      "min_inclusive": { "absolute": 8 },
      "max_inclusive": { "absolute": 180 }
    },
    "yScale": { "type": "minecraft:uniform", "min_inclusive": 0.0, "max_exclusive": 0.5 },
    "lava_level": { "above_bottom": 10 },
    "horizontal_radius_multiplier": { "type": "minecraft:uniform", "min_inclusive": 1.0, "max_exclusive": 1.0 },
    "vertical_radius_multiplier": { "type": "minecraft:uniform", "min_inclusive": 1.0, "max_exclusive": 1.0 },
    "floor_level": { "type": "minecraft:uniform", "min_inclusive": -1.0, "max_exclusive": -0.4 }
  }
}
```

Carver types: `minecraft:cave`, `minecraft:canyon`, `minecraft:nether_cave`

## Block Predicates (Used in Features & Processors)
```json
{ "predicate_type": "minecraft:tag_match", "tag": "minecraft:stone_ore_replaceables" }
{ "predicate_type": "minecraft:block_match", "block": "minecraft:stone" }
{ "predicate_type": "minecraft:random_block_match", "block": "minecraft:stone", "probability": 0.5 }
{ "predicate_type": "minecraft:always_true" }
{ "predicate_type": "minecraft:has_sturdy_face", "offset": [0, -1, 0] }
{ "predicate_type": "minecraft:matching_blocks", "blocks": ["minecraft:stone"], "offset": [0, -1, 0] }
{ "predicate_type": "minecraft:solid", "offset": [0, -1, 0] }
{ "predicate_type": "minecraft:inside_world_bounds", "offset": [0, 0, 0] }
{ "predicate_type": "minecraft:unobstructed", "offset": [0, 0, 0] }
```

## Number Providers (Worldgen)
```json
// Constant
{ "type": "minecraft:constant", "value": 5 }
{ "type": "minecraft:constant", "value": { "type": "minecraft:uniform", "min_inclusive": 1, "max_inclusive": 3 } }

// Uniform
{ "type": "minecraft:uniform", "value": { "min_inclusive": 1, "max_inclusive": 10 } }

// Biased to bottom
{ "type": "minecraft:biased_to_bottom", "value": { "min_inclusive": 1, "max_inclusive": 10 } }

// Clamped
{ "type": "minecraft:clamped", "value": { "min_inclusive": 0, "max_inclusive": 10, "source": { "type": "minecraft:uniform", "min_inclusive": -5, "max_inclusive": 20 } } }

// Clamped normal
{ "type": "minecraft:clamped_normal", "value": { "min": 0, "max": 10, "mean": 5, "deviation": 2 } }

// Weighted list
{ "type": "minecraft:weighted_list", "distribution": [{ "data": 1, "weight": 5 }, { "data": 3, "weight": 2 }] }
```

## Height Providers
```json
{ "type": "minecraft:constant", "value": { "absolute": 64 } }
{ "type": "minecraft:uniform", "min_inclusive": { "absolute": 0 }, "max_inclusive": { "absolute": 256 } }
{ "type": "minecraft:biased_to_bottom", "min_inclusive": { "absolute": 0 }, "max_inclusive": { "absolute": 256 } }
{ "type": "minecraft:very_biased_to_bottom", "min_inclusive": { "absolute": 0 }, "max_inclusive": { "absolute": 256 } }
{ "type": "minecraft:trapezoid", "min_inclusive": { "absolute": 0 }, "max_inclusive": { "absolute": 256 }, "plateau": 0 }
```

Vertical anchors:
```json
{ "absolute": 64 }
{ "above_bottom": 10 }
{ "below_top": 10 }
```

## Block State Providers
```json
{ "type": "minecraft:simple_state_provider", "state": { "Name": "minecraft:stone" } }
{ "type": "minecraft:weighted_state_provider", "entries": [...] }
{ "type": "minecraft:noise_provider", "noise": { "firstOctave": -7, "amplitudes": [1.0] }, "states": [...], "scale": 0.02 }
{ "type": "minecraft:noise_threshold_provider", "noise": {...}, "states": [...], "threshold": 0.0, "high_chance": 0.5, "scale": 0.02 }
{ "type": "minecraft:dual_noise_provider", "noise": {...}, "variety": 6, "states": [...], "slow_noise": {...}, "slow_scale": 0.005 }
{ "type": "minecraft:randomized_int_state_provider", "source": {...}, "property": "age", "values": { "type": "minecraft:uniform", "min_inclusive": 0, "max_inclusive": 3 } }
{ "type": "minecraft:rule_based_state_provider", "rules": [...] }  # New in v26.1
```
