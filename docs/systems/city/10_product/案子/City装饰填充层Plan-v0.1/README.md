# City 案子：装饰填充层 Plan v0.1

## Summary

本案新增 City 装饰填充层，用来解决结构真实落地后“只有建筑，没有生活痕迹”的问题。

装饰填充层不让 AI 手写每个酒桶、灯柱、稻草人或花坛坐标。AI 只选择功能区用途、风格、密度、装饰池和填充算法；程序读取 D5 规划下来的低优先级装饰 mask、RoadWeaver 在玩家可见前锁定的道路 corridor / route plan 和地形，扣出剩余可用空地后，自动生成地表换皮、小品落点和可执行 block operation。

核心判断：

- 大结构负责城市标志物。
- D4 阵列负责房屋和功能建筑组织。
- RoadWeaver 负责真实道路。
- 装饰填充层负责把道路和建筑之间的剩余空地变成有人使用过的土地。
- 装饰件不是 City 结构，不进入 `StructureAnchorPlan`、planned structure registry 或 RoadWeaver endpoint。

## Position In Workflow

首版实现时序：

```text
D4 结构 anchor / array zones
  -> D5 reservation mask / wall corridor
  -> D6 probe-and-lock 结构 footprint
  -> plan_city_dressing 扣出 effective dressing mask 并生成装饰计划
  -> execute_d5 激活结构、mask、RoadWeaver endpoint 和装饰 worldgen plan
  -> worldgen-time 结构、道路连接、装饰在玩家可见前落地
  -> 可选 post-check / 微修报告
```

装饰填充层不能等待玩家已经看见 RoadWeaver 真实道路后再补刷。原因：

- 玩家看见道路后再修改周边地表会穿帮，并且可能产生高成本二次写入。
- 装饰不能刷到道路上，因此需要在 `plan_city_dressing` 阶段读取 RoadWeaver route plan / corridor mask；RoadWeaver 暂未提供真实 locked corridor 时，首版使用 City 侧连接计划生成预估 corridor 并扩大避让。
- 路边灯、围栏门、摊位、花坛入口依赖 road corridor，而不是等待事后扫描。
- 结构、道路、装饰应尽量在同一批 worldgen-time / chunk-visible-before 阶段完成。
- 若 RoadWeaver 的最终道路可能偏离规划 corridor，必须要求 RoadWeaver 返回稳定 corridor / segment id，或扩大装饰层的 road avoidance margin。

## Core Abstraction

装饰填充层的核心不是“刷一种方块”，而是功能区填充算法：

```text
D5 low-priority dressing mask
  + placed structure ledger
  + roadweaver planned road corridor / route segments
  + terrain / biome facts
  + city style
  + dressing brush plan
  -> remaining empty-space mask
  -> surface operations
  -> small decoration placements
  -> dressing zones
  -> preview / mutation report
```

## Mask Boundary

装饰填充层不改变当前 D5 reservation mask 的定位，但装饰区域也应在 D5 一起规划下去。这里需要明确区分三类东西：

```text
layout envelope
  用于 D4/D6 规划阶段防碰撞，例如 collisionEnvelope / safetyEnvelope。

reservation mask
  用于 worldgen 抑制和保护，例如 noVegetationMask / noVanillaStructureMask / wallCorridorMask。

D5 low-priority dressing mask
  用于给装饰填充层留生活化空间，并在不被高优先级对象占用时抑制植被 / 地物抢占。
```

装饰 mask 不是防碰撞真值，而是低优先级 reservation。它应该在 D5 产出和归档，但必须让位给更高优先级对象：

```text
structure / locked planned structure > wall corridor / gate corridor > road corridor > dressing
```

含义：

- 结构可以占装饰 mask 的位置。
- 墙体和道路可以裁掉装饰 mask。
- 装饰不能占结构、墙体或道路的位置。
- 装饰 mask 不参与 D4/D6 结构防碰撞评分。
- 装饰 mask 在高优先级扣减后，可以进入 D5 worldgen 抑制通道，避免装饰执行前被树、草、原版地物或原版结构抢占。

装饰层执行前再计算实际可刷区域：

```text
effective_dressing_mask =
  D5 low-priority dressing mask
  - D7 actualFootprint / lockedCollisionEnvelope
  - RoadWeaver plannedRoadCorridor / lockedRouteCorridor
  - wall corridor / placed wall footprint
  - water / steep slope / hard blocked cells
```

规则：

- low-priority dressing mask 不阻止后续结构、道路或城墙占用。
- D5 激活 worldgen mask 时，应先完成高优先级扣减，再将剩余 dressing 区域加入对应抑制通道。
- 装饰填充层只在扣减后的 `effective_dressing_mask` / `remaining empty-space mask` 内执行。
- 每个 surface operation 和 decoration placement 都必须二次检查 mask，不满足则 repair 或 skip。
- mask 是约束，不是形状模板；外形应贴合 patch member cells、道路、河岸和真实地形，内部再生成有秩序的行列 / 花坛 / 院落。

### AI / 人负责

- 选择要填充的区域语义，例如庄园西侧、居民区间隙、道路边、河岸边。
- 选择用途：葡萄园、农田、花园、菜地、院子、市集边角、墓园、工坊堆场。
- 选择密度、整洁度、富裕度、风格和装饰池。
- 选择填充算法，不选择具体坐标。

### 程序负责

- 从 planned structure registry / D6 locked ledger 扣除结构 `lockedCollisionEnvelope` / safety margin。
- 从 RoadWeaver pre-visible route plan 扣除 `plannedRoadCorridor` / `lockedRouteCorridor`。
- 从 D3 / terrain scan 扣除水体、陡坡、不可替换方块和硬边界。
- 将剩余空地切成可填充子区域。
- 按算法生成骨架、地表操作和小品落点。
- 每个小品落点执行贴地、碰撞、朝向、坡度和道路距离检查。
- 无法放置的小品可以跳过并写 warning，不应导致整城失败。

## Dressing Brush Plan

顶层 schema：

```json
{
  "schemaVersion": "city_dressing_brush_plan.v0.1",
  "cityId": "city_seed_id",
  "styleIntent": {
    "wealth": "modest",
    "order": "tidy",
    "biomeAdaptation": "respect_existing"
  },
  "dressingLayoutItems": [
    {
      "schemaVersion": "parallel_rows_dressing_item",
      "brushId": "manor_vineyard_west",
      "itemId": "manor_vineyard_west",
      "role": "vineyard",
      "targetAreaRef": "remaining_mask:near_anchor:manor_core:west",
      "density": "medium",
      "orientationStrategy": "patch_long_axis",
      "surfacePalette": "grass_path_and_farmland",
      "decorationPool": [
        {"pieceId": "vine_trellis_segment", "weight": 1.0},
        {"pieceId": "barrel_stack", "weight": 0.35},
        {"pieceId": "handcart", "weight": 0.15},
        {"pieceId": "lamp_post", "weight": 0.2},
        {"pieceId": "fence_gate", "weight": 0.2}
      ],
      "countPolicy": {
        "minDecorations": 6,
        "targetDecorations": 16,
        "maxDecorations": 24
      },
      "coordinationPolicy": {
        "placementOrder": "skeleton_then_major_then_minor",
        "comfortSpacing": "normal",
        "socketMode": "prefer_contextual",
        "minorFailurePolicy": "skip_with_warning"
      }
    }
  ]
}
```

兼容期可接受旧 `brushes[]` 字段，但当前真值字段是 `dressingLayoutItems[]`。HTTP 入口保持一个 `POST /realm/city/plan_city_dressing`，payload 内按阵列方式拆成多个 item schema，避免一个巨型 optional 参数对象。

`targetAreaRef` 不应是手写坐标。可选来源：

- `dressing_mask:near_anchor:<anchorId>:<sector>`
- `dressing_mask:inside_array_zone:<zoneId>`
- `dressing_mask:between_anchor:<a>:<b>`
- `dressing_mask:roadside:<roadSegmentId>`
- `dressing_mask:patch:<patchRef>:<sector>`

## Fill Algorithms

算法本身应通用，具体用途由 palette 和 decoration pool 决定。

| fillAlgorithm | 适合用途 | 核心行为 |
| --- | --- | --- |
| `parallel_rows` | 葡萄园、花田、规则农田 | 沿长轴 / 坡向 / 道路方向生成平行行列，再在行列端点和边角放小品。 |
| `parcel_fields` | 农田、菜地、稻田 | 将区域切成多个田畦，插入水渠 / 田埂 / 小桥和稻草人。 |
| `formal_axis_garden` | 庄园花园、教堂花园 | 生成中轴、对称花坛、中心小品和边界树篱。 |
| `courtyard_dressing` | 居民院落、工坊院子 | 在建筑簇内部剩余空地放井、柴堆、晾晒、箱桶和小路。 |
| `roadside_edge` | 路边生活感 | 沿 RoadWeaver locked route corridor 两侧放灯、花坛、摊位、矮栅栏和告示牌。 |
| `corner_clutter` | 边角杂物 | 在不规则边角放木桶、手推车、干草、木箱、堆肥桶。 |
| `boundary_frame` | 围栏、树篱、矮墙 | 沿区域外缘生成边界和少量入口，不填满内部。 |

当前 item schema：

| schemaVersion | fillAlgorithm | 说明 |
| --- | --- | --- |
| `parallel_rows_dressing_item` | `parallel_rows` | 葡萄棚、花架、规则排布装饰。 |
| `parcel_fields_dressing_item` | `parcel_fields` | 农田、水渠、田埂、稻草人、干草堆。 |
| `formal_axis_garden_dressing_item` | `formal_axis_garden` | 中轴花园、对称花坛、长椅、灯。 |
| `courtyard_dressing_item` | `courtyard_dressing` | 建筑院落、门前空地、小型生活物件。 |
| `roadside_edge_dressing_item` | `roadside_edge` | 道路边灯笼栅栏、长椅、酒桶、杂物。 |
| `corner_clutter_dressing_item` | `corner_clutter` | 角落杂物、推车、箱桶、干草。 |
| `boundary_frame_dressing_item` | `boundary_frame` | 围栏、树篱、边界灯。 |

公共字段只保留 `itemId / targetMaskId / targetAreaRef / targetBounds / priority / density / seed / piecePool / skipPolicy`。每种 item 只接受自己的专属参数；跨 schema 参数返回 `CITY_DRESSING_ITEM_FIELD_UNSUPPORTED`。

示例映射：

```text
葡萄园 = parallel_rows + vine_trellis pool + barrel / handcart / fence decoration
农田 = parcel_fields + crop / water_channel / scarecrow / hay decoration
花园 = formal_axis_garden + flower_bed / hedge / fountain / lamp decoration
居民院子 = courtyard_dressing + well / woodpile / clothesline / crate decoration
```

## Local Occupancy And Coordination

装饰填充层不允许把装饰当作互不相关的随机点撒进 mask。每个 brush 执行时都必须维护局部占位场：

```text
effective_dressing_mask
  -> dressing zone
  -> skeleton / guide lines
  -> local occupied field
  -> prioritized decoration placements
  -> socket / adjacency repair
  -> placement trace
```

装饰 piece 至少需要声明两层 envelope：

| Envelope | 用途 | 规则 |
| --- | --- | --- |
| `bodyEnvelope` | 实际方块占地。 | 不得与结构、道路、墙体、硬 mask 或其他 decoration body 重叠。 |
| `comfortEnvelope` | 视觉留白 / 操作空间。 | 默认避免重叠；贫穷、杂乱或高密度风格可允许轻微压缩。 |

放置顺序固定为：

1. `skeleton`：先生成田畦、水渠、花园中轴、边界、路边参考线等骨架。
2. `major`：再放井、葡萄棚、摊位、栅栏门、中心小品等大件或语义关键件。
3. `minor`：最后放酒桶、箱子、花盆、灯、柴堆、干草等小件。

每成功放置一个 surface operation 或 prefab，都必须写入该 brush 的 `localOccupiedField`；同一功能区的后续 brush 还应读取前序 brush 的 occupied field，避免跨 brush 重叠。

装饰之间通过 socket / adjacency 规则配合，而不是只靠随机距离：

| 规则类型 | 示例 |
| --- | --- |
| `attach_to_wall` | 酒桶堆、木箱、柴堆优先贴建筑边、围栏内侧或角落。 |
| `near_path_edge` | 手推车、路灯、摊位靠小路 / RoadWeaver corridor 边缘，但不得堵门。 |
| `row_endpoint` | 葡萄棚端点可放酒桶、手推车、栅栏门或小灯。 |
| `field_corner` | 稻草人、干草堆、井优先放在田块角点或田埂交汇处。 |
| `axis_node` | 花园喷泉、雕像、灯柱优先放在中轴节点或对称节点。 |
| `boundary_gap` | 栅栏门必须落在边界缺口，并朝向内部通路或道路。 |

失败策略：

- skeleton 失败：brush 降级、缩小区域或 hard warning；必要时跳过该 brush。
- required / major piece 失败：按 `minorFailurePolicy` 之前的专门策略处理，可 repair、降级或 warning。
- minor piece 失败：跳过单个 placement，并写入 `CITY_DRESSING_DECORATION_SKIPPED`。
- 最终数量低于 `countPolicy.minDecorations` 时，返回 `CITY_DRESSING_MIN_DECORATION_UNSATISFIED`。

## Terrain Adaptation

装饰填充层首版不要求复杂地形重塑，但必须适应原版地形残留：

- 可清理雪层、草、花、小灌木和树叶残片。
- 可将小范围地表替换成 grass block、path、farmland、coarse dirt、gravel、stone path。
- 不默认大规模削山或填湖。
- 坡度超过阈值时，算法应缩小区域、改成 `boundary_frame`，或跳过并 warning。
- 水渠、田埂、台阶应按局部高度贴地，不跨越大高差硬刷。

## Decoration Pieces

装饰件建议作为小型 prefab / NBT piece 或直接 block operation，不走完整 jigsaw 扩张，也不作为 City 结构注册：

- `barrel_stack_3x3`
- `handcart_3x5`
- `scarecrow_1x1`
- `lamp_post_1x1`
- `well_5x5`
- `hay_corner_4x4`
- `vine_trellis_segment_1x5`
- `fence_gate_3w`
- `flower_bed_segment`
- `water_channel_segment`

程序只负责在 brush 内部找槽位、旋转、贴地和避让。

装饰件分类：

| 类型 | 说明 | 是否触发道路 |
| --- | --- | --- |
| `surface_operation` | 草地整理、路径、农田、水渠、花坛、雪层清理。 | 否 |
| `dressing_prefab` | 酒桶堆、手推车、稻草人、灯柱、葡萄棚段等小型 NBT / 模板。 | 否 |
| `dressing_boundary` | 栅栏、树篱、矮墙、门洞。 | 否 |

禁止事项：

- 不生成 `StructureAnchorPlan.anchors[]`。
- 不写入 active planned structure registry。
- 不注册 RoadWeaver structure endpoint / connection endpoint。
- 不作为 D6 planned worldgen structure probe-and-lock。
- 不使用完整原版 village jigsaw 做扩张。

如果某个装饰区需要道路感，只能通过 `roadside_edge` 读取 RoadWeaver locked route corridor 后沿路布置灯、花坛或摊位；不得让每个装饰件反向驱动 RoadWeaver 生成道路。

## Outputs

当前 artifact：

| Artifact | 说明 |
| --- | --- |
| `city_dressing_brush_plan.json` | AI / 人提交的装饰填充计划。 |
| `city_dressing_effective_mask.json` | 装饰层执行前从 D5 装饰 mask 扣除 locked 结构 envelope、RoadWeaver route corridor、水体、墙体和硬边界后的可用空地。 |
| `city_dressing_execution_trace.json` | 每个 brush 的骨架、落点、跳过原因和耗时。 |
| `city_dressing_surface_operation_plan.json` | 地表替换、清理、铺装、水渠和田埂操作。 |
| `city_dressing_decoration_placement_plan.json` | 小型 prefab / 装饰件落点和旋转；不转成 `StructureAnchorPlan`。 |
| `city_dressing_occupied_field.json` | 每个 dressing zone / brush 的 bodyEnvelope、comfortEnvelope、socket 绑定和跳过记录。 |
| `city_dressing_zones.json` | 已完成装饰功能区，用于复盘和后续风格化。 |
| `city_dressing_preview_index.json` | 每张局部预览的索引、itemId、bounds、previewMode。 |
| `city_dressing_preview_<itemId>.png` | 单个装饰区裁切放大图，显示有效 mask、骨架线、装饰占地、piece id 和跳过位置。 |
| `city_dressing_templates/city_dressing_template_library.json` | 内置测试装饰模板库定义。 |
| `city_dressing_templates/*.nbt` | 葡萄棚、灯笼栅栏、稻草人、酒桶 / 箱子、干草堆、长椅、方块代理推车。 |
| `active_city_dressing_plan.json` / `city_dressing_worldgen_ledger.json` | `execute_d5` 激活后的 server-root 装饰 worldgen 计划和幂等 ledger。 |

## Reason Codes

```text
CITY_DRESSING_ROAD_CORRIDOR_REQUIRED
CITY_DRESSING_RESERVATION_MASK_UNAVAILABLE
CITY_DRESSING_REMAINING_SPACE_UNAVAILABLE
CITY_DRESSING_TARGET_AREA_EMPTY
CITY_DRESSING_FILL_ALGORITHM_UNSUPPORTED
CITY_DRESSING_ITEM_FIELD_UNSUPPORTED
CITY_DRESSING_DECORATION_POOL_EMPTY
CITY_DRESSING_MIN_DECORATION_UNSATISFIED
CITY_DRESSING_SURFACE_OPERATION_BLOCKED
CITY_DRESSING_TERRAIN_TOO_STEEP
CITY_DRESSING_COLLISION_CONFLICT
CITY_DRESSING_DECORATION_SKIPPED
CITY_DRESSING_SOCKET_UNSATISFIED
```

## Tests

- 能从 locked structure ledger + RoadWeaver locked route corridor 生成 remaining space mask。
- D5 能生成低优先级 dressing mask，并在结构 / 墙体 / 道路扣减后把剩余区域写入 worldgen 抑制通道。
- dressing mask 不影响 D4/D6 结构防碰撞，且不能覆盖结构 / 墙体 / 道路。
- 装饰件不写入 `StructureAnchorPlan`、planned structure registry 或 RoadWeaver endpoint。
- 不把装饰或地表刷到结构 locked envelope、RoadWeaver corridor、水体或硬 mask 上。
- 每个 brush 必须维护 `localOccupiedField`，同 brush 内 decoration body 不得重叠。
- 跨 brush 执行时，后续 brush 必须读取前序 brush occupied field，避免同一 zone 内互相覆盖。
- `comfortEnvelope` 默认避免重叠；高密度 / 杂乱风格只允许按策略压缩，不能压到 `bodyEnvelope`。
- socket / adjacency 规则必须能让酒桶贴墙、路灯贴路、稻草人贴田角、栅栏门贴边界缺口。
- `parallel_rows` 能在不规则区域内生成多条可读行列。
- `parcel_fields` 能生成田畦、水渠和少量小品。
- `formal_axis_garden` 能围绕 anchor / zone 生成中轴和对称花坛。
- `roadside_edge` 只沿 RoadWeaver locked route corridor 两侧落点。
- 小品失败只跳过单个 placement，除非低于 `minDecorations`。
- preview 能让人看出单个装饰区、有效 mask、阵列骨架、占地和被跳过原因。
- 测试模板库必须包含 `vine_trellis_segment`、`lantern_fence`、`scarecrow`、`barrel_stack`、`haystack`、`bench`、`handcart_proxy`，且 NBT 可读。

## Non-Goals

- 不恢复旧 `FunctionZoneMap` 主链。
- 不让 AI 手写每个装饰坐标。
- 不把装饰件当作 City 结构或 RoadWeaver endpoint。
- 不用完整原版 village jigsaw 做装饰生成。
- 不在 RoadWeaver route plan / route corridor 锁定前执行。
- 不把大规模地形改造混进首版。

## Open Questions

- D5 是否需要正式产出 `d5_dressing_reservation_mask.json`，还是继续由 `plan_city_dressing` 从现有 mask / patch / zone 推导 effective mask。
- RoadWeaver 是否能在玩家可见前输出稳定 road segment id / corridor id，供 `roadside_edge` 精确引用；首版先用 City 侧连接计划估算 corridor。
- 装饰 prefab 首版使用 City 内置小模板库；后续是否接 TerraSense 扫描并进入统一 profile catalog。
- 装饰填充层和 `City结构风格化换皮-v0.1` 的顺序：先换皮再装饰，还是先装饰再整体 palette pass。
