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
| `RealmProfile` | T1 | 国度设定。 | `TerritoryBlueprint`。 | 保留高层概念，删掉低层扫描参数。 |
| `RealmCandidateMapPackage` | T1 | 给 AI 选坐标的候选图包。 | 旧 T1 候选图 / 候选簇。 | 改成图上直接选坐标。 |
| `RealmCoordinateSelection` | T2 | 保存 AI 选点和程序校验结果。 | 旧 T1 / T2 selection artifact。 | 新建，替代选簇 / 选方向。 |
| `RealmSeed` | T2 | T3 扩张种子。 | 旧 territory config。 | 保留用途，结构重写。 |
| `CapitalCitySeed` | T2 | 首都城市种子。 | 旧 T3 后只有首都语义。 | 保留“首都必定存在”。 |
| `RealmTerritoryMap` | T3 | 国度扩张结果。 | `TerritoryManager` 扩张结果。 | 复用算法，重写实现。 |
| `CitySeedRegistry` | T4 | 全城市名册。 | 旧 T4 不匹配。 | 新建。 |

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
  "gridOriginBlock": { "x": -8192, "z": -8192 },
  "gridSize": { "width": 128, "height": 128 },
  "source": {
    "gisRefreshJobId": "gis_job_001",
    "sampleMode": "prior"
  },
  "createdAt": "2026-06-11T00:00:00Z"
}
```

## WorldPatchMap

T 阶段消费的粗地貌地图。实现可以内部建索引，但落盘契约至少要能按 grid 坐标和 patch id 追溯。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schemaVersion` | string | 是 | 结构版本。 |
| `surveyId` | string | 是 | 对应 `WorldSurveyContext`。 |
| `cells[]` | array | 是 | 粗 cell 列表。 |
| `patches[]` | array | 是 | patch 摘要。 |
| `continents[]` | array | 是 | 大陆 / 大区摘要。 |

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
| `heightAvg` | number? | 建议 | 平均高度。 |
| `slopeAvg` | number? | 建议 | 平均坡度。 |
| `waterDistanceBlocks` | number? | 建议 | 到水体或岸线距离，单位 block。 |
| `flags[]` | string[] | 否 | `coastal`、`lowland`、`mountain_edge` 等标签。 |

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
| `territoryCells[]` | array | 是 | cell 归属。 |
| `realmStats[]` | array | 是 | 国度摘要。 |
| `warnings[]` | string[] | 否 | 飞地、空洞、面积过小等异常。 |

`territoryCells[]`：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `gridX` | int | 是 | grid X。 |
| `gridZ` | int | 是 | grid Z。 |
| `realmId` | string | 是 | 归属国度。 |
| `claimStrength` | number | 否 | 占有强度或竞争余量。 |

`realmStats[]`：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `realmId` | string | 是 | 国度 ID。 |
| `areaCells` | int | 是 | 面积，单位 cell。 |
| `coastalRatio` | number | 否 | 海岸占比。 |
| `primaryLandforms[]` | string[] | 否 | 主要地貌。 |
| `neighbors[]` | string[] | 否 | 相邻国度。 |

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
| `role` | enum/string | 是 | `capital`、`port`、`border_fort`、`mining_town` 等。 |
| `theoreticalScale` | enum | 是 | 理论规模。 |
| `anchorGrid.x` / `anchorGrid.z` | int | 是 | 粗锚点。 |
| `anchorBlock.x` / `anchorBlock.z` | int | 是 | block 锚点。 |
| `candidateRangeCells` | int | 是 | 后续 C 阶段可搜索半径，单位 cell。 |
| `requiredConditions[]` | string[] | 是 | 生成条件。 |
| `coreFunctions[]` | string[] | 是 | 核心功能。 |
| `trigger` | enum/string | 是 | `always`、`player_nearby`、`realm_development`、`story_stage`、`debug`。 |
| `source` | object | 建议 | 来源说明，例如来自 capital seed、海岸 patch、边境条件。 |

## 关键校验规则

| 规则 | 阶段 | 说明 |
| --- | --- | --- |
| grid 转 block 必须可逆追溯 | W / T2 | manifest 中必须有 `gridOriginBlock` 和 `cellStepBlocks`。 |
| AI 主输入为 grid 坐标 | T2 | 不接受 AI 只给自然语言或只给 block 坐标作为正式选择。 |
| 拒绝静默跨域 snap | T2 | 跨大陆、跨海、跨禁用 patch 时必须拒绝或请求重试。 |
| T3 输入必须全部 accepted | T3 | `RealmCoordinateSelection.validation.status` 未通过的国度不能进入扩张。 |
| CitySeed 不包含城市内部规划 | T4 | 不出现道路、功能区边界、关键建筑坐标、jigsaw 参数等字段。 |
