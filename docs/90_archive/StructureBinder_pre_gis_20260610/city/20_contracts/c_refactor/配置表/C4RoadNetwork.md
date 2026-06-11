# C4RoadNetwork 草案

## 定位

`C4RoadNetwork` 是 C4 道路草图识别与网络化阶段的结构化输出。它消费 C1/image2 已画出的道路草图，以及 C3 的 `C3OwnershipBlocks`，生成城市级道路图、道路走廊、路口区域和 C5 可消费的 frontage hints。

它不是最终道路施工计划，也不是旧 `C4_FunctionPlan.json`。旧 `C4_FunctionPlan.json` 当前偏功能白名单和 district 语义分配，新 C4 应使用独立文件名，避免语义混用。

道路大形来自 C1 的 image2 意图图；C4 只负责识别、吸附、拓扑化、校验和走廊化。若道路主结构缺失或严重断裂，应回到 C1/image2 重画，而不是让 C4 自行重规划。

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `version` | int | 是 | 契约版本，初始建议为 `1` |
| `city_id` | string | 是 | 城市编号 |
| `source` | object | 是 | 输入来源和识别器版本 |
| `coordinate` | object | 是 | 继承 C3 的世界坐标映射 |
| `road_network_policy` | object | 是 | 识别阈值、吸附阈值、宽度映射和小修补策略 |
| `road_nodes` | array | 是 | 道路图节点 |
| `road_edges` | array | 是 | 道路图边 |
| `road_corridors` | array | 是 | 道路走廊，供 C5 切分 |
| `intersection_areas` | array | 否 | 广场、桥头、城门口和主要路口区域 |
| `frontage_hints` | array | 否 | 给 C5/C6 的临街、滨水、背街等提示 |
| `recognition_report` | object | 是 | 识别质量、warning 和阻断原因 |
| `preview` | object | 否 | 道路 overlay 预览路径 |

## `source`

| 字段 | 说明 |
| --- | --- |
| `c3_ownership_blocks_ref` | 输入 `C3OwnershipBlocks.json` 路径或 ID |
| `urban_intent_map_ref` | 上游 `UrbanIntentMap.json` 路径或 ID |
| `road_sketch_ref` | 上游道路草图结构或 mask 图层引用 |
| `district_weights_ref` | C2 权重表路径或 ID |
| `recognizer_version` | C4 识别/网络化器版本 |
| `generated_at` | 生成时间 |

## `road_network_policy`

| 字段 | 说明 |
| --- | --- |
| `snap_distance_blocks` | 道路端点、交叉点和锚点吸附距离 |
| `gap_repair_max_blocks` | 允许自动补齐的小断口最大距离 |
| `allow_major_redraw` | 第一版固定为 `false`，禁止 C4 大改道路 |
| `bridge_policy` | `none / hinted_only`；第一版只识别 image2 已画出的跨水提示 |
| `arterial_width_blocks` | 主路建议宽度 |
| `collector_width_blocks` | 支路建议宽度 |
| `local_hint_width_blocks` | C5 小路提示宽度 |
| `max_fragmentation_score` | 道路切碎功能区的最大容忍度 |

## `road_nodes`

| 字段 | 说明 |
| --- | --- |
| `node_id` | 稳定节点编号 |
| `type` | `entry / junction / district_center / plaza / port / bridge_head / landmark / service` |
| `x` / `z` | 世界坐标 |
| `source_ref` | 来源锚点、district、block seed 或识别适配器生成 |
| `priority` | 识别和校验优先级 |
| `function_weights` | 可选，继承相关 district / block 的功能权重 |

## `road_edges`

| 字段 | 说明 |
| --- | --- |
| `edge_id` | 稳定道路边编号 |
| `from_node` / `to_node` | 起止节点 |
| `class` | `arterial / collector / local_hint / bridge / plaza_link / waterfront` |
| `polyline` | 世界坐标折线 |
| `width_blocks` | 建议道路宽度 |
| `surface_hint` | `land / bridge / waterfront / tunnel_candidate` 等 |
| `serves_districts` | 服务的 district ID 列表 |
| `recognition_summary` | 来源颜色、线宽、吸附、跨水、越界等识别摘要 |
| `warnings` | 当前道路边的局部 warning |

## `road_corridors`

| 字段 | 说明 |
| --- | --- |
| `corridor_id` | 稳定走廊编号 |
| `edge_id` | 来源道路边 |
| `polygon` | 道路缓冲后的世界坐标多边形 |
| `reserved_for` | `road / bridge / plaza_edge / waterfront` |
| `blocks_c5_buildable_area` | 是否阻止 C5 切成普通 `buildable_area` |
| `frontage_type` | `main_street / side_street / waterfront / plaza_edge / service_back` |

## `intersection_areas`

| 字段 | 说明 |
| --- | --- |
| `area_id` | 稳定区域编号 |
| `type` | `junction / plaza / gate_mouth / bridge_head / port_yard` |
| `polygon` | 世界坐标多边形 |
| `connected_edges` | 关联道路边 |
| `reserved_for_c5` | C5 是否应保留为空地或公共空间 |

## `frontage_hints`

| 字段 | 说明 |
| --- | --- |
| `hint_id` | 稳定提示编号 |
| `target_ref` | district、block seed、road edge 或 corridor |
| `frontage_type` | `arterial_front / collector_front / quiet_back / waterfront / plaza_edge` |
| `weight` | 提示强度 |
| `reason` | 来源说明，如 market 权重高、port 锚点、plaza 连接等 |

## `recognition_report`

| 字段 | 说明 |
| --- | --- |
| `ok` | 是否可交给 C5 |
| `warnings` | 可继续但需要关注的问题 |
| `blocked_reasons` | 阻断原因 |
| `connectivity` | 连通分量、未连接锚点、未连接入口 |
| `boundary_conflicts` | 越城市边界、越领土边界或覆盖其他城市 |
| `water_crossings` | 过水边统计和桥策略结果 |
| `fragmentation` | 道路切碎功能区或 ownership 的指标 |
| `repair_actions` | 小断口补齐、端点吸附、裁剪、降级、删除边等修复记录 |
| `requires_redraw` | 是否建议回到 C1/image2 重画 |

## 真值边界

- `C4RoadNetwork` 是道路网络真值，但不是最终方块施工真值。
- C4 不重新规划道路大形，只网络化 image2 已画出的道路草图。
- C4 可以在粗粒度成本场上判断道路草图是否合理，但不做 step=1 施工合法性。
- `road_corridors` 是 C5 生成 area 图的保留边界。
- 桥、城门、广场只在 C4 作为道路节点、道路边或交叉区域，不选择具体结构模板。
- C4 不改写 C2 功能权重，不重新生成 C3 ownership。
