# CityLandUseAreaPlan 数据契约

## 定位

本契约定义建筑驱动土地使用层 v0.1 的输入、规则引用、block 级区域输出和 worldgen 交接。它位于 D6 locked actual footprint 之后、DecorationProgram 与 `execute_d5` 之前，不恢复已删除的 `FunctionZoneMap`。

## 版本与开关

| 对象 | schema / version |
| --- | --- |
| 外部 settings | `city_land_use_settings.v0.1` |
| D3 地形事实 | `city_land_use_terrain_field.v0.1` |
| 人工 / AI 意图 | `city_land_use_intent_plan.v0.1` |
| 规则目录 | `city_land_use_rules.v0.1` |
| 区域计划 | `city_land_use_area_plan.v0.1` |
| 规划完成标记 | `city_land_use_planning_complete.v0.1` |
| active registry | `city_active_land_use_area_plans.v0.1` |
| worldgen ledger | `city_land_use_worldgen_ledger.v0.1` |

`config/geomantia/city_land_use/settings.json` 的 bundled 默认值为：

```json
{
  "schemaVersion": "city_land_use_settings.v0.1",
  "enabledInWorkflow": false,
  "profileId": "default_v0_1"
}
```

目录缺失时安装 bundled default。`city_run_workflow.enableLandUseLayer` 优先于 settings；独立 `city_plan_land_use` 视为显式规划，不受 workflow 开关阻止。

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

`landUseIntentPlan` 可省略；服务端会归一为当前 schema、当前 `cityId`、空 overrides 和默认 seed salt。显式提交时必须是严格对象，所有未知字段 hard fail。

```json
{
  "schemaVersion": "city_land_use_intent_plan.v0.1",
  "cityId": "city_001",
  "seedSalt": "review-a",
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
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schemaVersion` | string | 是 | `city_land_use_intent_plan.v0.1`。 |
| `cityId` | string | 是 | 必须与请求 `citySeedId` 对应的 City 一致。 |
| `seedSalt` | string | 否 | 确定性扰动盐。 |
| `groupOverrides[]` | object[] | 否 | 显式创建 / 修正主体组合。 |
| `subjectOverrides[]` | object[] | 否 | 对 group 或 anchor 设置规则或排除。 |

`groupOverrides[]` 必须含 `groupId`、非空且去重的 `memberAnchorIds[]`；`ruleRef` 可选。一个 anchor 不得同时属于多个 group。

`subjectOverrides[]` 必须含 `targetType=group|anchor`、`targetId` 和 `mode=set_rule|exclude`。`set_rule` 必须含 `ruleRef`；`exclude` 禁止出现 `ruleRef`。不得提交面积、行动力、权重、逐项成本、block mask 或世界坐标。

规则选择优先级为 `subjectOverrides` > `groupOverrides.ruleRef` > D4 semantic 自动解析。未知 target、group 成员冲突和未知 `ruleRef` hard fail；无法解析规则的主体写 warning 并跳过。

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
| `areaId` | string | 稳定区域 ID。 |
| `ruleRef` / `landUseType` | string | 规则引用和用途。 |
| `sourceGroupIds[]` / `sourceAnchorIds[]` | string[] | 可追溯来源。 |
| `seedPoints[]` | BlockPoint[] | footprint 外缘、入口或组合内侧等多源起点。 |
| `spans[]` | ScanlineSpan[] | block 成员；每项为 `z,minX,maxX`，两端包含。 |
| `structureFootprintExclusions[]` | BlockBounds[] | D6 locked 结构硬排除区。 |
| `boundaryLoops[]` | object[] | `points[]` 与 `hole`；内部孔洞不得生成外边界。 |
| `gateSlots[]` | object[] | `gateId`、`block`、`direction`、`sourceAnchorId`。 |
| `claimCostTotal` | number | 解释扩张结果的累计成本，不作为执行参数回传。 |
| `surfacePolicy` | enum | `PRESERVE|PAVE|CULTIVATE|WATER_ADAPTIVE`。 |
| `vegetationPolicy` | enum | `PRESERVE|SELECTIVE_CLEAR|CLEAR`。 |
| `boundaryPolicy` | enum | `OPEN|FENCE|HEDGE|LOW_WALL|SHORELINE`。 |
| `decorationPolicy` | string | Decoration profile / program 选择引用。 |

区域几何与执行策略必须分离：`spans[]` 不得直接复制成 no-vegetation mask；例如 `forestry` 可以是 `PRESERVE + PRESERVE + FENCE`。

规划成功后最后发布 `city_land_use_planning_complete.json`，字段为 `schemaVersion`、`cityId`、`planHash`、`ruleProfileHash`、`sourceD6Hash`、`completedAt`。`execute_d5` 只在 area plan 与 completion 同时存在且 identity / hash 一致时激活；只存在其一必须返回 `CITY_LAND_USE_PLAN_INCOMPLETE`。

## Worldgen 交接

- active 文件：`geomantia_city_masks/active_city_land_use_area_plans.json`。每项冻结 dimension、city、planHash、`paletteHash` 和规范化 `materialPalette={surfaceMaterials,boundaryMaterials,paletteHash}`；重载时 palette hash 漂移必须拒绝旧计划。
- ledger 文件：`geomantia_city_masks/city_land_use_worldgen_ledger.json`。owner applied 项同时记录 planHash 与 paletteHash。
- activation preflight 必须枚举全部 member / boundary owner，只读当前 loaded status 或 region NBT；不得申请 ticket。任一 owner 已到 FEATURES 返回 `CITY_LAND_USE_CHUNK_ALREADY_AT_FEATURES`，读取失败或状态无法证明返回 `CITY_LAND_USE_CHUNK_STATUS_UNKNOWN`，两者都整体拒绝激活。只有磁盘明确不存在才视为 `NOT_PRESENT`。
- 只在 `WorldGenRegion` 首次 FEATURES owner 回调处理当前 chunk；不得跨 owner 写相邻 chunk。
- 编译器用 material palette 把 policy 映射为具体方块，几何 plan 不携带材质。owner 内先 surface、后 boundary，再交给 Decoration；RoadWeaver 真实道路最后写并拥有覆盖权。
- footprint、corridor 和 gate 必须从操作中排除；自然表面不在可替换白名单时单格 skip。
- 方块写失败逆序回滚；整 owner 成功后才追加 applied ledger。重复回调必须由 dimension / city / plan hash / palette hash / owner chunk 幂等阻断。
- 非 `WorldGenRegion` 或已到 FEATURES 的旧 chunk 返回 `CITY_LAND_USE_OLD_CHUNK_NOT_BACKFILLED`，不写方块、不记成功 ledger。
