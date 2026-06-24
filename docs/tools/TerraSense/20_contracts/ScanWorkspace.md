# TerraSense ScanWorkspace 契约

## 定位

`ScanWorkspace` 是 TerraSense in MC、TerraSense Studio 和后续导出器之间的本地文件协议。

MC 端只负责扫描、截图和硬事实导出；Studio 负责 AI 初标与人工审核；导出器只消费已审核结果和冻结术语。

## 目录结构

```text
TerraSenseWorkspace/
  scan_manifest.json
  vocabulary.json
  structures/
    <safe_structure_id>/
      data.json
      scan_config.json
      ai_suggestion.json
      review.json
      screenshots/
        front.png
        right.png
        top.png
        iso_45.png
  exports/
    C3_5_FunctionEnumTable.json
    C3_5_StructureCatalog.preprocessed.json
    StructureProfile.jsonl
```

`safe_structure_id` 使用结构 id 的文件安全形态，例如把 `minecraft:village/plains/houses/plains_small_house_1` 转为 `minecraft__village_plains_houses_plains_small_house_1`。

命令生成样本应添加样本类型前缀，避免和同名模板级样本冲突：

- `jigsaw_assembly`：例如 `minecraft:village/plains/town_centers` 转为 `jigsaw_assembly__minecraft__village_plains_town_centers`。
- `structure_assembly`：例如 `trek:village/plains` 转为 `structure_assembly__trek__village_plains`。

## `vocabulary.json`

`vocabulary.json` 是 Studio 维护的审核词表。词表允许 AI 发现新标签，但落盘后必须保持稳定、可搜索、可去重。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `term_id` | string | canonical term id，由 `vocab_type` 和主标签生成 |
| `vocab_type` | string | `function/style/placement/usage/template_role/quality` |
| `label` | string | 中文主标签，用于人工审核和正式展示 |
| `aliases` | array | 英文别名、同义词或旧称，用于搜索和去重 |
| `status` | string | `approved/proposed/deprecated` |
| `description` | string | 术语说明 |
| `merge_into` | string/null | 废弃或合并时指向的 canonical term |

AI 初标提示词可以要求新增标签使用 `中文（English）` 格式，例如 `蘑菇图腾（Mushroom Totem）`。Studio 写入词表时不把整串作为主标签，而是归一化为：

- `label = 蘑菇图腾`
- `aliases = ["Mushroom Totem"]`

`ai_suggestion.json` 中的单项 `source_label` 保留模型原始输出，方便追溯模型当时给出的完整文本。只有括号内包含英文字母时才按英文别名拆分；类似 `道路节点（小型）` 的中文括注应作为完整中文标签保留。

## `scan_manifest.json`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `workspace_version` | number | workspace 契约版本 |
| `run_id` | string | 本次扫描运行 id |
| `created_at` | string | ISO 时间 |
| `source` | object | MC 版本、Forge 版本、TerraSense 版本、已加载 mod 摘要 |
| `sample_set` | array | 本次扫描的样本类型与结构 id |
| `structures` | array | 单结构产物索引 |
| `status` | string | `running/completed/failed/partial` |
| `errors` | array | 扫描或截图错误 |

单结构索引至少包含：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `structure_id` | string | 原始结构 id |
| `safe_structure_id` | string | 文件安全 id |
| `sample_type` | string | `single/template/single_template/jigsaw_assembly/structure_assembly` |
| `state` | string | `pending/scanned/ai_done/reviewed/failed` |
| `paths` | object | `data/scan_config/screenshots/ai_suggestion/review` 相对路径 |
| `placement_command` | string | 命令生成样本可选，记录实际使用的 MC 放置命令 |
| `error` | string | 可选错误说明 |

## `data.json`

`data.json` 是硬事实，只能来自 MC runtime、NBT 扫描或确定性规则。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `structure_id` | string | 原始结构 id |
| `size` | object | `width/height/depth` |
| `source` | object | namespace、path、mod hint |
| `palette` | object | 方块统计 |
| `jigsaw_points` | array | 原始 jigsaw 语义 |
| `connectors` | array | 从水平 `front` 派生的兼容 connector |
| `footprint` | object | 占地与 origin offset |

命令生成样本额外字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `sample_type` | string | `jigsaw_assembly` 或 `structure_assembly` |
| `profile_type` | string | 固定为 `jigsaw_system` |
| `independent_semantic_unit` | boolean | 固定为 `true`，表示整套生成结果可作为一个语义单元审核 |
| `placement_kind` | string | `minecraft_place_structure` 或 `minecraft_place_jigsaw` |
| `placement_command` | string | 实际执行的 `place structure` 或 `place jigsaw` 命令 |
| `assembly` | object | structure/start pool、命令锚点、内容包围盒原点等整包样本信息 |

命令生成样本的 `footprint.origin_offset` 含义是：实际内容包围盒最小点相对命令锚点的偏移。后续整包落地消费必须使用该偏移还原命令锚点与内容范围的关系。

`structure_assembly` 使用地表模式扫描：命令锚点不一定等于固定摄影 origin，而是由当前世界表面高度计算出的 `surface_anchor`。MC 端放置前记录地表基线，放置后只统计相对基线变化的非空气方块；天然地形表面不应进入结构 palette。相关坐标字段如下：

| 字段 | 说明 |
| --- | --- |
| `footprint.origin_offset` | 内容包围盒最小点相对实际命令锚点的偏移 |
| `assembly.command_anchor` | `stage_origin` 或 `surface_anchor` |
| `assembly.command_anchor_world_pos` | 实际执行 `place` 命令的世界坐标 |
| `assembly.command_anchor_offset` | 命令锚点相对固定摄影 origin 的偏移 |
| `assembly.content_origin_world_pos` | 内容包围盒最小点的世界坐标 |

`jigsaw_points` 必须保留：

| 字段 | 说明 |
| --- | --- |
| `local_pos` | 结构内坐标 |
| `orientation_raw` | runtime 原始 orientation |
| `front` | `JigsawBlock.getFrontFacing` 结果 |
| `top` | `JigsawBlock.getTopFacing` 结果 |
| `name` | jigsaw name |
| `target` | jigsaw target |
| `pool` | jigsaw pool |
| `joint` | jigsaw joint |
| `final_state` | jigsaw final_state |

## `scan_config.json`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `sample_type` | string | `single/template/single_template/jigsaw_assembly/structure_assembly` |
| `camera` | object | 截图视角配置；`camera.angles` 至少包含 `id/label/file/yaw/pitch` |
| `placement` | object | 摄影场 origin、内容 origin、清场边距、底板设置；命令生成样本额外记录 `command` |
| `screenshot_files` | array | 本结构截图文件列表 |
| `scan_options` | object | 是否跳过 AI、是否强制重扫等 |

标准截图视角为四张：

| `id` | 文件 | 说明 |
| --- | --- | --- |
| `front` | `screenshots/front.png` | 正面立面视图，用于判断入口、门窗和主要外观 |
| `right` | `screenshots/right.png` | 侧向立面视图，用于补足结构深度、侧面连接和遮挡信息 |
| `top` | `screenshots/top.png` | 俯视图，用于判断占地、道路关系和整体平面轮廓 |
| `iso_45` | `screenshots/iso_45.png` | 45 度斜俯视图，用于判断整体体量和视觉质量 |

## `ai_suggestion.json`

AI 初标只作为建议，不是最终真值。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `mode` | string | `mock` 或 `vision_api` |
| `model` | string | 使用的模型或 mock 名称 |
| `created_at` | string | 生成时间 |
| `inputs` | object | 使用的截图、硬事实、词表版本和低置信路径语义包 |
| `suggested_curation` | object | 功能、风格、用途、位置、质量建议 |
| `confidence` | object | 分项置信度 |
| `evidence` | array | 视觉或硬事实依据 |
| `warnings` | array | 不确定项或需要人工关注的问题 |

`inputs.source_semantics` 用于把结构路径名显式交给 AI，但它不是硬事实真值。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `structure_id` | string | 原始结构 id |
| `namespace` | string | namespace |
| `path` | string | 结构 path，例如 `village/plains/town_centers` |
| `path_segments` | array | 按 `/` 拆分后的路径段 |
| `tokens` | array | 从结构 id、path、placement command 拆出的低置信语义 token |
| `sample_type` | string | 样本类型 |
| `placement_command` | string/null | 命令样本的放置命令 |
| `start_pool` | string/null | `jigsaw_assembly` 的 start pool |
| `structure` | string/null | `structure_assembly` 的 configured structure id |
| `confidence` | string | 固定为 `low` |
| `usage_note` | string | 提醒 AI 路径语义只能辅助，不能覆盖视觉、硬事实和人工审核 |

自动流程不生成 `interior` 截图字段，也不要求 AI 推断看不见的内饰。内饰用途、室内质量和可进入性先由人工审核写入 `review.json`。

## `review.json`

`review.json` 是人工审核真值。导出正式 StructureBinder catalog 时默认只消费 `review_state=approved` 的结构。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `review_state` | string | `pending/approved/rejected/needs_review` |
| `reviewer` | string | 审核人 |
| `manual_override` | boolean | 是否覆盖 AI 建议 |
| `curation` | object | 人工确认后的功能、风格、用途、位置、质量 |
| `vocabulary_refs` | array | 引用的 canonical term |
| `manual_notes` | string | 人工备注 |
| `updated_at` | string | 更新时间 |

## 约束

- MC 端不得写入人工审核真值。
- Studio 的 AI 初标不得直接覆盖 `review.json`。
- `proposed` 术语默认不得进入正式 StructureBinder catalog。
- `connectors` 必须从 `jigsaw_points.front` 为水平的 jigsaw 派生。
- `front=up/down` 的 jigsaw 不得伪造成水平 connector。
