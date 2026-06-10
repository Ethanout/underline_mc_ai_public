---
name: mcf-commands
description: Complete reference for all Minecraft Java Edition commands (v26.1.2). Use when writing .mcfunction files, command blocks, or any command execution. Covers all subcommands of /execute, /scoreboard, /data, /item, and every Java Edition command with syntax and examples.
license: MIT
compatibility: opencode
metadata:
  version: "1.0"
  game-version: "26.1.2"
  category: minecraft-datapack
---

# Minecraft Commands Reference

## Command Syntax Notation
- `literal` - Type exactly as shown
- `<argument>` - Required argument
- `[optional]` - Optional argument
- `(a|b)` - Required choice between a or b
- `[a|b]` - Optional choice between a or b

## /execute - Context Manipulation

### Modifier Subcommands
```
execute align <axes>                 -- Align position to block grid (x/y/z combo)
execute anchored (eyes|feet)         -- Set execution anchor
execute as <targets>                 -- Set executor (forks per entity)
execute at <targets>                 -- Set position/rotation/dimension (forks)
execute facing <pos>                 -- Set rotation facing coordinate
execute facing entity <targets> (eyes|feet) -- Set rotation facing entity
execute in <dimension>               -- Set execution dimension
execute on (attacker|controller|leasher|origin|owner|passengers|target|vehicle) -- JE only
execute positioned <pos>             -- Set execution position
execute positioned as <targets>       -- Set position to entity position
execute positioned over <heightmap>   -- JE: world_surface/motion_blocking/motion_blocking_no_leaves/ocean_floor
execute rotated <yaw> <pitch>        -- Set execution rotation
execute rotated as <targets>          -- Set rotation to entity rotation
execute summon <entity>              -- JE: summon entity as executor
```

### Condition Subcommands
```
execute (if|unless) biome <pos> <biome>                   -- JE: check biome at position
execute (if|unless) block <pos> <block>                   -- Check block at position
execute (if|unless) blocks <start> <end> <dest> (all|masked) -- Compare regions
execute (if|unless) data block <pos> <path>                -- JE: check NBT path on block
execute (if|unless) data entity <target> <path>             -- JE: check NBT path on entity
execute (if|unless) data storage <id> <path>                -- JE: check NBT path in storage
execute (if|unless) dimension <dimension>                   -- JE: check current dimension
execute (if|unless) entity <targets>                       -- Check entity existence
execute (if|unless) function <name>                        -- JE: check function non-zero return
execute (if|unless) items block <pos> <slots> <predicate>  -- JE: check items in block
execute (if|unless) items entity <targets> <slots> <predicate> -- JE: check items in entity
execute (if|unless) loaded <pos>                           -- JE: check if position loaded
execute (if|unless) predicate <predicate>                   -- JE: check predicate result
execute (if|unless) score <target> <obj> (=|<|<=|>|>=) <source> <srcObj>
execute (if|unless) score <target> <obj> matches <range>
execute (if|unless) stopwatch <id> <range>                  -- JE: check stopwatch time
```

### Store Subcommands (JE only)
```
execute store (result|success) block <pos> <path> (byte|short|int|long|float|double) <scale>
execute store (result|success) bossbar <id> (value|max)
execute store (result|success) entity <target> <path> (byte|short|int|long|float|double) <scale>
execute store (result|success) score <targets> <objective>
execute store (result|success) storage <id> <path> (byte|short|int|long|float|double) <scale>
```

### Common Patterns
```mcfunction
# Execute as all sheep at their own position
execute as @e[type=sheep] at @s run tp @s ~ ~1 ~

# Check if block below is stone and run function if true
execute if block ~ ~-1 ~ minecraft:stone run function mypack:stone_action

# Store player count to scoreboard
execute store result score #count player_count if entity @a

# Kill all creepers within 5 blocks of any player
execute at @a run kill @e[type=creeper,distance=..5]
```

## /function
```
function <name>                           -- Run function or function tag
function <name> <arguments>               -- Run macro with NBT args
function <name> with block <pos> [<path>] -- Run macro with block NBT
function <name> with entity <target> [<path>] -- Run macro with entity NBT
function <name> with storage <id> [<path>]    -- Run macro with storage NBT
```

## /scoreboard
```
# Objectives
scoreboard objectives add <name> <criteria> [<displayName>]
scoreboard objectives remove <name>
scoreboard objectives list
scoreboard objectives modify <name> displayname <name>
scoreboard objectives modify <name> rendertype (hearts|int)
scoreboard objectives modify <name> displayautoupdate <bool>

# Players
scoreboard players add <targets> <obj> <score>
scoreboard players remove <targets> <obj> <score>
scoreboard players set <targets> <obj> <score>
scoreboard players get <target> <obj>
scoreboard players reset <targets> [<obj>]
scoreboard players enable <targets> <trigger_obj>
scoreboard players operation <targets> <targetObj> <operation> <source> <sourceObj>
scoreboard players display name <targets> <obj> <name>
scoreboard players display numberformat <targets> <obj> (styled|blank|fixed <content>) [<style>]

# Display
scoreboard objectives setdisplay <slot> [<obj>]
scoreboard objectives setdisplay below_name [<obj>]
```

Operations: `+=`, `-=`, `*=`, `/=`, `%=`, `=`, `<`, `>`, `><` (swap)
Slots: `sidebar`, `sidebar.team.<color>`, `list`, `below_name`

## /data (JE only)
```
data get block <pos> [<path>] [<scale>]
data get entity <target> [<path>] [<scale>]
data get storage <id> [<path>] [<scale>]
data merge block <pos> <nbt>
data merge entity <target> <nbt>
data merge storage <id> <nbt>
data modify block <pos> <path> (append|insert <index>|merge|prepend|set) from block <sourcePos> <sourcePath>
data modify block <pos> <path> (append|insert <index>|merge|prepend|set) from entity <source> <sourcePath>
data modify block <pos> <path> (append|insert <index>|merge|prepend|set) from storage <source> <sourcePath>
data modify block <pos> <path> (append|insert <index>|merge|prepend|set) value <value>
data remove block <pos> <path>
data remove entity <target> <path>
data remove storage <id> <path>
```

## /item (JE only)
```
item modify (block <pos>|entity <targets>) <slot> <modifier>
item replace (block <pos>|entity <targets>) <slot> from (block <pos>|entity <targets>) <slot> [<modifier>]
item replace (block <pos>|entity <targets>) <slot> with <item> [<count>]
```

Slot patterns: `container.<n>`, `weapon`, `weapon.mainhand`, `weapon.offhand`, `armor.head`, `armor.chest`, `armor.legs`, `armor.feet`, `horse.saddle`, `horse.chest`, `horse.armor`, `horse.<n>`

## /give
```
give <targets> <item> [<count>]
```

## /kill
```
kill <targets>
```

## /summon
```
summon <entity> [<pos>] [<nbt>]
```

## /teleport /tp
```
teleport <targets> <location>
teleport <targets> <destination>
teleport <targets> <x> <y> <z> [<yaw> <pitch>]
tp <targets> <location>
```

Facing: using `facing <pos>` or `facing entity <target> [eyes|feet]`

## /setblock
```
setblock <pos> <block> [destroy|keep|replace]
```

## /fill
```
fill <from> <to> <block> [destroy|hollow|keep|outline|replace [<filter>]]
```

## /clone
```
clone <begin> <end> <destination> [replace|masked|filtered [<filter>]] [force|move|normal]
```

## /effect
```
effect clear <targets> [<effect>]
effect give <targets> <effect> [<duration>] [<amplifier>] [<hideParticles>]
effect give <targets> <effect> infinite [<amplifier>] [<hideParticles>]
```

## /weather
```
weather (clear|rain|thunder) [<duration>]
```

## /time
```
time add <time>
time set <time>
time set (day|noon|night|midnight)
time query (daytime|gametime|day)
```

Time units: `1d` (day), `1s` (second), `1t` (tick), or raw ticks

## /gamerule
```
gamerule <rule> [<value>]
gamerule <rule>
```

Key gamerules for datapacks:
- `maxCommandChainLength` (default: 65536)
- `doImmediateRespawn`
- `doDaylightCycle`
- `doWeatherCycle`
- `doMobSpawning`
- `doMobLoot`
- `keepInventory`
- `commandBlockOutput`
- `sendCommandFeedback`
- `randomTickSpeed`
- `spawnRadius`
- `playersSleepingPercentage`

## /gamemode
```
gamemode (survival|creative|adventure|spectator) [<target>]
```

## /difficulty
```
difficulty [peaceful|easy|normal|hard]
```

## /say
```
say <message>
```

## /tellraw
```
tellraw <targets> <message>
```

Message is a text component: `{"text":"Hello","color":"red"}`

## /title
```
title <targets> (clear|reset)
title <targets> (title|subtitle|actionbar) <message>
title <targets> times <fadeIn> <stay> <fadeOut>
```

## /playsound /stopsound
```
playsound <sound> <source> <targets> [<pos>] [<volume>] [<pitch>] [<minVolume>]
stopsound <targets> <source> <sound>
```
Sources: `master`, `music`, `record`, `weather`, `block`, `hostile`, `neutral`, `player`, `ambient`, `voice`

## /particle
```
particle <name> [<pos>] [<delta>] <speed> <count> [<mode>] [<viewers>]
```

## /advancement (JE only)
```
advancement (grant|revoke) <targets> everything
advancement (grant|revoke) <targets> from <advancement>
advancement (grant|revoke) <targets> only <advancement> [<criterion>]
advancement (grant|revoke) <targets> through <advancement>
```

## /attribute (JE only)
```
attribute <target> <attribute> get [<scale>]
attribute <target> <attribute> base get [<scale>]
attribute <target> <attribute> base set <value>
attribute <target> <attribute> modifier add <uuid> <name> <value> (add_value|add_multiplied_base|add_multiplied_total)
attribute <target> <attribute> modifier remove <uuid>
attribute <target> <attribute> modifier value get <uuid> [<scale>]
```

## /bossbar (JE only)
```
bossbar add <id> <name>
bossbar remove <id>
bossbar list
bossbar set <id> name <name>
bossbar set <id> color (blue|green|pink|purple|red|white|yellow)
bossbar set <id> style (notched_6|notched_10|notched_12|notched_20|progress)
bossbar set <id> value <value>
bossbar set <id> max <max>
bossbar set <id> visible <visible>
bossbar set <id> players [<targets>]
bossbar get <id> (value|max|visible|players)
```

## /clear
```
clear [<targets>] [<item>] [<maxCount>]
```

## /enchant (JE only)
```
enchant <targets> <enchantment> [<level>]
```

## /experience /xp
```
experience add <targets> <amount> [levels|points]
experience set <targets> <amount> [levels|points]
experience query <targets> (levels|points)
```

## /locate
```
locate structure <structure>
locate biome <biome>
locate poi <poi>
```

## /loot
```
loot spawn <pos> (fish|loot|kill|mine) ...
loot give <targets> (fish|loot|kill|mine) ...
loot insert <pos> (fish|loot|kill|mine) ...
Loot sources: loot <table>, fish <table> <pos> [<tool>|mainhand|offhand], kill @<selector>, mine <pos> [<tool>|mainhand|offhand]
```

## /place (JE only)
```
place feature <feature> [<pos>]
place jigsaw <pool> <target> <depth> [<pos>]
place structure <structure> [<pos>]
```

## /recipe (JE only)
```
recipe give <targets> (everything|*|<recipe>)
recipe take <targets> (everything|*|<recipe>)
```

## /schedule (JE only)
```
schedule function <function> <time> [append|replace]
schedule clear <function>
```

## /setworldspawn
```
setworldspawn [<pos>] [<angle>]
```

## /spawnpoint
```
spawnpoint [<targets>] [<pos>] [<angle>]
```

## /spreadplayers
```
spreadplayers <center> <spreadDistance> <maxRange> <respectTeams> <targets>
spreadplayers <center> <spreadDistance> <maxRange> under <maxHeight> <respectTeams> <targets>
```

## /tag
```
tag <targets> add <name>
tag <targets> list
tag <targets> remove <name>
```

## /team
```
team add <name> [<displayName>]
team empty <name>
team remove <name>
team join <team> [<targets>]
team leave <targets>
team list [<team>]
team modify <team> collisionRule (always|never|pushOtherTeams|pushOwnTeam)
team modify <team> color <color>
team modify <team> displayName <name>
team modify <team> friendlyFire <bool>
team modify <team> nametagVisibility (always|never|hideForOtherTeams|hideForOwnTeam)
team modify <team> prefix <prefix>
team modify <team> seeFriendlyInvisibles <bool>
team modify <team> suffix <suffix>
```

## /worldborder
```
worldborder add <distance> [<time>]
worldborder center <pos>
worldborder damage amount <damagePerBlock>
worldborder damage buffer <distance>
worldborder get
worldborder set <distance> [<time>]
worldborder warning distance <distance>
worldborder warning time <time>
```

## /forceload (JE only)
```
forceload add <from> [<to>]
forceload remove <from> [<to>]
forceload remove all
forceload query [<pos>]
```

## /fillbiome (JE only)
```
fillbiome <from> <to> <biome> [replace <filter>]
```

## /ride (JE only)
```
ride <targets> mount <vehicle>
ride <targets> dismount
```

## /rotate (JE only)
```
rotate <targets> (facing <pos>|facing entity <target> [eyes|feet]|<yaw> <pitch>)
```

## /spectate (JE only)
```
spectate <target> [<player>]
spectate <player> stop
```

## /transfer (JE only)
```
transfer <hostname> [<port>] [<targets>]
```

## /trigger (JE only)
```
trigger <objective> [add <value>|set <value>]
```

## /random (JE only)
```
random (value|roll) <range> [<sequence>]
random reset [*|<sequence>]
```

## /return (JE only)
```
return <value>
return fail
return run <command>
```

## /damage
```
damage <target> <amount> [<damageType>] [at <location>|by <entity> [from <cause>]]
```

## /dialog (JE only)
```
dialog show <dialog> <targets>
dialog clear <targets>
```

## /waypoint (JE only)
```
waypoint list [<targets>]
waypoint offer (structure|biome|poi) [<targets>] [<pos>]
waypoint offer on <entity> [<targets>]
```

## /tick (JE only)
```
tick query
tick rate <rate>
tick freeze
tick step [<time>]
tick step stop
tick unfreeze
tick sprint [<time>]
tick sprint stop
```

## /reload
```
reload
```

## /datapack (JE only)
```
datapack disable <name>
datapack enable <name> [first|last|(before|after) <existing>]
datapack list [available|enabled]
```

## /ban /ban-ip /banlist /pardon /pardon-ip (JE only)
```
ban <targets> [<reason>]
ban-ip <target> [<reason>]
banlist [ips|players]
pardon <targets>
pardon-ip <target>
```

## /op /deop (JE only)
```
op <targets>
deop <targets>
```

## /whitelist (JE only)
```
whitelist add <targets>
whitelist list
whitelist off
whitelist on
whitelist reload
whitelist remove <targets>
```

## /kick (JE only)
```
kick <targets> [<reason>]
```

## /stopwatch (JE only)
```
stopwatch start <id>
stopwatch stop <id>
stopwatch lap <id>
stopwatch query <id>
stopwatch reset <id>
```

## /me
```
me <action>
```

## /msg /tell /w
```
msg <targets> <message>
tell <targets> <message>
w <targets> <message>
```

## /teammsg /tm
```
teammsg <message>
tm <message>
```

## /list
```
list [uuids]
```

## /help
```
help [<command>]
```

## /seed (JE only)
```
seed
```

## /stop
```
stop
```

## /save-all /save-off /save-on (JE only server)
```
save-all [flush]
save-off
save-on
```

## /defaultgamemode (JE only)
```
defaultgamemode (survival|creative|adventure|spectator)
```

## /publish (JE only singleplayer)
```
publish [<port>]
```

## Common Target Selector Parameters
```
@a[<args>]  -- all players
@e[<args>]  -- all entities
@p[<args>]  -- nearest player
@r[<args>]  -- random player
@s          -- self

Arguments: x, y, z, dx, dy, dz, distance, type, tag, name, team, scores, 
           advancements, predicate, level, gamemode, limit, sort, nbt, hasitem
```

## Coordinate Types
- Absolute: `100 64 100`
- Relative: `~ ~1 ~` (offset from current position)
- Local: `^ ^ ^1` (direction-based, 1 block forward)
- Block: Integer coordinates for block positions
