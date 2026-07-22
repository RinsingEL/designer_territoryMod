# CityLandUseAreaPlan 数据契约

## 定位

本契约定义建筑驱动土地使用层 v0.1 的输入、规则引用、block 级区域输出和 worldgen 交接。它位于 D6 locked actual footprint 之后、DecorationProgram 与 `execute_d5` 之前，不恢复已删除的 `FunctionZoneMap`。

## 版本与开关

| 对象 | schema / version |
| --- | --- |
| 外部 settings | `city_land_use_settings.v0.1` |
| D3 地形事实 | `city_land_use_terrain_field.v0.1` |
| 人工 / AI 意图 | `city_land_use_intent_plan.v0.2`；v0.1 明确拒绝 |
| 规则目录 | `city_land_use_rules.v0.1` |
| 区域计划 | `city_land_use_area_plan.v0.1` |
| 批量地表计划 | `city_land_use_surface_print_plan.v0.1` |
| 规划完成标记 | `city_land_use_planning_complete.v0.1` |
| active registry | `city_active_land_use_area_plans.v0.2`；兼容读取 v0.1 legacy palette plan |
| worldgen ledger | `city_land_use_worldgen_ledger.v0.3`；兼容读取 v0.1/v0.2 |

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

bundled `default_v0_1` 的 `industry` 规则包含 TerraSense canonical term `function.矿业`，以及 `mining`、`mine`、`quarry`、`workshop` 等别名；其 `landUseType` 和 `decorationPolicy` 都为 `industry`。

`city_run_workflow.enableLandUseLayer` 优先于 settings；独立 `city_plan_land_use` 视为显式规划，不受 workflow 开关阻止。

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
  "schemaVersion": "city_land_use_intent_plan.v0.2",
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
  ],
  "surfaceOverrides": [
    {
      "targetGroupId": "farm_mill_cluster",
      "surfacePrintEnabled": true,
      "autoConnect": true,
      "surfaceBlockId": "minecraft:farmland",
      "cropBlockId": "minecraft:wheat",
      "directionMode": "radial",
      "directionCenter": {"x": 651600, "z": 652100}
    }
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schemaVersion` | string | 是 | `city_land_use_intent_plan.v0.2`。旧 v0.1 不自动迁移。 |
| `cityId` | string | 是 | 必须与请求 `citySeedId` 对应的 City 一致。 |
| `seedSalt` | string | 否 | 确定性扰动盐。 |
| `groupOverrides[]` | object[] | 否 | 显式创建 / 修正主体组合。 |
| `subjectOverrides[]` | object[] | 否 | 对 group 或 anchor 设置规则或排除。 |
| `surfaceOverrides[]` | object[] | 否 | 对最终 group 覆写地表印刷、自动连接、方块或方向；未配置字段使用 policy 默认值。 |

`groupOverrides[]` 必须含 `groupId`、非空且去重的 `memberAnchorIds[]`；`ruleRef` 可选。一个 anchor 不得同时属于多个 group。

`subjectOverrides[]` 必须含 `targetType=group|anchor`、`targetId` 和 `mode=set_rule|exclude`。`set_rule` 必须含 `ruleRef`；`exclude` 禁止出现 `ruleRef`。不得提交面积、行动力、权重、逐项成本、block mask 或世界坐标。

`surfaceOverrides[]` 每项字段如下：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `targetGroupId` | string | 是 | 指向 group override 归组后或 D4 provenance 派生的最终 group；同一 target 只能出现一次。 |
| `surfacePrintEnabled` | boolean | 否 | 是否进入 LandUse 批量地表。PAVE / CULTIVATE 默认 true；PRESERVE / WATER 默认 false。 |
| `autoConnect` | boolean | 否 | 是否参加 64 格内兼容近邻相向扩张；按 policy 默认。 |
| `surfaceBlockId` | resource id | 否 | 目标地表 block；PAVE 默认 `minecraft:stone_bricks`，CULTIVATE 默认 `minecraft:farmland`。 |
| `cropBlockId` | resource id | 否 | 批量作物 block；CULTIVATE 默认 `minecraft:wheat`，PAVE 默认空。 |
| `directionMode` | enum | 否 | `global_axis|radial`；默认 `global_axis`。 |
| `directionCenter` | BlockPoint | 条件 | 仅 `directionMode=radial` 可提交；省略时由最终 area `memberSpans` 的稳定质心派生。 |

- PAVE 和 CULTIVATE 使用不同 `compatibilityCategory`，不会互相自动连接；同类别允许具体方块不同，例如两种城区石材仍可连接。
- PRESERVE / WATER 显式 `surfacePrintEnabled=true` 且提供地表方块时提升为 PAVE 兼容类别；`autoConnect` 未显式关闭时随之默认开启。
- `global_axis` 按最终 area bbox 长轴冻结一个全局 cardinal continuation axis 和 origin，相位跨 chunk 不重启。
- `radial` 以显式或稳定派生中心为基准；每个 block 按相对中心的主导轴选择横截面方向与符号，使四个象限向外展开。它仍与全局不规则 mask 求交，不生成圆形或矩形新边界。
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

## CityLandUseSurfacePrintPlan

`city_land_use_surface_print_plan.v0.1` 是与 area plan 分离冻结的执行计划。顶层字段为 `schemaVersion`、`cityId`、`sourceLandUsePlanHash`、`catalogHash`、`planHash`、`areas[]`；hash 必须由严格 codec 的规范 JSON 计算。只要存在 CULTIVATE recipe，`catalogHash` 必须非空并与激活目录一致。

`areas[]` 每项至少包含：

| 字段 | 说明 |
| --- | --- |
| `printAreaId` / `landUseAreaId` / `sourceGroupIds[]` | 稳定执行 ID、来源 area 与 group。不同精确 surface settings 不得在几何编译时误合并。 |
| `surfaceSettings` | 完整冻结 `surfacePrintEnabled`、`autoConnect`、两个 block id、兼容类别、`directionMode` 与 nullable `directionCenter`。 |
| `memberSpans[]` / `exclusionSpans[]` | 全局不规则 mask 和硬排除。chunk 只能裁切这份 mask，不得使用 bbox 重建形状。 |
| `origin` / `continuationAxis` / `directionMode` / `directionCenter` | 全局相位与方向真值；nullable 字段必须显式写 JSON null。 |
| `recipe` | `uniform` 或 `cultivate_lined` 判别联合。 |

`uniform` 只冻结 `surfaceBlockId`。`cultivate_lined` 固定 `repeatPeriodBlocks=13`、`fieldBeforeBlocks=5`、`channelWidthBlocks=3`、`fieldAfterBlocks=5`、`channelOffsetBlocks=5`，并冻结 `cropBlockId`、straight/end-cap prefab spec、terrain policy、`runs[]` 与汇总 `foundationSegments[]`。straight / end-cap contentRef 必须精确为：

- `geomantia:decoration/water_channel_lined_straight_01`
- `geomantia:decoration/water_channel_lined_endcap_01`

每个 prefab spec 冻结 content hash 和尺寸；每个 run 冻结 continuation axis、cross coordinate、稳定 placements、termination ordinal/reason 与 foundation。placement 冻结粗 `surfaceY/targetY` 的相对偏移、sample point、anchor、rotation、footprint、terrain class、decision 和实际 applied content identity。激活后首次相关 owner 以 `liveSurfaceY + (targetY - surfaceY)` 计算真实 targetY，并在 BASE 前按 surface hash + placement ID 持久化；后续 owner 与重启只复用该 datum，不重跑终止决策。

同一个 surface-owned `landUseAreaId` 禁止 Decoration 使用 `uniform_fill`、`cross_section_repeat` 或 `parallel_rows`，避免批量地表重复落地；`deterministic_scatter`、`edge_repeat`、`grid_repeat` 等稀疏细节仍允许。

## LandUse 规划 Trace

`land_use_plan_trace.json` 当前为 `city_land_use_planning_trace.v0.3`。`automaticSurfaceConnections[]` 记录稳定 group 对、兼容类别、初次边界间距与 `already_connected|connected_by_expansion|not_reached` 结果。该 trace 只解释相向扩张，不是 AI 输入或 worldgen 执行参数。

区域几何与执行策略必须分离：`spans[]` 不得直接复制成 no-vegetation mask；例如 `forestry` 可以是 `PRESERVE + PRESERVE + FENCE`。

规划成功后最后发布 `city_land_use_planning_complete.json`，字段为 `schemaVersion`、`cityId`、`planHash`、`surfacePrintPlanHash`、`surfacePrintCatalogHash`、`ruleProfileHash`、`sourceD6Hash`、`completedAt`。新计划必须让 area plan、SurfacePrintPlan 与 completion 三者 identity / hash 一致；旧 completion 未声明 surface hash 时可按 legacy palette 路径读取，声明了 hash 却缺 artifact 必须 hard fail。

## Worldgen 交接

- active 文件：`geomantia_city_masks/active_city_land_use_area_plans.json`，当前 schema v0.2。surface 项冻结 dimension、city、area plan、SurfacePrintPlan、catalog root/hash、material palette/hash；加载时严格复核三类 hash，并一次构建 area、prefab footprint、prefab placement 与 foundation owner index。v0.1 只含 plan + palette 的 legacy 项可读并显式保持旧执行路径。
- ledger 文件：`geomantia_city_masks/city_land_use_worldgen_ledger.json`，当前 schema v0.3。owner applied 项记录 area / surface / palette identity 及 base/crop/boundary/prefab/fallback 数量；`placementDatums[]` 冻结现场 targetY，`placementDecisions[]` 按 surface hash + placement key 冻结 content hash、resolved targetY、`MATERIALIZE|FALLBACK`、reason 与时间。v0.1/v0.2 可读；v0.2 已成功 owner 相交的 placement 迁移为 `MATERIALIZE`。
- activation preflight 必须枚举全部 member / boundary owner，只读当前 loaded status 或 region NBT；不得申请 ticket。任一 owner 已到 FEATURES 返回 `CITY_LAND_USE_CHUNK_ALREADY_AT_FEATURES`，读取失败或状态无法证明返回 `CITY_LAND_USE_CHUNK_STATUS_UNKNOWN`，两者都整体拒绝激活。只有磁盘明确不存在才视为 `NOT_PRESENT`。
- 只在 `WorldGenRegion` 首次 FEATURES owner 回调处理当前 chunk；不得跨 owner 写相邻 chunk。
- legacy 编译器仍用 material palette 把 policy 映射为方块；surface 模式严格消费双计划。owner fragment 只读 prepared 局部索引，不重算 plan hash、不扫描全城 placements、不读取无关 owner NBT。PAVE 可携带只读 grading halo；不得把 halo 计为 owner relevant cell 或跨 owner 主动写入。
- PAVE 微整地固定使用 7x7 真实顶层高度的中位数作为局部参考，只接受补高 1..3 格、连通面积 <=16 且 X/Z span <=4 的封闭低洼。连通低洼触及另一 area、footprint、corridor、gate、水体、非自然表面，或超过深度 / 面积 / span 阈值时不得填充；只向上补方块，不削地、不读取或填充地下空洞。基层使用 `MICRO_FILL_SUBGRADE`，目标顶层仍使用原 PAVE surface material。
- owner 统一事务顺序为 `BASE -> NBT -> CROP -> BOUNDARY`。首次相关 owner 必须在首写前对 placement 全 footprint 预检并同步持久化共享决议：replace-policy 不适配或目标整体越界冻结为 `FALLBACK`，各 owner 恢复原本被该 placement 抑制且仍满足 member/exclusion 的 CROP 与合法 BOUNDARY；`MATERIALIZE` 才写各自 NBT fragment，重叠 placement 仍抑制作物和边界。不可写、状态/快照不可用、实际写入失败等系统错误仍使整个 owner 逆序回滚；后续 owner 或重启不得重新判定已冻结决议。
- boundary 等连接类方块落地前必须按现场邻居求最终 BlockState，并触发原版邻居更新；跨 owner 接缝只允许由该原版更新传播，不得额外生成跨 owner 几何写入。
- footprint、corridor 和 gate 必须从操作中排除；自然表面不在可替换白名单时单格 skip。
- runtime datum 与 placement decision 查找使用内存 O(1) 索引；缺失 datum 先在 registry 全局锁外采样世界，缺失 decision 以单飞方式完成全 footprint 预检，二者都必须持久化成功后才允许首写。非 `FIRST_WORLDGEN_FEATURES` owner 必须在 datum 前短路，不采样、不写 ledger。
- 整 owner 成功后才追加 applied ledger。重复回调必须由 dimension / city / area plan hash / surface plan hash / palette hash / owner chunk 幂等阻断。
- 非 `WorldGenRegion` 或已到 FEATURES 的旧 chunk 返回 `CITY_LAND_USE_OLD_CHUNK_NOT_BACKFILLED`，不写方块、不记成功 ledger。
