---
id: t0430
title: "延时命令执行"
title_en: "delayed_command_execution"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202505/1/content"
source_type: "feature_article"
source_issue: "202505"
version_min: "1.21.4"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["delay", "scheduling", "firework", "command"]
verified_in_game: false
---

## 核心洞见

通过launch函数中的life参数和cmdv列表，可以在数据包中实现延时执行命令的效果，模拟烟花升空过程。

## 代码示例

```mcfunction
function sklibs:skfirework/fx/launch
{
  "config": {
    "life": 50,
    "cmdv": [
      {"cmd": "function sklibs:skfirework/fx/spread", "args": {"config": {"n": 30, "v": 0.5, "g": 0.04, "tick_cmdv": [{"cmd": "particle flame ~ ~ ~ 0 0 0 0 1 force"}], "cmdv": [{"cmd": "function sklibs:skfirework/fx/firework", "args": {"config": {"shape": 0, "colors": [{"from": [I;13047173], "to": [I;16761035]}, {"from": [I;16711680], "to": [I;10824234]}], "n": 1}}}]}}}
    ]
  }
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

launch函数接受一个life参数（表示延时tick数）和一个cmdv列表（在延时结束后执行的命令）。在内部，launch函数可能使用一个计数器或调度机制，在life个tick后执行cmdv中的命令。这类似于一个简单的定时器，允许开发者将升空阶段（如粒子尾迹）与爆炸阶段分离。通过嵌套调用，可以实现多阶段延时效果，如先升空、再扩散、再二次爆炸。这种设计避免了手动管理多个schedule命令的复杂性。

## 注意事项

- life值过大会导致玩家等待时间过长，影响体验
- cmdv中的命令执行顺序可能受函数调用深度影响
- 多个延时任务同时运行时可能产生冲突
- 常见误解：开发者可能认为延时执行只能通过schedule命令或重复函数实现，缺乏简洁的封装方式。
