# City 案子：D4 阵列布局 Agent Loop v0.2 / v0.3

## Summary

本案承载同一条 D4 阵列布局版本线：

- v0.2：已接入程序侧 Array Layout Agent Loop，用平级多个 array item 顺序生成填充结构。
- v0.3：已补嵌套阵列首版，让父阵列生成 parent zone / subZones，child array 在子区域内继承方向、occupied 和剩余空地继续排布。

v0.2 把 D4 阵列从当前 v0.1 的“通用 `arrayCandidatePlan` + 三种基础 pattern”，升级为“城市级 array layout loop + 多个小型 planner 协议 + stateful item replay”。

核心目标：

- AI 不直接写结构坐标，只选择 patch、起始方位、结构列表和阵列方式。
- 每种排列方式有自己的小协议，不做一个万能大参数对象。
- 阵列流程由程序侧 agent loop 驱动，不把循环逻辑藏在提示词 workflow 里。
- 程序按 loop item 顺序执行，每执行一个阵列就更新 occupied field、patch availability 和 preview。
- 结构级做防撞和 repair，不因为一个填充结构失败就删除整个阵列。
- 每个成功阵列沉淀为一个功能区 / array zone，供 D5、D6、D7、RoadWeaver、城墙和预览消费。

本案不替代 D4 `key_then_array` 主流程。它是 D4 阵列层的显式版本线：关键结构仍先逐个定锚，填充结构再按 array layout loop 的 item 顺序生成。v0.3 嵌套阵列仍沿用这条版本线，不另开独立案子。

## Background

当前 v0.1 阵列已经支持：

- `loose_cluster`
- `patch_axis_band`
- `scattered`
- `round_robin` / `seeded_random` / `weighted_random`
- 组内 estimated collision envelope 防撞
- 避让上一阶段 `StructureAnchorMap`

但它仍然偏“撒点候选”：

- 同一个 `arrayCandidatePlan` 同时塞多个 pattern，参数会继续膨胀。
- `patch_axis_band` 只是按 patch 长轴排点，还不是真正的沿线 / 河岸 / 等高线布局。
- `scattered` 能填空，但不太产生城市秩序感。
- 道路不应由 City 自己生成；RoadWeaver 已负责真实道路连接。
- 完整原版 village jigsaw 不适合作为城市生成器，过于不可控；如果用 jigsaw，也应先给受控 slot / bounds。

因此 v0.2 的方向是：City 负责建筑排列秩序，RoadWeaver 负责道路连接。

## Design Position

### AI / 人负责

- 阅读 D3 patch 地形图和城市设定。
- 选择要从哪些 patch / patch sector 开始布局。
- 选择关键建筑与阵列填充结构。
- 为每个阵列选择一个 planner type，并填写该 planner 的小参数表。
- 在每次 loop 返回后，根据 updated occupied / preview 决定提交下一个阵列 item，或结束阵列设计。

### 程序负责

- 将 `patchRef + startSector` snap 到 patch 内可用代表点。
- 根据 planner type 生成候选 anchor 序列。
- 估算 footprint / collision / mask envelope。
- 顺序执行阵列，维护 occupied field。
- 对单个结构做防撞、换候选点、降级 repair。
- 维护 array layout loop state、迭代次数、stop reason、stale state 校验和每轮 preview。
- 输出标准 `StructureAnchorPlan`、array zone 和 road access points。

### RoadWeaver 负责

- 读取结构 / 功能区的少量 road access point。
- 生成真实道路连接。
- City 不为每栋房子生成道路目标，不提前画主路网。

## Target Flow

v0.2 不应实现为“一次提示词写完整座城市”。推荐实现为程序侧 agent loop：

```text
城市设定 + D3 patch 图
  -> AI 选择关键结构列表
  -> 程序完成关键结构逐个定锚，冻结 occupiedField
  -> start Array Layout Agent Loop
      -> 程序返回 currentLoopState / patchAvailability / preview
      -> AI 提交 1 个 next ArrayLayoutPlanItem
      -> 程序执行该 item，做结构级 repair / skip / hardBlock
      -> 程序返回 updatedLoopState / arrayZone / preview / warnings
      -> AI 决定继续、修改方向或 stop
      -> 直到达到 stop condition 或 maxArrayPlans
  -> end Array Layout Agent Loop
  -> 程序汇总所有 anchors，调用标准 city_plan_d4
  -> D6 probe-and-lock
  -> D5 / execute_d5 / worldgen / D7 / RoadWeaver / city walls
```

## Current Implementation Boundary

当前实现能力结论：

- 已支持多个 `layoutPlans[]` 按顺序 replay，每个执行成功后更新 occupied field、patch availability、array anchors 和 functional array zone。
- 已支持在线 endpoint 每次只提交一个 `nextArrayLayoutPlanItem`。
- 已支持 stale state、`maxArrayPlans`、required / fill 分层和 `minCount` hard block。
- 已支持 v0.3 `composite_array` 一层嵌套：一个 execute item 可以生成 parent zone / subZones，并把 `childLayoutPlans[]` 约束在子区域内继续生成结构 anchor。

当前嵌套边界：

- `nextArrayLayoutPlanItem.layoutPlans[]` 仍然禁止，避免把整城计划一次性塞进单轮 execute。
- 只有 `plannerType=composite_array` 可以携带 `childLayoutPlans[]`。
- 首版只保证一层 parent -> child，不做 child 内继续 composite 的深递归。
- parent zone 负责分区、方向继承和 subZone bounds；child array 负责真实结构 anchor。
- child array 继承父 zone 的 occupied、方向和可用 bounds；候选点仍来自 patch member cells，结构硬防撞只使用 collision/body envelope。

实现上仍应保持单轮单 item 边界：如果 `nextArrayLayoutPlanItem` 内直接携带 `layoutPlans`，应拒绝并返回 `D4_ARRAY_LAYOUT_ONE_ITEM_PER_EXECUTE`。

真实测试暴露的设计问题是：仅用平级 `compound_cluster` / `plaza_ring` 为了满足数量和防撞，会变成“避障点阵”，不像居民楼聚在一起。后续需要补“父阵列生成局部空间，子阵列在局部空间内继续排布”的能力。

### Loop State

`ArrayLayoutLoopState` 是程序运行时状态，不是提示词说明文本。每轮必须显式传递或引用稳定 state id：

```json
{
  "schemaVersion": "city_d4_array_layout_loop_state.v0.2",
  "loopId": "city_seed_id/d4_array_layout",
  "stateId": "loop_state_0003",
  "iteration": 3,
  "cityScale": "town",
  "maxArrayPlans": 7,
  "executedArrayIds": ["market_ring_01", "residential_cluster_01"],
  "occupiedFieldRef": "d4_array_occupied_field.json#state_0003",
  "patchAvailabilityRef": "d4_array_patch_availability.json#state_0003",
  "functionalArrayZoneRefs": ["market_ring_01", "residential_cluster_01"],
  "lastPreviewRef": "d4_array_layout_preview_0003.png",
  "stopOptions": ["continue", "finish_city_array_layout", "revise_next_item"],
  "warnings": []
}
```

Loop state 规则：

- AI 每轮只提交一个 `nextArrayLayoutPlanItem`，不得在同一请求里追加多个未执行 item。
- 程序必须用 `stateId` 做 stale state 校验，过期 state 返回 `D4_ARRAY_LAYOUT_LOOP_STATE_STALE`。
- 每轮执行成功后生成新的 `stateId`，旧 state 只可复盘，不可继续写入。
- `d4_array_layout_plan.json` 是 loop 的累计历史和最终归档，不是首轮一次性输入要求。
- stop 必须是显式状态：AI 主动完成、达到 `maxArrayPlans`、patch 容量不足、连续低收益、required item hardBlock。

## Scale Budget

城市规模决定最多阵列数量，避免 AI 无限制追加 Plan：

| cityScale | maxArrayPlans | 典型用途 |
| --- | ---: | --- |
| `starter_village` | 1-2 | 新手村，少量住宅和功能点。 |
| `hamlet` | 1-2 | 小聚落，小房屋簇或一条短街。 |
| `village` | 2-4 | 中心区 + 居民区 + 农田 / 工棚。 |
| `town` | 4-7 | 市场、工坊、居民、河岸、矿区等多组。 |
| `city` | 7-12 | 多节点、多区块、多层次城市。 |

超过上限返回 `D4_ARRAY_LAYOUT_SCALE_LIMIT_EXCEEDED`，让 AI 明确删减或升级城市规模。

## City ArrayLayoutPlan v0.2

顶层 Plan 使用一个城市级协议，但它更像 loop 累计记录。在线执行时，每轮只新增一个 `layoutPlans[]` item；每个 item 只允许一个 planner type。

```json
{
  "schemaVersion": "city_d4_array_layout_plan.v0.2",
  "cityId": "city_seed_id",
  "cityScale": "town",
  "designIntent": {
    "summary": "紧凑矿业山脚镇，市场和行政楼形成中心，居民沿山脚和河岸展开。",
    "density": "high",
    "compactness": "compact"
  },
  "uniqueKeyStructures": [
    {
      "slotId": "civic_core",
      "structureId": "example:admin_hall",
      "candidatePatchRefs": ["plain_01"],
      "startSector": "center"
    }
  ],
  "layoutPlans": []
}
```

首轮可以只包含 `uniqueKeyStructures` 和空 `layoutPlans[]`。阵列 loop 开始后，程序按轮次把已执行 item 追加进归档 Plan。

v0.3 顶层 `schemaVersion=city_d4_array_layout_plan.v0.3` 或 `planningMode=array_layout_loop_v0_3`。v0.2 payload 继续兼容；未使用 `composite_array` 时行为与平级阵列 loop 相同。

### Shared Layout Item Header

每个 `layoutPlans[]` item 都有极薄共享头：

```json
{
  "arrayId": "residential_cluster_01",
  "plannerType": "compound_cluster",
  "role": "residential",
  "candidatePatchRefs": ["plain_01"],
  "startSector": "southeast",
  "requiredItems": [],
  "featuredItems": [],
  "fillPool": [],
  "countPolicy": {
    "minCount": 8,
    "targetCount": 12,
    "maxCount": 14
  },
  "variantSelectionMode": "weighted_random",
  "collisionPolicy": "repair_item_then_skip_fill",
  "roadAccessStrategy": "few_gateways"
}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `arrayId` | 本阵列稳定 ID。 |
| `plannerType` | 只允许一个 planner，例如 `compound_cluster`。 |
| `role` | 人类 review 文本，不投影成 City 枚举。 |
| `candidatePatchRefs[]` | D3 patch id 或 map label。 |
| `startSector` | `center` / `north` / `south` / `east` / `west` / `northeast` / `northwest` / `southeast` / `southwest`。 |
| `requiredItems[]` | 必须放下的唯一结构；失败会 hard block。 |
| `featuredItems[]` | 阵列内特殊点，例如井、钟、小仓库；失败可按策略降级。 |
| `fillPool[]` | 可重复填充结构池，支持权重。 |
| `countPolicy` | 填充数量下限、目标和上限。 |
| `collisionPolicy` | 结构级 repair 规则。 |
| `roadAccessStrategy` | 默认少量入口点，不给每栋房子连路。 |

## Structure Lists

### uniqueKeyStructures

城市级唯一关键结构先走现有 D4 v2 sequential session：

- 行政楼
- 教堂
- 市场主建筑
- 塔楼
- 矿业公会
- 港口核心

这些结构不进入填充随机池，不重复放置。

### requiredItems

阵列内必须存在的结构，例如：

```json
{
  "itemId": "residential_well",
  "structureId": "example:village_well",
  "placementRole": "cluster_center"
}
```

如果 required item 无法放置，阵列返回 hard block：

```text
D4_ARRAY_LAYOUT_REQUIRED_ITEM_UNPLACED
```

### featuredItems

阵列内的特色结构，例如小仓库、井、钟、装饰塔。可配置失败策略：

```json
{
  "itemId": "small_storage",
  "structureId": "example:storage_shed",
  "failurePolicy": "skip_with_warning"
}
```

### fillPool

可重复填充结构池：

```json
[
  {"structureId": "example:house_01", "weight": 0.5},
  {"structureId": "example:house_02", "weight": 0.3},
  {"structureId": "example:hut_01", "weight": 0.2}
]
```

`targetCount` 可以大于 `fillPool` 类型数量，程序按 `variantSelectionMode` 分配。

## Patch Start Sector

AI 不写坐标，但可以选择 `startSector`。程序将 sector 解析为 patch 内代表点：

- `center`：patch 中心或最大可建连通域中心。
- `north/south/east/west`：patch 对应边缘向内收缩后的可用点。
- 四个角 sector：对应象限内可用点。

如果 sector 不可用，程序可按同 patch 内邻近 sector repair，并记录：

```text
D4_ARRAY_LAYOUT_START_SECTOR_REPAIRED
```

若 patch 不存在或无可用代表点，返回：

```text
D4_ARRAY_LAYOUT_PATCH_UNAVAILABLE
```

## Occupied Field

每执行一个 layout item，程序更新 `occupiedField`，而不是简单 mute 整个 patch。

`occupiedField` 至少包含：

- `occupiedEnvelopes[]`
- `occupiedSectors[]`
- `patchAvailability[]`
- `remainingCapacityEstimate`
- `recommendedNextSectors[]`

patch availability 示例：

```json
{
  "patchRef": "plain_01",
  "occupiedSectors": ["center", "southeast"],
  "remainingSectors": ["north", "west", "southwest"],
  "remainingCapacityEstimate": {
    "small": 12,
    "medium": 4,
    "large": 1
  }
}
```

原则：

- 不默认 mute 整个 patch。
- 大 patch 可以承载多个阵列。
- 已占用结构的 `collisionEnvelope` / body envelope 必须成为后续阵列硬避让；`maskEnvelope`、`safetyEnvelope`、道路 corridor、装饰 mask 只可作为后序 reservation / 诊断参考，不得反向撑开 D4 结构点。
- sector 只是 AI 可理解的粗语义，不替代 envelope 防撞。
- 阵列候选点必须从 D3 patch 的 `memberCells[]` 或等价可用 cell 集合出发；patch bbox / subZone bounds 只限制搜索范围，不等于可填满用地。

## Planner Types

### 1. `plaza_ring`

围绕中心结构 / 广场点做环形或半环阵列。

适合：

- 市场摊位
- 广场周边住宅
- 教堂绿地周边小建筑

参数：

```json
{
  "plazaRing": {
    "centerRef": "anchor:market",
    "radiusBlocks": 42,
    "arcDegrees": [30, 330],
    "count": 10,
    "faceCenter": true,
    "ringJitterBlocks": 3
  }
}
```

约束：

- `centerRef` 可以引用已放 anchor、patch sector 或当前阵列 required item。
- `arcDegrees` 允许做半环，避免压水体或陡坡。
- 输出 1-2 个 road access point，不为每个摊位连路。

### 2. `compound_cluster`

紧凑簇 / 院落式阵列，比 v0.1 `loose_cluster` 更有行列和内院秩序。

适合：

- 居民小组
- 工棚区
- 矿工营地
- 小型新手村主体

参数：

```json
{
  "compoundCluster": {
    "centerRef": "patch_sector:plain_01:southeast",
    "clusterShape": "courtyard",
    "rows": 3,
    "columns": 4,
    "spacingBlocks": 22,
    "courtyard": true,
    "jitterBlocks": 2,
    "faceCourtyard": true
  }
}
```

可选 `clusterShape`：

- `grid`
- `courtyard`
- `l_shape`
- `u_shape`
- `organic_compact`

### 3. `guide_line_dual_side`

沿一条引导线两侧排布。引导线不是道路，只是建筑排列参考。真实道路由 RoadWeaver 连接少量 gateway。

适合：

- 两个关键结构之间的街带
- 山脚线
- patch 长轴
- 城门到市场的建筑带

参数：

```json
{
  "guideLineDualSide": {
    "lineRef": "between:anchor:market:anchor:mine_gate",
    "sideMode": "both",
    "countPerSide": 6,
    "setbackBlocks": 14,
    "spacingBlocks": 24,
    "faceLine": true,
    "stagger": true
  }
}
```

`lineRef` 可选：

- `patch_long_axis:<patchRef>`
- `between:anchor:<a>:anchor:<b>`
- `between:patch_sector:<patch>:<sector>:anchor:<b>`
- `manual_hint:<name>`，由上层 recipe 给出抽象 hint，不是坐标。

### 4. `riverbank_dual_side`

沿水岸 patch / shore cells 排布，可单岸或双岸。

适合：

- 渔村
- 河港
- 水岸市场
- 河两岸住宅

参数：

```json
{
  "riverbankDualSide": {
    "shorePatchRefs": ["shore_01", "river_01"],
    "bankMode": "one_bank",
    "countPerBank": 7,
    "waterSetbackBlocks": 10,
    "spacingBlocks": 24,
    "faceWater": true,
    "avoidFloodCells": true
  }
}
```

约束：

- 必须依赖 C1/D3 细扫后的 water / shore member cells。
- 不接受 W 粗 patch 直接驱动。
- water setback 内不得放结构 footprint。

### 5. `contour_band`

沿相近高度带排布，减少硬跨坡。

适合：

- 山城
- 矿业坡地
- 山脚镇
- 梯田式住宅

参数：

```json
{
  "contourBand": {
    "heightBandRef": "auto_from_start_sector",
    "bandWidthBlocks": 18,
    "count": 10,
    "spacingBlocks": 24,
    "maxLocalSlope": 4,
    "terraceStepBlocks": 3,
    "faceDownSlope": true
  }
}
```

约束：

- 需要 D3 / local height facts 支持。
- 候选点必须通过局部高度差和 slope 检查。
- 如果无法满足 `minCount`，返回 `D4_ARRAY_LAYOUT_MIN_COUNT_UNSATISFIED`。

## D4 Array Layout Agent Loop v0.3 Composite Array

嵌套阵列属于同一条版本线的 `D4 阵列布局 Agent Loop v0.3`。v0.2 已经完成程序侧 loop、平级多阵列顺序执行、occupied / patch availability / preview 更新；v0.3 在同一条 array layout loop 版本线里补父子阵列组合能力。

目标不是让 AI 规划更多坐标，而是让 AI 选择“组合排列方法”，程序自动把大阵列拆成多个子阵列：

```text
父阵列算法
  -> 生成 parent zone / orientation / subZones
  -> 子阵列算法 A 在 subZone_01 内放房屋
  -> 子阵列算法 B 在 subZone_02 内放小院 / 附属建筑
  -> 子阵列算法 C 在剩余边角内放填充结构
  -> 汇总为一个 functional array zone 和标准 anchors
```

当前实现采用 `plannerType=composite_array`，而不是把现有五个 planner 的参数继续塞大。

草案示例：

```json
{
  "arrayId": "residential_neighborhood_01",
  "plannerType": "composite_array",
  "candidatePatchRefs": ["plain_01"],
  "startSector": "south",
  "subZoneStrategy": "grid",
  "subZones": [
    {
      "subZoneId": "subZone_01"
    },
    {
      "subZoneId": "subZone_02"
    }
  ],
  "childLayoutPlans": [
    {
      "arrayId": "homes_row_a",
      "plannerType": "guide_line_dual_side",
      "targetSubZoneId": "subZone_01",
      "fillPool": [{"structureId": "example:house_01"}],
      "countPolicy": {
        "minCount": 4,
        "targetCount": 6
      }
    },
    {
      "arrayId": "homes_cluster_b",
      "plannerType": "compound_cluster",
      "targetSubZoneId": "subZone_02",
      "fillPool": [{"structureId": "example:house_02"}],
      "countPolicy": {
        "minCount": 3,
        "targetCount": 4
      }
    }
  ]
}
```

嵌套执行规则：

- 父阵列先生成局部坐标系、方向、父级 zone 和 `subZones[]`，但不一定直接放结构。
- 每个 child plan 只能在目标 `subZone` 的 bounds 内，从源 patch member cells 中采样；subZone bounds 不是可直接填满的矩形地。
- child plan 必须继承父级 occupied field，并把自身结构 `collisionEnvelope` 回写给后续 child。
- child plan 失败只影响本 child，除非父 item 的 `minCount` 或 required item 不满足。
- 最终对外仍输出标准 `StructureAnchorPlan`，下游 D5/D6/D7 不感知嵌套。

适用场景：

- 居民区：父级切成 2-4 个街坊，子级用双排街 / 小簇分别填房子。
- 庄园附属区：父级确定庄园侧翼区域，子级分别放马厩、仓库、仆役房。
- 工坊区：父级确定作坊院落，子级放工棚、材料堆、仓库。
- 未来装饰填充层：父级装饰 brush 也可在 array zone 的剩余空地里执行。

非目标：

- 不允许 AI 在 child plan 里手写每个结构坐标。
- 不允许一次递归无限层；首版最多 2 层：parent + children。
- 不把装饰件混进 D4 结构 anchor；装饰填充层只消费 D4 / D5 的 zone、dressing mask 和 remaining mask。

## Collision And Repair

执行时按结构级候选点搜索，不默认删除整个 Plan，也不允许通过降低数量、扩大 / 缩小语义、切换其他 patch 或 bbox 网格兜底来假装成功。

推荐策略：

| collisionPolicy | 行为 |
| --- | --- |
| `strict_all_or_nothing` | 任意 item 失败则整个阵列 hard fail。 |
| `repair_item_then_skip_fill` | required 必须成功；fill item 碰撞则换点，仍失败可跳过。 |
| `repair_until_min_count` | 只有显式配置 `minCount < targetCount` 时允许少于 targetCount；未配置 `minCount` 时默认 `minCount=targetCount`。 |

执行顺序：

1. required items
2. featured items
3. fill pool items until targetCount
4. 如仍有空间，可补到 maxCount

每个 item 依次检查：

- patch / sector 可用。
- anchor 在 D3 grid 内。
- anchor 来自源 patch member cells / 可用 cell 集合。
- estimated `collisionEnvelope` 不撞 occupied field。
- estimated `collisionEnvelope` 不撞本阵列已接受 item。
- `collisionEnvelope` 不越过硬边界。
- `safetyEnvelope` 只写入 JSON/debug，不参与 D4 结构选点、spacing、repair 或 occupiedField。
- `roadAccessMarginBlocks` 只表达后序 RoadWeaver / D5 意图，不参与 D4 阵列 spacing 或结构防撞。

填充结构失败示例：

```json
{
  "itemId": "house_09",
  "status": "skipped",
  "reasonCode": "D4_ARRAY_LAYOUT_OCCUPIED_CONFLICT",
  "repairAttempts": 5
}
```

## Functional Array Zones

每个成功阵列输出一个 zone：

```json
{
  "zoneId": "zone_residential_cluster_01",
  "schemaVersion": "city_d4_functional_array_zone.v0.2",
  "arrayId": "residential_cluster_01",
  "plannerType": "compound_cluster",
  "role": "residential",
  "sourcePatchRefs": ["plain_01"],
  "placedAnchors": [],
  "requiredPlacedCount": 1,
  "featuredPlacedCount": 1,
  "fillPlacedCount": 10,
  "actualFootprintUnion": {},
  "reservedEnvelopeUnion": {},
  "roadAccessPoints": [],
  "remainingCapacity": {}
}
```

这些 zone 是真实落地结果的归类和后续消费对象，不恢复旧 `FunctionZoneMap` 主链。

## Road Access Points

阵列默认只输出少量入口点：

- `gateway`
- `market_entry`
- `residential_entry`
- `workshop_entry`
- `riverbank_entry`

规则：

- 不给每栋房子注册 RoadWeaver endpoint。
- 每个阵列默认 1 个入口，大型阵列最多 3 个。
- 关键结构仍可单独注册道路端点。
- RoadWeaver 负责连接这些入口与关键结构，City 不提前画路。

## Artifacts

新增或计划新增 artifact：

| Artifact | 说明 |
| --- | --- |
| `d4_array_layout_plan.json` | AI 提交的 v0.2/v0.3 城市级阵列布局计划。 |
| `d4_array_layout_loop_state.json` | 当前 agent loop 状态，含 `stateId`、iteration、stopOptions、occupied / patch availability 引用。 |
| `d4_array_layout_execution_trace.json` | 每个 layout item 的候选、repair、跳过和耗时。 |
| `d4_array_occupied_field.json` | 每步后的 occupied / patch availability 状态。 |
| `d4_functional_array_zones.json` | 成功阵列沉淀出的功能区 / cluster；v0.3 增加 `zoneKind`、`parentArrayId`、`subZoneId`、`subZones[]`、`childArrayZoneIds[]`。 |
| `d4_array_layout_preview.png` | 显示已执行阵列、parent/subZones、child zones、剩余 patch sector 和 road access point。 |
| `structure_anchor_plan.json` | 标准 D4 输出，后续流程不改。 |

## Reason Codes

```text
D4_ARRAY_LAYOUT_PLAN_SCHEMA_INVALID
D4_ARRAY_LAYOUT_PLANNER_TYPE_UNSUPPORTED
D4_ARRAY_LAYOUT_SCALE_LIMIT_EXCEEDED
D4_ARRAY_LAYOUT_PATCH_UNAVAILABLE
D4_ARRAY_LAYOUT_START_SECTOR_REPAIRED
D4_ARRAY_LAYOUT_REQUIRED_ITEM_UNPLACED
D4_ARRAY_LAYOUT_MIN_COUNT_UNSATISFIED
D4_ARRAY_LAYOUT_OCCUPIED_CONFLICT
D4_ARRAY_LAYOUT_NO_CAPACITY
D4_ARRAY_LAYOUT_ROAD_ACCESS_POINT_UNAVAILABLE
D4_ARRAY_LAYOUT_LOOP_STATE_STALE
D4_ARRAY_LAYOUT_LOOP_MAX_ITERATIONS
D4_ARRAY_LAYOUT_LOOP_STOPPED_LOW_GAIN
D4_ARRAY_LAYOUT_ONE_ITEM_PER_EXECUTE
D4_ARRAY_LAYOUT_ONE_ITEM_PER_EXECUTE
```

## Migration From v0.1

v0.1 保留为基础候选 / legacy path：

- `loose_cluster` 可映射到 `compound_cluster.clusterShape=organic_compact`。
- `patch_axis_band` 可映射到 `guide_line_dual_side.lineRef=patch_long_axis:<patchRef>`。
- `scattered` 仅可作为显式低优先级阵列方式；不得在其他 planner 容量不足时自动切换为 bbox 网格兜底。

v0.2/v0.3 不要求一次删除 v0.1 endpoint。当前已新增独立 executor，在 `city_run_workflow` 中用显式开关启用：

```text
d4CandidateMode=array_layout_loop_v0_2
d4CandidateMode=array_layout_loop_v0_3
```

默认仍保留当前 `key_then_array`，直到真实测试证明 v0.3 阵列嵌套能稳定提升紧凑度和设计效率。

## Tests

### Planner Unit Tests

- 每种 planner 都能从 `patchRef + startSector` 生成候选点，且最终候选点必须落在 D3 `memberCells[]` / 可用 cell 集合内。
- `plaza_ring` 能生成指定 arc 内的点，并按 `faceCenter` 给出朝向。
- `compound_cluster` 能生成 grid / courtyard / l_shape / u_shape 基础形态。
- `guide_line_dual_side` 能沿 line 两侧生成 staggered anchors。
- `riverbank_dual_side` 不把结构放进 water setback。
- `contour_band` 不跨越超过 `maxLocalSlope` 的高度差。

### Execution Tests

- layout plans 按顺序执行，后一个 plan 只按前一个 plan 的结构 `collisionEnvelope` / body occupied 避让。
- required item 失败会 hard fail。
- fill item 冲突时只跳过该 item，不删除整个阵列。
- 未显式设置 `minCount` 时默认 `minCount=targetCount`；不足时返回 `D4_ARRAY_LAYOUT_MIN_COUNT_UNSATISFIED`。
- 显式 `minCount < targetCount` 时允许部分成功，但 trace 必须记录 `targetShortfallCount`。
- 两个结构 `collisionEnvelope` 不重叠但 `safetyEnvelope` 重叠时，D4 阵列必须允许放置。
- `roadAccessMarginBlocks`、道路 corridor、装饰 mask、院落或植被 margin 不得改变 D4 anchors / spacing。
- 每个成功阵列输出 functional array zone。

### Workflow Tests

- 城市规模限制 `maxArrayPlans` 生效。
- array layout loop 每轮只接受一个 next item，并在执行后递增 `stateId`。
- 使用过期 `stateId` 继续提交时返回 `D4_ARRAY_LAYOUT_LOOP_STATE_STALE`。
- AI 主动 stop、达到 `maxArrayPlans`、patch 容量不足、连续低收益都能生成清晰 stop reason。
- 输出的 `StructureAnchorPlan` 可被现有 `city_plan_d4` 消费。
- RoadWeaver endpoint 注册只使用关键结构和阵列 road access points，不为每个 fill item 注册端点。
- D6 probe-and-lock 仍是最终 collision 真值。
- 当前 v0.2 必须拒绝 `nextArrayLayoutPlanItem.layoutPlans[]`，返回 `D4_ARRAY_LAYOUT_ONE_ITEM_PER_EXECUTE`。
- `D4 阵列布局 Agent Loop v0.3` 首版应覆盖 parent zone 生成、child subZone 继承 occupied、最终合并标准 `StructureAnchorPlan`。
- `nextArrayLayoutPlanItem.layoutPlans[]` 继续 hard fail；`composite_array.childLayoutPlans[]` 才是合法嵌套入口。

### Real Playtest Acceptance

- 同等结构数量下，城市明显比 v0.1 `loose_cluster/scattered` 更紧凑。
- 每个阵列组在预览图上有可读的秩序：环、簇、沿线、河岸或等高线。
- AI 不需要写坐标，只填写 patch、sector、planner type 和小参数表。
- 失败能定位到具体 array item，而不是整城重来。
- RoadWeaver 连接后不出现每栋房子都引路的乱线。
- 居民区不应只达成“数量够且不碰撞”，还应避免变成环形点阵；应优先用 `composite_array` 形成街坊、院落、排屋等局部组织。

## Non-Goals

- 不生成主路网。
- 不直接使用完整原版 village jigsaw 作为城市主流程。
- 不恢复旧 `FunctionZoneMap` / `BuildableAreaMap` 主链。
- 不做一个万能阵列参数协议。
- 不让 AI 手写每个结构坐标。
- 不把 v0.2 阵列 zone 当作 D6 最终 actual footprint 真值。
- v0.3 不支持无限嵌套阵列；首版只保证 parent + children 一层。

## Open Questions

- `contour_band` 首版是否需要新增更细的 local height tile cache。
- `riverbank_dual_side` 如何从 D3 shore member cells 提取稳定岸线方向。
- RoadWeaver endpoint 是否应该注册到 array zone center，还是 road access point。
- 是否支持撤销上一个 layout item 并回滚 occupied field。
- 是否需要在 UI / preview 中给 AI 显示下一步推荐 sector。
- 是否需要在 `composite_array` 上继续增加撤销 / 重排 child zone 的交互能力。
