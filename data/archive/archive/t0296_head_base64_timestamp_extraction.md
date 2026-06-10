---
id: t0296
title: "头颅Base64时间戳提取"
title_en: "head_base64_timestamp_extraction"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202512/4/content"
source_type: "feature_article"
source_issue: "202512"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["base64解码", "Unix时间戳", "玩家头颅", "数据提取", "计分板"]
verified_in_game: false
---

## 核心洞见

玩家头颅数据中的base64字符串包含Unix时间戳，可通过固定偏移量直接定位并解码，无需完整解析整个base64。

## 代码示例

```mcfunction
函数 tm:init/base64 (添加到 minecraft:load 标签)

scoreboard objectives add base64 dummy
scoreboard players set 64 base64 64
scoreboard players set 256 base64 256
scoreboard players set 10 base64 10

生成函数 tm:init/base64_chr 的代码如下: (添加到 minecraft:load 标签)

with open('data/tm/function/init/base64_chr.mcfunction', mode='w', encoding='utf-8') as f:
    f.write('scoreboard objectives add base64_chr dummy')
    for i,ch in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'):
        f.write(f'\nscoreboard players set #{ch} base64_chr {i}')
    f.write('\nscoreboard players set #= base64_chr 0')

函数 tm:base64_decode/_ （固定处理16个字符。）

data modify storage base64: output set value [B;]
function tm:base64_decode/__
function tm:base64_decode/__
function tm:base64_decode/__
function tm:base64_decode/__

函数 tm:base64_decode/__ (每一次读取4个字符并转换成3个字节的数据。)

scoreboard players set #temp0 base64 0
function tm:base64_decode/___
function tm:base64_decode/___
function tm:base64_decode/___
function tm:base64_decode/___
scoreboard players operation #temp1 base64 = #temp0 base64
scoreboard players operation #temp1 base64 %= 256 base64
scoreboard players operation #temp0 base64 /= 256 base64
data modify storage base64: output append value 0b
data modify storage base64: output append value 0b
data modify storage base64: output append value 0b
execute store result storage base64: output[-1] byte 1 run scoreboard players get #temp1 base64
scoreboard players operation #temp1 base64 = #temp0 base64
scoreboard players operation #temp1 base64 %= 256 base64
scoreboard players operation #temp0 base64 /= 256 base64
execute store result storage base64: output[-2] byte 1 run scoreboard players get #temp1 base64
execute store result storage base64: output[-3] byte 1 run scoreboard players get #temp0 base64

函数 tm:base64_decode/___ (读取一个字符。)

data modify storage base64: input.1 set string storage base64: input.0 0 1
data modify storage base64: input.0 set string storage base64: input.0 1
execute store result score #temp1 base64 run function tm:base64_decode/____ with storage base64: input
scoreboard players operation #temp0 base64 *= 64 base64
scoreboard players operation #temp0 base64 += #temp1 base64

函数 tm:base64_decode/____

$return run scoreboard players get #$(1) base64_chr

函数 tm:timestamp_get/_

scoreboard players set #temp0 base64 0
scoreboard players set #i base64 0
execute store result score #temp1 base64 run data get storage base64: output[0]
data remove storage base64: output[0]
execute if score #i base64 matches ..9 run function tm:timestamp_get/__

函数 tm:timestamp_get/__

scoreboard players operation #temp0 base64 *= 10 base64
scoreboard players operation #temp0 base64 += #temp1 base64
scoreboard players remove #temp0 base64 48
execute store result score #temp1 base64 run data get storage base64: output[0]
data remove storage base64: output[0]
scoreboard players add #i base64 1
execute if score #i base64 matches ..9 run function tm:timestamp_get/__
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

玩家头颅的profile.properties[0].value字段存储了一个base64编码的JSON字符串，其中包含'timestamp'字段。该JSON以固定前缀'{\n "timestamp" : '开头（18个字符），对应base64编码的前24个字符。时间戳固定为13位数字（前10位为Unix秒数，后3位为毫秒），因此从base64字符串的第24位到第40位（共16个base64字符）正好对应时间戳的12个ASCII字符（包括前导空格等，实际有效数字为10位）。通过自定义base64解码函数，可以只提取这16个字符并解码为10字节数据，再通过ASCII码转换（每位减48）和按位组合（乘以10累加）还原出Unix时间戳数值。该技术利用了base64编码的确定性偏移和固定长度特性，避免了完整解析整个base64字符串的复杂性。

## 注意事项

- 该方案在25w34a之后变为半自动，需要玩家配合使用/fetchprofile命令获取完整profile数据
- 使用计分板（int范围）处理时间数据，会受到2038年问题的影响（2038-01-19 03:14:07 UTC之后失效）
- base64解码时需注意固定偏移量，不同版本的头颅数据格式可能变化（如24w09a和24w10a的格式变更）
- 时间戳包含毫秒，但网络请求延迟导致毫秒不准确，建议只使用前10位秒数
- 常见误解：开发者可能认为获取Unix时间戳需要外部工具或模组，或者认为头颅数据中的时间戳无法通过原版命令提取，因为它是base64编码的。
