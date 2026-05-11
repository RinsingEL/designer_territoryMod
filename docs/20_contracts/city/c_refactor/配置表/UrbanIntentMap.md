# UrbanIntentMap 草案

## 定位

`UrbanIntentMap` 是 C1 新城市画布阶段的核心产物。它不是最终施工计划，而是基于 `step = 8` 宏观底图、image2 输出和 CV 解析得到的城市意图图。

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `version` | int | 是 | 契约版本，初始建议为 `1` |
| `city_id` | string | 是 | 城市编号 |
| `source` | object | 是 | 来源说明，包含 image2、手工、程序生成等 |
| `coordinate` | object | 是 | 图像像素、grid、world block 的映射关系 |
| `pre_city_context` | object | 是 | C0/C1-pre 保留的领土、中心锚点、规模分档和规划软提示 |
| `color_mapping` | array | 是 | 生成后由颜色提取和多模态复核得到的颜色到功能区/图层映射 |
| `base_map` | object | 是 | 海陆、等高线、已有城市边界、领土边界等宏观底图信息 |
| `city_boundary` | object | 是 | image2/CV 得到的城市边界 |
| `district_polygons` | array | 是 | 功能区多边形 |
| `road_sketch` | object | 否 | 主路、入口、桥、广场连接草图 |
| `anchor_points` | array | 否 | 城门、广场、港口、地标等锚点 |
| `district_weight_hints` | object | 否 | 从图层解析出的功能权重提示 |
| `cv_report` | object | 是 | CV 解析报告 |
| `basic_check` | object | 是 | 基础一致性检查结果 |

## `source`

| 字段 | 说明 |
| --- | --- |
| `kind` | `image2`、`manual_paint`、`program_fallback` 等 |
| `prompt_id` | image2 prompt 或生成记录编号 |
| `input_preview` | 输入预览图路径 |
| `raw_output` | 原始意图图路径 |
| `generated_at` | 生成时间 |

## `coordinate`

| 字段 | 说明 |
| --- | --- |
| `image_size` | 固定为 `[512, 512]` |
| `source_step_blocks` | 宏观地理采样精度，第一版建议 `8` |
| `world_extent_blocks` | 底图覆盖的世界范围，由城市规模分档决定 |
| `world_origin_x` / `world_origin_z` | 图像左上或参考原点对应的世界坐标 |
| `pixel_to_block` | 像素到方块比例，不要求等于 `source_step_blocks` |
| `source_grid_size` | `world_extent_blocks / source_step_blocks` 得到的原始采样网格 |
| `city_scale_bucket` | `small / normal / large / capital`，只决定底图覆盖范围 |
| `rotation` | 图像方向与世界方向关系 |

## `pre_city_context`

| 字段 | 说明 |
| --- | --- |
| `territory_id` | 所属领土 |
| `center_x` / `center_z` | 当前旧 C1 使用的城市落点；新方案中作为 512 底图取景中心和锚点 |
| `city_scale_bucket` | 城市规模分档，建议为 `small / normal / large / capital` |
| `city_role` | 城市定位，如首都、港城、边镇、贸易城、矿镇等 |
| `density` | 建造紧凑程度，建议为 `low / mid / high`；不表示大中小城市 |
| `ecology` | 生态策略，如保留、适应或清理 |
| `water_policy` | 水域策略，如避水、滨水、港口、跨水等 |

`pre_city_context` 不允许出现 `target_chunk_count`、`bias`、`layers`、`layer_count`、`layer_thresholds`、`selected_cluster_ref` 或它们的 `legacy / summary / hint` 变体。实现过渡期可以在 adapter 内部读取旧 C1 配置，但 `UrbanIntentMap` 落盘结果必须只保留上表字段。

## `color_mapping`

| 字段 | 说明 |
| --- | --- |
| `color_cluster_id` | 颜色簇编号 |
| `sample_rgb` | 代表色 |
| `tolerance` | 程序提取时使用的颜色容差 |
| `layer_type` | `district`、`road`、`anchor`、`boundary`、`water` 等 |
| `district_id` | 若为功能区颜色，对应功能区编号 |
| `function_weights` | 若为功能区颜色，对应功能权重 |
| `llm_reason` | 多模态模型判断该颜色语义的理由 |
| `confidence` | 映射置信度 |

## `base_map`

| 字段 | 说明 |
| --- | --- |
| `land_water` | 海陆、水域、海岸线 |
| `contours` | 等高线或高度分层 |
| `existing_city_boundaries` | 其他城市边界 |
| `territory_boundary` | 当前允许规划范围 |
| `major_geo_notes` | 河流、湖泊、山脊、谷地等主要地理信息 |

## `district_polygons`

| 字段 | 说明 |
| --- | --- |
| `district_id` | 功能区编号 |
| `polygon` | 多边形坐标 |
| `dominant_function` | 主功能 |
| `function_weights` | 功能权重表 |
| `source` | image2、CV、人工修正等 |

## `anchor_points`

| 字段 | 说明 |
| --- | --- |
| `anchor_id` | 稳定编号 |
| `type` | `gate`、`plaza`、`port`、`bridge`、`landmark` 等 |
| `x` / `z` | 世界坐标或 grid 坐标 |
| `weight` | 影响强度 |
| `source` | image2、CV、人工或程序 |

## `basic_check`

| 字段 | 说明 |
| --- | --- |
| `ok` | 是否通过基础校验 |
| `warnings` | 可继续但需关注的问题 |
| `boundary_conflicts` | 与领土边界、其他城市边界的冲突 |
| `repair_actions` | 小碎块清理、断路连接、多边形裁剪等修正 |

## 下游消费

- C2 消费 `district_polygons`、`district_weight_hints`、`road_sketch`、`anchor_points` 生成多边形功能区权重表。
- C3-C5 消费城市边界、功能区多边形和道路草图生成 ownership、road、area。
- C6-C9 不直接信任原始 image2 图，只信任校验后的结构化产物。
- 精细施工级地形检查不在 C1 完成，进入单功能区 `step = 1` 后再处理。
