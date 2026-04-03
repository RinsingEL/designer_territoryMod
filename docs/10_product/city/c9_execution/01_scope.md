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

## 当前明确约束

### 区块门控

- 结构只有在其所需全部区块都达到 `FULL` 后，才允许进入 `PREPARE_TERRAIN` 和 `PLACE_STRUCTURE`
- 当前只按单个 `chunk_x / chunk_z` 激活任务的做法，不足以覆盖跨区块结构，后续需要改为基于 `required_chunks` 的完整门控
- 地形预处理也必须服从同一条门控规则，不允许在结构所需区块未全部就绪时先行清理部分区域

### 地形预处理

- 不按 `ConfiguredFeature / PlacedFeature` 枚举来决定清理逻辑
- 第一阶段不强依赖 `GEN_BASE_HEIGHT` 一类生成器口径
- 普通建筑默认通过运行时“地面锚点搜索”来确定保留地面，而不是直接按“当前世界最高点”做清理
- 地面锚点搜索应从当前列顶向下跳过树叶、原木、花草、灌木、藤蔓等可清理地物，遇到草方块、泥土、石头、沙子、砂砾等可作为地面的方块后停止
- 只清理施工范围内、地面锚点以上的可清理地物，不删除锚点本身及其以下地层，避免结构落地后整体凹陷

### 植被清理策略

- 草、花、灌木等小地物，允许按施工范围直接清理
- 树木类对象命中后，必须按局部连通体整体清理，避免出现被腰斩的树干或残留树冠
- 所有植被清理都建立在“结构完整施工范围已可见、已可操作”这一前提上

### 参数控制

- 第一阶段执行层不引入大量数值型调参项
- 优先保留少量固定策略，例如：
  - `ALL_REQUIRED_CHUNKS_FULL`
  - `PRESERVE_GROUND`
  - `CUT_AND_CLEAR`
  - `RETRY_THEN_BLOCK`
- 不在第一阶段引入大量 feature 白名单、树种枚举、复杂半径配置或多套区块门控级别

## 当前推荐答案

1. `required_chunks`
   - 在入队时基于完整施工范围计算，而不是只按结构原点或结构本体 bounds 计算
   - 完整施工范围至少包括：
     - 结构 placement bounds
     - terrain prepare 所需的清理缓冲区
   - 再把该完整施工范围覆盖到的所有 chunk 坐标收集为 `required_chunks`
   - `BuildTask` 的就绪判定以后应基于 `required_chunks` 全部 `FULL`，而不是只看原点所在 chunk
2. 树木“局部连通体”清理边界
   - 当清理范围命中 `log/leaves` 时，从命中点开始做局部连通搜索
   - 搜索对象只包含树干与树叶，不把泥土、草方块、藤蔓以外的非树类方块并入
   - 搜索结果只删除与该命中点连成一体的 `log + leaves`
   - 搜索过程仍要求整体发生在结构完整施工范围已经可见、相关区块已全部 `FULL` 的前提下
3. 地表口径
   - 第一阶段优先采用运行时地面锚点搜索，而不是先引入多套高度模式
   - 如果后续实践证明运行时锚点不稳，再补 `generator.getBaseHeight(...)` 一类生成器口径作为增强实现

## 历史背景

- `../../../../90_archive/StructureBinder/dev_docs/current_20260403_114442/`
- `../../../../90_archive/StructureBinder/workFlow/C9_结构落地与装饰计划.md`
