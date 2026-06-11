# C6AreaSafetySpec 草案

## 定位

`C6AreaSafetySpec` 是 C6 Area 安全规范阶段的结构化输出。它消费 `C5AreaPlan`、C4 道路上下文、`step = 1` 局部地图、结构画像库和人工关注点，为每个 area 生成安全边界、风险等级、例外规则和复核要求。

它不是工头计划，不是建筑建议，也不是最终结构可落地判定。C7 可以继续读取 `step = 1` 地图并自由规划；C6 只提供统一安全规范。

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `version` | int | 是 | 契约版本，初始建议为 `1` |
| `city_id` | string | 是 | 城市编号 |
| `source` | object | 是 | 输入来源和生成器版本 |
| `coordinate` | object | 是 | 继承 C5/C4 的世界坐标映射 |
| `safety_policy` | object | 是 | 安全规范生成策略 |
| `area_safety_specs` | array | 是 | area 级安全规范 |
| `global_safety_rules` | array | 否 | 城市级通用安全规则 |
| `c6_report` | object | 是 | 生成报告、warning 和缺失数据 |
| `preview` | object | 否 | 安全边界 overlay 预览 |

## `source`

| 字段 | 说明 |
| --- | --- |
| `c5_area_plan_ref` | 输入 `C5AreaPlan.json` 路径或 ID |
| `c4_road_network_ref` | 输入 `C4RoadNetwork.json` 路径或 ID |
| `structure_profile_ref` | 结构画像库路径或 ID |
| `local_map_ref` | `step = 1` 局部地图或扫描数据引用 |
| `human_review_ref` | 人工特别要求或 C5 review 引用 |
| `generator_version` | C6 safety 生成器版本 |
| `generated_at` | 生成时间 |

## `safety_policy`

| 字段 | 说明 |
| --- | --- |
| `local_map_step` | C6 使用的局部地图精度，默认应为 `1` |
| `allow_c7_read_local_map` | 必须为 `true`，C6 不阻止 C7 读图 |
| `allow_c7_soft_override` | 是否允许 C7 对软风险写理由后继续规划 |
| `hard_override_requires_human_review` | 硬约束越界是否必须人工评估 |
| `emit_debug_rects` | 是否输出 debug rect / optional slot |
| `evidence_required_for_high_risk` | 高风险规划是否要求 C8/C9 输出证据 |

## `area_safety_specs`

| 字段 | 说明 |
| --- | --- |
| `area_id` | 对应 C5 area ID |
| `area_type` | `buildable_area / reserved_area / residual_area` |
| `parent_area_id` | 父级 area |
| `layout_profile` | 继承 C5 的布局 profile |
| `reserved_strategy` | 如存在，继承 C5 的保留策略 |
| `safety_level` | `normal / caution / restricted / blocked` |
| `hard_constraints` | 硬约束列表 |
| `soft_risks` | 软风险列表 |
| `exception_policy` | C7 例外处理规则 |
| `review_requirements` | C8/C9 或人工复核要求 |
| `evidence_refs` | 生成该规范的地形、道路、结构或人工证据引用 |
| `notes` | 短说明 |

## `hard_constraints`

| 字段 | 说明 |
| --- | --- |
| `constraint_id` | 约束 ID |
| `type` | 约束类型 |
| `target_ref` | 对应道路、area、地形区域、结构硬事实或人工要求 |
| `severity` | 固定建议为 `hard` |
| `reason` | 约束原因 |
| `override_policy` | `human_review_only / c8_runtime_proof / forbidden` |

推荐类型：

| 类型 | 说明 |
| --- | --- |
| `keep_road_corridor_clear` | 道路走廊不能被普通建筑覆盖 |
| `keep_intersection_area_clear` | 路口、桥头、城门口缓冲不能被普通填充 |
| `protect_reserved_area` | 保留地不能被普通建筑吞掉 |
| `avoid_other_city_boundary` | 不得越入其他城市边界 |
| `avoid_invalid_water_build` | 普通建筑不能覆盖水下区域 |
| `respect_manual_lock` | 人工锁定要求 |

## `soft_risks`

| 字段 | 说明 |
| --- | --- |
| `risk_id` | 风险 ID |
| `type` | 风险类型 |
| `severity` | `low / medium / high` |
| `reason` | 风险原因 |
| `c7_action` | `note_only / require_reason / prefer_conservative_plan / require_review` |

推荐类型：

| 类型 | 说明 |
| --- | --- |
| `large_structure_risk_high` | 大结构风险高 |
| `slope_risk_high` | 坡度风险高 |
| `solid_base_uncertain` | 承托面不确定 |
| `water_overlap_risk` | 与水域重叠风险 |
| `road_buffer_conflict` | 可能挤占道路缓冲 |
| `too_small_for_normal_build` | 面积太小，不适合普通建筑 |

## `exception_policy`

| 字段 | 说明 |
| --- | --- |
| `allow_c7_override` | 是否允许 C7 对软风险继续规划 |
| `requires_reason` | C7 是否必须写理由 |
| `requires_human_review` | 是否需要人工评估 |
| `allowed_exception_types` | `bridge / dock / cliff_building / landmark / manual_override` 等 |
| `blocked_exception_types` | 明确禁止的例外类型 |

## `review_requirements`

| 字段 | 说明 |
| --- | --- |
| `requirement_id` | 复核要求 ID |
| `type` | `footprint_evidence / connector_evidence / terrain_evidence / human_review` |
| `trigger` | 触发条件 |
| `required_stage` | `C7 / C8 / C9 / human` |
| `description` | 复核说明 |

## `global_safety_rules`

| 字段 | 说明 |
| --- | --- |
| `rule_id` | 城市级安全规则 ID |
| `type` | 规则类型 |
| `applies_to` | 适用 area 类型、功能或道路关系 |
| `description` | 规则说明 |

## `c6_report`

| 字段 | 说明 |
| --- | --- |
| `ok` | 是否可交给 C7 |
| `warnings` | 可继续但需要关注的问题 |
| `blocked_area_count` | `safety_level = blocked` 的 area 数 |
| `missing_inputs` | 缺失的输入 |
| `fallback_used` | 是否使用旧 C6 layout / rect guidance 兼容信息 |
| `debug_rects_emitted` | 是否输出 debug rect / optional slot |

## 真值边界

- `C6AreaSafetySpec` 是安全规范，不是设计方案。
- C6 不替 C7 读图；C7 可以读取 `step = 1` 局部地图。
- C6 不选择结构模板，不输出最终坐标、旋转或 jigsaw 约束。
- C6 不修改 C5 area 图，不修改 C4 道路网络。
- 软风险允许 C7 写理由后继续规划；硬约束越界必须人工评估或由 C8/C9 给出合法特例证据。
- 旧 C6 矩形能力可作为 debug/fallback，不能重新成为新主线真值。
