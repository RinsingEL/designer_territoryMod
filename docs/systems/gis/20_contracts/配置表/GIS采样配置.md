# GIS 采样配置

本文描述 GIS v1 初版稳定版需要暴露的采样与刷新配置。配置名是文档约定，最终代码可以按项目命名规范调整，但语义不应偏离。

## 基础配置

| 配置 | 默认值 | 说明 |
| --- | --- | --- |
| cellStepBlocks | 4 | 一个 AtlasCell 覆盖的方块步长。 |
| regionSizeChunks | 32 | 一个 AtlasRegion 单边包含的区块数。 |
| stableRadiusChunks | 16 | v1 默认稳定刷新半径。 |
| dependencyMarginCells | 12 | 邻域指标额外依赖边界，至少覆盖大尺度 TPI。 |
| maxWaterDistanceCells | 64 | 水距传播或搜索上限。 |
| budgetCellsPerBatch | 4096 | 单批处理 Cell 上限。 |
| defaultSampleMode | prior | 默认只做生成器先验采样，不主动生成 chunk。 |

## 高度采样

GIS 高度采样默认调用当前维度的生成器接口，不读取原版固定噪声参数，也不要求 chunk 已经生成。`heightSource` 这类配置描述采样语义，不代表必须从真实 chunk heightmap 读取。

| 配置 | 默认值 | 说明 |
| --- | --- | --- |
| priorHeightType | WORLD_SURFACE_WG | 生成器先验高度采样语义。 |
| observedHeightType | WORLD_SURFACE_WG | 已加载 chunk 后验观测时使用的高度图语义。 |
| collisionHeightSource | MOTION_BLOCKING_NO_LEAVES | 可选事实层，用于记录可碰撞表面高度，供消费者按需参考。 |
| waterFloorSource | OCEAN_FLOOR_WG | 水深和岸线估计可参考该高度语义。 |

## 采样模式

| 模式 | 默认用途 | 说明 |
| --- | --- | --- |
| prior | Atlas 半径刷新。 | 只调用生成器和 biome source，不主动生成 chunk。 |
| observedIfLoaded | 玩家附近或调试对照。 | chunk 已加载或已生成时读取真实数据，否则回退 prior。 |
| verifySurface | 结构物化前局部校验。 | 只允许小范围使用，必要时等待或推进到足够表面状态。 |

## 指标半径

| 配置 | 默认值 | 说明 |
| --- | --- | --- |
| slopeRadiusCells | 1 | 坡度邻域半径。 |
| localReliefRadiusCells | 2 | 局部起伏邻域半径。 |
| roughnessRadiusCells | 2 | 粗糙度邻域半径。 |
| tpiSmallRadiusCells | 3 | 小尺度 TPI 邻域半径。 |
| tpiLargeRadiusCells | 12 | 大尺度 TPI 邻域半径。 |

## 调整原则

- `cellStepBlocks` 越小，结果越细，但成本越高。
- `tpiLargeRadiusCells` 越大，越能识别大地貌，但边缘依赖越重。
- `dependencyMarginCells` 必须大于或等于最大邻域半径。
- v1 不要同时调太多参数，优先用固定 seed 和预览图验证单项变化。
