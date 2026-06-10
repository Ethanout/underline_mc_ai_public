---
id: t0271
title: "帧动画播放框架"
title_en: "sequencer_helper_animation_framework"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202605/6/content"
source_type: "feature_article"
source_issue: "202605"
version_min: "1.20.5"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["帧动画", "物品模型映射", "数据包", "custom_model_data", "展示实体"]
verified_in_game: false
---

## 核心洞见

通过物品模型映射与数据包函数调度，可以在Minecraft中实现可复用的帧动画播放系统，无需依赖原版动画引擎。

## 代码示例

```mcfunction
python
"""
Minecraft帧动画序列模型映射文件生成脚本
参数说明:
- 源路径SOURCE_PATH: 指定帧动画的目录，为一相对路径，格式必定为<任意路径>/assets/<命名空间>/models/<其他路径>
- 目标路径TARGET_PATH: 生成模型映射文件的路径，相对路径（不需要带./）
- 文件名FILE_NAME: 映射文件的名字，程序会自动添加.json后缀
- 动画列表ANIMATION_LIST: 字符串列表，每一个项代表一个动画，表示原路径下的一个文件夹，内部为按数字标识的帧动画模型文件
- 回落映射FALLBACK_MAPPING: 可选，字符串，表示在不播放动画时的模型；若不存在则使用动画列表第一项的第一个模型
- 动画索引ANIMATION_INDEX: 影响动画索引字符串在物品custom_model_data.strings的第几项，例如0表示决定模型播放哪个动画的字符串在对应cmd的第一项
- 帧索引FRAME_INDEX: 影响帧索引字符串在物品custom_model_data.floats的第几项
"""
# 输入参数配置区 - 修改这里的参数来生成不同的映射文件
SOURCE_PATH = "assets\kaleidoscope_lab\models\leave_me_alone_box"  # 源路径：指定帧动画的目录
TARGET_PATH = "assets\kaleidoscope_lab\items"  # 目标路径：生成模型映射文件的路径
FILE_NAME = "leave_me_alone_box"  # 文件名：映射文件的名字（不含.json后缀）
ANIMATION_LIST = ["open", "close1", "close2", "close3", "close4"]  # 动画列表：每个项代表一个动画
FALLBACK_MAPPING = None  # 回落映射：可选，表示在不播放动画时的模型
ANIMATION_INDEX = 0  # 动画索引：影响最外层index
FRAME_INDEX = 0  # 帧索引：影响内层帧对应的index
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术利用Minecraft的物品模型映射机制，通过custom_model_data的strings和floats字段动态选择模型。Python脚本generate.py将Java Block Sequencor导出的帧动画模型（按数字编号的.json文件）映射到物品模型的overrides中，每个动画对应一个字符串（如"open"），每帧对应一个浮点数。数据包通过函数sh:init初始化参数，sh:start根据storage sh:props中的id、frames、anim_index、frame_index等参数，使用data modify命令设置展示实体的Item.tag.CustomModelData，从而切换模型帧。动画播放完成后，根据type参数（1循环、2停止、其他重置）执行相应操作，并可调用回调函数。核心机制是：物品模型映射的overrides按顺序匹配，strings和floats的索引位置由ANIMATION_INDEX和FRAME_INDEX决定，数据包通过计分板sh_frame追踪当前帧，利用schedule或循环函数实现逐帧更新。

## 注意事项

- custom_model_data的strings和floats索引必须与生成脚本中的ANIMATION_INDEX和FRAME_INDEX一致，否则模型映射会错乱
- 动画帧模型文件必须按数字编号且连续，否则映射会缺失或错误
- 回调函数如果使用宏函数，双引号需要转义，否则命令解析会失败
- 常见误解：开发者可能认为帧动画只能通过资源包中的模型文件硬编码实现，或者需要复杂的命令链逐帧手动控制展示实体的模型变化。
