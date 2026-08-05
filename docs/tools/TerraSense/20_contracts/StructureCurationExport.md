# TerraSense StructureCurationExport 草案

## 定位

`StructureCurationExport` 是 TerraSense Studio 审核后的结构策展导出结果。它用于生成当前 StructureBinder / City 结构目录查询、envelope profiling 与 D4 候选链可消费的 `StructureProfile.jsonl` 和显式 debug catalog。

TerraSense Studio 可以保留丰富的策展资料；StructureBinder 消费的正式结构画像只冻结三组白名单 term：`functionTerms`、`planningRoleTerms`、`styleTerms`，以及 City 固定 placement topology 枚举数组 `terrainModes`。`styleTerms` 只给 AI / 人工理解结构风格，不进入 City 程序评分、候选合法性、placement 或 worldgen；`terrainModes` 不属于动态词表。泛化 placement、usage、template role 和 quality 不再进入 City 结构语义目录，也不再通过总集 `semanticTerms` 重复导出。

## 单结构审核对象

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `structure_id` | string | 结构 id |
| `profile_type` | string | `single` 或 `jigsaw_system` |
| `independent_semantic_unit` | boolean | 是否能独立表达结构含义 |
| `source` | object | namespace、path、mod hint、扫描时间 |
| `scan_bundle` | object | `data.json`、截图、AI 初标路径 |
| `hard_facts` | object | 尺寸、footprint、palette、jigsaw、connector、pool |
| `curation` | object | 人工审核后的功能、规划角色、City placement topology 和风格 |
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

对于 `profile_type=single` 且仍含 connector 的原始 NBT，TerraSense 的四视图与人工审核可作为“能够独栋”的证据，但不能替代 City 导入闸门。StructureBinder 通用清洗器仍需单独冻结源 SHA-256、Jigsaw 数量和 `standaloneConfirmed=true`，再逐个按 `final_state` 收尾；扫描得到的 connector 方向只产生待确认道路入口候选，不自动成为 City `roadEntrances[]`。`jigsaw_system` 子模板不得进入该独栋清洗路径。

## `curation`

| 字段 | 说明 |
| --- | --- |
| `function` | 功能语义 term 列表，例如 `function.村庄`、`function.灯塔`。 |
| `planning_role` | 规划角色 term 列表，例如 `planning_role.key`、`planning_role.fill`；连接不是结构永久角色。 |
| `terrain_modes` | City 固定 placement topology 枚举数组，值域为 `SURFACE`、`EMBEDDED`、`FLOATING`，可多选并按 OR 解释。 |
| `style` | 结构风格 term 列表；只作为 AI-facing 语义，不形成程序规则。 |
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
- `review_state=approved` 是正式目录唯一准入门禁；拒绝结构直接使用 `review_state=rejected`，不再叠加 quality term 门禁。
- `manual_override=true` 时，导出结果应优先采用人工字段。
- `function`、`planning_role`、`style` 必须来自术语表 canonical term；`function` 至少一项，后两组在尚未完成可信重标记时允许为空。`terrain_modes` 不进术语表，正式画像至少一项，只允许 City 固定枚举值。
- `function` 术语必须保留 TerraSense 原始 term，不得映射为 City `functionType`、`function_candidates` 或 `functionTags`。
- `proposed` 术语不得进入默认的 StructureBinder 正式 catalog；若调试阶段需要导出，必须显式标记为 `catalogMode=debug`。
- `hard_facts` 中的 footprint、jigsaw、connector、rotation、pool 不得由 AI 编造。
- `tag_source.manual_override` 和 `tag_source.scanner` 必须正确写入，以便 StructureBinder 严格过滤。

## 静态导出产物

StructureBinder 侧消费的产物必须是冻结快照：

| 产物 | 说明 |
| --- | --- |
| `StructureProfile.jsonl` | 正式结构画像，一行一个 approved 结构；包含必填 `functionTerms/terrainModes` 和允许为空的 `planningRoleTerms/styleTerms`。 |
| `StructureVocabulary.snapshot.json` | 本次导出采用的冻结术语表快照，只包含正式链路可用的 approved term。 |
| `TerraSenseStructureProfileSource.official.json` | City 结构画像正式输入来源描述，`sourceType=structure_profile_jsonl`。 |
| `debug_structure_profile_catalog.json` | 显式 debug catalog，可包含未审核 / proposed 信息，但必须 `catalogMode=debug`。 |
| `TerraSenseStructureProfileSource.debug.json` | City 结构画像 debug 输入来源描述，`sourceType=debug_catalog`。 |

`TerraSenseStructureProfileSource.official.json` 至少写入：

```json
{
  "schemaVersion": "terrasense_structure_profile_source.v0.1",
  "sourceType": "structure_profile_jsonl",
  "catalogMode": "official",
  "profilePath": "StructureProfile.jsonl",
  "vocabularySnapshotPath": "StructureVocabulary.snapshot.json"
}
```

`vocabularySnapshotPath` 是可选但推荐随正式 source 冻结的相对路径。当前 City 结构画像与 D4-D6 链只读取 profile；`city_query_structure_catalog` 额外使用它把 `label` / `aliases[]` 解析回 canonical `term_id`。未提供时，查询接口只接受 profile 中存在的 canonical termId，绝不按文件名、旧 C3.5 catalog 或 City 映射表猜标签。

TerraSense 新 binder 导出使用严格 `terrasense_structure_profile_source.v0.2`：`sourceType=structure_profile_jsonl`、`catalogMode=binder`、`sampleType=single_template`、`allowDebugUnapproved=false`，并必填 `profilePath`、`vocabularySnapshotPath`、`terrasenseRunId`。StructureBinder 不把其他未知 catalogMode 当作正式目录兼容；v0.2 binder 画像仍只按 `reviewState=approved` 准入。

正式画像最小语义片段：

```json
{
  "structureId": "geomantia:city/example/house_01",
  "sourceProfileRef": "terrasense://example/house_01",
  "reviewState": "approved",
  "functionTerms": ["function.residential"],
  "planningRoleTerms": ["planning_role.fill"],
  "terrainModes": ["SURFACE"],
  "styleTerms": ["style.coastal_wood_stone"]
}
```

结构尺寸、NBT 内容和普通旋转由 Minecraft / City template catalog 链提供，不属于上述结构语义与 topology 字段。正式和 debug 导出不得再写 `semanticTerms`、`placementTerms`、`usageTerms`、`templateRoleTerms`、`qualityTerms`、`terrainTerms`；City 导入器发现这些退役字段必须明确拒绝，不得静默忽略。显式 debug 缺审核状态时 City 归一为 `reviewState=unreviewed`，不得向 AI 暴露空字符串。

`terrainModes` 只声明结构与地表的拓扑关系，不携带坡度、局部起伏或群系阈值，也不需要独立 Terrain Policy。当前 StructureBinder 只实现 `SURFACE`：完整 footprint 覆盖的 D3 格必须存在、已采样且非水；`EMBEDDED/FLOATING` 先作为稳定枚举导出，单独声明时由 City 明确返回不支持。沙漠、沼泽等环境风貌继续使用 `styleTerms` 给 AI 阅读，不转成程序群系门禁。

导入 StructureBinder 本地运行配置时，必须复制 `StructureProfile.jsonl`、词表快照与 source 描述，不得让 City 继续引用客户端或 TerraSense 工程目录。City 请求仍显式携带 source 描述；当前 v0.1 的只读查询与 D4/D6 请求工作目录不同，因此导入 source 的 `profilePath` / `vocabularySnapshotPath` 必须写为 StructureBinder 本地运行配置的绝对路径，不使用跨 endpoint 的相对路径。

旧 `C3_5_FunctionEnumTable.json`、`C3_5_StructureCatalog.preprocessed.json`、`function_candidates` 和 `functionTags` 不再属于当前 City 结构落地主链。

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
