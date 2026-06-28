# TerraSense StructureCurationExport 草案

## 定位

`StructureCurationExport` 是 TerraSense Studio 审核后的结构策展导出结果。它用于生成当前 StructureBinder / City D6 可消费的 `StructureProfile.jsonl` 和显式 debug catalog。

TerraSense Studio 标记阶段使用动态术语表；StructureBinder 消费阶段只接收冻结后的 TerraSense 白名单 term 和静态结构画像，不再把语义投影成 City 功能枚举。

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
| `function` | 功能语义 term 列表，例如 `function.村庄`、`function.灯塔`。 |
| `style` | 风格 term 列表。 |
| `placement` | 位置倾向 term 列表。 |
| `usage` | 主建筑、次级建筑、装饰、地标、新手村核心等用途 term。 |
| `template_role` | start、child、middle、end、connector、decor、roof、wall、room、corridor 等角色 |
| `system_ref` | 所属 jigsaw system 或 pool |
| `quality` | excellent、usable、needs_fix、reject 等质量 term |
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
| `approved` | 已审核，可进入 StructureBinder 正式 `StructureProfile.jsonl` |
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
- `quality` / `qualityTerms` 包含 `reject` 或 `quality.reject` 的结构不得进入城市生成候选。
- `manual_override=true` 时，导出结果应优先采用人工字段。
- `function`、`style`、`placement`、`usage`、`template_role`、`quality` 必须来自术语表 canonical term。
- `function` 术语必须保留 TerraSense 原始 term，不得映射为 City `functionType`、`function_candidates` 或 `functionTags`。
- `proposed` 术语不得进入默认的 StructureBinder 正式 catalog；若调试阶段需要导出，必须显式标记为 `catalogMode=debug`。
- `hard_facts` 中的 footprint、jigsaw、connector、rotation、pool 不得由 AI 编造。
- `tag_source.manual_override` 和 `tag_source.scanner` 必须正确写入，以便 StructureBinder 严格过滤。

## 静态导出产物

StructureBinder 侧消费的产物必须是冻结快照：

| 产物 | 说明 |
| --- | --- |
| `StructureProfile.jsonl` | 正式结构画像，一行一个 approved configured structure，包含 `semanticTerms`、`functionTerms`、`styleTerms`、`placementTerms`、`usageTerms`、`templateRoleTerms`、`qualityTerms`。 |
| `StructureVocabulary.snapshot.json` | 本次导出采用的冻结术语表快照，只包含正式链路可用的 approved term。 |
| `TerraSenseStructureProfileSource.official.json` | City D6 正式输入来源描述，`sourceType=structure_profile_jsonl`。 |
| `debug_structure_profile_catalog.json` | 显式 debug catalog，可包含未审核 / proposed 信息，但必须 `catalogMode=debug`。 |
| `TerraSenseStructureProfileSource.debug.json` | City D6 debug 输入来源描述，`sourceType=debug_catalog`。 |

旧 `C3_5_FunctionEnumTable.json`、`C3_5_StructureCatalog.preprocessed.json`、`function_candidates` 和 `functionTags` 不再属于当前 City D6 / D7 主链。

## Structure Envelope Facts

`structure_envelope_facts.json` 属于结构硬事实画像的派生产物，用于 City D4-D6 的防撞、mask 和 preflight，不是新的 City 语义枚举。

生成方：

- 当前由 StructureBinder 的 `city_profile_structure_envelopes` 读取 TerraSense `StructureProfile.jsonl` / debug catalog 后采样生成。
- 后续 TerraSense Studio 可以把同类统计作为结构审核步骤的一部分固化，但仍应保持为硬事实画像。

采样对象：

- 只采顶层 configured structure，即 `/place structure <id>` 可触发的 `worldgen/structure/*.json`。
- 不把 jigsaw 子模板、house/street/decor pool element 当 D4 anchor。

数据用途：

- `localEnvelopeP95`：City D4 collision envelope。
- `localEnvelopeP99`：City D5 vegetation / vanilla structure mask envelope。
- `maxObservedEnvelope`：safety / trace / 越界诊断。
- `profileHash`、`structureConfigHash`、`sourcePackHash`：用于判断事实画像是否仍匹配当前 TerraSense profile 和结构资源。

约束：

- facts 是 bbox / piece count / area / invalid ratio 等硬事实，不引入新的 function / style / placement 语义 term。
- facts 失效时不得在 City 侧偷偷映射或降级为旧 functionTag 逻辑。
- 对约定必须回归大小区间的测试结构，facts 缺失或 hash 不匹配应让 D4 hard fail。
