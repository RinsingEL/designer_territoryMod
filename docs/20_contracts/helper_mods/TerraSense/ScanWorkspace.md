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
        angle_01.png
        angle_02.png
  exports/
    C3_5_FunctionEnumTable.json
    C3_5_StructureCatalog.preprocessed.json
    StructureProfile.jsonl
```

`safe_structure_id` 使用结构 id 的文件安全形态，例如把 `minecraft:village/plains/houses/plains_small_house_1` 转为 `minecraft__village_plains_houses_plains_small_house_1`。

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
| `sample_type` | string | `single/template/single_template` |
| `state` | string | `pending/scanned/ai_done/reviewed/failed` |
| `paths` | object | `data/scan_config/screenshots/ai_suggestion/review` 相对路径 |
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
| `sample_type` | string | `single/template/single_template` 三类固定样本之一 |
| `camera` | object | 截图角度、距离、pitch、yaw |
| `placement` | object | 摄影场 origin、清场边距、底板设置 |
| `screenshot_files` | array | 本结构截图文件列表 |
| `scan_options` | object | 是否跳过 AI、是否强制重扫等 |

## `ai_suggestion.json`

AI 初标只作为建议，不是最终真值。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `mode` | string | `mock` 或 `vision_api` |
| `model` | string | 使用的模型或 mock 名称 |
| `created_at` | string | 生成时间 |
| `inputs` | object | 使用的截图、硬事实和词表版本 |
| `suggested_curation` | object | 功能、风格、用途、位置、质量建议 |
| `confidence` | object | 分项置信度 |
| `evidence` | array | 视觉或硬事实依据 |
| `warnings` | array | 不确定项或需要人工关注的问题 |

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
