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
| `CapitalCitySeed` | T2 | 首都城市种子。 | 旧 T3 后只有首都语义。 | 保留“首都必定存在”。 |
| `RealmTerritoryMap` | T3 | 国度扩张结果。 | `TerritoryManager` 扩张结果。 | 复用算法，重写实现。 |
| `TerritoryRepairLog` | T3 | v1.2 记录飞地、孔洞和边界修复。 | 旧实现无稳定产物。 | 新增。 |
| `RealmCityCandidateMapPackage` | T4 | v1.2 单国度城市候选图包。 | 旧实现无稳定产物。 | 新增。 |
| `CitySeedRegistry` | T4 | 全城市名册。 | 旧 T4 不匹配。 | 新建。 |
| `ScoreManifest` | 验收 | v1.2 记录质量评分、硬阻断和人工 review。 | 无旧结构。 | 新增。 |

## v1.2 扩展口径

v1.2 不废弃 v1.1 的 `WorldPatchMap`、`RealmTerritoryMap` 和 `CitySeedRegistry`。实现可先保持 v1.1 字段兼容，同时新增 clean id、feature stats、repair log、单国度城市候选图包和 `score_manifest.json`。正式消费层应优先读取 v1.2 clean / score 字段；缺失时只能按 v1.1 smoke 口径验收，不能宣称 strict 质量通过。

## WorldSurveyContext

记录一次世界粗扫的配置和坐标上下文。

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
| `config` | object | 是 | 维度、seed、中心、`planningRadiusBlocks`、`cellStepBlocks`、`microSampleStrideBlocks`、`localSlopeRadiusBlocks`、`sampleMode`、`resumePolicy`。 |
| `scanBounds` | object | 是 | block 级扫描边界和直径。 |
| `grid` | object | 是 | grid 原点、宽高、cell 数。 |
| `stats` | object | 是 | `tileCount`、`scannedTileCount`、`cachedTileCount`、`failedTileCount`、`artifactBytes`、`microSampleBudget`、`microSampleBudgetPerCell`、`microSampleCount`、`adaptiveSampling`。 |
| `tiles[]` | array | 是 | 每个 tile / GIS Region 的坐标、状态、cache 路径、`configHash` 和错误信息。 |

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
| `baseLandform` | enum/string? | v1.2 建议 | 清洗后的主地貌；建议 `water`、`shore`、`lowland`、`upland`、`ridge`、`valley`、`unknown`。 |
| `landformTags[]` | string[] | v1.2 建议 | `steep`、`cliff`、`wet`、`rugged`、`mountain_front`、`harbor_candidate` 等二级标签。v1.5 起，`cellStepBlocks>=64` 且有 micro 指标时，正式 `cliff` / `steep` 必须由局部 `slopeStats` 支撑；coarse GIS 的 cliff 只能进入 `cliff_candidate` / `micro_contradiction` 等诊断 tag。 |
| `continentIdClean` | string? | v1.2 建议 | 清洗 / 合并后的大陆 id。 |
| `patchIdClean` | string? | v1.2 建议 | 清洗 / 合并后的 macro patch id。 |
| `heightAvg` | number? | 建议 | 平均高度。 |
| `slopeAvg` | number? | 建议 | 平均坡度。 |
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

v1.5 开发期调试产物，用少量抽样点的局部精确扫描评估 W 粗扫 tag 正确率。它只在 `runTagAudit=true` 或开发工具显式触发时输出，不属于普通玩家开局必跑流程。

Tag Audit 的 reference tags 使用比 W 粗扫更密的局部扫描事实复判：

| reference tag | 判定口径 |
| --- | --- |
| `steep` | `slopeP90 >= 14` 或 `steepFrac >= 0.25`。 |
| `cliff` | `slopeP95 >= 18` 且 `steepFrac >= 0.35`；如果 `waterFrac` 在 `0.05..0.95` 的水陆混合区，`steepFrac` 阈值提升到 `0.45`。 |
| `coastal` | `waterFrac` 在 `0.05..0.95` 之间。 |

W 正式 tag 与 Tag Audit reference 使用同一套语义，但 W 在高 step 下基于每个粗采样点的 micro 指标判定，Tag Audit 则对抽样点周围 `auditRadiusBlocks` 范围做局部精扫，用于开发期估算 precision / recall。

### tag_audit_samples.json

数组，每项记录一个抽样点：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `gridX/gridZ` | int | W planning grid 坐标。 |
| `blockX/blockZ` | int | 抽样点 block 坐标。 |
| `baseLandform` | string | W 输出主地貌。 |
| `coarseLandform` | string | GIS coarse landform 原值。 |
| `wTags[]` | string[] | W 输出 tags。 |
| `referenceTags[]` | string[] | 局部精扫重新判定的参考 tags。 |
| `cliffMatch/steepMatch/coastalMatch` | boolean | 关键 tag 是否和 reference 一致。 |
| `auditMetrics` | object | 局部精扫指标。 |

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
| `sampleCount` | int | 实际抽样点数量。 |
| `auditRadiusBlocks` | int | 局部精扫半径。 |
| `auditStrideBlocks` | int | 局部精扫步长。 |
| `centerSlopeRadiusBlocks` | int | 局部坡度半径。 |
| `tagMetrics` | object | 按 tag 统计 `precision`、`recall`、TP / FP / FN / TN。 |
| `confusionMatrix` | object | 关键 tag 的混淆矩阵。 |
| `cliffFalsePositiveExamples[]` | array | 前若干个 cliff 误报样例坐标。 |
| `cliffFalseNegativeExamples[]` | array | 前若干个 cliff 漏报样例坐标。 |
| `microContradictionAcceptedRate` | number | 被 micro 拒绝的 coarse cliff 中，局部精扫仍判定 cliff 的比例。 |

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
| `normalizationGroup` | string | 是 | 比例归一化分组，通常为 continent id。 |

`expansionStyle` 控制“怎么长”。数值建议先用语义化范围，不让 AI 填 T3 算法裸参数：

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

T1 产物，供 AI 和程序共同使用。AI 看图选坐标，程序读 manifest 校验坐标。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `packageId` | string | 是 | 图包 ID。 |
| `realmId` | string | 是 | 对应国度。 |
| `surveyId` | string | 是 | 对应 W 粗扫。 |
| `candidateMapImage` | string | 是 | 候选图路径。 |
| `gridLegend.originBlock` | object | 是 | grid 原点。 |
| `gridLegend.cellStepBlocks` | int | 是 | grid cell 步长。 |
| `gridLegend.coordinateFormat` | string | 是 | 例如 `gridX,gridZ`。 |
| `allowedPatches[]` | string[] | 是 | 可选 patch。 |
| `blockedCells[]` | array | 否 | 禁用 cell 与原因。 |
| `occupiedSeeds[]` | array | 否 | 已有国度种子，用于距离约束。 |
| `selectionRules` | object | 是 | AI 选择约束和返回格式。 |

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

## CapitalCitySeed

首都一定存在，但还不是城市规划结果。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `citySeedId` | string | 是 | 城市种子 ID。 |
| `realmId` | string | 是 | 所属国度。 |
| `cityRole` | enum | 是 | 当前固定为 `capital`。 |
| `anchorGrid.x` / `anchorGrid.z` | int | 是 | 首都锚点 grid 坐标。 |
| `anchorBlock.x` / `anchorBlock.z` | int | 是 | 首都锚点 block 坐标。 |
| `theoreticalScale` | enum | 是 | `village`、`town`、`city`、`large_city`、`capital`。 |
| `growthAnchor` | string | 否 | 例如 `coastal_plain`、`river_mouth`。 |
| `mustExist` | boolean | 是 | 首都必须为 `true`。 |

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

## RealmCityCandidateMapPackage

T4 v1.2 的 AI / 人类输入包。它只围绕单个国度，而不是整张世界图。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `packageId` | string | 是 | 图包 ID。 |
| `realmId` | string | 是 | 对应国度。 |
| `territoryMapId` | string | 是 | 来源 T3 国境图。 |
| `candidateMapImage` | string | 是 | 单国度城市候选图。 |
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
| `offTerritoryAnchorCount` | number | 城市锚点未落在同 realm owned territory 内的数量，非 0 时 hard block。 |
| `allAnchorsInOwnedTerritory` | boolean | 是否所有城市锚点都落在同 realm owned territory 内。 |

## 关键校验规则

| 规则 | 阶段 | 说明 |
| --- | --- | --- |
| grid 转 block 必须可逆追溯 | W / T2 | manifest 中必须有 `gridOriginBlock` 和 `cellStepBlocks`。 |
| AI 主输入为 grid 坐标 | T2 | 不接受 AI 只给自然语言或只给 block 坐标作为正式选择。 |
| 拒绝静默跨域 snap | T2 | 跨大陆、跨海、跨禁用 patch 时必须拒绝或请求重试。 |
| T3 输入必须全部 accepted | T3 | `RealmCoordinateSelection.validation.status` 未通过的国度不能进入扩张。 |
| CitySeed 不包含城市内部规划 | T4 | 不出现道路、功能区边界、关键建筑坐标、jigsaw 参数等字段。 |
| 非海权国领土必须基本连通 | T3 v1.2 | `largestComponentRatio < 0.90` 应进入硬阻断。 |
| 国度面积弹性 | T3 v1.4 | `quota_frontier` 下仍按 `scalePlan.minAreaRatio/maxAreaRatio` 阻断；`action_budget` 下 `scalePlan` 为软目标，面积偏差进入 `budgetCoherenceScore` / `overExpansionPenalty`，不再单独硬阻断。 |
| 行动力最低可玩领地 | T3 v1.4 | strict + `action_budget` 下，每个国度必须有 owned territory；极小 owned 结果应进入硬阻断，不能只靠首都点放行。 |
| 城市锚点必须在 owned territory | T4 v1.4 | `CitySeedRegistry.citySeeds[].anchorGrid` 必须落在同 realm 的 owned cell 内；无 owned 领地的国度不能生成首都种子。 |
| 高 step cliff 必须有局部证据 | W v1.5 | `cellStepBlocks>=64` 且 `microSamplingImplemented=true` 时，正式 `cliff` / `steep` tag 必须由 `slopeStats` / `steepFrac` 支撑；coarse cliff 不得直接进入正式 cliff tag。 |
| Tag Audit 抽样精扫 | W v1.5 | 开发期 `runTagAudit=true` 应输出 `tag_audit_samples.json` 与 `tag_audit_report.json`，报告中至少包含 `cliff/steep/coastal` 的 precision / recall。 |
| 城市种子不得同格重叠 | T4 v1.2 | 除显式复合城市 / 卫星节点外，同格城市直接阻断。 |
| 坏质量不能只靠 `passed=true` 放行 | 验收 v1.2 | `score_manifest.json` 的硬阻断优先于端到端链路状态。 |
