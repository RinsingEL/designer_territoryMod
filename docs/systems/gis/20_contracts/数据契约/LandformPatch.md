# LandformPatch 数据契约

LandformPatch 是由相邻 AtlasCell 合并得到的地貌区。它是城市、道路、国度和结构系统的主要 GIS 查询对象。

## 设计目标

- 把大量 Cell 压缩成更适合规划的区域对象。
- 保留地貌类型、面积、坡度、水距、水体接触等地形事实摘要。
- 让消费者优先处理区域，而不是直接遍历栅格。
- 明确区分 Patch 的真实栅格形状和外接范围摘要，避免把 bbox 当成地貌区形状。
- 不输出通用可建性评分，避免 GIS 替结构、城市或道路系统做落地判断。

## 字段

### 当前 v1 摘要字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| patchId | string | Patch 唯一标识。 |
| regionId | string | 所属 AtlasRegion。 |
| landformType | enum | 主地貌类型。 |
| cellCount | int | 包含的 Cell 数量。 |
| blockMinX | int | PatchEnvelope 的最小方块 X；外接范围摘要，不是真实形状。 |
| blockMinZ | int | PatchEnvelope 的最小方块 Z；外接范围摘要，不是真实形状。 |
| blockMaxX | int | PatchEnvelope 的最大方块 X；外接范围摘要，不是真实形状。 |
| blockMaxZ | int | PatchEnvelope 的最大方块 Z；外接范围摘要，不是真实形状。 |
| meanElevation | float | 平均高度。 |
| minElevation | float | 最小高度。 |
| maxElevation | float | 最大高度。 |
| meanSlope | float | 平均坡度。 |
| waterDistanceMean | float | 平均水距。 |
| touchesWater | boolean | 是否接触水体。 |
| touchesRegionEdge | boolean | 是否接触 Region 边缘。 |
| confidence | float | 完整度或置信度，建议范围 0 到 1。 |
| flags | bitset | fragment、edgeDirty、crossRegionCandidate 等。 |

### PatchShape 目标语义

Patch 的真实几何形状应来自成员 Cell，而不是来自 `blockMinX/Z` 和 `blockMaxX/Z`。

v1 后续实现允许采用以下任一种等价表达：

| 表达 | 说明 |
| --- | --- |
| `memberCells` | Patch 内成员 Cell 的 Region 内坐标列表或压缩 range。 |
| `cellPatchId` | AtlasRegion 或 AtlasCell 上记录每个 Cell 所属的 `patchId`，由 Region 反查 Patch 成员。 |
| `PatchShape` | 独立对象，保存成员 Cell、轮廓边界或栅格多边形。 |

无论采用哪种表达，语义必须满足：

- 成员 Cell 集合才是 Patch 的真实 shape。
- `cellCount` 必须等于真实成员 Cell 数量。
- preview、精确查询、消费者落点判断必须基于成员 Cell 或 shape。
- `blockMinX/Z` 和 `blockMaxX/Z` 只能由成员 Cell 派生，不能反向决定成员 Cell。

### PatchEnvelope 语义

`blockMinX`、`blockMinZ`、`blockMaxX`、`blockMaxZ` 是 PatchEnvelope，也就是真实 shape 的外接方块范围。

PatchEnvelope 的作用只包括：

- 快速定位 Patch 大致范围。
- 作为空间索引的粗筛条件。
- 在查询时把 Patch 放入候选集。
- 帮助日志、报告和人工定位。

PatchEnvelope 不允许用于：

- 判断某个 Cell 或方块一定属于 Patch。
- 作为 `patch.png` 的真实形状。
- 作为消费者最终选址、道路通过、结构落点的精确几何依据。
- 替代成员 Cell、轮廓或栅格多边形。

查询流程必须是：

```text
查询范围 -> PatchEnvelope 粗筛 -> candidate patches -> PatchShape / memberCells 精查 -> final patches
```

经过 envelope 命中的结果只能命名为 candidate，不得命名为 final match。

## 使用约束

- 消费者应优先读取 `confidence` 和 `flags`。
- `fragment` Patch 不应直接作为城市主体候选，但可以作为细节或结构点位候选。
- `edgeDirty` Patch 可以显示在调试图中，但不应作为稳定决策的唯一依据。
- Patch 的真实几何边界优先用成员 Cell 或 PatchShape 表达；多边形轮廓可以后续由成员 Cell 派生。
- PatchEnvelope 可以长期保留为查询优化字段，但不得升级成真实形状字段。
- 消费者需要根据自己的 profile 使用 `landformType`、坡度、水距、水深、面积等事实计算适配度，不能要求 GIS 给出一刀切的可建性结论。
