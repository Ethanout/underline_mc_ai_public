---
id: t0327
title: "条件事件链"
title_en: "conditional_event_chain"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202509/1/content"
source_type: "feature_article"
source_issue: "202509"
version_min: "1.21.8"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["conditional", "event_chain", "interaction", "predicate", "state_machine"]
verified_in_game: false
---

## 核心洞见

通过条件列表按顺序检查主手物品、副手物品和实体谓词，匹配第一个通过的项目执行事件，实现类似状态机的交互逻辑。

## 代码示例

（原文无完整代码示例）

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术定义了一个条件列表（criteria），包含多个检查项目。每个项目可检查主手物品（`mainhand_item`）、副手物品（`offhand_item`）和实体谓词（`predicate`）。系统按顺序遍历列表，找到第一个所有条件都通过的项目，执行其关联的事件列表，然后停止后续检查。这实现了类似switch-case的交互逻辑，例如：手持小麦喂羊、手持染料染色、手持剪刀剪毛。关键推导：顺序检查保证了优先级（第一个匹配优先），避免了多个条件同时满足时的冲突；条件组合（物品+谓词）支持复杂交互场景。

## 注意事项

- 条件列表顺序很重要，错误的顺序可能导致预期外的行为
- 物品谓词和实体谓词需要精确匹配，否则可能漏过条件
- 没有默认分支（else），如果所有条件都不满足则无操作
- 常见误解：开发者可能为每种交互条件单独编写if-else链，导致代码重复且难以扩展。
