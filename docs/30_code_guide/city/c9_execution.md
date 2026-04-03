# C9 执行层代码导览

## 主要类

- `src/main/java/com/user/terra_script/world/city/stage/c9/CityC9BuildQueue.java`
- `src/main/java/com/user/terra_script/world/city/stage/c9/CityC9Stages.java`
- `src/main/java/com/user/terra_script/world/city/CityBuildQueueExecutor.java`
- `src/main/java/com/user/terra_script/world/StructureInjector.java`

## 当前主链

1. `CityC9Stages.generate(...)`
2. `CityC9BuildQueue.upsertFromPlan(...)`
3. `CityBuildQueueExecutor.executeLoadedTasksNow(...)`
4. `CityBuildQueueExecutor.executeTask(...)`
5. `StructureInjector.spawnStructureAtBlock(...)`

## 当前遗留

- `CityC9Stages` 中仍保留旧式直落辅助逻辑
- 高度口径与地表处理还未统一抽层

## 当前建议后续拆分

- 队列管理
- 区块门控
- 地形预处理
- 结构落地
- 运行时校验
- fallback
