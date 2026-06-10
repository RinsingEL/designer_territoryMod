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
| cellPatchIndex | object? | 可选；Region 内 Cell 到 `patchId` 的映射，用于表达 PatchShape。若 `AtlasCell.patchId` 已持久记录，可不重复保存。 |
| status | enum | empty、sampled、metricsPartial、ready、dirty。 |
| updatedAt | long | 最近更新时间。 |

## 边界规则

- Region 内部 Cell 可以直接合并 Patch。
- 跨 Region 的 Patch v1 允许断开。
- 如果 Region 边缘缺少邻域依赖，对应 Cell 必须标记 `edgeDirty`。
- 后续实现跨 Region 缝合时，应新增独立 merge pass，不改变 Cell 基础契约。
- Patch 的真实 shape 由成员 Cell 或 `cellPatchIndex` 表达；PatchEnvelope 只服务查询粗筛和定位，不代表真实覆盖范围。

## 持久化原则

- 主数据不使用人工维护 JSON。
- Region 主缓存后续优先使用紧凑二进制或 Minecraft SavedData 管理索引。
- JSON 可用于调试摘要、PreviewManifest、人工验收报告，以及 v1 基线中的轻量 Region 快照。
- 轻量 Region 快照只用于自动测试复现、现场还原和调试交接，不是生产级 Atlas 主缓存。
- 轻量快照必须显式记录用途，例如 `snapshotPurpose = test-reproduction-and-field-restore`，并标记 `productionPersistence = false`。
- v1 不实现完整生产级 SavedData / 二进制长期持久层。后续若把 Region 主数据持久化为 SavedData 或紧凑二进制，需要另起契约版本并提升 `atlasVersion`。

## 轻量 Region 快照

当前实现仓库提供 `AtlasRegionSnapshotIo`，用于把单个 Region 的 Cell、Patch、状态和版本写成 JSON，再从 JSON 读回内存对象。

快照字段沿用本契约的 `AtlasRegion`、`AtlasCell` 和 `LandformPatch` 字段，并额外包含：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| snapshotPurpose | string | 固定用于说明快照用途，v1 为 `test-reproduction-and-field-restore`。 |
| productionPersistence | boolean | v1 固定为 `false`，避免被误当作生产主缓存。 |
