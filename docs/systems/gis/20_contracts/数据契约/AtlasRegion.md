# AtlasRegion 数据契约

AtlasRegion 是 AtlasCell 的区域容器。它负责组织缓存、刷新状态、边界依赖和调试导出。

## 建议尺度

| 字段 | 默认值 |
| --- | --- |
| regionSizeChunks | 32x32 chunks |
| regionSizeBlocks | 512x512 blocks |
| cellStepBlocks | 4 |
| cellsPerRegion | 128x128 cells |

默认值可以后续通过配置调整，但 v1 实现应先固定一个尺度，避免缓存和调试图复杂化。

## 字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| regionId | string | Region 唯一标识，建议包含维度和 Region 坐标。 |
| dimensionId | string | Minecraft 维度。 |
| regionX | int | Region X 坐标。 |
| regionZ | int | Region Z 坐标。 |
| blockMinX | int | 覆盖范围最小方块 X。 |
| blockMinZ | int | 覆盖范围最小方块 Z。 |
| sizeChunks | int | 单边区块数量。 |
| cellStepBlocks | int | Cell 采样步长。 |
| atlasVersion | int | Atlas 数据格式版本。 |
| configVersion | string | 指标和分类配置版本。 |
| cells | AtlasCell[] | Region 内 Cell 数据。 |
| patches | LandformPatch[] | Region 内 Patch 列表。 |
| status | enum | empty、sampled、metricsPartial、ready、dirty。 |
| updatedAt | long | 最近更新时间。 |

## 边界规则

- Region 内部 Cell 可以直接合并 Patch。
- 跨 Region 的 Patch v1 允许断开。
- 如果 Region 边缘缺少邻域依赖，对应 Cell 必须标记 `edgeDirty`。
- 后续实现跨 Region 缝合时，应新增独立 merge pass，不改变 Cell 基础契约。

## 持久化原则

- 主数据不使用人工维护 JSON。
- Region 主缓存后续优先使用紧凑二进制或 Minecraft SavedData 管理索引。
- JSON 可用于调试摘要、PreviewManifest 和人工验收报告。
