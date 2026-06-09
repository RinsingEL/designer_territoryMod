# LandformPatch 数据契约

LandformPatch 是由相邻 AtlasCell 合并得到的地貌区。它是城市、道路、国度和结构系统的主要 GIS 查询对象。

## 设计目标

- 把大量 Cell 压缩成更适合规划的区域对象。
- 保留地貌类型、面积、坡度、水距、水体接触等地形事实摘要。
- 让消费者优先处理区域，而不是直接遍历栅格。
- 不输出通用可建性评分，避免 GIS 替结构、城市或道路系统做落地判断。

## 字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| patchId | string | Patch 唯一标识。 |
| regionId | string | 所属 AtlasRegion。 |
| landformType | enum | 主地貌类型。 |
| cellCount | int | 包含的 Cell 数量。 |
| blockMinX | int | 包围盒最小方块 X。 |
| blockMinZ | int | 包围盒最小方块 Z。 |
| blockMaxX | int | 包围盒最大方块 X。 |
| blockMaxZ | int | 包围盒最大方块 Z。 |
| meanElevation | float | 平均高度。 |
| minElevation | float | 最小高度。 |
| maxElevation | float | 最大高度。 |
| meanSlope | float | 平均坡度。 |
| waterDistanceMean | float | 平均水距。 |
| touchesWater | boolean | 是否接触水体。 |
| touchesRegionEdge | boolean | 是否接触 Region 边缘。 |
| confidence | float | 完整度或置信度，建议范围 0 到 1。 |
| flags | bitset | fragment、edgeDirty、crossRegionCandidate 等。 |

## 使用约束

- 消费者应优先读取 `confidence` 和 `flags`。
- `fragment` Patch 不应直接作为城市主体候选，但可以作为细节或结构点位候选。
- `edgeDirty` Patch 可以显示在调试图中，但不应作为稳定决策的唯一依据。
- Patch 的几何边界 v1 可只保存 Cell 集合和包围盒，后续再升级为多边形轮廓。
- 消费者需要根据自己的 profile 使用 `landformType`、坡度、水距、水深、面积等事实计算适配度，不能要求 GIS 给出一刀切的可建性结论。
