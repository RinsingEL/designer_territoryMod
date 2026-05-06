# C3OwnershipBlocks 草案

## 定位

`C3OwnershipBlocks` 是 C3 意图图转换阶段的结构化输出。它把 C1 `UrbanIntentMap` 和 C2 功能区权重表转换成世界坐标下可追踪的 district / ownership / block seed / road hint 数据，供 C4-C6 临时兼容消费。

它不是最终道路、parcel 或施工计划。

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `version` | int | 是 | 契约版本，初始建议为 `1` |
| `city_id` | string | 是 | 城市编号 |
| `source` | object | 是 | 来源说明，指向 `UrbanIntentMap`、C2 权重表和转换器版本 |
| `coordinate` | object | 是 | 继承并固化本次转换使用的坐标映射 |
| `district_seeds` | array | 是 | 功能区种子，保留 C2 权重 |
| `ownership_polygons` | array | 是 | 世界坐标下的 ownership 多边形 |
| `block_seeds` | array | 是 | 给 C4/C5/C6 消费的街坊或片区种子 |
| `road_hints` | object | 否 | 从道路草图和锚点转换来的道路提示 |
| `anchor_refs` | array | 否 | 被 C3 继承的锚点引用 |
| `conversion_report` | object | 是 | 裁剪、清理、合并、丢弃和 warning 记录 |
| `preview` | object | 否 | 程序重渲染的 overlay 预览路径 |

## `source`

| 字段 | 说明 |
| --- | --- |
| `urban_intent_map_ref` | 输入 `UrbanIntentMap.json` 路径或 ID |
| `district_weights_ref` | 输入 C2 权重表路径或 ID |
| `intent_mask_ref` | 原始纯色机器 mask 路径，仅用于追溯，不供 C3 再解析 |
| `adapter_version` | C3 转换器版本 |
| `generated_at` | 生成时间 |

## `district_seeds`

| 字段 | 说明 |
| --- | --- |
| `district_id` | 稳定功能区编号，继承或规范化自 C2 |
| `source_district_id` | 原始 C1/C2 功能区编号 |
| `dominant_function` | 主功能摘要，仅供日志和 UI |
| `function_weights` | C2 功能权重表，不能压扁成单标签 |
| `world_polygon` | 世界坐标下的功能区多边形 |
| `area_blocks_estimate` | 估算面积 |
| `confidence` | 转换置信度 |

## `ownership_polygons`

| 字段 | 说明 |
| --- | --- |
| `ownership_id` | 稳定 ownership 编号 |
| `district_id` | 所属功能区 |
| `world_polygon` | 裁剪和清理后的世界坐标多边形 |
| `function_weights` | 继承自所属 district 的功能权重 |
| `repair_notes` | 裁剪、合并、碎片清理说明 |

## `block_seeds`

| 字段 | 说明 |
| --- | --- |
| `block_id` | 稳定街坊或片区种子编号 |
| `ownership_id` | 所属 ownership |
| `district_id` | 所属 district |
| `seed_point` | 世界坐标下的代表点 |
| `boundary_hint` | 可选边界提示，供 C4/C5 继续求解 |
| `function_weights` | 继承后的功能权重 |
| `placement_context_hints` | waterfront、road_frontage、plaza_edge 等位置提示 |

## `road_hints`

| 字段 | 说明 |
| --- | --- |
| `main_axis` | 主路轴线提示 |
| `entries` | 城市入口、城门或外部连接点 |
| `bridge_candidates` | 桥或跨水连接候选 |
| `plaza_connections` | 广场连接提示 |
| `warnings` | 断路、过密或无法映射的道路草图问题 |

## `conversion_report`

| 字段 | 说明 |
| --- | --- |
| `ok` | 转换是否可交给下游 |
| `warnings` | 可继续但需要关注的问题 |
| `blocked_reasons` | 阻断转换的原因 |
| `clipped_polygons` | 被城市边界裁剪的多边形 |
| `merged_fragments` | 被合并的小碎片 |
| `discarded_fragments` | 被丢弃的小碎片 |
| `overlap_repairs` | 重叠区域修正记录 |
| `coordinate_check` | 坐标映射检查结果 |

## 真值边界

- `C3OwnershipBlocks` 是 C3 转换真值。
- `intent_overlay_preview.png` 只用于复核，不得反向作为机器解析源。
- `intent_mask.png` 只作为 C1/CV 解析源和追溯材料，C3 不直接读取像素。
- `function_weights` 必须继承 C2 结果，不允许在 C3 被压成单标签。
- C3 不做最终道路、parcel、结构选择或施工合法性判断。
