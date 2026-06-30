# City 案子：结构风格化换皮 v0.1

## 定位

本案处理结构已经真实落地后的风格统一问题。它不是结构选择、结构防撞、道路连接或地形融合，而是基于 `worldgen ledger` 的真实结构 footprint，把同一座城市 / 国度内的结构做成更统一、更有阵营辨识度的建筑材料风格。

本案默认发生在 D7 ledger 完整之后，可视为后续 `D8 style pass`。它不改变结构是否生成、不改变结构 bbox、不参与 D4 / D6 防撞决策。

## 核心目标

- 让来自不同结构包的建筑在同一座城市中拥有统一的国度 / 城市风格。
- 支持按国度、城市、区域、结构角色选择不同 block palette。
- 换皮只在结构真实 `actualFootprint` / `pieceBoxes` 内执行，不越界污染自然地形。
- 尽量摆脱 WorldEdit 依赖，优先使用 Forge / 原版 `setBlock` 能力；WorldEdit 仅保留为调试或大批量施工后端候选。
- 保留结构功能，不把箱子、床、门、刷怪笼、红石、告示牌等关键方块替换坏。
- 保留 blockstate，例如楼梯朝向、半砖上下、墙连接、门朝向、含水状态等。

## 输入

- D7 `placed_structure_ledger.json`
  - `actualFootprint`
  - `pieceBoxes`
  - `structureId`
  - `anchorId`
  - inferred function area / semantic terms
- TerraSense `StructureProfile`
  - 结构材质特征
  - 结构功能语义
  - 可替换 / 不可替换方块提示
- 国度 / 城市 palette profile
  - 主材质
  - 屋顶材质
  - 装饰材质
  - 道路 / 城墙 / 港口等专题材质
- 可选：Road Weaver 道路结果、城墙结果、地形兼容结果。

## 输出

- `structure_reskin_plan.json`
- `structure_reskin_trace.json`
- `structure_reskin_preview.png`
- 可选 `structure_reskin_ledger.json`

## 初版流程

```text
D7 worldgen ledger complete
  -> collect actualFootprint / pieceBoxes
  -> choose city / realm palette profile
  -> build per-structure replacement plan
  -> validate protected blocks / blockstate rules
  -> preview and trace
  -> execute style pass with confirmed mutation
```

## Palette 口径

初版只做 block family 替换，不做复杂重建：

- 木材族：橡木、云杉、深色橡木、红树、竹子等互换。
- 石材族：圆石、石砖、深板岩、凝灰岩、黑石等互换。
- 屋顶族：木台阶、砖、铜、深色屋顶、苔藓屋顶等互换。
- 装饰族：灯笼、旗帜、花盆、地毯、藤蔓、栅栏等可按主题调整。
- 地表族：路径、砂砾、泥土、苔藓、石板等只在结构 footprint 内调整，不替代 D7 道路系统。

每个 palette 必须声明：

- `replaceableBlockFamilies`
- `protectedBlockTags`
- `preserveBlockStateProperties`
- `fallbackPolicy`

## 方块保护规则

默认保护：

- 容器：箱子、木桶、漏斗等。
- 功能方块：床、门、活板门、工作站、钟、刷怪笼、命令方块、红石元件。
- 信息方块：告示牌、书、讲台。
- 实体关联方块：物品展示框、画、盔甲架附近方块。
- 结构关键方块：jigsaw、structure block、barrier、light。
- mod 方块：未知 block entity 默认保护，除非 palette 显式允许。

## 执行边界

City 负责：

- 根据 ledger 定位结构真实范围。
- 按国度 / 城市 / 结构语义选择 palette。
- 生成换皮计划、预览和 trace。
- 执行时保证不越过 `actualFootprint` / `pieceBoxes`。

TerraSense 负责：

- 输出结构原始材质画像。
- 标注结构语义和可替换提示。
- 提供 block family / tag 白名单，不让 City 自建语义枚举。

后续专门的风格系统可负责：

- 管理国度主题 palette。
- 管理阵营、文化、时代、贫富层级等风格参数。
- 生成更复杂的装饰和老化效果。

## 与其他案子的关系

- Road Weaver：道路材质可以共享 palette，但道路生成和道路换皮不由本案负责。
- 结构地形兼容：台基 / 地形融合先决定结构如何贴地；本案只处理结构内部材料风格。
- 城市边界与城墙：城墙可共享国度 palette，但城墙布局不由本案负责。
- 结构语义重标记：语义越清晰，换皮越能按建筑功能选择材料层级。

## 验收

- 换皮不会改变结构 bbox、不会造成结构重叠或越界。
- 换皮后箱子、床、门、工作站、刷怪笼、红石等功能仍可用。
- 楼梯、半砖、门、栅栏、墙等 blockstate 不丢失。
- 同一城市内多个结构的材料风格明显更统一。
- trace 能说明每个结构使用了哪个 palette、替换了哪些 block family、保护了哪些 block。
- 未知 mod 方块默认保护，不静默替换成错误方块。

## 暂不处理

- 不在本案重做结构布局。
- 不在本案修复悬空 / 硬切地形问题。
- 不在本案生成道路、桥、城墙。
- 不做复杂模型级重建或 AI 视觉重绘。
- 不承诺一次性支持所有 mod 方块，未知方块先保护。

## 待定

- `D8 style pass` 是否作为正式阶段名。
- palette profile 放在 City、Realm Planning，还是独立风格系统。
- 是否需要 non-mutating block diff preview。
- 是否需要按建筑贫富等级、行政等级、国度派系做多层 palette。
- 是否支持把结构包原始材质反向归一成 TerraSense 材质画像。
