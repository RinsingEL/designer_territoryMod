# C阶段 AI 图像总规大重构案

## 定位

本案作为 `03_ai_design_sketch_refactor.md` 与 `04_c1_city_boundary_refactor.md` 的上位重构方案：C 阶段不再让程序扩张、选簇、随机 polygon 或矩形槽位主导城市形态，而是改为 AI 图像总规先画出城市边界、功能区、道路骨架与保留区，程序负责把图像结果转成可校验、可修复、可执行的数据。

核心结论：

- AI 可以直接参与城市边界、功能区和主道路生成。
- 只画网格线不够，还必须有固定坐标底图、图例、硬约束、分层 mask 与结构化回收协议。
- 旧选簇、扩张和矩形工具不删除，降级为 fallback、低成本聚落、调试对照与局部修复工具。
- C8/C9 的程序校验和 Minecraft 落地能力继续保留，AI 图像不能绕过执行层真值。

## 新主链

```text
T4 / C2 地形事实
-> C1 生成 AI 设计底图包
-> C2 AI 生成城市总规图
-> C3 解析成 boundary / district / road / preserve 结构化数据
-> C4 自动审查与修复
-> C5 生成 group intent 与道路接口
-> C6 生成轻量可建约束图
-> C7 生成导演意图卡
-> C8 Jigsaw / connector 局部生长
-> C9 执行落地
```

这条链路中，AI 决定“城市看起来应该怎么组织”，程序决定“这个组织是否真实可用，以及怎么落到 Minecraft 世界里”。

## 阶段职责

### C1：AI 设计底图包

C1 不再自己决定最终边界。它负责把国度、城市中心、T4 地形、海陆、高度、roughness、已有城市、可用主权范围和坐标网格整理成 AI 可读的设计底图包。

必须输出：

- 固定世界坐标窗口的地形底图
- chunk / block 网格与坐标标签
- 城市中心、可用主权范围、已有城市占用
- 水体、海岸、高差、roughness、不可建或高风险提示
- 颜色图例与 AI 绘制规则

### C2：AI 城市总规图

C2 改为 AI-first 的城市总规阶段。AI 在 C1 底图包上画出：

- 城市外边界
- core / urban / transition / preserve 功能区
- 主路、次路、入口、桥、港口或山路等道路骨架
- 广场、留白、水岸、坡地保留、城墙或防御边等宏观意图

AI 输出不能只是一张好看的混合图，必须伴随可解析图层或可分离 mask。

### C3：图像解析与矢量化

C3 从旧数学分区阶段改为 parser / vectorizer。它读取 AI 总规图和分层 mask，生成：

- `boundary_polygon`
- `district_polygons`
- `road_graph`
- `preserve_polygons`
- `entry_bands`
- 置信度与解析警告

C3 的真值是程序解析并通过校验后的结构化 JSON，不是未经处理的图像像素。

### C4：自动审查与修复

C4 负责检查 AI 设计是否越界、压水、压陡坡、道路断开、区域过细、核心区失衡或缺少入口。可自动裁剪、合并、平滑、补路，也可要求 AI 重画局部 mask。

### C5：组团与道路接口

C5 把功能区和道路骨架转成下游可消费的 group intent：

- 每个 group 的主题、密度、入口、边界和生长方向
- 主路/支路接口
- 与保留区、水岸、坡地的关系
- C8 可用的扩张预算和停止条件

旧选簇能力在这里保留为 fallback：当 AI 区域不可解析、小型聚落不值得走全套总规，或需要局部补洞时，可用选簇生成保守 group。

### C6：轻量可建约束图

C6 不再主导矩形 placement。它只输出可建区域、禁建区域、风险区、入口带、扩展方向和面积预算。旧 `rect_guidance` 可迁移期保留，但不再是默认主输入。

### C7：导演意图卡

C7 从排列枚举器降级为导演意图卡，描述 group 的风格、节奏、密度、结构族、最大节点数、分支预算、靠水/靠路/留白等意图。

### C8 / C9：程序落地

C8 继续负责 connector / jigsaw / bounds / collision / terrain 校验和局部生长。C9 继续只消费已校验节点并执行放置，不重新解释 AI 总规。

## 图像输入要求

只画网格线不够。AI 输入图至少需要：

- 与世界坐标绑定的 C2/T4 底图
- 海陆、高度、roughness 和主要不可通行提示
- 国境/主权范围与城市可用范围
- 已有城市、道路、结构或保留区
- 清晰图例：边界、功能区、道路、保留区分别使用固定颜色
- 目标规模、城市类型、风格偏好和允许利用的地形

网格线的作用是回收坐标，不是替代地形事实。

## 图像输出要求

建议输出四类图：

- `C2_ai_masterplan_preview.png`：给人看的混合总规预览
- `C2_boundary_mask.png`：城市边界 mask
- `C2_district_mask.png`：功能区 mask
- `C2_road_mask.png`：道路骨架 mask

颜色必须稳定，避免让程序在一张自由绘画图里猜语义。

## 结构化产物

### CityDesignPlan.json

```json
{
  "step": "C_STAGE_AI_MASTERPLAN",
  "city_id": "city_3120_-3200",
  "source": {
    "base_map": "C1_design_base.png",
    "masterplan_preview": "C2_ai_masterplan_preview.png",
    "boundary_mask": "C2_boundary_mask.png",
    "district_mask": "C2_district_mask.png",
    "road_mask": "C2_road_mask.png"
  },
  "boundary_polygon": [],
  "districts": [],
  "roads": [],
  "preserve_areas": [],
  "entry_bands": [],
  "validation": {
    "status": "pass",
    "blocking_errors": [],
    "warnings": []
  }
}
```

### group_intent.json

`group_intent` 继续作为 C7/C8 的关键中间层，但来源从旧数学区域改为 AI 总规解析结果。

```json
{
  "group_id": "g_waterfront_market_01",
  "source_district_ids": ["district_waterfront_01"],
  "allowed_polygon": [],
  "road_interfaces": [],
  "intent": {
    "theme": "滨水市场",
    "density": "medium",
    "growth_mode": "jigsaw_growth",
    "max_nodes": 8,
    "branch_budget": 2
  }
}
```

## 旧工具去留

保留但降级：

- C1 survival / chunk 扩张：用于合法性兜底、小型聚落、测试样本。
- 选簇：用于 AI 失败、低成本村庄、局部补洞和 group fallback。
- C3 数学 polygon：用于无 AI 环境和回归测试。
- C6 矩形槽位：用于 debug 与非常规则的建筑群，不再默认主导城市形态。
- C7 arrangement 枚举：保留为迁移兼容字段，不再作为 AI-first 主线必填。

删除方向暂不执行。第一阶段只做降级和旁路，避免破坏现有 C8/C9 可运行能力。

## 校验原则

硬阻塞：

- 边界越出国度或城市允许范围且无法裁剪
- 核心区完全不在可用范围内
- 道路骨架与 group 入口完全断开
- 功能区碎成不可落地的小片且无法合并
- 缺少可解析 mask 或结构化 JSON

软提示：

- 普通陆城压水过多
- 山城 roughness 高但可做台地
- 港口/水城利用水体
- 规则城边界偏方
- transition / preserve 偏小但高密度设定允许

## 迁移步骤

1. 文档阶段：明确 AI-first 总规方案、契约和验收口径。
2. 预览阶段：先实现 C1 设计底图包，让 AI 输入可信。
3. 导入阶段：允许人工或 AI 产出的总规图导入并解析。
4. 校验阶段：实现 boundary / district / road / preserve validator。
5. 衔接阶段：从 CityDesignPlan 生成 group intent，喂给 C7/C8。
6. 主线切换：AI-first 成为默认路线，旧算法保留 fallback。

## 当前建议

从 C 阶段开头重构是合理的。真正该被替换的不是 C8/C9 的落地求解，而是 C1-C7 里过早替城市决定形状的程序工具。新主线应让 AI 先画总规，程序再把它变成可靠、可解释、可执行的城市计划。
