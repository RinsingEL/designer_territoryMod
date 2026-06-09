# GIS 采样配置

本文描述 GIS 首版需要暴露的采样与刷新配置。配置名是文档约定，最终代码可以按项目命名规范调整，但语义不应偏离。

## 基础配置

| 配置 | 默认值 | 说明 |
| --- | --- | --- |
| cellStepBlocks | 4 | 一个 AtlasCell 覆盖的方块步长。 |
| regionSizeChunks | 32 | 一个 AtlasRegion 单边包含的区块数。 |
| stableRadiusChunks | 16 | 首版默认稳定刷新半径。 |
| dependencyMarginCells | 12 | 邻域指标额外依赖边界，至少覆盖大尺度 TPI。 |
| maxWaterDistanceCells | 64 | 水距传播或搜索上限。 |
| budgetCellsPerBatch | 4096 | 单批处理 Cell 上限。 |

## 高度采样

| 配置 | 默认值 | 说明 |
| --- | --- | --- |
| heightSource | WORLD_SURFACE_WG | 地形形态优先使用 worldgen surface。 |
| landingHeightSource | MOTION_BLOCKING_NO_LEAVES | 后续落点可建性可参考该高度图。 |
| waterFloorSource | OCEAN_FLOOR_WG | 水深和岸线估计可参考该高度图。 |

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
- 首版不要同时调太多参数，优先用固定 seed 和预览图验证单项变化。

