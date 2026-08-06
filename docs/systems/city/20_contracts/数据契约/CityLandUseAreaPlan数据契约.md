# CityLandUseAreaPlan 数据契约

## 定位

本契约定义建筑驱动土地使用层 v0.1 的输入、规则引用、block 级区域输出和 worldgen 交接。它位于 D6 locked actual footprint 之后、DecorationProgram 与 `execute_d5` 之前，不恢复已删除的 `FunctionZoneMap`。

## 版本与开关

| 对象 | schema / version |
| --- | --- |
| 外部 settings | `city_land_use_settings.v0.1` |
| D3 地形事实 | `city_land_use_terrain_field.v0.1` |
| legacy/debug 人工意图 | `city_land_use_intent_plan.v0.3`；v0.1/v0.2 明确拒绝 |
| Blueprint 户外投影 | `city_outdoor_intent_plan.v0.1` |
| 城市包络与残余空间 | `city_urban_space_plan.v0.1` |
| 规则目录 | `city_land_use_rules.v0.1` |
| 区域计划 | `city_land_use_area_plan.v0.1` |
| 批量地表计划 | `city_land_use_surface_print_plan.v0.2` |
| 规划完成标记 | `city_land_use_planning_complete.v0.1` |
| active registry | `city_active_land_use_area_plans.v0.2` |
| worldgen ledger | `city_land_use_worldgen_ledger.v0.3` |

`config/geomantia/city_land_use/settings.json` 的 bundled 默认值为：

```json
{
  "schemaVersion": "city_land_use_settings.v0.1",
  "enabledInWorkflow": false,
  "profileId": "default_v0_1"
}
```

规则档案路径固定为 `config/geomantia/city_land_use/profiles/<profileId>.json`。`profileId` 必须匹配 `[a-z0-9][a-z0-9_.-]*`，并且规则文件顶层同名字段必须与 settings 一致；默认档案为 `profiles/default_v0_1.json`。目录或缺失 bundled 文件会补装，但不会覆盖用户已有 settings 或 profile。

规则文件是严格对象：

```json
{
  "schemaVersion": "city_land_use_rules.v0.1",
  "profileId": "default_v0_1",
  "rules": [
    {
      "ruleRef": "military",
      "landUseType": "military",
      "semanticTerms": ["military", "barracks", "guard_tower"],
      "footprintMultiplier": 1.5,
      "extraAreaBlocks": 96,
      "minAreaBlocks": 96,
      "maxAreaBlocks": 2048,
      "actionBudget": 360,
      "baseStepCost": 1.0,
      "slopeCost": 1.1,
      "reliefCost": 1.1,
      "waterCost": 8.0,
      "forestAffinity": 0.0,
      "competitionWeight": 1.0,
      "mergeSameType": true,
      "surfacePolicy": "PRESERVE",
      "vegetationPolicy": "SELECTIVE_CLEAR",
      "boundaryPolicy": "LOW_WALL",
      "decorationPolicy": "military"
    }
  ]
}
```

规则目录不再包含事后桥接阈值。相向扩张的边界间距阈值由程序固定为 64 格：初次扩张后，兼容类别相同且两侧 `autoConnect=true` 的主体进入双向引导；超过阈值、地形不可通行或存在硬障碍时不会强接。该距离不接受 AI 或 profile 覆写。

`rules[]` 每项的字段必须完整且无未知字段；`ruleRef` 在同一 profile 内唯一。`semanticTerms[]` 按最长包含词匹配 D4 / D6 语义；`surfacePolicy` 只允许 `PRESERVE|PAVE|CULTIVATE|WATER_ADAPTIVE`，`vegetationPolicy` 只允许 `PRESERVE|SELECTIVE_CLEAR|CLEAR`，`boundaryPolicy` 只允许 `OPEN|FENCE|HEDGE|LOW_WALL|SHORELINE`。profile 内容参与 `ruleProfileHash`，配置发生变化后旧 completion 的 hash 校验必须拒绝激活，要求重跑 `city_plan_land_use`。

legacy/debug intent 仍按建筑来源 growth region 计算面积。正式 Blueprint v0.5 路径改为 structure ground / landscape 级共享预算：同一 D4 Group 的全部 D6 anchors 先汇总真实 footprint，再只生成一份 `min/preferred/max`；同一 landscape 的多个 attached buildings 只贡献 seed，不重复贡献完整景观面积。该规则尤其用于阻止农业面积随农舍数量线性膨胀。

bundled `default_v0_1` 的 `industry` 规则包含 TerraSense canonical term `function.矿业`，以及 `mining`、`mine`、`quarry`、`workshop` 等别名；其 `landUseType` 和 `decorationPolicy` 都为 `industry`。

bundled `default_v0_1` 同时包含 `military` 规则，用于 `barracks`、`guard_tower`、`watch_post` 及其中文语义；其默认保留地表、选择性清理植被并使用矮墙边界。

正式 `d4CandidateMode=blueprint` 以 Blueprint `outdoorPlan.mode` 为唯一开关：`GENERATE` 在 D6 后自动规划，`PRESERVE` 明确跳过。正式模式禁止请求级 `enableLandUseLayer` 或 `landUseIntentPlan` 覆写。legacy/debug D4 仍按 settings / `enableLandUseLayer` 进入独立 LandUse intent；独立 `city_plan_land_use` 视为显式 debug 规划。

## LandUseTerrainField

D3 产出 `land_use_terrain_field.json`。它只使用规划期可用的 GIS / 地形先验，不得主动加载未生成 chunk。

顶层字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schemaVersion` | string | 是 | `city_land_use_terrain_field.v0.1`。 |
| `cityId` | string | 是 | 必须与本次 City 一致。 |
| `planningBounds` | BlockBounds | 是 | LandUse 可竞争的 block 范围。 |
| `cellStepBlocks` | int | 是 | D3 粗格步长，必须大于 0。 |
| `cells[]` | object[] | 是 | 按 `cellZ, cellX` 稳定排序的地形事实。 |

`cells[]` 字段为 `cellX`、`cellZ`、`blockMinX`、`blockMinZ`、`cellStepBlocks`、`elevation`、`slope`、`localRelief`、`roughness`、`water`、`waterDepth`、`waterDistance`、`biomeId`、`landformType`、`landformPatchId`、`sampled`。未采样事实必须显式标记 `sampled=false`，不能伪装为真实 block 采样。

## D4 provenance 与 D6 权威

- D4 `city_structure_anchor_plan.v0.2` / `city_structure_anchor_map.v0.2` 至少保留稳定 `anchorId`、`placementGroupId`、`placementProvenance={slotId,arrayId,parentArrayId,subZoneId}` 和结构语义。显式 group 先形成一个主体；未显式分组时服务端按 parent array -> array -> source slot -> anchorId 稳定派生 group ID，不得按 bbox 邻近关系反猜。
- D6 `structure_materialization_plan.json` 的 `lockedActualFootprint` / `lockedCollisionEnvelope` 是最终结构排除区和种子几何权威。D4 planned footprint 只服务预案与预览。
- 主路最终形状不是 LandUse 输入。已有 D5 corridor / entrance 可以作为排除或 gate 上下文，但不得猜测 RoadWeaver 的最终路径。

## LandUseIntentPlan

本节仅描述 legacy/debug 独立入口。正式 Blueprint workflow 不让调用方再提交这份对象；程序从已接受的 `outdoorPlan`、冻结 catalog 和 D6 事实生成 `city_outdoor_intent_plan.v0.1`，再投影为相同的 rule/surface 输入。

`landUseIntentPlan` 可省略；服务端会归一为当前 schema、当前 `cityId`、空 overrides 和默认 seed salt。显式提交时必须是严格对象，所有未知字段 hard fail。

```json
{
  "schemaVersion": "city_land_use_intent_plan.v0.3",
  "cityId": "city_001",
  "seedSalt": "review-a",
  "surfaceAlgorithmDefaults": [
    {
      "surfaceAlgorithm": "uniform",
      "surfaceBlockId": "minecraft:stone_bricks"
    },
    {
      "surfaceAlgorithm": "contour_bands",
      "surfaceBlockId": "minecraft:farmland",
      "cropBlockId": "minecraft:wheat",
      "channelBankBlockId": "minecraft:dirt",
      "channelWaterBlockId": "minecraft:water",
      "channelBankOverlayBlockId": "minecraft:oak_slab"
    }
  ],
  "groupOverrides": [
    {
      "groupId": "central_plaza",
      "memberAnchorIds": ["fountain", "shop_01", "shop_02"],
      "ruleRef": "plaza"
    }
  ],
  "subjectOverrides": [
    {
      "targetType": "anchor",
      "targetId": "house_09",
      "mode": "exclude"
    }
  ],
  "surfaceOverrides": [
    {
      "targetGroupId": "farm_mill_cluster",
      "surfacePrintEnabled": true,
      "autoConnect": true,
      "surfaceAlgorithm": "contour_bands",
      "algorithmAnchor": {"x": 651600, "z": 652100}
    }
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schemaVersion` | string | 是 | `city_land_use_intent_plan.v0.3`。旧 v0.1/v0.2 不自动迁移。 |
| `cityId` | string | 是 | 必须与请求 `citySeedId` 对应的 City 一致。 |
| `seedSalt` | string | 否 | 确定性扰动盐。 |
| `surfaceAlgorithmDefaults[]` | object[] | 否 | 本次城市规划的算法级材料默认；同一 `surfaceAlgorithm` 最多一项。 |
| `groupOverrides[]` | object[] | 否 | 显式创建 / 修正主体组合。 |
| `subjectOverrides[]` | object[] | 否 | 对 group 或 anchor 设置规则或排除。 |
| `surfaceOverrides[]` | object[] | 否 | 对最终 group 覆写刷地算法、算法锚点或材料；未配置字段按固定优先级继承。 |

`groupOverrides[]` 必须含 `groupId`、非空且去重的 `memberAnchorIds[]`；`ruleRef` 可选。一个 anchor 不得同时属于多个 group。

`subjectOverrides[]` 必须含 `targetType=group|anchor`、`targetId` 和 `mode=set_rule|exclude`。`set_rule` 必须含 `ruleRef`；`exclude` 禁止出现 `ruleRef`。不得提交面积、行动力、权重、逐项成本、block mask 或世界坐标。

`surfaceAlgorithmDefaults[]` 每项字段如下：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `surfaceAlgorithm` | enum | 是 | `uniform|contour_bands`；同一算法最多一项。 |
| `surfaceBlockId` | resource id | 是 | `uniform` 的统一地表；`contour_bands` 的 FIELD 地表。 |
| `cropBlockId` | resource id | 否 | `contour_bands` 的 FIELD 作物；省略时使用该算法的内置 fallback。 |
| `channelBankBlockId` | resource id | 否 | `contour_bands` 的 BANK 基层；省略时 fallback 为 `minecraft:dirt`。 |
| `channelWaterBlockId` | resource id | 否 | `contour_bands` 的 WATER 方块；省略时 fallback 为 `minecraft:water`。 |
| `channelBankOverlayBlockId` | resource id | 否 | `contour_bands` 的 BANK 上层；省略时 fallback 为 `minecraft:oak_slab`。 |

这些字段属于本次 `city_plan_land_use` 运行时输入。服务端 profile / 内置值只提供 fallback，不作为某座城市的材质真值。规划时按 `group surface override > 本次 surfaceAlgorithmDefaults > policy 内置 fallback` 解析，随后将具体 block ID 冻结进 SurfacePrintPlan；worldgen 不重新读取 intent 或配置。

`surfaceOverrides[]` 每项字段如下：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `targetGroupId` | string | 是 | 指向 group override 归组后或 D4 provenance 派生的最终 group；同一 target 只能出现一次。 |
| `surfacePrintEnabled` | boolean | 否 | 是否进入 LandUse 批量地表。PAVE / CULTIVATE 默认 true；PRESERVE / WATER 默认 false。 |
| `autoConnect` | boolean | 否 | 是否参加 64 格内兼容近邻相向扩张；按 policy 默认。 |
| `surfaceAlgorithm` | enum | 否 | `uniform|contour_bands`；默认由 policy 映射，PAVE -> uniform、CULTIVATE -> contour_bands。 |
| `algorithmAnchor` | BlockPoint 或 null | 否 | `contour_bands` 的稳定回退中心；省略或 null 时由最终 area `memberSpans` 的稳定质心派生。不是四象限方向输入。 |
| `surfaceBlockId` | resource id | 否 | 覆写当前 group 的统一地表或 FIELD 地表。 |
| `cropBlockId` | resource id | 否 | 覆写当前 group 的 FIELD 作物。 |
| `channelBankBlockId` | resource id | 否 | 覆写当前 group 的水槽 BANK 基层。 |
| `channelWaterBlockId` | resource id | 否 | 覆写当前 group 的 WATER 方块。 |
| `channelBankOverlayBlockId` | resource id | 否 | 覆写当前 group 的 BANK 上层方块。 |

- PAVE 和 CULTIVATE 使用不同 `compatibilityCategory`，不会互相自动连接；同类别允许具体方块不同，例如两种城区石材仍可连接。兼容类别与 `autoConnect` 属于 LandUse 扩张层，不由 `surfaceAlgorithm` 推导连接结果。
- PRESERVE / WATER 显式 `surfacePrintEnabled=true` 且提供地表方块时提升为 PAVE 兼容类别；`autoConnect` 未显式关闭时随之默认开启。
- `uniform` 只做最终 mask 内单方块刷地，不改变 LandUse 几何或连接。
- `contour_bands` 在连续高程场上计算梯度 / 等高线法向距离，按固定 `5 FIELD + 3 CHANNEL + 5 FIELD` 分类，三格 CHANNEL 冻结为 `BANK + WATER + BANK`；法向不稳定的连续平地使用 `algorithmAnchor` 做 `RADIAL_FALLBACK`。旧 v0.2 四象限 `radial` 不再接受。
- 规则选择优先级为 `subjectOverrides` > `groupOverrides.ruleRef` > D4 semantic 自动解析。未知 target、重复 surface target、group 成员冲突和未知 `ruleRef` hard fail；无法解析规则的主体写 warning 并跳过。

## LandUseAreaPlan

顶层字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schemaVersion` | string | `city_land_use_area_plan.v0.1`。 |
| `ruleVersion` | string | 当前为 `city_land_use_rules.v0.1`。 |
| `cityId` | string | 所属 City。 |
| `planHash` | string | 规范化计划 hash，供 active registry 与 ledger 校验。 |
| `planningBounds` | BlockBounds | 全局竞争范围。 |
| `areas[]` | object[] | 已取得的 block 级土地使用区域。 |
| `unclaimedSpans[]` | ScanlineSpan[] | 未取得的 natural / wild / blocked / unreachable 空间。 |
| `corridorExclusions[]` | object[] | 已知 corridor 排除，含 `exclusionId`、`blockBounds`、`sourceRef`。 |
| `warnings[]` | string[] | 未知语义等可继续规划的警告。 |

`areas[]` 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `areaId` | string | 稳定逻辑区域 ID；同一 group 被竞争结果拆成的多个不连通组件可共享同一 ID。按该 ID 消费区域的下游必须先合并全部匹配项的成员 spans，再执行 inset 与硬障碍扣除。 |
| `ruleRef` / `landUseType` | string | 规则引用和用途。 |
| `sourceGroupIds[]` / `sourceAnchorIds[]` | string[] | 可追溯来源。 |
| `seedPoints[]` | BlockPoint[] | footprint 外缘、入口或组合内侧等多源起点。 |
| `spans[]` | ScanlineSpan[] | block 成员；每项为 `z,minX,maxX`，两端包含。 |
| `structureFootprintExclusions[]` | BlockBounds[] | D6 locked 结构硬排除区。 |
| `boundaryLoops[]` | object[] | `points[]` 与 `hole`；内部孔洞不得生成外边界。 |
| `gateSlots[]` | object[] | `gateId`、`block`、`direction`、`sourceAnchorId`。模板入口派生的 `gateId` 必须为 `sourceAnchorId::entranceId`，使同一模板在多个建筑实例中复用时仍全局唯一。 |
| `claimCostTotal` | number | 解释扩张结果的累计成本，不作为执行参数回传。 |
| `surfacePolicy` | enum | `PRESERVE|PAVE|CULTIVATE|WATER_ADAPTIVE`。 |
| `vegetationPolicy` | enum | `PRESERVE|SELECTIVE_CLEAR|CLEAR`。 |
| `boundaryPolicy` | enum | `OPEN|FENCE|HEDGE|LOW_WALL|SHORELINE`。 |
| `decorationPolicy` | string | Decoration profile / program 选择引用。 |

相向扩张仍只产生普通 `spans[]`，不会追加桥线或第二种区域。兼容主体的扩张前沿自然接触后可由几何编译器融合；异类 area 仍是独立区域和硬障碍。

`unclaimedSpans[]` 仍表示整个 D3 `planningBounds` 内 AreaPlan claim 的补集，其中混合城市外部自然、结构/走廊排除和不可达地形。它不得用于判断城市内部是否存在原版群系漏洞；该口径由 `CityUrbanSpacePlan` 单独承担。

## CityOutdoorIntentPlan

`city_outdoor_intent_plan.v0.1` 是 Blueprint `outdoorPlan` 在 D6 后的程序投影，不是第二次 AI 输入。它至少冻结：

- `cityId`、`sourceBlueprintHash`、`sourceD6Hash`、`sourceTerrainFieldHash`、`sourceOutdoorCatalogHash`。
- 每个 structure ground 实际解析的 D6 anchor、rule、Surface recipe、共享面积预算、seed 和程序派生 growth bias。
- 每个 landscape 实际解析的 profile、attached anchors / preferred patch、共享面积预算、seed、membership 与 required 状态。
- Blueprint envelope profile 与 residual policy。

相同 Blueprint、D6、terrain field 和 catalog 必须输出相同规范 JSON 与 hash。任一来源漂移都不得复用旧 completion。

农田 profile 继续生成一个共享 `CULTIVATE + CONTOUR_BANDS` region。extent 选择 profile 的 SMALL/MEDIUM/LARGE 基准面积，intensity 由固定 `LOW/MEDIUM/HIGH` 系数换算；AI 不提交 block 数。`AWAY_FROM_REFERENCE` 的参考点和 seed 全部由 locked footprint 质心与外缘推导。

## CityUrbanSpacePlan

`city_urban_space_plan.v0.1` 与 AreaPlan 并列，记录城市包络和残余空间验收，不进入 worldgen recipe parser。顶层严格包含 `schemaVersion`、`cityId`、`planHash`、`enabled`、`closeRadiusBlocks`、nullable `workingBounds`、`envelopeSpans[]`、`residualRegions[]` 和 `coverageSummary`。包络档位已经在 OutdoorIntent 中冻结；UrbanSpacePlan 只保留编译后的闭合半径和实际几何。

城市包络只由 `membership=URBAN` 的 claims、对应 D6 structure footprint 和已冻结 corridor/gate 支撑；`LANDSCAPE` 农田、林地和池塘不得扩大包络。程序在紧凑局部 raster 上按 `COMPACT|BALANCED|LOOSE` 固定 profile 收口，再对包络内所有未归属组件分类。

`residualRegions[]` 每项严格记录 `residualId`、`residualClass`、`disposition`、`memberSpans[]`、`adjacentGroupIds[]`、`absorbedGroupId`、`blockCount`、`terrainDominated` 和 `touchesEnvelopeEdge`。小孔/窄缝按 Blueprint 可吸收到相邻 urban claim；水体、陡坡和未采样区域只能进入显式自然；其余 common green、service ground 或 natural reserve 即使不写方块，也必须拥有明确类型。显式 residual 的几何由各项 `memberSpans[]` 直接承载，不另设重复的 `explicitNaturalSpans[]`。

`coverageSummary` 必填：`envelopeBlocks`、`landUseBlocks`、`structureBlocks`、`corridorBlocks`、`absorbedResidualBlocks`、`explicitResidualBlocks`、`unknownResidualBlocks`。这些计数按优先级去重、两两互斥，并必须满足 `envelopeBlocks = landUseBlocks + structureBlocks + corridorBlocks + absorbedResidualBlocks + explicitResidualBlocks + unknownResidualBlocks`；正式规划成功要求 `unknownResidualBlocks=0`。

## CityLandUseSurfacePrintPlan

`city_land_use_surface_print_plan.v0.2` 是与 area plan 分离冻结的当前执行计划。顶层字段为 `schemaVersion`、`cityId`、`sourceLandUsePlanHash`、`planHash`、`areas[]`；hash 必须由严格 codec 的规范 JSON 计算。recipe 判别联合只允许 `uniform|contour_bands`，不包含 catalog、prefab、run、placement 或 foundation 字段。

`areas[]` 每项至少包含：

| 字段 | 说明 |
| --- | --- |
| `printAreaId` / `landUseAreaId` / `sourceGroupIds[]` | 稳定执行 ID、来源 area 与 group。不同精确 surface settings 不得在几何编译时误合并。 |
| `surfaceSettings` | 完整冻结 `surfacePrintEnabled`、LandUse 连接字段、`surfaceAlgorithm`、nullable `algorithmAnchor` 和解析后的全部 block ID。 |
| `memberSpans[]` / `exclusionSpans[]` | 全局不规则 mask 和硬排除。chunk 只能裁切这份 mask，不得使用 bbox 重建形状。 |
| `surfaceAlgorithm` / `algorithmAnchor` | `uniform|contour_bands` 与 nullable 回退中心；nullable 字段必须显式写 JSON null。 |
| `recipe` | `uniform` 或 `contour_bands` 判别联合。 |

`uniform` 只冻结 `surfaceBlockId`。

`contour_bands` 固定 `repeatPeriodBlocks=13`、`fieldBeforeBlocks=5`、`channelWidthBlocks=3`、`fieldAfterBlocks=5`，并冻结 `surfaceBlockId`、`cropBlockId`、`channelBankBlockId`、`channelWaterBlockId`、`channelBankOverlayBlockId`、`classificationMode`、`anchor` 与 `bandSpans[]`。`classificationMode` 只允许 `CONTOUR_NORMAL|RADIAL_FALLBACK`；`bandSpans[]` 每项为 `{z,minX,maxX,role}`。核心分类器先输出 `field|channel_before_bank|channel_water|channel_after_bank`，planner 再按完整全局 WATER 四邻接把所有开放端点改为 `channel_end_cap`；最终 SurfacePrintPlan 接受这五种 role。

- 先对 D3 粗格高程做确定性的连续插值 / 平滑，再计算局部梯度与法向距离；不得直接把粗 cell 边界当等高线。
- 在完整 member mask 上一次性分类并扣除 exclusions，再冻结全局 spans；chunk 只裁切，不重算梯度、anchor、相位或 role。
- 把每条三格水槽解释为 `CHANNEL_BEFORE_BANK + CHANNEL_WATER + CHANNEL_AFTER_BANK`；开放 `CHANNEL_WATER` 端点按完整全局邻接冻结 bank 封口，禁止按 owner chunk 局部猜测。
- 固定输入、算法版本和 seed 得到相同 spans；输入 spans 顺序或 chunk 执行顺序不得改变结果。

同一个 surface-owned `landUseAreaId` 禁止 Decoration 使用 `uniform_fill`、`cross_section_repeat` 或 `parallel_rows`，避免批量地表重复落地；`deterministic_scatter`、`edge_repeat`、`grid_repeat` 等稀疏细节仍允许。

## LandUse 规划 Trace

`land_use_plan_trace.json` 当前为 `city_land_use_planning_trace.v0.3`。`seedGroups[].growthRegions[]` 记录 `regionId`、anchor、`min/preferred/max` 与实际取得面积：legacy/debug 可按原来源分区，Blueprint landscape 则按 continuity 记录程序派生的 parcel region。group 顶层是求和摘要，所有 parcel 的三档预算必须分别严格等于该 landscape 总预算，region 之间不得借用上限；quality 同时报告 group 和 growth region 的低于最小面积结果。`automaticSurfaceConnections[]` 记录稳定 group 对、兼容类别、初次边界间距与 `already_connected|connected_by_expansion|not_reached` 结果。该 trace 只解释相向扩张，不是 AI 输入或 worldgen 执行参数。

区域几何与执行策略必须分离：`spans[]` 不得直接复制成 no-vegetation mask；例如 `forestry` 可以是 `PRESERVE + PRESERVE + FENCE`。

规划成功后最后发布严格的 `city_land_use_planning_complete.v0.2`。正式 Blueprint 路径字段为 `schemaVersion`、`cityId`、`planningSource=city_blueprint`、`sourceBlueprintHash`、`sourceCatalogSnapshotHash`、`sourceReferenceCatalogHash`、`sourceTerrainFieldHash`、`sourceD6Hash`、`outdoorIntentPlanHash`、`urbanSpacePlanHash`、`planHash`、`surfacePrintPlanHash`、`ruleProfileHash` 和 `completedAt`。AreaPlan、SurfacePrintPlan、OutdoorIntent、UrbanSpace 与 completion identity 必须一致；缺少任一当前产物或 hash 漂移时 hard fail。

## Worldgen 交接

- active 文件：`geomantia_city_masks/active_city_land_use_area_plans.json`，当前 schema v0.2。每项只冻结 dimension、city、area plan、SurfacePrintPlan v0.2、material palette/hash 与 prepared band index，不携带 LandUse catalog、prefab 或 run 状态。
- ledger 文件：`geomantia_city_masks/city_land_use_worldgen_ledger.json`，当前 schema v0.3。owner applied 项记录 area / surface / palette identity，以及 FIELD / CHANNEL / crop / boundary 的阶段计数和结果摘要；不保存 placement datum、prefab decision 或旧 schema 迁移状态。
- SurfacePrintPlan v0.1、旧 active registry、旧 ledger 和旧 completion 都不进入当前 parser / activation。切换版本前必须清理旧任务产物与 server-root LandUse 状态，再重跑 `city_plan_land_use -> city_execute_d5`；不做内存迁移、磁盘迁移或静默降级，历史实现只保留在 Git。
- activation preflight 必须基于 AreaPlan + SurfacePrintPlan 的当前编译结果，只枚举实际包含 surface 或 boundary 操作的 owner；微整地 mask 只是 surface 操作的上下文，不能单独令 owner relevant，`PRESERVE + OPEN` 等零写入 owner 不得阻断激活。预检只读当前 loaded status 或 region NBT，不得申请 ticket。任一待写 owner 已到 FEATURES 返回 `CITY_LAND_USE_CHUNK_ALREADY_AT_FEATURES`，读取失败或状态无法证明返回 `CITY_LAND_USE_CHUNK_STATUS_UNKNOWN`，两者都整体拒绝激活。只有磁盘明确不存在才视为 `NOT_PRESENT`。
- 只在 `WorldGenRegion` 首次 FEATURES owner 回调处理当前 chunk；不得跨 owner 写相邻 chunk。
- owner fragment 只读 prepared 局部索引，不重算 plan hash、不扫描全城 band spans、不读取无关 owner 状态。PAVE 可携带只读 grading halo；不得把 halo 计为 owner relevant cell 或跨 owner 主动写入。
- PAVE 微整地固定使用 7x7 真实顶层高度的中位数作为局部参考，只接受补高 1..3 格、连通面积 <=16 且 X/Z span <=4 的封闭低洼。连通低洼触及另一 area、footprint、corridor、gate、水体、非自然表面，或超过深度 / 面积 / span 阈值时不得填充；只向上补方块，不削地、不读取或填充地下空洞。基层使用 `MICRO_FILL_SUBGRADE`，目标顶层仍使用原 PAVE surface material。
- v0.2 direct-mask owner 先写 FIELD / BANK / WATER base 与 BANK overlay，再只在 FIELD mask 写 CROP，最后写不覆盖 BANK / WATER 的 BOUNDARY；相邻 WATER 状态更新与端点封口必须来自冻结全局邻接。整个 owner 共用一次预检、快照与逆序回滚。
- boundary 等连接类方块落地前必须按现场邻居求最终 BlockState，并触发原版邻居更新；跨 owner 接缝只允许由该原版更新传播，不得额外生成跨 owner 几何写入。
- footprint、corridor 和 gate 必须从操作中排除；自然表面不在可替换白名单时单格 skip。
- 整 owner 成功后才追加 applied ledger。重复回调必须由 dimension / city / area plan hash / surface plan hash / palette hash / owner chunk 幂等阻断。
- 非 `WorldGenRegion` 或已到 FEATURES 的旧 chunk 返回 `CITY_LAND_USE_OLD_CHUNK_NOT_BACKFILLED`，不写方块、不记成功 ledger。
