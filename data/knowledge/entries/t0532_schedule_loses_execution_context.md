---
id: t0532
title: "schedule 不保留执行上下文"
title_en: "schedule_loses_execution_context"
layer: concept
source_url: "data/archive/inbox/20260606_140955.md"
source_type: manual
version_min: "1.14"
version_max: ""
wiki_covers_this: false
confidence: high
tags: ["schedule", "execution_context", "executor", "position", "delayed_action"]
verified_in_game: false
---

## 核心洞见

`schedule function` 会在未来 tick 创建新的执行环境，不继承调用时的执行者、位置、旋转和维度。因此不能假设延迟函数中的 `@s` 仍是原玩家。

## 代码示例

```mcfunction
# 错误：delayed 中没有原玩家作为 @s
execute as @a run schedule function mypack:delayed 1t

# 正确：先保存身份，再在 delayed 中重新选择
tag @s add mypack.delayed_action
schedule function mypack:delayed 1t

# delayed.mcfunction
execute as @a[tag=mypack.delayed_action] at @s run function mypack:run_delayed
tag @a[tag=mypack.delayed_action] remove mypack.delayed_action
```

## 机制原理

执行上下文只沿当前命令链和同步函数调用继承。`schedule` 将函数登记到未来 tick 的调度队列，届时由服务器创建新的无实体执行上下文运行，因此原调用者信息必须显式持久化。

## 注意事项

- 多名玩家同时调度时，简单 tag 可能混合不同任务；复杂任务应保存 ID、时间或参数。
- 延迟期间玩家可能下线或死亡，执行前需要重新验证目标。

