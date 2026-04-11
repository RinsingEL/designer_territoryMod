# C9 执行层代码导览

## 主要类

- `src/main/java/com/user/terra_script/world/city/stage/c9/CityC9BuildQueue.java`
- `src/main/java/com/user/terra_script/world/city/stage/c9/CityC9Stages.java`
- `src/main/java/com/user/terra_script/world/city/CityBuildQueueExecutor.java`
- `src/main/java/com/user/terra_script/world/city/execution/BuildExecutionPipeline.java`
- `src/main/java/com/user/terra_script/world/city/execution/BuildChunkGate.java`
- `src/main/java/com/user/terra_script/world/city/execution/BuildRuntimeValidator.java`
- `src/main/java/com/user/terra_script/world/city/execution/BuildTerrainPreparationService.java`
- `src/main/java/com/user/terra_script/world/city/execution/BuildPlacementService.java`
- `src/main/java/com/user/terra_script/world/StructureInjector.java`

## 当前主链

1. `CityC9Stages.generate(...)`
2. `CityC9BuildQueue.upsertFromPlan(...)`
3. `CityBuildQueueExecutor.executeLoadedTasksNow(...)`
4. `BuildExecutionPipeline.execute(...)`
5. `BuildChunkGate` / `BuildRuntimeValidator`
6. `BuildTerrainPreparationService`
7. `BuildPlacementService`
8. `StructureInjector.placeStructureDetailed(...)`
9. `StructureInjector.finalizePlacedJigsaws(...)`

## 与主模块求解器的边界

- `C8` 应输出已经求解完成的 child placement
- `C9` 不负责随机从模板池挑下一个结构
- `C9` 不负责继续猜 child origin
- `start` 直接放置路径继续有效
- child 节点应以“已解算 placement + runtime 最终复核”的模式进入执行层

## 当前遗留

- child 节点的求解器主链仍在接线中
- 需要把 `C8` 的 connector / jigsaw 求解结果稳定下沉到 `BuildTask`
- 高度口径与地表处理已收口到 `placement.origin_offset.y`、`group_surface_clear` 与 post-cleanup 语义，但后续仍可继续抽公共合同层

## 当前已收口语义

- `BuildTask.y` 的默认真值来自 `foundation/base_y + placement.origin_offset.y`，默认 `origin_offset.y = 0`。
- `group_surface_clear` 默认从 `foundation.base_y - 1` 开始清；显式 `min_y / max_y` 仍优先。
- 所有落地后的 jigsaw 方块统一执行 `final_state -> air fallback`，并把统计写入 `terrain_preparation.post_cleanup`。
- `BuildTerrainPreparationService` 清理当前节点时，当前会从 transient queue 中推导已落地父节点的保护 bounds，并跳过这些区域；因此后续 child/grandchild 不再允许把父节点主体当成普通 `embedded_solid` 大面积挖掉。

## 当前建议后续拆分

- 队列管理
- 区块门控
- 地形预处理
- 结构落地
- 运行时校验
- fallback
- solver-aware placement bridge
