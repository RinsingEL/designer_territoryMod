# RefreshJob 数据契约

RefreshJob 描述一次 GIS 半径刷新任务。它用于把刷新请求拆成可预算执行、可追踪、可恢复的任务。

## 字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| jobId | string | 刷新任务标识。 |
| dimensionId | string | Minecraft 维度。 |
| centerBlockX | int | 刷新中心方块 X。 |
| centerBlockZ | int | 刷新中心方块 Z。 |
| radiusChunks | int | 稳定刷新半径，单位为 chunk。 |
| dependencyMarginCells | int | 指标计算所需的外扩 Cell 边界。 |
| cellStepBlocks | int | Cell 采样步长。 |
| priority | enum | low、normal、high、debug。 |
| budgetCellsPerBatch | int | 每批最多处理 Cell 数。 |
| status | enum | queued、sampling、metrics、classifying、patching、completed、failed。 |
| completedCells | int | 已处理 Cell 数。 |
| totalCells | int | 预计 Cell 数。 |
| dirtyRegions | string[] | 本次影响的 Region。 |
| startedAt | long | 开始时间。 |
| finishedAt | long | 完成时间。 |
| errorMessage | string | 失败原因，仅失败时填写。 |

## 执行约束

- 同一 Region 可以合并多个低优先级刷新请求。
- debug 优先级可以跳过后台节流，但不应在正式运行中长期占用预算。
- 如果刷新边缘缺少依赖数据，不应失败，应标记 `edgeDirty`。
- `completed` 只表示本次半径内可执行步骤完成，不表示跨 Region 缝合已经完成。

