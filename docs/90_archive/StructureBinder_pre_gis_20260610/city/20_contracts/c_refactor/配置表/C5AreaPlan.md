# C5AreaPlan 草案

## 定位

`C5AreaPlan` 是 C5 Area 图规划与保留策略阶段的结构化输出。它消费 `C3OwnershipBlocks` 和 `C4RoadNetwork`，生成可供 C6 area 安全规范和 C7 工头计划消费的 area 图。

它不是最终结构放置结果，也不是 C6 安全规范。C5 只负责把功能区、道路、锚点和保留空间整理成清晰、可追踪、不过度破碎的候选空间。

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `version` | int | 是 | 契约版本，初始建议为 `1` |
| `city_id` | string | 是 | 城市编号 |
| `source` | object | 是 | 输入来源和规划器版本 |
| `coordinate` | object | 是 | 继承 C3/C4 的世界坐标映射 |
| `area_policy` | object | 是 | 切分、合并、保留和碎片处理策略 |
| `district_areas` | array | 是 | 父级功能区 area |
| `buildable_areas` | array | 是 | 可建设候选 area |
| `reserved_areas` | array | 否 | 公共空间、大结构、组合结构或缓冲预留 |
| `residual_areas` | array | 否 | 边角、碎片、装饰和绿化候选 |
| `area_adjacency` | array | 否 | area 与道路、锚点、相邻 area 的关系 |
| `llm_review` | object | 否 | 多模态复查与策略配置摘要 |
| `planning_report` | object | 是 | 切分、合并、保留、warning 和阻断原因 |
| `preview` | object | 否 | area overlay 预览路径 |

## `source`

| 字段 | 说明 |
| --- | --- |
| `c3_ownership_blocks_ref` | 输入 `C3OwnershipBlocks.json` 路径或 ID |
| `c4_road_network_ref` | 输入 `C4RoadNetwork.json` 路径或 ID |
| `urban_intent_map_ref` | 上游 `UrbanIntentMap.json` 路径或 ID |
| `district_weights_ref` | C2 权重表路径或 ID |
| `planner_version` | C5 area planner 版本 |
| `generated_at` | 生成时间 |

## `area_policy`

| 字段 | 说明 |
| --- | --- |
| `min_buildable_area_blocks` | 最小普通建设候选面积，低于该值优先转 residual |
| `min_frontage_length_blocks` | 临路建设候选最小边长 |
| `max_split_depth` | 单个 district area 最大切分深度 |
| `allow_micro_areas` | 是否允许极小 area 作为摊位、装饰或绿化候选 |
| `respect_road_corridors` | 必须为 `true`，道路走廊不能切成普通建设地 |
| `reserve_intersection_areas` | 是否保留 C4 路口、桥头、城门口、广场边区域 |
| `merge_small_fragments` | 是否合并小碎片 |
| `llm_config_enabled` | 是否启用多模态 LLM 复查和策略配置 |

## area 通用字段

以下字段适用于 `district_areas / buildable_areas / reserved_areas / residual_areas`。

| 字段 | 说明 |
| --- | --- |
| `area_id` | 稳定 area 编号 |
| `area_type` | `district_area / buildable_area / reserved_area / residual_area` |
| `parent_area_id` | 父级 area，可为空 |
| `source_refs` | 来源 district、road corridor、intersection、anchor 或切分动作 |
| `polygon` | 世界坐标多边形 |
| `function_weights` | 继承或修正后的功能权重 |
| `dominant_function` | 摘要用主功能，不作为唯一真值 |
| `size_band` | `tiny / small / medium / large / huge` |
| `split_policy` | `keep_whole / split_later / can_merge / can_trim` |
| `layout_profile` | 布局 profile |
| `frontage` | 临街、滨水、广场边、背街等关系 |
| `constraints` | 道路保留、地标保留、边界、不可切等约束 |
| `confidence` | C5 对该 area 分类和策略的置信度 |
| `warnings` | 局部 warning |

## `buildable_areas`

| 字段 | 说明 |
| --- | --- |
| `candidate_role` | `normal_fill / street_front / courtyard_fill / yard_fill / single_structure_candidate` |
| `preferred_scale` | 建议结构尺度：`small / medium / large / compound` |
| `can_host_multiple_structures` | 是否允许 C7 规划多个结构 |
| `requires_c6_safety_spec` | 是否必须进入 C6 生成 area 安全规范 |
| `avoid_overfill` | 是否要求 C7 保留空隙或院落 |

## `reserved_areas`

| 字段 | 说明 |
| --- | --- |
| `reserved_strategy` | `open_space / single_landmark / compound / service_yard / gate_mouth / bridge_head` |
| `reservation_reason` | 保留原因，如 plaza、port、gate、landmark、road intersection |
| `may_be_built_later` | 是否允许后续放大结构或组合结构 |
| `blocks_normal_fill` | 是否禁止普通住宅/商铺填充 |
| `related_anchor_id` | 关联锚点 |

## `residual_areas`

| 字段 | 说明 |
| --- | --- |
| `residual_kind` | `decor / greenery / stall / buffer / plaza_edge / waterfront_detail / merge_candidate` |
| `merge_candidate_with` | 可合并的相邻 area ID |
| `usable_by_c7` | 是否允许 C7 工头决定用途 |
| `must_not_count_as_capacity` | 是否禁止计入普通建设容量 |

## `area_adjacency`

| 字段 | 说明 |
| --- | --- |
| `from_area` / `to_ref` | area 到 area、road edge、corridor、anchor 的关系 |
| `relation` | `adjacent / fronts / backs_to / faces_water / faces_plaza / blocked_by_road / near_anchor` |
| `weight` | 关系强度 |
| `reason` | 来源说明 |

## `llm_review`

| 字段 | 说明 |
| --- | --- |
| `enabled` | 是否启用 LLM 复查 |
| `input_refs` | 复查输入，如 image2 图、C4 overlay、C5 overlay、结构化 JSON |
| `checked_items` | LLM 检查项 |
| `strategy_suggestions` | 对 `layout_profile / reserved_strategy / split_policy / size_band` 的建议 |
| `accepted_suggestions` | 被程序或人工接受的建议 |
| `rejected_suggestions` | 被拒绝的建议和原因 |
| `requires_human_review` | 是否需要人工评估 |
| `requires_road_review` | 是否发现需要回 C4 或 C1 处理的道路问题 |

## `planning_report`

| 字段 | 说明 |
| --- | --- |
| `ok` | 是否可交给 C6/C7 |
| `warnings` | 可继续但需要关注的问题 |
| `blocked_reasons` | 阻断原因 |
| `split_actions` | 切分记录 |
| `merge_actions` | 合并记录 |
| `reserved_actions` | 保留地生成记录 |
| `residual_actions` | 碎片分类记录 |
| `fragmentation_score` | 破碎度指标 |
| `coverage_summary` | buildable / reserved / residual 面积占比 |

## 真值边界

- `C5AreaPlan` 是 C5 的 area 规划真值，但不是最终结构放置真值。
- C5 不生成最终道路，不修改 `C4RoadNetwork`。
- C5 不选择结构模板，不决定 area 安全规范或最终 footprint。
- `reserved_area` 不是永久空地，而是给 C7/C8 的保留意图。
- `residual_area` 不应计入普通建设容量，除非 C7 明确把它作为装饰、绿化、摊位或合并对象。
- LLM 可以辅助配置 area 策略，但不能覆盖程序的坐标、拓扑和面积计算。
