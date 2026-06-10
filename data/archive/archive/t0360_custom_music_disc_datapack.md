---
id: t0360
title: "自定义唱片数据包"
title_en: "custom_music_disc_datapack"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202506/3/content"
source_type: "feature_article"
source_issue: "202506"
version_min: "1.21"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["唱片", "资源包", "数据包", "声音事件", "jukebox_playable"]
verified_in_game: false
---

## 核心洞见

通过资源包定义声音事件、数据包定义唱片曲目、物品组件引用曲目，三步即可在游戏中添加自定义唱片。

## 代码示例

```mcfunction
// 资源包 sounds.json
{
  "disc.hajimisic": {
    "sounds": [
      {
        "name": "hajimi:hajimisic",
        "stream": true
      }
    ],
    "subtitle": "哈基米：哈气"
  }
}

// 数据包 jukebox_song/hajimi_song.json
{
  "comparator_output": 0,
  "description": "哈基米想要哈气",
  "length_in_seconds": 99.0,
  "sound_event": {
    "sound_id": "hajimi:disc.hajimisic"
  }
}

// 1.21.4 版本 give 命令
#1.21.4
give @s diamond[jukebox_playable={song:"hajimidatapack:hajimi_song"}]

// 1.21.5 版本 give 命令
#1.21.5
give @s diamond[jukebox_playable="hajimidatapack:hajimi_song"]
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Minecraft 1.21+ 中，自定义唱片需要三个层次的定义：1) 资源包中的 sounds.json 定义声音事件（如 hajimi:disc.hajimisic），指定音频文件路径和流式播放属性；2) 数据包中的 jukebox_song 文件定义唱片曲目（如 hajimidatapack:hajimi_song），关联声音事件、设置红石输出强度、描述和时长；3) 物品的 jukebox_playable 组件引用曲目 ID，使物品可放入唱片机播放。这种分层设计将音频资源、曲目元数据和物品绑定分离，便于复用和扩展。关键机制是声音事件必须通过资源包注册，而曲目和物品组件通过数据包注册，两者通过命名空间 ID 关联。

## 注意事项

- 音频文件必须为单声道 ogg 格式，否则播放时音量不会随距离衰减（颅内播放）
- 长音频（>60秒）必须在 sounds.json 中设置 stream: true，否则可能无法正常播放
- 声音事件 ID 和唱片曲目 ID 的命名空间必须与资源包/数据包命名空间一致，否则无法关联
- 1.21.4 和 1.21.5 的 jukebox_playable 组件语法不同，需根据版本选择正确格式
- 常见误解：开发者可能认为自定义唱片只需要修改物品或直接替换原版唱片文件，而不知道需要资源包和数据包协同定义声音事件和曲目。
