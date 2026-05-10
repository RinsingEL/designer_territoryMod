# TerraSense StructureCurationExport 草案

## 定位

`StructureCurationExport` 是 TerraSense Studio 审核后的结构策展导出结果。它用于生成当前 StructureBinder 可消费的 `C3_5_StructureCatalog.preprocessed.json`，并兼容下一代 `StructureProfile`。

TerraSense Studio 标记阶段使用动态术语表；StructureBinder 消费阶段只接收冻结后的静态枚举和静态画像。

## 单结构审核对象

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `structure_id` | string | 结构 id |
| `profile_type` | string | `single` 或 `jigsaw_system` |
| `independent_semantic_unit` | boolean | 是否能独立表达结构含义 |
| `source` | object | namespace、path、mod hint、扫描时间 |
| `scan_bundle` | object | `data.json`、截图、AI 初标路径 |
| `hard_facts` | object | 尺寸、footprint、palette、jigsaw、connector、pool |
| `curation` | object | 人工审核后的功能、风格、用途、位置倾向 |
| `vocabulary_refs` | array | 本结构引用的术语表 canonical term、版本和审核状态 |
| `review` | object | 审核状态、审核人、备注、更新时间 |
| `export_targets` | object | 是否进入 C3.5 catalog、StructureProfile、优秀范例库 |

## 类型口径

| `profile_type` | 说明 |
| --- | --- |
| `single` | 可作为独立语义单元使用的结构 |
| `jigsaw_system` | 需要 start + templates / pool 组合后才形成完整语义的结构系统 |

判断依据是“能否独立表达语义”，不是是否存在 jigsaw 方块。

带 jigsaw connector 的完整建筑可以是 `single`，同时设置：

```json
{
  "profile_type": "single",
  "independent_semantic_unit": true,
  "hard_facts": {
    "has_jigsaw_connectors": true
  }
}
```

不能独立使用的屋顶、走廊、墙段、房间片段等模板，应作为 `jigsaw_system` 的子模板处理。

## `curation`

| 字段 | 说明 |
| --- | --- |
| `function_affinity` | 功能权重 |
| `style_affinity` | 风格权重 |
| `placement_affinity` | 位置倾向权重 |
| `usage_affinity` | 主建筑、次级建筑、装饰、地标、新手村核心等用途倾向 |
| `template_role` | start、child、middle、end、connector、decor、roof、wall、room、corridor 等角色 |
| `system_ref` | 所属 jigsaw system 或 pool |
| `quality_tags` | excellent、usable、needs_fix、reject |
| `recommended_contexts` | 适合的城市、功能区、国度文化或新手村场景 |
| `avoid_contexts` | 不适合的场景 |
| `pairing_hints` | 适合搭配的结构或功能 |
| `evidence` | 标注证据 |

## `vocabulary_refs`

TerraSense 的标记字段必须引用动态术语表，而不是任意散落字符串。

```json
{
  "vocabulary_refs": [
    {
      "vocab_type": "function",
      "term_id": "commercial.market",
      "label": "市场",
      "status": "approved",
      "version": 3,
      "source": "manual_review"
    }
  ]
}
```

术语状态：

| 状态 | 说明 |
| --- | --- |
| `approved` | 已审核，可进入 StructureBinder 静态枚举 |
| `proposed` | 标记阶段临时新增，等待人工审核 |
| `deprecated` | 已废弃，不应继续新增引用 |
| `merged` | 已合并到其他 canonical term |

如果 AI 或人工标记时找不到相似术语，Studio 可以先创建 `proposed` 术语并允许当前结构引用它。但导出给 StructureBinder 的正式 catalog 默认只允许 `approved` 术语。

## `review`

| 字段 | 说明 |
| --- | --- |
| `review_state` | pending、approved、rejected、needs_review |
| `reviewer` | 审核人 |
| `manual_override` | 是否人工覆盖 AI 初标 |
| `manual_notes` | 人工备注 |
| `updated_at` | 更新时间 |

## 导出约束

- `review_state != approved` 的结构默认不得进入主 catalog。
- `quality_tags` 包含 `reject` 的结构不得进入城市生成候选。
- `manual_override=true` 时，导出结果应优先采用人工字段。
- `function_affinity` 应映射到当前 `function_candidates`，同时保留下一代权重字段。
- `function_affinity`、`style_affinity`、`placement_affinity`、`usage_affinity`、`template_role`、`quality_tags` 必须来自术语表 canonical term。
- `proposed` 术语不得进入默认的 StructureBinder 静态枚举；若调试阶段需要导出，必须显式标记为非正式 catalog。
- `hard_facts` 中的 footprint、jigsaw、connector、rotation、pool 不得由 AI 编造。
- `tag_source.manual_override` 和 `tag_source.scanner` 必须正确写入，以便 StructureBinder 严格过滤。

## 静态导出产物

StructureBinder 侧消费的产物必须是冻结快照：

| 产物 | 说明 |
| --- | --- |
| `C3_5_FunctionEnumTable.json` | 当前兼容层的功能枚举，只包含 approved function 术语 |
| `C3_5_StructureCatalog.preprocessed.json` | 当前兼容层结构 catalog，字段值已归一为静态 canonical term |
| `StructureProfile.jsonl` | 下一代画像，可带 `vocabulary_snapshot_id` 追踪术语表版本 |
| `StructureVocabulary.snapshot.json` | 可选调试产物，用于说明本次导出采用的冻结术语表 |
