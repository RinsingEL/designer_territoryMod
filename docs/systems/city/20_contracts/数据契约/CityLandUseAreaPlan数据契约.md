# CityLandUseAreaPlan 数据契约

当前破坏性版本：`city_land_use_area_plan.v0.2`；户外意图为 `city_outdoor_intent_plan.v0.4`，SurfacePrint 为 `city_land_use_surface_print_plan.v0.7`。旧 artifact 不迁移。

Landscape source 必须冻结 `landscapeInstanceId/parcelId/parentParcelId/rootSource/sourceFrontier/sharedBoundarySpans`。一 Parcel 仍对应一个独立 Area，不因同类型或接壤合并。fill program 含 `GROUND|BANK + CORRIDOR` 时，父子 Parcel 不直接贴边：child 从父边界外第二格接力，中间一格不被任何 Parcel claim，保留原地表作为随地形形成的自然路隙；若该格本来位于 Foundation 域内，则显露 Foundation owner。其余接壤关系的 `sharedBoundarySpans` 每格包含唯一 `writerParcelId`、边界材料和关系类型 `PARENT_CHILD|CROSS_LANDSCAPE`；owner chunk 只裁切这些冻结 spans，不重算归属。

required Parcel 只消费 D4 `city_landscape_capacity_reservation_plan.v0.2` 实际冻结的非零容量；主体引用、D6 footprint 或候选身份漂移仍 hard fail。目标实例或 Parcel 因地形缩减、零格时继承 D4 warning，不得在 D6 重新补成固定形状或让整城失败。optional 自由景观逐实例记录 `admitted` 或 `skipped_insufficient_space`。

## 定位

本契约定义城市空间织体的 block 级执行投影和 worldgen 交接。它位于 D6 locked actual footprint 之后与 worldgen 执行之前。正式 Blueprint v0.12 路径把 AreaPlan 解释为一个 Foundation 底层加若干显式 Landscape Parcel，不再是逐建筑竞争占地。

## 版本与开关

| 对象 | schema / version |
| --- | --- |
| 外部 settings | `city_land_use_settings.v0.1` |
| D3 地形事实 | `city_land_use_terrain_field.v0.1` |
| legacy/debug 人工意图 | `city_land_use_intent_plan.v0.3`；v0.1/v0.2 明确拒绝 |
| Blueprint 户外投影 | `city_outdoor_intent_plan.v0.4` |
| 城市包络与残余空间 | `city_urban_space_plan.v0.1` |
| 规则目录 | `city_land_use_rules.v0.1` |
| 区域计划 | `city_land_use_area_plan.v0.2` |
| 批量地表计划 | `city_land_use_surface_print_plan.v0.7` |
| 规划完成标记 | `city_land_use_planning_complete.v0.4` |
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

规则目录不再包含事后桥接阈值。正式 Blueprint v0.12 路径固定关闭 LandUse 自动连接：城市连通由一块 Foundation domain 保证，景观 Parcel 按冻结父子树保持独立 Area。相向扩张只保留给 legacy/debug intent，不得进入正式户外编译。

`rules[]` 每项的字段必须完整且无未知字段；`ruleRef` 在同一 profile 内唯一。`semanticTerms[]` 按最长包含词匹配 D4 / D6 语义；`surfacePolicy` 只允许 `PRESERVE|PAVE|CULTIVATE|WATER_ADAPTIVE`，`vegetationPolicy` 只允许 `PRESERVE|SELECTIVE_CLEAR|CLEAR`，`boundaryPolicy` 只允许 `OPEN|FENCE|HEDGE|LOW_WALL|SHORELINE`。profile 内容参与 `ruleProfileHash`，配置发生变化后旧 completion 的 hash 校验必须拒绝激活，要求重跑 `city_plan_land_use`。

正式 Blueprint v0.12 路径只有一个 Foundation owner；它可包含多个互不强接的局部平台组件。全部 SpatialGround 只贡献建筑学语义和 D6 footprint，不各自拥有规则、配方或面积。ATTACHED Landscape 只绑定唯一 required 主体，fill/connectivity 永不拥有 Landscape；FREE_STANDING optional 由 placement domain 从剩余空间选址。

正式 Landscape 的每个 GrowthRegion 对应一个独立 Parcel 和唯一根 seed。`preferredAreaBlocks` 是正常停止目标，`maxAreaBlocks` 是硬上限而不是默认填充目标；可用空间充足时 `claimedAreaBlocks == preferredAreaBlocks`。frontier 因地形、边界、结构、竞争或 action budget 耗尽时允许 `minAreaBlocks <= claimedAreaBlocks < preferredAreaBlocks`，再由 required / optional 准入规则裁决；不得仅因存在剩余可通行格继续增长到 max。

Parcel 外壳必须是根 seed 发出的四邻接逐格 claim。候选排序可读取规则地形成本、terrain bias、preferred patch、growth bias、局部同 Parcel 邻接和由 `generationSeed + Parcel identity` 派生的稳定连续扰动；不得由圆、菱形、矩形、bbox、全局距离环或预制 mask 直接生成，也不得把这些固定几何作为失败兜底。相同输入必须得到相同 claims，改变稳定 seed 或 terrain field 必须能够改变候选排序和外轮廓。

required Parcel 先按 D4 实际容量域和冻结父子来源生成。D4 已把非零实际面积作为有效地形结果，因此 LandUse 的最小面积为 1；若实际容量小于 AI 填充阶段数，只保留从主角色开始、当前面积能够承载的前序阶段并重新归一占比，不得因间隔阶段放不下拒绝整城。required claims 冻结后，optional FREE_STANDING 按稳定实例 ID 逐实例探测；实例内全部 Parcel 达标才整体合并，否则该实例候选 claims 全部丢弃并记录 `CITY_LANDSCAPE_OPTIONAL_SKIPPED_INSUFFICIENT_SPACE:<landscapeInstanceId>`。

optional 实例若在户外编译阶段无法为全部目标 Parcel 取得合法 seed，则不创建该实例的任何 seed group，并记录 `skipped_insufficient_space:<landscapeInstanceId>`；required 景观以 D4 v0.2 的 `instances[]/warnings[]` 为准，零格不创建 seed group，身份或 hash 漂移才 hard fail。

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

- D4 `city_structure_anchor_plan.v0.3` / `city_structure_anchor_map.v0.3` 至少保留稳定 `anchorId`、`placementGroupId`、`placementProvenance={slotId,arrayId,parentArrayId,subZoneId}` 和结构语义。显式 group 先形成一个主体；未显式分组时服务端按 parent array -> array -> source slot -> anchorId 稳定派生 group ID，不得按 bbox 邻近关系反猜。
- D6 `structure_materialization_plan.json` 的 `lockedActualFootprint` / `lockedCollisionEnvelope` 是最终结构排除区和种子几何权威。D4 planned footprint 只服务预案与预览。
- D4 `streetBands[].platformBounds` 中的区内道路和 Blueprint 城市主干路是 Foundation 正式几何输入。RoadWeaver 外部长距道路的最终形状、D5 corridor 和模板 entrance 本身不是 LandUse 几何输入；RoadWeaver 在户外地表之后覆盖并清除其道路范围内的景观、作物和边界，LandUse 不为缺失 RoadWeaver 数据提供兜底线。

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
- `contour_bands` 在连续高程场上计算梯度 / 等高线法向距离，按 SurfaceRecipe 冻结的 `fieldBeforeBlocks + channelWidthBlocks + fieldAfterBlocks` 分类；CHANNEL 内冻结两侧 BANK 与中间 WATER，法向不稳定的连续平地使用 `algorithmAnchor` 做 `RADIAL_FALLBACK`。旧 v0.2 四象限 `radial` 不再接受。
- 规则选择优先级为 `subjectOverrides` > `groupOverrides.ruleRef` > D4 semantic 自动解析。未知 target、重复 surface target、group 成员冲突和未知 `ruleRef` hard fail；无法解析规则的主体写 warning 并跳过。

## LandUseAreaPlan

顶层字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schemaVersion` | string | `city_land_use_area_plan.v0.2`。 |
| `ruleVersion` | string | 当前为 `city_land_use_rules.v0.1`。 |
| `cityId` | string | 所属 City。 |
| `planHash` | string | 规范化计划 hash，供 active registry 与 ledger 校验。 |
| `planningBounds` | BlockBounds | 全局竞争范围。 |
| `areas[]` | object[] | 已取得的 block 级土地使用区域。 |
| `sharedBoundarySpans[]` | object[] | Landscape Parcel 接壤时冻结的单侧一格写入；含 `z/minX/maxX/writerAreaId/neighborAreaId/relation`。 |
| `unclaimedSpans[]` | ScanlineSpan[] | 未取得的 natural / wild / blocked / unreachable 空间。 |
| `corridorExclusions[]` | object[] | 已知 corridor 排除，含 `exclusionId`、`blockBounds`、`sourceRef`。 |
| `warnings[]` | string[] | 未知语义等可继续规划的警告。 |

`areas[]` 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `areaId` | string | 稳定逻辑区域 ID。正式城市 Foundation 只有一个连续 Area；每个景观 Parcel 都有独立 Area，禁止同类型相邻合并。 |
| `ruleRef` / `landUseType` | string | 规则引用和用途。 |
| `sourceGroupIds[]` / `sourceAnchorIds[]` | string[] | 可追溯来源。 |
| `seedPoints[]` | BlockPoint[] | Foundation 记录建筑影响域的稳定来源；景观记录 Parcel 自身 seed。正式路径禁止入口、组内最小连接树、跨组关系线和 RoadWeaver corridor seed。 |
| `spans[]` | ScanlineSpan[] | block 成员；每项为 `z,minX,maxX`，两端包含。 |
| `structureFootprintExclusions[]` | BlockBounds[] | D6 locked 结构硬排除区。 |
| `boundaryLoops[]` | object[] | `points[]` 与 `hole`；内部孔洞不得生成外边界。 |
| `gateSlots[]` | object[] | `gateId`、`block`、`direction`、`sourceAnchorId`。模板入口派生的 `gateId` 必须为 `sourceAnchorId::entranceId`，使同一模板在多个建筑实例中复用时仍全局唯一。 |
| `claimCostTotal` | number | 解释扩张结果的累计成本，不作为执行参数回传。 |
| `surfacePolicy` | enum | `PRESERVE|PAVE|CULTIVATE|WATER_ADAPTIVE`。 |
| `vegetationPolicy` | enum | `PRESERVE|SELECTIVE_CLEAR|CLEAR`。 |
| `boundaryPolicy` | enum | `OPEN|FENCE|HEDGE|LOW_WALL|SHORELINE`。 |
| `decorationPolicy` | string | Decoration profile / program 选择引用。 |

正式 Blueprint v0.12 不执行相向扩张或事后桥线。Foundation 几何由专用 planner 一次生成；Landscape Parcel 即使 rule、配方和材料完全相同也不得融合。普通同实例父子接壤由 child 单侧占一格；启用自然路隙的父子 Parcel 保持一格 Foundation 间隔，不生成 shared boundary；跨实例接壤按非 `OPEN` 优先和规范化实例 ID 冻结唯一 owner。

`unclaimedSpans[]` 只允许表示 Foundation domain 外部。正式路径没有道路走廊排除；Foundation domain 内不得存在未归属原群系。

## CityOutdoorIntentPlan

`city_outdoor_intent_plan.v0.4` 是 Blueprint `outdoorPlan` 在 D6 后的程序投影，不是第二次 AI 输入。它至少冻结：

- `cityId`、`sourceBlueprintHash`、`sourceD6Hash`、`sourceTerrainFieldHash`、`sourceOutdoorCatalogHash`。
- 唯一 Foundation 实际解析的 Profile、D6 anchors/footprints、rule、Surface recipe、结构外扩、请求闭合范围、实际闭合半径和连续性证明。
- 每个 SpatialGround 的来源 Group、共享空间类型、层级和 membership；不含铺地规则、配方或道路 seed。
- 每个 Landscape 实际解析的 Profile、`purpose/originMode`、owner 或 placement domain、目标实例/Parcel 数，以及 D4 地形缩减后的实际数量。
- 每个 Parcel 的 `landscapeInstanceId/parcelId/parentParcelId/rootSource/sourceFrontier`、D4 capacity identity、独立 seed、面积预算和短缺原因。

相同 Blueprint、D6、terrain field 和 catalog 必须输出相同规范 JSON 与 hash。任一来源漂移都不得复用旧 completion。

围栏农田、花田、绿化带和林场都通过显式 Landscape 进入。AI 提交目标 `instanceCount` 和 `parcelCount`；程序按 owner 种子与地形选择实际实例位置、父子拓扑、数量、面积和逐格外轮廓。ATTACHED required 必须复核 D4 owner anchor 与 footprint，所有实际非零 Parcel 只能在对应容量域内生成；FREE_STANDING optional 逐实例原子准入。

## CityUrbanSpacePlan

`city_urban_space_plan.v0.1` 只保留给 legacy/debug LandUse。正式 Blueprint v0.12 分层规划返回 disabled plan，覆盖证明改由 Foundation 各局部组件的 resolved close radius 和最小颈宽承担；它不进入 worldgen recipe parser。

城市基础域由纳入主体的 D6 structure footprint、LINEAR `platformBounds` 和 Foundation Profile 支撑，不读取 D5 corridor/gate。程序先按 `maxJoinDistanceBlocks` 分局部簇，再从 `closeRadiusBlocks` 开始为每簇选择首个通过最小颈宽验收的闭合半径；全城强连只会形成细桥时，按 close radius 重分局部平台，不生成细长地板桥。几何闭合只受 planning bounds 和 footprint 距离约束，D3 的 `water/slope/localRelief` 不参与通行判定。Landscape 后写覆盖 Foundation，并可按 membership 向主体外缘扩展。

正式路径 `residualRegions[]` 必须为空。Foundation domain 内除 Landscape 覆盖外必须全部归属同一 Foundation Area；任何按 SpatialGround 分配 residual、原群系洞或道路 corridor 空洞都是旧产物或规划失败。自然与绿地必须是 Blueprint 显式 landscape。

`coverageSummary` 必填：`envelopeBlocks`、`landUseBlocks`、`structureBlocks`、`corridorBlocks`、`absorbedResidualBlocks`、`explicitResidualBlocks`、`unknownResidualBlocks`。这些计数按优先级去重、两两互斥，并必须满足恒等式；正式规划成功同时要求 `explicitResidualBlocks=0` 与 `unknownResidualBlocks=0`。

## CityLandUseSurfacePrintPlan

`city_land_use_surface_print_plan.v0.7` 是与 area plan 分离冻结的当前执行计划。顶层字段为 `schemaVersion`、`cityId`、`sourceLandUsePlanHash`、`planHash`、`areas[]`、`sharedBoundarySpans[]`、`featureCells[]`；hash 必须由严格 codec 的规范 JSON 计算。Area recipe 判别联合只允许 `uniform|contour_bands|relay_region_growth`；正式道路、建筑自带绿化和住宅外溢边界以精确 feature cells 表达，执行期不重新读取 Blueprint、目录或 D4 几何。

`featureCells[]` 每项严格为 `{sourceId,x,z,blockId,surfaceOffset,kind,facing}`，同一 `{x,z,surfaceOffset}` 唯一。`kind` 只允许 `ROAD_SLAB|ROAD_STAIR|BRIDGE_DECK|BRIDGE_RAIL|GREEN_GROUND|GREEN_PATH|GREEN_PLANT|OVERFLOW_BOUNDARY`；只有 `ROAD_STAIR` 的 `facing` 可为 `NORTH|EAST|SOUTH|WEST`，其余固定 `NONE`。主路使用深色 deepslate tile，普通街使用 polished andesite，COMPACT 巷使用 mud brick；它们都与 Foundation/广场铺装分离。陆地道路 `widthBlocks` 范围冻结为 bottom slab，轴线两侧外加一格 bottom stair 路缘；桥段冻结 spruce bottom slab 桥面与 spruce fence 护栏，执行层沿护栏按稳定 7 格节奏向水底写 stone-brick 成对桥墩。建筑绿化只消费 D4 `buildingParcelPlan.resolvedBounds`，并把 D6 locked collision 作为硬排除；不得再用偏置 collision rectangle 充当花坛地块。FREEFORM 按密度稳定散布，FIELD_GRID 先冻结十字路，再按城市 style profile 的加权植物 palette 稳定选择 plant block；两种花纹都从 transformed entrance 留到地块外缘的连续引路。住宅外溢边界沿冻结矩形写 `boundaryBlockId`，所有关联 street bounds 从边界中扣除形成门洞。道路优先于绿化与边界，冲突植物上层必须删除。

`sharedBoundarySpans[]` 在 AreaPlan 的单侧 owner 基础上再冻结最终 `boundaryBlockId`。双方均 `OPEN` 时允许空材料；否则 owner chunk 只裁切这些全局 spans 并写一次，不得按 chunk 邻接或执行顺序重算归属。

`areas[]` 每项至少包含：

| 字段 | 说明 |
| --- | --- |
| `printAreaId` / `landUseAreaId` / `sourceGroupIds[]` | 稳定执行 ID、来源 area 与 group。不同精确 surface settings 不得在几何编译时误合并。 |
| `surfaceSettings` | 完整冻结 `surfacePrintEnabled`、`surfaceAlgorithm`、nullable `algorithmAnchor`、`boundaryBlockId`、旧等高线三段宽度和解析后的全部 block ID。正式 v0.10 的 `autoConnect=false`。 |
| `memberSpans[]` / `exclusionSpans[]` | 全局不规则 mask 和硬排除。chunk 只能裁切这份 mask，不得使用 bbox 重建形状。 |
| `surfaceAlgorithm` / `algorithmAnchor` | `uniform|contour_bands|relay_region_growth` 与 nullable/有效根起点；nullable 字段必须显式写 JSON null。 |
| `recipe` | `uniform`、`contour_bands` 或 `relay_region_growth` 判别联合。 |

`uniform` 冻结 `surfaceBlockId` 与可选 `boundaryBlockId`。

`contour_bands` 冻结配置的正整数 `fieldBeforeBlocks/channelWidthBlocks/fieldAfterBlocks` 及其和 `repeatPeriodBlocks`，并冻结 `surfaceBlockId`、`cropBlockId`、`channelBankBlockId`、`channelWaterBlockId`、`channelBankOverlayBlockId`、可选 `boundaryBlockId`、`classificationMode`、`anchor` 与 `bandSpans[]`。`classificationMode` 只允许 `CONTOUR_NORMAL|RADIAL_FALLBACK`；`bandSpans[]` 每项为 `{z,minX,maxX,role}`。核心分类器先输出 `field|channel_before_bank|channel_water|channel_after_bank`，planner 再按完整全局 WATER 四邻接把所有开放端点改为 `channel_end_cap`；最终 SurfacePrintPlan 接受这五种 role。

- 先对 D3 粗格高程做确定性的连续插值 / 平滑，再计算局部梯度与法向距离；不得直接把粗 cell 边界当等高线。
- 在完整 member mask 上一次性分类并扣除 exclusions，再冻结全局 spans；chunk 只裁切，不重算梯度、anchor、相位或 role。
- 把每条三格水槽解释为 `CHANNEL_BEFORE_BANK + CHANNEL_WATER + CHANNEL_AFTER_BANK`；开放 `CHANNEL_WATER` 端点按完整全局邻接冻结 bank 封口，禁止按 owner chunk 局部猜测。
- 固定输入、算法版本和 seed 得到相同 spans；输入 spans 顺序或 chunk 执行顺序不得改变结果。

`relay_region_growth` 是正式 Blueprint v0.12 景观填充配方。它冻结：

- Surface Recipe 已解析材料：`surfaceBlockId`、可选 `cropBlockId`、可选 bank/water/overlay、可选 `boundaryBlockId`。
- AI/目录决策：`fillProfileRef`、`primaryRoleRef`、`stableSeed`、有序区域阶段的角色、`PATCH|CORRIDOR` 生长偏置及 `targetShare`、内容权重。
- 程序解析：合法根起点、每个区域的 `regionId/parentRegionId/start/sourceFrontier/targetAreaBlocks/actualAreaBlocks/growthForm` 和逐格扩张 provenance。
- 最终执行 mask：全局稳定的 `regionSpans[]`，每项至少为 `{z,minX,maxX,regionId,roleRef}`；同一角色的不同区域身份不能在压缩时丢失。

核心分类器在完整 `memberSpans - exclusionSpans` 上使用 4 邻接逐格 frontier 扩张。第一块区域从根起点生长；后继区域的首格必须邻接父区域的局部边界，区内每格必须邻接本区已生长格。`PATCH` 偏向局部凝聚分叉，`CORRIDOR` 偏向活跃端点和方向连续，但两者都不是固定形状或固定宽度。根起点非法、mask 断开、接力界面耗尽或覆盖不能完成时 hard fail；不得吸附到图形中心、静默重播种、使用距离环或 bbox/fixed-shape fallback。chunk 执行只查冻结 region span，不得重新计算 frontier、父子关系、占比或随机内容。

`materialRole` 的执行映射固定为：

| materialRole | SurfacePrint 行为 |
| --- | --- |
| `PRIMARY_CONTENT` | 写 `surfaceBlockId`；`cropBlockId` 非空时在上层写作物/主题内容槽。 |
| `BANK` | 写 bank 基层；overlay 非空时写上层半砖、地毯或叶带。 |
| `WATER` | 写 water 基层。 |
| `GROUND` | 只写 bank/ground 基层，用于土路、石子带等纯地面间隔。 |

Landscape `contentWeights[]` 继续只进入 plan hash、trace 和预览审计，不由 SurfacePrint 把任意 semantic contentRef 解释成方块；Landscape 多作物/多树种仍需对应内容目录。建筑自带绿化是独立已冻结能力：它只消费 Reference Catalog v0.9 `styleProfiles[].plantPalette[]` 的真实 blockId/weight，并通过 `GREEN_PLANT` feature cells 执行，不能与 Landscape semantic contentWeights 混用。

同一个 surface-owned `landUseAreaId` 禁止 Decoration 使用 `uniform_fill`、`cross_section_repeat` 或 `parallel_rows`，避免批量地表重复落地；`deterministic_scatter`、`edge_repeat`、`grid_repeat` 等稀疏细节仍允许。

## LandUse 规划 Trace

`city_land_use_planning_trace.v0.6` 正式路径记录 Foundation `foundationComponentCount`、resolved close radius、各局部组件颈宽证明、Landscape Parcel 的 anchor phase、方向、请求/实际面积和失败重试。每个 admitted Parcel 的 `parcelExpansionOrigin` 必须冻结 `kind=ROOT_SOURCE|PARENT_PARCEL_INTERFACE|PARENT_PARCEL_ROAD_GAP`、实际 `start`、`parentParcelId` 和 nullable `sourceFrontier`。普通父接力要求 `sourceFrontier` 与 `start` 四邻接；`PARENT_PARCEL_ROAD_GAP` 要求曼哈顿距离恰为 2，中间格必须已采样、可通行、未被任一 Parcel claim；若中间格位于 Foundation 域内则保留 Foundation owner，否则保持未 claim 原地表。找不到合法界面必须明确失败，不得回落到预设 seed。带填充方案的 group 另记录 `fillProfileRef`、稳定 seed、主角色、有序区域阶段、角色/materialRole/growthForm/目标占比和内容权重。SurfacePrint 区域 trace 冻结每块区域的父子关系、接力界面和目标/实际面积。每个 Parcel 是独立 group/area，不从其他 Parcel 借用上限。`automaticSurfaceConnections[]` 在正式 v0.10 必须为空；非空只允许出现在显式 legacy/debug 规划。

区域几何与执行策略必须分离：`spans[]` 不得直接复制成 no-vegetation mask；例如 `forestry` 可以是 `PRESERVE + PRESERVE + FENCE`。

规划成功后最后发布严格的 `city_land_use_planning_complete.v0.4`。正式 Blueprint 路径字段为 `schemaVersion`、`cityId`、`planningSource=city_blueprint`、`sourceBlueprintHash`、`sourceCatalogSnapshotHash`、`sourceReferenceCatalogHash`、`sourceTerrainFieldHash`、`sourceD6Hash`、`outdoorIntentPlanHash`、`urbanSpacePlanHash`、`planHash`、`surfacePrintPlanHash`、`ruleProfileHash` 和 `completedAt`。AreaPlan、SurfacePrintPlan、OutdoorIntent、disabled UrbanSpace 与 completion identity 必须一致；缺少任一当前产物或 hash 漂移时 hard fail。

## Worldgen 交接

- active 文件：`geomantia_city_masks/active_city_land_use_area_plans.json`。每项只冻结 dimension、city、area plan、SurfacePrintPlan v0.7、material palette/hash 与 prepared owner index，不携带 LandUse catalog、prefab 或 run 状态。
- 传入 SurfacePrintPlan 的 `land_use_preview` metadata 为 `city_land_use_preview.v0.5`；除 Landscape 区域摘要外，必须叠加道路 slab/curb、绿化 ground/path/plant 和外溢边界，并记录 `featureCellCount`。
- owner chunk 编译产物为 `city_land_use_chunk_fragment.v0.3`，按世界坐标把 `featureCells[]` 与 Area spans 一起裁切；feature-only owner 同样 relevant，不得因没有 Area surface 操作而丢失。
- ledger 文件：`geomantia_city_masks/city_land_use_worldgen_ledger.json`，当前 schema v0.3。owner applied 项增加 `featureOperationCount`，并继续记录 area / surface / palette identity 与 base/crop/boundary 阶段计数。
- SurfacePrintPlan v0.1-v0.6、旧 active registry、旧 ledger 和旧 completion 都不进入当前 parser / activation。切换版本前必须清理旧任务产物与 server-root LandUse 状态，再重跑 `city_plan_land_use -> city_execute_d5`；不做内存迁移、磁盘迁移或静默降级。
- activation preflight 必须基于 AreaPlan + SurfacePrintPlan v0.7 的当前编译结果，枚举实际包含 surface、boundary 或 feature 操作的 owner。预检只读当前 loaded status 或 region NBT；任一待写 owner 已到 FEATURES 或状态不明都整体拒绝。
- 只在 `WorldGenRegion` 首次 FEATURES owner 回调处理当前 chunk；不得跨 owner 写相邻 chunk。
- owner fragment 只读 prepared 局部索引，不重算 plan hash、不扫描全城 band spans、不读取无关 owner 状态。PAVE 可携带只读 grading halo；不得把 halo 计为 owner relevant cell 或跨 owner 主动写入。
- 普通 PAVE 微整地固定使用 7x7 真实顶层高度的中位数作为局部参考，只接受补高 1..3 格、连通面积 <=16 且 X/Z span <=4 的封闭低洼。Foundation PAVE 使用独立执行策略：以 7x7 外环中位高度为目标，低处最多补高 48 格并允许覆盖水/岩浆，小凸起最多削低 4 格；7x7 局部起伏达到 12 格的非低洼列视为山体并跳过 Foundation surface/boundary。两者都不读取或填充地下空洞；填方基层使用 `MICRO_FILL_SUBGRADE`，目标顶层仍使用原 PAVE surface material。
- owner 先写 Area base/overlay，再写 `surfaceOffset=0` 的道路/绿化 feature，随后写 crop/plant/外溢边界上层，最后执行 Area boundary finalize。ROAD_SLAB 使用 bottom slab；ROAD_STAIR 使用 bottom straight stair 和冻结外向。整个 owner 共用一次预检、快照与逆序回滚，任一 feature 写入失败也必须回滚同 owner 已写内容。
- boundary 等连接类方块落地前必须按现场邻居求最终 BlockState，并触发原版邻居更新；跨 owner 接缝只允许由该原版更新传播，不得额外生成跨 owner 几何写入。
- footprint、corridor 和 gate 必须从操作中排除；自然表面不在可替换白名单时单格 skip。
- 整 owner 成功后才追加 applied ledger。重复回调必须由 dimension / city / area plan hash / surface plan hash / palette hash / owner chunk 幂等阻断。
- 普通 worldgen 回调中，非 `WorldGenRegion` 或已到 FEATURES 的旧 chunk 返回 `CITY_LAND_USE_OLD_CHUNK_NOT_BACKFILLED`，不写方块、不记成功 ledger。唯一例外是显式 `city_execute_d7 + executeStructurePlacement=true`：D7 可按当前完整 plan identity 对计划 owner 与成功 ledger 做差集，并以 `CONTROLLED_D7_BACKFILL` 只补缺失 owner；该能力不得作为任意旧区块重铺入口。
- D7 受控补写继续使用整 owner 预检、快照、写入、rollback 与成功 ledger 事务，并写 `steps/d7/land_use_owner_completion.json`（schema `city_land_use_owner_completion.v0.1`）。至少包含 city/area/surface identity、`plannedOwnerCount/appliedBeforeCount/backfilledOwnerCount/appliedAfterCount`、`missingOwners[]` 与 `failures[] {chunkX,chunkZ,reasonCode,rollbackComplete}`。`appliedAfterCount != plannedOwnerCount` 必须返回 `CITY_LAND_USE_D7_OWNER_INCOMPLETE`。
