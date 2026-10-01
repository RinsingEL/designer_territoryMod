# W / T 阶段数据契约

## 定位

本文定义国度规划系统 v1.1 的最小结构化产物。字段以指导实现和结构校验为目标，不提前承诺所有未来 C 阶段字段。

通用约束：

| 约束 | 说明 |
| --- | --- |
| 坐标单位 | `gridX/gridZ` 为 W / T 粗 cell 坐标；`blockX/blockZ` 为 Minecraft 世界方块坐标。 |
| step 单位 | `cellStepBlocks` 单位为 block。 |
| ID 风格 | 文档示例使用可读字符串；实现可用稳定 slug 或 UUID，但必须可追溯。 |
| 版本 | 结构落盘时建议包含 `schemaVersion`，v1.1 初始值可为 `realm_planning.v1.1`。 |
| 未实现字段 | 不得用空壳字段伪装能力；无法稳定产出的字段先不进入契约。 |

## 数据结构总览

| 数据结构 | 阶段 | 用途 | legacy 参考 | 当前判断 |
| --- | --- | --- | --- | --- |
| `WorldSurveyContext` | W | 记录一次 W 粗扫上下文。 | 旧 W 阶段扫描上下文。 | 新建。 |
| `WorldPatchMap` | W | 给 T 阶段消费的粗地貌地图。 | W3 大陆聚类、W4 地貌图集。 | 复用思路，新建结构。 |
| `WorldFeatureGrid` | W | v1.2 记录 micro-sampling 后的稳健特征。 | 无直接旧结构。 | 新增。 |
| `RealmProfile` | T1 | 国度设定。 | `TerritoryBlueprint`。 | 保留高层概念，删掉低层扫描参数。 |
| `RealmCandidateMapPackage` | T1 | 给 AI 选坐标的候选图包。 | 旧 T1 候选图 / 候选簇。 | 改成图上直接选坐标。 |
| `RealmCoordinateSelection` | T2 | 保存 AI 选点和程序校验结果。 | 旧 T1 / T2 selection artifact。 | 新建，替代选簇 / 选方向。 |
| `RealmSeed` | T2 | T3 扩张种子。 | 旧 territory config。 | 保留用途，结构重写。 |
| `CapitalCityIntent` | T2 | 无坐标首都意图。 | 旧 T3 后只有首都语义。 | 保留“首都必定存在”，最终坐标交给 T4。 |
| `RealmTerritoryMap` | T3 | 国度扩张结果。 | `TerritoryManager` 扩张结果。 | 复用算法，重写实现。 |
| `TerritoryRepairLog` | T3 | v1.2 记录飞地、孔洞和边界修复。 | 旧实现无稳定产物。 | 新增。 |
| `RealmCityCandidateMapPackage` | T4 | v1.2 单国度城市候选图包。 | 旧实现无稳定产物。 | 新增。 |
| `CitySeedRegistry` | T4 | 全城市名册。 | 旧 T4 不匹配。 | 新建。 |
| `ScoreManifest` | 验收 | v1.2 记录质量评分、硬阻断和人工 review。 | 无旧结构。 | 新增。 |

## 持久化 checkpoint 恢复

`RealmRun` 是当前进程内工作状态，不是跨客户端生命周期的唯一真值。服务重启后的恢复顺序为：

1. 以 sealed `world_survey_manifest.json`、tile snapshots 和 `world_feature_grid.json` 重建 W 内存模型。
2. T1 同时存在 `realm_profiles.json`、`candidate_map_packages.json`、`t1_manifest.json` 时恢复 profiles，并由 sealed W 确定性重建候选内存索引。
3. T2 同时存在 `realm_coordinate_selections.json`、`realm_seeds.json`、`capital_city_intents.json`、`t2_report.json` 时恢复已完成或已拒绝的选择状态。历史 `capital_city_seeds.json` 只作迁移输入。
4. T3 同时存在 `realm_territory_map.json`、`t3_report.json` 时恢复 territory、统计、归一化比例、行动预算和地形成本。
5. T4 同时存在 `city_seed_registry.json`、`t4_report.json` 且 `territoryMapId` 与 T3 一致时恢复城市名册；`score_manifest.json` 存在时一并恢复评分。

恢复不得修改任何来源文件。完整 checkpoint 内部身份、realm、candidate package、grid、continent、patch、survey 或 territory 引用不一致时必须返回 `REALM_CHECKPOINT_INVALID`。缺少一部分阶段文件只表示该阶段未形成可恢复 checkpoint，不允许据此伪造完成状态。

## v1.2 扩展口径

v1.2 不废弃 v1.1 的 `WorldPatchMap`、`RealmTerritoryMap` 和 `CitySeedRegistry`。实现可先保持 v1.1 字段兼容，同时新增 clean id、feature stats、repair log、单国度城市候选图包和 `score_manifest.json`。正式消费层应优先读取 v1.2 clean / score 字段；缺失时只能按 v1.1 smoke 口径验收，不能宣称 strict 质量通过。

## W 原生气候补充图层（2026-09-28）

RTF 支持时，W 在独立 sidecar 保存原生气候，不从 Minecraft 群系标签反推。新扫描自动生成；旧 sealed 扫描在重新进入世界时补采。补采必须核对世界种子、维度及既有 W 的 provider/preset 指纹，不修改地貌、国度和城市的已完成产物。非 RTF 或字段不支持时不伪造数据。

- `world_climate_grid.json`：schema `geomantia_world_climate.v1`，保存 W 对齐范围、原点、格数、步长、configHash、sourceFingerprint、columns 与 cells。
- 按每个 W 粗格中心单点采样（默认步长 128，偏移 64）；不冒充高度图的每格 16 点微采样平均。
- 每行依次为 `gridX, gridZ, blockX, blockZ, regionTemperature, regionMoisture, temperature, moisture, water`。四项气候值都是 RTF Cell 原生字段。
- `world_temperature_preview.png` 使用 `regionTemperature`，`world_moisture_preview.png` 使用 `regionMoisture`，与 RTF 0.0.5a 温湿度预览所取字段相同；输出配色独立。水域在图上遮盖为蓝色，JSON 仍保留其气候值。
- 数值是生成器无量纲参数，不是摄氏度、实际湿度、降雨量或季节；最终 `temperature/moisture` 与区域 `region*` 分开保存，不混用。
- `world_climate_manifest.json` 最后发布，记录 sealed、来源、采样数、耗时、原始范围和三份产物 SHA-256。再次进入时校验后复用；缺失、损坏或不匹配的 sidecar 需重采。中断不发布半成品完成标记。

## WorldSurveyContext

记录一次世界粗扫的配置和坐标上下文。

W 范围由 `config/geomantia/world_survey.json` 的 `planningRadiusBlocks` 配置。2026-09-28 用户要求扩大到 RTF 预览尺度，默认配置半径由 12288 改为 **19200 格**，中心仍为 `(0,0)`。对应已安装 RTF 0.0.5a 最大预览（Zoom=1）的 256×150=38400 格边长；RTF 预览中心可能随出生模式偏移，本项只对齐覆盖尺度。W 按 512 格分块向外对齐，实际 X/Z 范围为 `[-19456,19455]`，边长 38912；128 格粗采样为 304×304，共 92416 格，固定采样密度下约为旧 12288 半径扫描面积的 2.5069 倍。已有显式配置保持原值，需单独修改；本次已同步用户当前 PCL 实例配置，其他实例不自动迁移。旧 sealed 扫描不会因配置或默认值改变而自动扩展。下方 8192 示例仅说明数据格式。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schemaVersion` | string | 是 | 结构版本。 |
| `surveyId` | string | 是 | 本次粗扫 ID。 |
| `dimensionId` | string | 是 | Minecraft 维度 ID。 |
| `worldSeed` | long/string | 建议 | 世界 seed；无法直接记录时可写 hash。 |
| `cellStepBlocks` | int | 是 | 粗 cell 步长，单位 block。 |
| `gridOriginBlock.x` | int | 是 | grid 原点对应的世界方块 X。 |
| `gridOriginBlock.z` | int | 是 | grid 原点对应的世界方块 Z。 |
| `gridSize.width` | int | 是 | grid 宽度，单位 cell。 |
| `gridSize.height` | int | 是 | grid 高度，单位 cell。 |
| `sealed` | boolean | 是 | 配置范围内所有 tile 完成且全局 patch 汇总完成后为 `true`。T 阶段只接受 sealed survey。 |
| `scanBounds` | object | 是 | 本次可规划世界范围，记录中心、半径和 block 边界。 |
| `surveyStats` | object | 是 | 记录 tile 数、缓存命中、失败数、耗时和产物数据量。 |
| `microSampleStrideBlocks` | int? | v1.3 | W feature 提取步长，默认 `32`。 |
| `metricSampleStrideBlocks` | int? | v1.3 | `microSampleStrideBlocks` 的契约别名，用于强调这是指标采样尺度。 |
| `localSlopeRadiusBlocks` | int? | v1.3 | micro sample 周边局部坡度半径，默认 `8`。 |
| `microSamplingImplemented` | boolean? | v1.3 | 是否真实执行 cell 内 micro-sampling。strict 验收应为 `true`。 |
| `microSampleBudget` | long? | v1.3 | 本次 W survey 计划采样预算。当前固定 stride 模式为 `gridCellCount * microSampleBudgetPerCell`。 |
| `microSampleBudgetPerCell` | int? | v1.3 | 单个 planning cell 的 micro sample 预算；例如 `cellStepBlocks=128`、`microSampleStrideBlocks=32` 时为 `16`。 |
| `microSampleCount` | long? | v1.3 | 本次 W survey 实际 micro sample 总数。 |
| `adaptiveSampling` | boolean? | v1.3 | 是否启用自适应加密；当前固定 stride 实现必须显式写 `false`，不得伪装成自适应。 |
| `configHash` | string? | v1.3 | seed / 维度 / 范围 / step / stride / slope radius 等配置哈希，用于 tile 和 feature cache 校验。 |
| `source.terrainProvider` | object? | 生成器快路径 | W 实际采样提供器追溯，字段同下述 manifest `terrainProvider`；用于解释本轮世界地貌来源。 |
| `metricScales` | object? | v1.6 | 多尺度 GIS 派生指标的物理尺度说明，例如 `scanHeightRank=scan_bounds`、`localScaleBlocks=512`、`regionalScaleBlocks=2048`、`plateauCoreScaleBlocks=512`、`plateauOuterScaleBlocks=1536`、`plateauProminenceThreshold`、`rankDriftThreshold`。 |
| `scoreManifest` | string? | v1.2 建议 | `score_manifest.json` 路径。 |
| `source.gisRefreshJobId` | string? | 否 | 若来自 GIS refresh，记录 job ID。 |
| `source.sampleMode` | string? | 否 | 例如 `prior`。 |
| `createdAt` | string | 是 | 生成时间。 |

示例：

```json
{
  "schemaVersion": "realm_planning.v1.1",
  "surveyId": "overworld_seed_123_step128_r0",
  "dimensionId": "minecraft:overworld",
  "worldSeed": 123,
  "cellStepBlocks": 128,
  "sealed": true,
  "gridOriginBlock": { "x": -8192, "z": -8192 },
  "gridSize": { "width": 128, "height": 128 },
  "scanBounds": {
    "centerBlockX": 0,
    "centerBlockZ": 0,
    "planningRadiusBlocks": 8192,
    "minBlockX": -8192,
    "minBlockZ": -8192,
    "maxBlockX": 8191,
    "maxBlockZ": 8191
  },
  "surveyStats": {
    "durationMs": 120000,
    "tileCount": 1024,
    "scannedTileCount": 1024,
    "cachedTileCount": 0,
    "failedTileCount": 0,
    "artifactBytes": 12345678
  },
  "source": {
    "sourceType": "world_survey_tiles",
    "worldSurveyManifest": "world_survey_manifest.json",
    "sampleMode": "prior"
  },
  "createdAt": "2026-06-11T00:00:00Z"
}
```

## WorldSurveyManifest

W 调度层还必须写出 `world_survey_manifest.json`，用于断点续扫和真实验收统计。它不是 T 阶段主要消费数据，但它是 W 是否完整 sealed 的审计依据。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schemaVersion` | string | 是 | 结构版本。 |
| `surveyId` | string | 是 | 对应 `WorldSurveyContext`。 |
| `status` | enum | 是 | `sealed` 或 `failed`。 |
| `config` | object | 是 | 维度、seed、中心、`planningRadiusBlocks`、`cellStepBlocks`、`microSampleStrideBlocks`、`localSlopeRadiusBlocks`、`sampleMode`、`resumePolicy`、`preferGeneratorNativeTerrain` 和 `terrainProvider`。 |
| `scanBounds` | object | 是 | block 级扫描边界和直径。 |
| `grid` | object | 是 | grid 原点、宽高、cell 数。 |
| `stats` | object | 是 | `tileCount`、`scannedTileCount`、`cachedTileCount`、`failedTileCount`、`artifactBytes`、`microSampleBudget`、`microSampleBudgetPerCell`、`microSampleCount`、`adaptiveSampling` 和实际 `terrainProvider`。 |
| `tiles[]` | array | 是 | 每个 tile / GIS Region 的坐标、状态、cache 路径、`configHash` 和错误信息。 |

`terrainProvider` 必须包含 `generatorNativeRequested`、`providerId`、`sourceKind`、`fastPath`、`fallbackReason`、`sourceFingerprint` 和 `samplingSemantics`。完整 provider 身份必须进入 `configHash`；开关变化、RTF 设置变化或实际 provider 变化时，不得命中旧 W tile / feature cache。

W 完成后必须额外写出 `world_biome_preview.png`，并通过 `artifacts.worldBiomePreview` 返回。每个 W cell 使用 `biomeHist` 中计数最高的最终 Minecraft biome id 着色；它与 `world_patch_preview.png` 分离，不改变 W Patch 分类。

## WorldSurveyProgress

开发期 W 扫描可额外写出 `world_survey_progress.json`，并按约 1 秒间隔输出同内容的 debug 日志。该文件用于观察长时间扫描，不是 T 阶段输入，也不替代 sealed 的 `world_survey_manifest.json`。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `status` | enum | `queued`、`running`、`completed`、`failed`。 |
| `phase` | enum | `tile_scan`、`micro_sampling`、`complete`。 |
| `elapsedMs` / `phaseElapsedMs` | long | 总耗时和当前阶段耗时。 |
| `phaseProgressPercent` | number | 当前阶段完成百分比；tile 和 micro-sampling 分开计量。 |
| `estimatedRemainingMs` | long | 按当前阶段速度估算的剩余时间；无法估算时为 `-1`。 |
| `tileSpeedPerSecond` | number | 每秒完成的 Region tile 数。 |
| `microCellsPerSecond` / `microSamplesPerSecond` | number | 当前阶段每秒完成的 W cell / micro sample 数。 |
| `tiles` | object | `processed`、`total`、`scanned`、`cached`、`failed`。 |
| `microSampling` | object | `completedCells`、`totalCells`、`completedSamples`、`totalSamples`。 |
| `currentTile` | object? | 当前 Region tile 的坐标和采样模式。 |

## WorldPatchMap

T 阶段消费的粗地貌地图。实现可以内部建索引，但落盘契约至少要能按 grid 坐标和 patch id 追溯。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schemaVersion` | string | 是 | 结构版本。 |
| `surveyId` | string | 是 | 对应 `WorldSurveyContext`。 |
| `cells[]` | array | 是 | 粗 cell 列表。 |
| `patches[]` | array | 是 | patch 摘要。 |
| `continents[]` | array | 是 | 大陆 / 大区摘要。 |
| `cleaningSummary` | object? | v1.2 建议 | land mask 清洗、小斑块合并、孔洞填补和跨 tile merge 摘要。 |

`cells[]`：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `gridX` | int | 是 | 粗 grid X。 |
| `gridZ` | int | 是 | 粗 grid Z。 |
| `blockX` | int | 是 | cell 代表点或左上角 block X，具体语义必须在 manifest 固定。 |
| `blockZ` | int | 是 | cell 代表点或左上角 block Z。 |
| `continentId` | string? | 陆地必填 | 所属大陆 / 大区。 |
| `patchId` | string? | 已分类必填 | 所属 patch。 |
| `landWater` | enum | 是 | `land`、`water`、`shore`、`unknown`。 |
| `landform` | enum/string | 是 | 粗地貌类型。 |
| `baseLandform` | enum/string? | v1.2 建议 | 清洗后的主地貌；建议 `water`、`shore`、`lowland`、`plateau`、`upland`、`ridge`、`valley`、`unknown`。 |
| `landformTags[]` | string[] | v1.2 建议 | `steep`、`cliff`、`water_edge`、`seacoast`、`riverbank`、`lakeshore`、`coastal`、`wet`、`rugged`、`mountain_front`、`harbor_candidate` 等二级标签。v1.5 起，`cellStepBlocks>=64` 且有 micro 指标时，正式 `cliff` / `steep` 必须由局部 `slopeStats` 支撑；coarse GIS 的 cliff 只能进入 `cliff_candidate` / `micro_contradiction` 等诊断 tag；`coastal` 保留为 `seacoast` 兼容别名，不再表示所有水边；water / unknown 主体不生成正式 `water_edge`。v1.6 起可出现 `mixed_cell`、`low_confidence`、`rank_drift`、`boundary_truncated`、`open_water_unknown` 等诊断 tag。 |
| `overlayTags[]` | string[]? | v1.6 | 非互斥叠加层，当前从 `landformTags[]` 中筛出 `cliff`、`steep`、`water_edge`、水边类型、`mixed_cell`、`low_confidence`、`rank_drift`、`mountain_front` 等，供预览 / 审计 / PCG suitability 消费。 |
| `landformConfidence` | number? | v1.6 | `0..1` 主地貌置信度，由 rank 稳定性、局部坡度、形态和水边不确定性派生。 |
| `landformEvidence[]` | array? | v1.6 | 多尺度证据列表，记录 `scan_height_rank`、`local_height_rank`、`regional_height_rank`、`dev_local`、`dev_regional`、`roughness_local`、`plateau_prominence`、`plateau_core_flat_support`、`geomorphon` 等证据名、数值和说明。 |
| `debugReasons[]` | string[]? | v1.6 | 开发期解释字符串，用于人工 TP 抽样时理解 base landform、rank、DEV、roughness、plateau prominence/support、geomorphon 和水边来源。 |
| `waterEdgeType` | enum/string? | v1.5/v1.6 | 可分配水边 cell 的水边类型：`seacoast`、`riverbank`、`lakeshore`、`boundary_truncated`。`boundary_truncated` 表示扫描边界截断水体，不能直接当作高置信海岸。 |
| `waterComponentId` | string? | v1.5 调试 | 最近水体连通域 id；用于解释 `waterEdgeType` 来源。 |
| `waterComponentType` | enum/string? | v1.6 | 最近水体连通域语义：`open_water`、`river_like`、`lake_like`、`boundary_truncated`。 |
| `waterComponentAreaCells` | int? | v1.5 调试 | 最近水体连通域面积，单位 W cell。 |
| `waterBoundaryConfidence` | number? | v1.6 | 水体边界置信度；扫描边界截断且无 ocean / 大水体证据时应降低。 |
| `continentIdClean` | string? | v1.2 建议 | 清洗 / 合并后的大陆 id。 |
| `patchIdClean` | string? | v1.2 建议 | 清洗 / 合并后的 macro patch id。 |
| `heightAvg` | number? | 建议 | 平均高度。 |
| `slopeAvg` | number? | 建议 | 平均坡度。 |
| `relativeHeightRank` | number? | v1.5 | 本次扫描可分配陆地内的相对高度分位，`0..1`；v1.6 起等价于 `scanHeightRank`，只能作为辅助特征，不能单独决定 `ridge` / `plateau` / `lowland`。 |
| `scanHeightRank` | number? | v1.6 | `relativeHeightRank` 的明确别名，强调其依赖本次扫描范围。 |
| `localHeightRank` | number? | v1.6 | 当前 cell 在约 512 block 局部窗口内的高度分位。 |
| `regionalHeightRank` | number? | v1.6 | 当前 cell 在约 2048 block 区域窗口内的高度分位。 |
| `heightRankStability` | number? | v1.6 | 多尺度 rank 一致性，低值表示扫描 / 尺度敏感。 |
| `terrainMetrics` | object? | v1.6 | 多尺度派生指标集合，包含 local / regional scale、TPI、DEV、roughness、relief、`plateauCoreScaleBlocks`、`plateauOuterScaleBlocks`、`plateauCoreMeanHeight`、`plateauOuterMeanHeight`、`plateauProminence`、`plateauCoreFlatSupport`、`geomorphonClass`、`supportConfidence` 等。 |
| `heightStats` | object? | v1.2 建议 | `p10`、`p50`、`p90`、`robustRelief`。 |
| `slopeStats` | object? | v1.2 建议 | `mean`、`p90`、`steepFrac`。 |
| `barrierCost` | number/object? | v1.3 | 当前实现写单 cell 通行成本；后续可扩展为 `north/east/south/west` edge cost。 |
| `waterFrac` | number? | v1.3 | cell 内 micro sample 水体比例。 |
| `microSampleCount` | int? | v1.3 | 本 cell 实际 micro sample 数。 |
| `biomeHist` | object? | v1.3 | cell 内 biome 采样直方图。 |
| `waterDistanceBlocks` | number? | 建议 | 到水体或岸线距离，单位 block。 |
| `flags[]` | string[] | 否 | `coastal`、`lowland`、`mountain_edge` 等标签。 |

## WorldFeatureGrid

v1.3 中，`WorldFeatureGrid` 记录 planning cell 内真实 micro-sampling 的稳健统计。当前实现由 `WorldSurveyRunner` 在 W survey 后按 `microSampleStrideBlocks` 构造 micro sample，聚合后写入 `world_feature_grid.json`，并把同一统计内嵌到 `WorldPatchMap.cells[]`。`configHash` 一致时可复用 feature grid 缓存。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `surveyId` | string | 是 | 来源 W survey。 |
| `cellStepBlocks` | int | 是 | planning cell 尺寸。 |
| `microSampleStrideBlocks` | int | 是 | cell 内采样步长，建议 `16` 或 `32`。 |
| `metricSampleStrideBlocks` | int | 是 | 指标采样步长别名。 |
| `localSlopeRadiusBlocks` | int | 是 | 局部坡度采样半径。 |
| `microSamplingImplemented` | boolean | 是 | 是否真实执行 micro-sampling。 |
| `microSampleCount` | long | 是 | 全部 cell 的 micro sample 总数。 |
| `configHash` | string | 是 | 与 `world_survey_manifest.json` 对齐的配置哈希。 |
| `cells[]` | array | 是 | 每个 planning cell 的特征统计。 |

`cells[]` 建议包含：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `gridX/gridZ` | int | planning grid 坐标。 |
| `heightP10/P50/P90` | number | 稳健高度分位。 |
| `robustRelief` | number | `P90 - P10`。 |
| `slopeMean/slopeP90/steepFrac` | number | 坡度统计。 |
| `roughnessTri` | number | 粗糙度。 |
| `dev32/dev64/dev128` | number | 多尺度相对地形位置。 |
| `waterFrac` | number | 水体占比。 |
| `microSampleCount` | int | 本 planning cell 实际样本数。 |
| `biomeHist` | object | biome 直方图。 |
| `shoreDist` | number | 到岸线 / 水体距离。 |
| `passability` | number | 规划通行性。 |
| `barrierCostN/E/S/W` | number | 边穿越成本。 |

## TagAudit

v1.5 开发期调试产物，用少量抽样点的局部精确扫描评估 W 粗扫 tag 正确率。v1.6 起，Tag Audit 的抽样单位升级为 W coarse cell：每个样本 cell 同时输出代表点、point reference 和 cell reference，用于区分“玩家 TP 点观察”和“128x128 cell 面域标签”之间的尺度差异。它只在 `runTagAudit=true` 或开发工具显式触发时输出，不属于普通玩家开局必跑流程。

Tag Audit 的 reference tags 使用比 W 粗扫更密的局部扫描事实复判：

| reference tag | 判定口径 |
| --- | --- |
| `steep` | `slopeP90 >= 14` 或 `steepFrac >= 0.25`。 |
| `cliff` | `slopeP95 >= 18` 且 `steepFrac >= 0.55`；如果 `waterFrac` 在 `0.05..0.95` 的水陆混合区，`steepFrac` 阈值提升到 `0.65`。 |
| `water_edge` | W 正式输出只用于可分配陆地 / shore 边缘；Tag Audit reference 仍用局部 `waterFrac` 在 `0.05..0.95` 之间估算水陆混合事实。 |
| `seacoast` / `coastal` | W 正式输出优先由最近水体连通域判定：大水体、触扫描边界、或含 ocean biome。 |
| `riverbank` | W 正式输出优先由最近水体连通域判定：river biome、狭长或较小水体组件。 |
| `lakeshore` | W 正式输出优先由最近水体连通域判定：闭合且非狭长的内陆水体组件。 |

W 正式 tag 与 Tag Audit reference 使用同一套语义，但 W 在高 step 下基于每个粗采样点的 micro 指标判定，Tag Audit 则对抽样点周围 `auditRadiusBlocks` 范围做局部精扫，用于开发期估算 precision / recall。

### tag_audit_samples.json

数组，每项记录一个抽样点：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `gridX/gridZ` | int | W planning grid 坐标，v1.6 起表示抽中的 W coarse cell。 |
| `blockX/blockZ` | int | 推荐 TP 点 block 坐标，可直接用于人工传送复核。v1.6 起它不再必然是 cell 中心，而是按标签选择的代表点。 |
| `cellMinBlockX/cellMinBlockZ` | int | 来源 W coarse cell 的最小 block 坐标，用于追溯 `WorldPatchMap.cells[]`。 |
| `auditLayer` | string | 本点来自的抽样分层，例如 `confirmed_cliff`、`coarse_cliff_micro_rejected`、`water_edge`、`upland_macro`、`land_baseline`。 |
| `tpCommand` | string | 开发期人工复核辅助命令，例如 `/tp @s <blockX> ~ <blockZ>`。 |
| `baseLandform` | string | W 输出主地貌。 |
| `coarseLandform` | string | GIS coarse landform 原值。 |
| `cellReferenceBaseLandform` | string? | v1.6 | 对整个 W cell 或 cell 内规则网格精扫得到的面域 reference 主地貌。 |
| `mixedCell` | boolean? | v1.6 | cell 内是否存在水陆混合、缓坡高差或多种 reference 并存。 |
| `representativePointMismatch` | boolean? | v1.6 | 推荐 TP 点的 point reference 是否与 cell reference 不一致。 |
| `wTags[]` | string[] | W 输出 tags。 |
| `referenceTags[]` | string[] | 兼容字段，v1.6 起等价于 `pointReferenceTags[]`。 |
| `pointReferenceTags[]` | string[]? | v1.6 | 推荐 TP 点周围局部精扫重新判定的参考 tags。 |
| `cellReferenceTags[]` | string[]? | v1.6 | 对整个 W coarse cell 面域精扫汇总得到的参考 tags。 |
| `representativePoints` | object? | v1.6 | `cellCenter`、`highestMicroPoint`、`lowestMicroPoint`、`maxSlopeMicroPoint`、`recommendedTpPoint`，每个点包含 block 坐标和 `/tp` 命令。 |
| `cliffMatch/steepMatch/coastalMatch` | boolean | 关键 tag 是否和 reference 一致。 |
| `auditMetrics` | object | 兼容字段，v1.6 起等价于 `pointReferenceMetrics`。 |
| `pointReferenceMetrics` | object? | v1.6 | 推荐 TP 点周围局部精扫指标。 |
| `cellReferenceMetrics` | object? | v1.6 | 整个 W coarse cell 面域精扫指标。 |

`auditMetrics` 至少包含：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `sampleCount` | int | 局部精扫样本数。 |
| `heightP05/P50/P95` | number | 高度分位。 |
| `reliefP95P05` | number | 局部稳健起伏。 |
| `slopeP90/slopeP95/slopeMax` | number | 局部坡度分布。 |
| `steepFrac` | number | 局部陡坡样本占比。 |
| `waterFrac` | number | 局部水体占比。 |
| `shoreMixScore` | number | 水陆混合程度。 |
| `dominantBiome` / `biomeHist` | string / object | 局部 biome 事实。 |

### tag_audit_report.json

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `runId` | string | 来源 run。 |
| `sampleSeed` | string | 本轮抽样 seed；同一 run 可换 seed 抽另一批点。 |
| `sampleCount` | int | 实际抽样点数量。 |
| `auditRadiusBlocks` | int | 局部精扫半径。 |
| `auditStrideBlocks` | int | 局部精扫步长。 |
| `centerSlopeRadiusBlocks` | int | 局部坡度半径。 |
| `sampleLayerCounts` | object | 各抽样分层实际入样数量。 |
| `tagMetrics` | object | 按 tag 统计 `precision`、`recall`、TP / FP / FN / TN。 |
| `cellTagMetrics` | object? | v1.6 | 使用 `cellReferenceTags[]` 统计的 tag user / producer accuracy、precision、recall。 |
| `baseLandformMetrics` | object? | v1.6 | 使用 `cellReferenceBaseLandform` 统计主地貌 user / producer accuracy。 |
| `confusionMatrix` | object | 关键 tag 的混淆矩阵。 |
| `cellConfusionMatrix` | object? | v1.6 | 使用 cell reference 的 tag 混淆矩阵。 |
| `cliffFalsePositiveExamples[]` | array | 前若干个 cliff 误报样例坐标。 |
| `cliffFalseNegativeExamples[]` | array | 前若干个 cliff 漏报样例坐标。 |
| `microContradictionAcceptedRate` | number | 被 micro 拒绝的 coarse cliff 中，局部精扫仍判定 cliff 的比例。 |
| `samplingUnit` | string? | v1.6 | 当前应为 `w_coarse_cell`。 |
| `responseDesign` | string? | v1.6 | 当前应为 `cell_reference_and_representative_point`。 |
| `referenceCellStrideBlocks` | int? | v1.6 | cell reference 精扫步长。 |
| `referenceCellRadiusBlocks` | int? | v1.6 | cell reference 精扫半径，通常为 `cellStepBlocks/2`。 |
| `mixedCellRate` | number? | v1.6 | 样本中 mixed cell 比例。 |
| `representativePointMismatchRate` | number? | v1.6 | 推荐 TP 点 reference 与 cell reference 不一致的比例。 |
| `rankDriftRate` | number? | v1.6 | 样本中 W 输出 `rank_drift` 的比例。 |
| `overallAccuracy` / `areaAdjustedAccuracy` | number? | v1.6 | 主地貌整体准确率；首版实现中 area-adjusted 与 overall 使用同一抽样权重，后续可按分层面积修正。 |

`patches[]`：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `patchId` | string | 是 | patch ID。 |
| `continentId` | string? | 陆地 patch 必填 | 所属大陆。 |
| `landform` | enum/string | 是 | 主地貌。 |
| `areaCells` | int | 是 | 面积，单位 cell。 |
| `centerGrid.x` / `centerGrid.z` | int | 是 | patch 中心 grid 坐标。 |
| `centerBlock.x` / `centerBlock.z` | int | 是 | patch 中心 block 坐标。 |
| `boundsGrid` | object | 是 | grid 外接范围。 |
| `summary` | object | 否 | 海岸占比、平坦占比、水体可达性等。 |

`continents[]`：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `continentId` | string | 是 | 大陆 / 大区 ID。 |
| `areaCells` | int | 是 | 面积，单位 cell。 |
| `centerBlock.x` / `centerBlock.z` | int | 是 | 中心 block 坐标。 |
| `primaryLandforms[]` | string[] | 是 | 主要地貌。 |

## RealmProfile

国度配置，表达高层设定和扩张倾向，不直接承载底层扫描参数。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `realmId` | string | 是 | 国度 ID。 |
| `name` | string | 是 | 国度名称。 |
| `targetContinentId` | string | 是 | 目标大陆 / 大区。 |
| `theme` | string | 是 | 国度主题。 |
| `cultureTags[]` | string[] | 否 | 文化标签。 |
| `industryTags[]` | string[] | 否 | 产业标签。 |
| `materialTags[]` | string[] | 否 | 材料倾向。 |
| `landformPreferences[]` | string[] | 否 | 偏好地貌。 |
| `avoidLandforms[]` | string[] | 否 | 避免地貌。 |
| `scalePlan` | object | 是 | 面积比例和国度量级计划。 |
| `expansionStyle` | object | 是 | 地貌、形状和竞争倾向。 |

`scalePlan` 控制“占多少”。它的分母不是 Minecraft 理论世界边界，而是目标大陆 / 目标大区内可分配 land cell 总数。AI 可以给初始数值，程序必须归一化和 clamp：

| 字段 | 范围 / 枚举 | 必填 | 说明 |
| --- | --- | --- | --- |
| `priority` | `minor`、`normal`、`major`、`empire` | 是 | 叙事量级。 |
| `targetAreaRatio` | `0..1` | 是 | 目标面积比例。 |
| `minAreaRatio` | `0..1` | 是 | 最小可接受比例。 |
| `maxAreaRatio` | `0..1` | 是 | 最大可接受比例。 |
| `normalizationGroup` | string | 是 | 逻辑分组标签，通常为 continent id，但不得作为地格大陆 ID；比例分母以 `targetContinentId` 指定的实际大陆为准，同大陆国度共同参与归一化和竞争。 |

`expansionStyle` 控制“怎么长”。数值建议先用语义化范围，不让 AI 填 T3 算法裸参数：

比例是大陆面积的绝对份额，不是必须铺满大陆的相对权重。目标总和小于 1 时保留原比例；超额时按比例缩减并保留 min/max 边界，最小比例总和超过 1 时明确拒绝。不得 clamp 后再次归一化突破 max。`action_budget` 保留行动力/地形竞争，但最大面积仍是硬上限；`quota_frontier` 以归一化目标配额停止。`allowUnclaimedLand=false` 不得覆盖明确的面积上限或将未申请土地强塞给国家。

| 字段 | 范围 / 枚举 | 说明 |
| --- | --- | --- |
| `waterAffinity` | `0..1` | 亲水程度，越高越偏好河流、湖泊和海岸附近。 |
| `mountainAffinity` | `-1..1` | 山地倾向；负数避山，正数亲山。 |
| `forestAffinity` | `-1..1` | 森林倾向；负数避森林，正数亲森林。 |
| `compactness` | `0..1` | 紧凑程度，越高越倾向短边界和集中领土。 |
| `coastalBias` | `0..1` | 沿海倾向。 |
| `resourceSeeking` | `0..1` | 追资源 patch 的倾向。 |
| `borderPressure` | `0..1` | 扩张竞争性，越高越愿意贴近边境。 |
| `seaCrossingPolicy` | `none`、`limited`、`allowed` | 跨海扩张策略；T3 可进一步限制。 |

示例：

```json
{
  "realmId": "realm_salt_kingdom",
  "name": "盐风王庭",
  "targetContinentId": "continent_0",
  "theme": "coastal trade realm",
  "scalePlan": {
    "priority": "major",
    "targetAreaRatio": 0.32,
    "minAreaRatio": 0.22,
    "maxAreaRatio": 0.40,
    "normalizationGroup": "continent_0"
  },
  "expansionStyle": {
    "waterAffinity": 0.85,
    "mountainAffinity": -0.35,
    "forestAffinity": 0.1,
    "compactness": 0.45,
    "coastalBias": 0.9,
    "resourceSeeking": 0.55,
    "borderPressure": 0.35,
    "seaCrossingPolicy": "limited"
  }
}
```

## RealmCandidateMapPackage

T1 产物，供 AI 和程序共同使用。该图包只表达目标大陆的合法 scope，不按国度文化或兴趣类型做差异化；同一大陆的多个国度可以引用内容相同的参考图。正常 AI 主链通过 Patch Explorer 探索并提交选择凭证；直接看图提交 grid 坐标只保留为兼容方式，程序仍以 manifest 做最终校验。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `packageId` | string | 是 | 图包 ID。 |
| `realmId` | string | 是 | 对应国度。 |
| `surveyId` | string | 是 | 对应 W 粗扫。 |
| `candidateMapImage` | string | 是 | 候选图路径。 |
| `mapRole` | enum | 是 | 固定为 `continent_scope_reference`。 |
| `scopeBasis` | enum | 是 | 当前固定为 `target_continent_assignable_land`。 |
| `profileDifferentiated` | boolean | 是 | 当前固定为 false，明确参考图不体现文明兴趣差异。 |
| `selectionMode` | enum | 是 | 固定为 `patch_explorer_primary`。 |
| `gridLegend.originBlock` | object | 是 | grid 原点。 |
| `gridLegend.cellStepBlocks` | int | 是 | grid cell 步长。 |
| `gridLegend.coordinateFormat` | string | 是 | 例如 `gridX,gridZ`。 |
| `allowedPatches[]` | string[] | 是 | 可选 patch。 |
| `blockedCells[]` | array | 否 | 禁用 cell 与原因。 |
| `occupiedSeeds[]` | array | 否 | 已有国度种子，用于距离约束。 |
| `selectionRules` | object | 是 | 必须含 Patch Explorer `primaryFlow`、`directGridSubmission=compatibility_only` 和兼容返回格式。 |

`blockedCells[]` 至少包含：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `gridX` | int | 是 | 禁用 cell X。 |
| `gridZ` | int | 是 | 禁用 cell Z。 |
| `reason` | string | 是 | 禁用原因。 |

## RealmCoordinateSelection

T2 产物，记录 AI 原始选择、程序转换和校验结果。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `selectionId` | string | 是 | 选择记录 ID。 |
| `realmId` | string | 是 | 对应国度。 |
| `packageId` | string | 是 | 来源候选图包。 |
| `selectedBy` | enum | 是 | `ai`、`human`、`debug`。 |
| `primaryGrid.x` / `primaryGrid.z` | int | 是 | AI 返回的主 grid 坐标。 |
| `primaryBlock.x` / `primaryBlock.z` | int | 是 | 程序换算后的 block 坐标。 |
| `alternatesGrid[]` | array | 否 | 备选 grid 坐标。 |
| `reason` | string | 否 | 选择理由。 |
| `validation.status` | enum | 是 | `accepted`、`rejected`、`accepted_with_snap`。 |
| `validation.continentId` | string? | 通过时建议 | 校验命中的大陆。 |
| `validation.patchId` | string? | 通过时建议 | 校验命中的 patch。 |
| `validation.snapApplied` | boolean | 是 | 是否发生 snap。 |
| `validation.warnings[]` | string[] | 否 | 警告。 |
| `validation.errors[]` | string[] | 拒绝时必填 | 拒绝原因。 |

通过 Patch Explorer 进入 T2 时，`primaryGrid` 由 `PatchSelection.suggestedAnchor` 转换而来，最终仍必须经过现有 `RealmPlanningService.selectT2` 校验与有限 snap；选择凭证不绕过跨大陆、跨海、禁用 patch 和种子冲突校验。

## PatchExplorerSession / CandidatePage / PatchSelection

跨尺度探索产物使用独立 schema：

| 产物 | schemaVersion | 关键字段 |
| --- | --- | --- |
| 会话 | `patch_explorer_session.v0.1` | `sessionId`、`runId`、`scopeType`、`scopeId`、`candidateModel`、`candidateBasis`、`sourceArtifacts[]`、`sourceIdentity`、`scopeSnapshotIdentity`、`displayedCandidates[]`；三个 scope 均冻结 `preferGeneratorNativeTerrain`。T2/T4 另含 `tScaleRefinementArtifact`、`tScaleRefinementIdentity`、`tScaleRefinementCacheHit`。 |
| 紧凑 scope 快照 | `patch_explorer_scope_snapshot.v0.1` | T2/T4 只冻结共享 `tScaleRefinementArtifact` 及内容 identity；City D4 和兼容路径内联候选 cell、来源 patch、scope 裁剪、hard occupied 扣除结果。用于避免翻页重读大型 W JSON，并避免同范围多国重复展开百 MB T cell。 |
| T 尺度共享 refinement | `t_scale_refinement_cache.v0.1` | 一次 T 尺度重采样、分类和跨 region 合并结果；缓存 key 必须绑定规范化搜索 cell、实际 provider / dimension / source fingerprint / sampling semantics、尺度和算法版本。会话仅引用，不复制内容。 |
| 候选页 | `patch_explorer_candidate_page.v0.1` | `interestTypes[]`、`page`、`pageSize`、`typePages[]`（各自含 `nextPageToken` 与 `candidates[]`）、`relations[]`；每个候选含 `terrainPreview`，artifact 以 `candidateTerrainPreviews.<candidateId>` 汇总。 |
| 选择 | `patch_selection.v0.1` | `selectionId`、`sessionId`、`scopeType`、`scopeId`、`candidateId`、`candidateType`、`sourcePatchRefs[]`、面积字段、`suggestedAnchor`、来源 identity、`confirmationPreviewPath`；另冻结城市尺度 `terrainPreview`。 |

候选字段口径：

- `areaBlocks`：候选当前 scope 内全部可用 cell 的面积；D4 为扣除 hard occupied 后的剩余总面积。
- `largestContinuousAreaBlocks`：当前候选最大连续可用分量，T4 城市容量和 D4 阵列承载判断以此为准。
- `originalAreaBlocks`：裁剪或扣除前来源 patch 的原始面积。
- `sourcePatchRefs[]`：同尺度自然地理真值引用，不得把 T 与 D3 patch ID 混用。
- `candidateBasis`：T2/T4 固定为 `t_scale_landform_patch`，City D4 固定为 `d3_landform_patch`。
- `patchType`：T2/T4 为 T 尺度重新采样、分类和连通合并后的 `landform`，City D4 为 D3 自身尺度的 `landform`。
- `terrainComposition` / `baseLandformComposition`：候选内最终地貌和基础地貌的 cell 数与比例；T 候选不继承 W Patch 的类型或边界。
- `relations[]`：只引用当前兴趣集合、当前页已展示候选；关系只含可计算的相邻、距离、方位和共享边界事实。
- `suggestedAnchor`：程序按候选内部连通性与硬边界生成的粗锚点，不代表文明叙事上的最佳选择。

`candidateModel=landform_patch_candidates_v0_2` 必须进入来源 identity。W Patch 只提供 T2/T4 的允许范围与来源关系；T 以不大于 32 格的 cell step 重新采样、计算地貌指标并跨 GIS region 合并连续 Patch。共享 refinement 文件在恢复会话时必须校验内容 SHA-256，缺失或被改写时返回 stale / tampered，不得静默使用。模型变化时旧探索会话和选择凭证直接 stale。`pageToken` 必须绑定兴趣类型集合、页大小、页号和来源 identity。`PatchSelection` 消费时必须重新验证来源文件 hash、scope 快照、候选类型、面积与来源 patch；存在高程预览证据时还必须验证证据 JSON 内容 identity，任何漂移都返回 stale，不得静默重算成另一个候选。

T2/T4 会话必须写 `biome_overview.png`，并在 open/show 的 `artifacts.biomeOverview` 与会话 `overviewArtifacts.biomeOverview` 中返回。图片读取本次 T 尺度 refinement cell 的最终 Minecraft `biomeId`，不得退回用 W 粗 cell 群系代替。

## RealmSeed

T3 扩张输入。它是程序消费对象，不保存 AI 原始长文本。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `realmId` | string | 是 | 国度 ID。 |
| `selectionId` | string | 是 | 来源选择记录。 |
| `seedGrid.x` / `seedGrid.z` | int | 是 | 扩张核心 grid 坐标。 |
| `seedBlock.x` / `seedBlock.z` | int | 是 | 扩张核心 block 坐标。 |
| `continentId` | string | 是 | 所属大陆。 |
| `patchId` | string | 是 | 所属 patch。 |
| `scalePlan` | object | 是 | 从 `RealmProfile` 归一化后的面积比例计划。 |
| `expansionStyle` | object | 是 | 从 `RealmProfile` 派生或复制的扩张倾向。 |

## CapitalCityIntent

首都一定存在，但 T2 只登记存在性与理论规模，不给出最终城市坐标。产物文件为 `capital_city_intents.json`。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `citySeedId` | string | 是 | 城市种子 ID。 |
| `realmId` | string | 是 | 所属国度。 |
| `cityRole` | enum | 是 | 当前固定为 `capital`。 |
| `theoreticalScale` | enum | 是 | `village`、`town`、`city`、`large_city`、`capital`。 |
| `mustExist` | boolean | 是 | 首都必须为 `true`。 |
| `requiredConditions[]` | string[] | 是 | 至少包含 `land`、`inside_realm`，供 T4 选址校验。 |
| `coreFunctions[]` | string[] | 是 | 首都必需的行政、市场、防御等功能。 |
| `realmCoreSelectionId` | string | 是 | 仅追溯 T2 国度核心选择；不表示首都坐标。 |

历史 `capital_city_seeds.json` 可在 checkpoint 恢复时迁移为 `CapitalCityIntent`，但旧 `anchorGrid` / `anchorBlock` 只能视为 realm core provenance，不能自动进入正式 T4 会话。

## RealmTerritoryMap

T3 输出，先按粗 cell 记录势力范围。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `territoryMapId` | string | 是 | 结果 ID。 |
| `surveyId` | string | 是 | 来源 W 粗扫。 |
| `expansionModel` | enum | v1.4 | `quota_frontier` 或 `action_budget`。strict 默认 `action_budget`。 |
| `territoryCells[]` | array | 是 | cell 归属。 |
| `realmStats[]` | array | 是 | 国度摘要。 |
| `warnings[]` | string[] | 否 | 飞地、空洞、面积过小等异常。 |

`territoryCells[]`：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `gridX` | int | 是 | grid X。 |
| `gridZ` | int | 是 | grid Z。 |
| `realmId` | string | 条件 | `owned` cell 的归属国度；`wild/blocked/unreachable` 可为空。 |
| `status` | enum | v1.4 | `owned`、`wild`、`contested`、`blocked`、`unreachable`。 |
| `claimStrength` | number | 否 | 占有强度或竞争余量。 |
| `claimCost` | number | v1.4 | action model 下的累计占领成本。 |

`realmStats[]`：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `realmId` | string | 是 | 国度 ID。 |
| `areaCells` | int | 是 | 面积，单位 cell。 |
| `coastalRatio` | number | 否 | 海岸占比。 |
| `primaryLandforms[]` | string[] | 否 | 主要地貌。 |
| `neighbors[]` | string[] | 否 | 相邻国度。 |
| `targetAreaCells` | int? | v1.2 建议 | 目标面积。 |
| `actualAreaCells` | int? | v1.2 建议 | 实际面积。 |
| `largestComponentRatio` | number? | v1.2 建议 | 最大连通块面积 / 本国总面积。 |
| `detachedAreaRatio` | number? | v1.2 建议 | 非最大连通块面积占比。 |
| `holeAreaRatio` | number? | v1.2 建议 | 小孔洞面积占比。 |
| `naturalBoundaryFit` | number? | v1.2 建议 | 国界落在强 barrier edge 上的比例。 |
| `budgetUsedRatio` | number? | v1.4 | 使用的行动力预算比例。 |
| `averageClaimCost` | number? | v1.4 | 平均累计占领成本。 |
| `maxClaimCost` | number? | v1.4 | 最大累计占领成本。 |
| `terrainCostBreakdown` | object? | v1.4 | 按 baseLandform 汇总的占领成本。 |
| `stopReasonSummary` | object? | v1.4 | 行动力耗尽、屏障阻断、竞争失败等停止原因计数。 |

`t3_report.json` v1.4 额外包含：

| 字段 | 说明 |
| --- | --- |
| `expansionModel` | 本次使用的扩张模型。 |
| `expansionBudgets` | 每国派生的 `baseActionBudget`、`budgetMultiplier`、`effectiveActionBudget`、`softStopThreshold`、`hardStopThreshold`、`maxClaimCost`、`wildlandTolerance`。 |
| `terrainCostProfiles` | 程序从 `expansionStyle` 派生的 base landform / tag cost 表。 |
| `territoryStatusSummary` | `owned/wild/contested/blocked/unreachable` 的 cell 数和比例。 |
| `ownedAreaRatio` | 顶层验收别名，等于 `territoryStatusSummary.ownedRatio`。 |
| `wildlandRatio` | 顶层验收别名，等于 `territoryStatusSummary.wildRatio`。 |
| `contestedRatio` | 顶层验收别名，等于 `territoryStatusSummary.contestedRatio`。 |
| `blockedRatio` | 顶层验收别名，等于 `territoryStatusSummary.blockedRatio`。 |
| `unreachableRatio` | 顶层验收别名，等于 `territoryStatusSummary.unreachableRatio`。 |

## TerritoryRepairLog

记录 T3 后处理，不作为城市规划主输入，但作为评分和 debug 依据。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `territoryMapId` | string | 是 | 来源国境图。 |
| `repairs[]` | array | 是 | 飞地合并、孔洞填补、边界平滑记录。 |
| `blockedRepairs[]` | array | 否 | 因强 barrier、海权规则或面积约束未执行的修复。 |
| `summary` | object | 是 | 修复数量、影响面积、剩余风险。 |

`repairs[]` 至少包含：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `type` | string | `detached_component_merge`、`hole_fill`、`boundary_smooth`、`sea_bridgehead` 等。 |
| `realmId` | string | 影响国度。 |
| `areaCells` | int | 影响面积。 |
| `reason` | string | 修复理由。 |

## RealmT4CoarseTerrainEvidence

T3 owned territory 冻结后、T4 选择城市粗落点前生成的可选建议证据。当前 schema 为 `realm_t4_coarse_terrain_evidence.v0.1`，单国单文件，不取代 sealed `WorldPatchMap` 或 D3 `CityLandformReviewPackage`。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `runId` / `realmId` / `dimensionId` | string | 是 | 本次 run、单国作用域和维度身份。 |
| `territoryMapId` / `territoryIdentity` | string | 是 | T3 国境来源与内容身份。 |
| `worldSurveyContextIdentity` | string | 是 | sealed W context 内容身份。 |
| `sourceIdentity` | string | 是 | territory、W context、step、dimension 与完整 provider provenance 的组合 hash。 |
| `advisoryOnly` | boolean | 是 | 固定为 `true`。 |
| `requiredNextGate` | string | 是 | 固定为 `city_d3_site_review`。 |
| `provider` | object | 是 | 当前粗览 provider 及回退追溯。 |
| `grid` | object | 是 | W cell step、中心偏移、owned 数、采样数和 grid bounds。 |
| `summary` | object | 是 | 高度分位、robust relief、水体比例、坡度代理和分类直方图。 |
| `cells[]` | array | 是 | 目标 realm 的 owned cell 粗样本；每格恰好一个。 |
| `artifacts.heightWaterPreview` | string | 是 | 相对 run 目录的高度/水体 PNG。 |

`provider`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `providerId` | string | 实际选中的 provider。 |
| `sourceKind` | enum | `generator_native` 或 `gis_atlas_sampler`。 |
| `fastPath` | boolean | 是否为生成器原生快速路径。 |
| `fallbackReason` | string | 原生 provider 不可用时的拒绝链；未回退时为空。 |
| `sourceFingerprint` | string | 绑定维度、seed、生成器 API / preset 或回退采样源的稳定身份。 |
| `samplingSemantics` | string | 例如 RTF 的 `estimated_coarse_heightmap` 或回退的 `base_height_feature_sample`。 |

`cells[]`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `gridX/gridZ` | int | W 粗格绝对 grid 坐标。 |
| `blockX/blockZ` | int | 该 W cell 的中心采样点。 |
| `elevation` | number | provider 返回的生成先验高度。 |
| `water` | boolean | provider 的粗水体判断。 |
| `biomeId` | string | Minecraft registry biome。 |
| `terrainId` / `sourceBiomeId` | string | 生成器可提供的 terrain / source biome；回退 provider 可为 `unknown`。 |
| `neighborCount` | int | 同国 owned 四邻样本数。 |
| `neighborElevationDeltaMean/Max` | number | 四邻绝对高度差。 |
| `slopeProxy` | number | `neighborElevationDeltaMax / cellStepBlocks`。 |
| `localRelief` | number | 当前格与 owned 四邻样本的最大最小高度差。 |

该产物只可用于 T4 候选摘要和建议粗锚点。provider 初始化失败可整国回退；provider 选定后的逐点失败必须终止，不得在同一文件混合数据源。粗证据变化后，依赖它的 Patch Explorer session / selection 必须 stale。

## PatchCandidateTerrainPreview

Patch Explorer 按当前展示候选生成局部采样证据和一张高程高亮主图。schema 为 `patch_candidate_terrain_preview.v0.1`；三个 scope 均生成，每个候选、每个采样级别独立落盘，不要求对整个 scope 升采样。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `runId` / `realmId` / `dimensionId` / `scopeType` / `candidateId` | string | 是 | run、scope、维度与候选身份；`realmId` 字段在 City D4 中承载 city scope ID。 |
| `scopeSourceIdentity` | string | 是 | 打开 Patch Explorer 时冻结的 scope 来源 identity。 |
| `sourceIdentity` | string | 是 | scope、候选 cell mask、锚点、级别与完整 provider provenance 的组合 hash。 |
| `evaluationLevel` | enum | 是 | `candidate_comparison` 或 `city_scale_confirmation`。 |
| `provider` | object | 是 | 本次主图实际使用的 provider 身份、fingerprint 与 sampling semantics；T4 必须与同会话粗览一致。 |
| `grid.sampleStepBlocks` | int | 是 | 候选比较按候选包围盒和周边上下文自适应；城市确认为 16。 |
| `grid.windowDiameterBlocks` | int | 是 | 候选比较为 `sampleStepBlocks × 64`；城市确认为 1024。 |
| `grid.framingMode` | enum | 是 | 候选比较为 `candidate_bounds_with_context`；城市确认为 `city_scale_anchor`。 |
| `grid.candidateSampleCount` | int | 是 | 方形扫描窗口内落入原候选连续区 mask 的样本数。 |
| `buildabilityPolicy` | object | 是 | 当前建议性城市承载判定口径，含坡度、局部起伏、水体和四邻连续规则。 |
| `summary` | object | 是 | 高程、水体、坡度、起伏、可建设比例与最大连续可建设面积。 |
| `cells[]` | array | 是 | 方形窗口样本，显式记录 `insideCandidate`、`slopeDegrees`、`localRelief`、`buildable` 与拒绝原因。 |
| `artifacts.terrainPreview` | string | 是 | 单张 PNG：陆地随绝对高程连续变色，水体单独着色，轻量方向山影叠入底图；候选内部保留完整颜色，外部降饱和变暗，并以边线直接高亮候选 mask。 |
| `advisoryOnly` | boolean | 是 | 固定为 `true`。 |
| `requiredNextGate` | string | 是 | T2 为 `realm_t2_selection_review`，T4 为 `city_d3_site_review`，City D4 为 `city_d4_placement_review`。 |

候选比较使用原候选 cell 集合作为 mask，不能把窗口内相邻但不属于候选的地形计入候选容量；选择确认仍绑定同一个候选 mask。选择凭证同时绑定 evidence 文件内容 hash，provider 来源变化或 evidence 被修改时，旧选择必须 stale / tampered。

## CitySeedRegistry

T4 输出，登记城市名册和生成条件。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `registryId` | string | 是 | 城市名册 ID。 |
| `surveyId` | string | 是 | 来源 W 粗扫。 |
| `territoryMapId` | string | 是 | 来源国度扩张图。 |
| `citySeeds[]` | array | 是 | 城市种子列表。 |

`citySeeds[]`：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `citySeedId` | string | 是 | 稳定城市种子 ID。 |
| `realmId` | string | 是 | 所属国度。 |
| `name` | string? | v1.2 建议 | AI / 人类给出的城市名。 |
| `role` | enum/string | 是 | `capital`、`port`、`border_fort`、`mining_town` 等。 |
| `theoreticalScale` | enum | 是 | 理论规模。 |
| `anchorGrid.x` / `anchorGrid.z` | int | 是 | 粗锚点。 |
| `anchorBlock.x` / `anchorBlock.z` | int | 是 | block 锚点。 |
| `candidateRangeCells` | int | 是 | 后续 C 阶段可搜索半径，单位 cell。 |
| `planningRadiusCells` | int? | v1.2 建议 | 规模影响半径，用于城市间约束。 |
| `subregionId` | string? | v1.2 建议 | 所属二级区域。 |
| `candidateId` | string? | v1.2 建议 | 来源候选点编号。 |
| `graphDistanceToNearestCity` | number? | v1.2 建议 | 到最近城市的国度内图距离。 |
| `satelliteOf` | string? | 否 | 若是卫星节点，指向主城市。 |
| `requiredConditions[]` | string[] | 是 | 生成条件。 |
| `coreFunctions[]` | string[] | 是 | 核心功能。 |
| `trigger` | enum/string | 是 | `always`、`player_nearby`、`realm_development`、`story_stage`、`debug`。 |
| `source` | object | 建议 | 来源说明，例如来自 capital seed、海岸 patch、边境条件。 |

## RealmT4PatchPlanningSession

AI 驱动的单国 T4 会话使用 `realm_t4_patch_planning_session.v0.2`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `planningSessionId` / `runId` / `realmId` | string | 会话身份与作用域。 |
| `status` | string | `open` 或 `finalized`。 |
| `territoryIdentity` | string | T3 owned territory 来源身份。 |
| `capitalIntent` | object | 当前国度的无坐标首都意图。 |
| `capitalSelectionStatus` | enum | `awaiting_selection` 或 `selected`。 |
| `citySeeds[]` | array | 当前会话城市；创建时必须为空。 |
| `usedPatchSelectionRefs[]` | string[] | 已消费的 `realm_t4` 选择凭证，禁止重复消费。 |
| `citySeedRegistry` | string | finalize 后合并写回的全局 `CitySeedRegistry` artifact 引用。 |

首都与非首都城市都必须记录 `source.patchSelectionRef`、`source.patchCandidateId`、`source.sourcePatchRefs[]` 和 `source.siteSelectionMode=ai_candidate_selection`。锚点必须在同 realm owned territory 内，并按 `largestContinuousAreaBlocks` 校验规模默认容量与 `minimumAreaBlocks`。会话必须先选且只选一座首都；通用 add city 不接受 `role=capital`。

finalize 前必须校验会话内恰好一座带选择追溯的首都。

finalize 以合并后的完整 `CitySeedRegistry` 为 T4 当前真值，并原样保留上述 `source` 追溯字段。`t4_report.json`、`city_seed_preview.png`、`realm_city_candidate_packages.json`、各国候选预览和 `score_manifest.json` 必须由同一份最终名册同步重建。旧 `acceptance_report.json` 若存在，必须写入 `stale=true`、`status=stale`、`passed=false`、`staleReason=t4_registry_replaced_by_patch_planning`；只有重新执行完整 acceptance 才能恢复通过状态。

## RealmCityCandidateMapPackage

T4 v1.2 的 AI / 人类输入包。它只围绕单个国度，而不是整张世界图。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `packageId` | string | 是 | 图包 ID。 |
| `realmId` | string | 是 | 对应国度。 |
| `territoryMapId` | string | 是 | 来源 T3 国境图。 |
| `candidateMapImage` | string | 是 | 单国度城市候选图；必须裁剪到该国 owned territory 的包围盒，并可带少量邻接上下文，不得继续使用整张世界图作为主输入。 |
| `mapScope` | string? | v1.6/T4 补充 | 当前应为 `realm_owned_territory`。 |
| `mapBounds` | object? | v1.6/T4 补充 | 候选图裁剪后的 grid 范围：`minGridX/minGridZ/maxGridX/maxGridZ/widthCells/heightCells`。 |
| `contextPolicy` | string? | v1.6/T4 补充 | 单国度图保留多少上下文；当前为 `crop_to_realm_owned_bounds_with_small_neighbor_context`。 |
| `subregions[]` | array | 是 | 二级区域摘要。 |
| `candidates[]` | array | 是 | 带编号的候选点。 |
| `selectionRules` | object | 是 | AI 返回格式和约束。 |

`candidates[]` 建议包含：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `candidateId` | string | 稳定候选编号，例如 `P03`、`B07`。 |
| `gridX/gridZ` | int | 候选坐标。 |
| `roleFits[]` | string[] | 适合的城市角色。 |
| `scoreBreakdown` | object | 中央性、岸线、矿业、边境、可建设性等分项。 |
| `constraints[]` | string[] | 必须满足或需要避开的约束。 |

## ScoreManifest

验收评分产物，用于避免“链路跑通但结果不可玩”被误判为通过。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `runId` | string | 是 | 验收 run。 |
| `surveyId` | string | 是 | 来源 W survey。 |
| `totalScore` | number | 是 | 0-100 总分。 |
| `passed` | boolean | 是 | 是否通过评分和硬阻断。 |
| `subScores` | object | 是 | W / patch / continent / T3 / T4 / preview 子分。 |
| `hardBlocks[]` | array | 是 | 硬阻断项。 |
| `manualReviewChecklist[]` | array | 是 | 人工 review 五问和结果。 |
| `badCases[]` | array | 否 | 关键坏例坐标、国度或 patch。 |
| `previewSet` | object | 否 | 关联预览图路径。 |

`subScores.W` v1.5 建议字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `cliffRatio` / `cliffTagRatio` | number | 正式 `cliff` tag 占可分配陆地比例。 |
| `steepTagRatio` | number | `steep` tag 占可分配陆地比例。 |
| `coarseCliffCandidateRatio` | number | coarse GIS `landform=cliff` 候选比例，仅作诊断。 |
| `microContradictionRatio` | number | coarse cliff 被 micro 局部证据否定的比例。 |
| `baseLandformDistribution` | object | 主地貌分布。 |
| `landformTagDistribution` | object | tag 分布。 |

`subScores.T4` v1.4 建议字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `citySeedCount` | number | 城市种子总数。 |
| `capitalCount` | number | 首都种子数量。 |
| `duplicateAnchorCount` | number | 非卫星城市同格锚点冲突数，非 0 时 hard block。 |
| `spacingViolationCount` | number | 非卫星城市规划半径冲突数，非 0 时 hard block。 |
| `offTerritoryAnchorCount` | number | 本轮 `RealmProfile` 所属城市锚点未落在同 realm owned territory 内的数量，非 0 时 hard block；按 realm 合并保留的其他规划轮次城市不纳入本轮 T3 领土评分。 |
| `allAnchorsInOwnedTerritory` | boolean | 本轮 `RealmProfile` 所属城市锚点是否都落在同 realm owned territory 内。 |

## 关键校验规则

| 规则 | 阶段 | 说明 |
| --- | --- | --- |
| grid 转 block 必须可逆追溯 | W / T2 | manifest 中必须有 `gridOriginBlock` 和 `cellStepBlocks`。 |
| AI 主输入为选择凭证或 grid 坐标 | T2 | 推荐提交同 run、同 realm 的 `patchSelectionRef`；兼容 grid 坐标。两者都不得只给自然语言或只给 block 坐标。 |
| 拒绝静默跨域 snap | T2 | 跨大陆、跨海、跨禁用 patch 时必须拒绝或请求重试。 |
| T3 输入必须全部 accepted | T3 | `RealmCoordinateSelection.validation.status` 未通过的国度不能进入扩张。 |
| CitySeed 不包含城市内部规划 | T4 | 不出现道路、功能区边界、关键建筑坐标、jigsaw 参数等字段。 |
| 非海权国领土必须基本连通 | T3 v1.2 | `largestComponentRatio < 0.90` 应进入硬阻断。 |
| 国度面积弹性 | T3 v1.4 | `quota_frontier` 下仍按 `scalePlan.minAreaRatio/maxAreaRatio` 阻断；`action_budget` 下 `scalePlan` 为软目标，面积偏差进入 `budgetCoherenceScore` / `overExpansionPenalty`，不再单独硬阻断。 |
| 行动力最低可玩领地 | T3 v1.4 | strict + `action_budget` 下，每个国度必须有 owned territory；极小 owned 结果应进入硬阻断，不能只靠首都点放行。 |
| 城市锚点必须在 owned territory | T4 v1.4 | 本轮 `RealmProfile` 所属的 `CitySeedRegistry.citySeeds[].anchorGrid` 必须落在同 realm 的 owned cell 内；无 owned 领地的本轮国度不能生成首都种子。全局名册按 realm 合并时可保留其他规划轮次的城市，它们不得用本轮 `RealmTerritoryMap` 误判。 |
| T4 粗地形证据不得替代 D3 | T4 / D3 | `RealmT4CoarseTerrainEvidence` 必须声明 `advisoryOnly=true`、`requiredNextGate=city_d3_site_review`；城市进入 D4 前仍以 D3 局部精扫和显式审查为准。 |
| 高 step cliff 必须有局部证据 | W v1.5 | `cellStepBlocks>=64` 且 `microSamplingImplemented=true` 时，正式 `cliff` / `steep` tag 必须由 `slopeStats` / `steepFrac` 支撑；coarse cliff 不得直接进入正式 cliff tag。 |
| Tag Audit 抽样精扫 | W v1.5 | 开发期 `runTagAudit=true` 应输出 `tag_audit_samples.json` 与 `tag_audit_report.json`，报告中至少包含 `cliff/steep/coastal` 的 precision / recall。 |
| 多尺度 rank 不替代真值 | W v1.6 | `relativeHeightRank` / `scanHeightRank` 只能作为辅助特征；`ridge`、`plateau`、`lowland` 判定必须至少可追溯到 local / regional rank、roughness、DEV 或 geomorphon evidence。 |
| plateau 必须有面域抬升证据 | W v1.6 | `plateau` 不得只由局部平坦或高度 rank 推出；正式判定必须可追溯到 `plateauProminence`、`plateauCoreFlatSupport` 和 regional rank，小型平顶土坡应降级为 `lowland` / `upland`。 |
| 面域 Tag Audit | W v1.6 | `runTagAudit=true` 时样本应以 W coarse cell 为抽样单位，输出 `representativePoints`、`pointReferenceTags`、`cellReferenceTags`、`cellReferenceBaseLandform`、`mixedCell` 和 `representativePointMismatch`。 |
| 扫描边界水体不直接等价海岸 | W v1.6 | 仅因水体触达扫描边界且缺少 ocean / 大水体证据时，应输出 `boundary_truncated` / `open_water_unknown` 或降低 `waterBoundaryConfidence`，不得直接给高置信 `seacoast`。 |
| 城市种子不得同格重叠 | T4 v1.2 | 除显式复合城市 / 卫星节点外，同格城市直接阻断。 |
| 坏质量不能只靠 `passed=true` 放行 | 验收 v1.2 | `score_manifest.json` 的硬阻断优先于端到端链路状态。 |


## 地理开放区域与城市保护（2026-09-09）

当前功能依据《大陆大洋分区开放与城市郊区隔离-v0.1》，取代按城市圆圈和旅行走廊开放的规则。

- 地理输入为 sealed W 的 `world_feature_grid.json`；格网与 manifest 的 `configHash` 必须一致。`waterFrac < 0.5` 的四邻接连通陆地形成大陆；水域按最短水上格网距离附属于最近大陆，等距时使用稳定格序。默认近海距离 1024 格。
- 剩余远海先按默认宽 4096 格的地理扇区切分，再各自按四邻接连通分量划区。单个远海区域必须连续，全球连通海水不能合并成一个区域。负坐标使用 floor division。政治领土不参与地理分区。
- T4 创建时写出 `geographic_regions.json`（`geomantia_geographic_regions.v0.1`）：`cellStepBlocks`、`regions[].regionId/kind/cells/adjacentRegions`、近海/大洋配置、源文件 identity。运行时从 W 与当前配置确定性重算，不把过期展示产物当开放许可。
- `planning_area_access.json` 保留 v0.1 schema，新增可选 `nearSeaDistanceBlocks=1024`、`oceanRegionSpanBlocks=4096`。旧配置不填时使用这些默认值。
- 新 T4 种子由程序写入 `designBounds` 和 `protectionBounds`，均为 inclusive block rectangle。设计范围使用与 D3 相同的规模半径及 clamp；保护矩形将原宽高扩大到 1.5 倍并向外取整。外圈仅用于安全，不增加建筑、道路、景观或外扩面积。不同规模、对角排列、跨国度和卫星城统一检查保护矩形不重叠。
- D3 必须沿用持久化的 `designBounds`。D4 最终建筑完整占地和道路路幅不得越出原预览边界；原有阵列、外扩、地块冻结继续在该边界内运行。
- 选址同时检查当前名册和其他未结束会话的预留；finalize 对合并名册再次检查。正式游戏入口读取已加载状态及磁盘 NBT，不申请区块票据。保护圈存在任何已加载/保存区块或状态不明即拒绝选址。初始活动区外另留 1024 格生成缓冲，城市完整保护圈必须避开它。旧自动建议可以由同国正式选址替换，已选定的保护范围不能被忽略。
- T4 finalize 写 `finalizedRealmIds` 和 `finalizedTerritoryIdentity`；territory identity 为带 `sha256:` 前缀的文件摘要。旧 finalized session 仅在 territory identity 一致时可提供名册封存证明。重新打开会话会撤销该国的封存状态。
- 初始探索区在 W sealed 后使用原点所在的大陆与附属近海，与移动、地图迷雾及新选址排除共用同一地理分区。无需等待 T 阶段或城市设计完成；T2 核心、T3 可分配地、T4 城市完整保护圈必须避开初始区及其 1024 格加载缓冲。尚无有效 sealed 地理区域时才使用原点半径配置兜底，不同时叠加圆形开放区。
- 旧存档已在出生大陆规划的城市不删除或重选；尚未就绪城市保留自身保护矩形及移动安全缓冲，其余初始区开放。初始探索开放本身不授予相邻远洋开放资格。地图取得粗图后不再绘制固定半径外框。
- 非初始大陆所触及的所有国度名册封存、全部关联城市进入可施工状态，且结构和对应维度的 LandUse 生成方案都已激活，才开放大陆及附属海洋。不能仅凭 queue 的 completed 或 D4 成功开放。城市保护圈跨过分区边缘时，所有被触及分区都纳入该城市依赖。
- W sealed 后，已扫描的大洋分区默认开放，不依赖相邻大陆、国度归属或名册封存；海域被未完成城市保护范围或尚未就绪的附属预留范围触及时仍关闭。大陆及附属近海继续按原有就绪条件开放，扫描范围外的未知区域不放行。
- 冒险者地图显示整片已开放区域。移动/传送共享同一开放结果，并在未开放边缘内留视距与生成依赖缓冲；服务端使用 `(viewDistance + 12) * 16` 格、最少 160 格，按方形区块依赖计算，不能用圆形距离漏掉对角加载。
- `ChunkMap.schedule` 在 EMPTY 读取或任何后续生成阶段前拒绝未开放区块，返回已完成的 `UNLOADED_CHUNK_FUTURE`；不推进状态、不创建等待开放的悬空 future。开放后由原版 ChunkHolder 正常重试。初始活动区的 1024 格加载缓冲可正常生成，但不得选作城市。
- 新 T4 变更在服务器线程串行写入并立即使开放缓存失效。已存安全位置若落入重新关闭区域，改回初始安全区。保护不删除既有区块，不把旧城回滚为未生成，也不在既有地形补建。
