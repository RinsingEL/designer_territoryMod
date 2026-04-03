# C9 执行层范围

## 目标

执行层不再被理解为单一“放结构方法”，而是一段完整施工流水线。

当前主链保留：

- `BuildQueue`
- `Executor`
- `StructureInjector`

但执行层内部应继续拆分为更清晰的能力层。

## 建议拆分

- `BuildQueueManager`
- `BuildChunkGate`
- `BuildTerrainPreparationService`
- `BuildPlacementService`
- `BuildRuntimeValidator`
- `BuildFallbackService`

## 建议流水线

1. `PRECHECK`
2. `PREPARE_TERRAIN`
3. `PLACE_STRUCTURE`
4. `POST_CLEANUP`
5. `POST_VALIDATE`

## 当前有效结论

- 继续保留“提前预存计划，区块 FULL 后再落地”的模式
- 结构放置、地表清理、嵌入式挖空不应再混在一个函数里
- 高度口径后续应统一进入一层 `BuildSurfaceResolver / TerrainHeightResolver`

## 历史背景

- `../../../../90_archive/StructureBinder/dev_docs/current_20260403_114442/`
- `../../../../90_archive/StructureBinder/workFlow/C9_结构落地与装饰计划.md`
