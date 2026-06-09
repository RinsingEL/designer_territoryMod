# AtlasCell 数据契约

AtlasCell 是 GIS 的最小栅格单元。它不是 Minecraft 方块，也不是区块，而是对一小片方块区域的地貌摘要。

## 设计目标

- 降低逐方块扫描和查询成本。
- 平滑 Minecraft 方块级噪声。
- 为坡度、TPI、地貌分类和 Patch 合并提供统一输入。
- 允许边缘 Cell 表达“部分完成”状态。

## 建议尺度

首版建议：

| 字段 | 默认值 |
| --- | --- |
| cellStepBlocks | 4 |
| cellSize | 4x4 blocks |
| heightSample | cell 中心点或代表点高度 |

后续可以为不同 LOD 引入 8x8 或 16x16 Cell，但首版先保持单一尺度。

## 字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| regionId | string | 所属 AtlasRegion 标识。 |
| cellX | int | Region 内或全局 Cell X 坐标。 |
| cellZ | int | Region 内或全局 Cell Z 坐标。 |
| blockMinX | int | Cell 覆盖范围的最小方块 X。 |
| blockMinZ | int | Cell 覆盖范围的最小方块 Z。 |
| elevation | float | 地表高度。 |
| surfaceType | enum | 表面方块粗分类。 |
| biomeId | string | 生物群系标识。 |
| isWater | boolean | 是否水体。 |
| waterDepth | float | 水深估计。 |
| slope | float | 坡度指标。 |
| localRelief | float | 局部起伏。 |
| roughness | float | 粗糙度。 |
| tpiSmall | float | 小尺度 TPI。 |
| tpiLarge | float | 大尺度 TPI。 |
| waterDistance | float | 到最近水体或岸线的距离。 |
| buildability | float | 可建性评分，建议范围 0 到 1。 |
| landformType | enum | Cell 级地貌分类。 |
| stateFlags | bitset | sampled、metricsReadySmall、metricsReadyLarge、landformReady、patchReady、edgeDirty 等。 |

## 状态约束

- `sampled = false` 时，不允许消费者使用指标层和地貌分类。
- `metricsReadySmall = false` 时，坡度、局部起伏、小尺度 TPI 不可信。
- `metricsReadyLarge = false` 时，大尺度 TPI、水距、区域级地貌分类不可信。
- `edgeDirty = true` 时，允许调试显示，但消费者应降低权重或等待补全。

