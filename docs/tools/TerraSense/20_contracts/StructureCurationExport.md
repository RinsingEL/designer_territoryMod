# TerraSense StructureCurationExport

## 当前实现

导出器位于 TerraSense 仓库 `studio/scripts/export-city-profiles.mjs`。它是纯文件工具，读取 `ScanWorkspace` 的 `scan_manifest.json`、`vocabulary.json`、每个样本的 `data.json` 与 `review.json`，不启动 Minecraft。

当前导出 schema：

- `terrasense_city_profile_export.v0.2`
- `terrasense_structure_profile_source.v0.2`
- `terrasense_structure_vocabulary_snapshot.v0.2`
- debug catalog：`city_structure_profile_catalog.v0.1`

## 导出模式

| mode | 输入样本 | 主要产物 | 当前用途 |
| --- | --- | --- | --- |
| `official` | `structure_assembly` / `minecraft_place_structure` | `StructureProfile.jsonl`、词表快照、official source | configured structure assembly 的审核导出；不属于当前 City fixed-template active path。 |
| `debug` | 同上，允许未审核信息 | debug catalog、debug source | TerraSense 调试与人工复核。 |
| `both` | 同上 | official + debug | 默认组合导出。 |
| `binder` | `single_template` | `StructureProfile.jsonl`、词表快照、binder source | 面向 StructureBinder 固定模板语义目录。 |

运行示例：

```powershell
node studio/scripts/export-city-profiles.mjs --workspace <workspace> --out <output> --mode binder
```

## binder 准入

当前 TerraSense exporter 对 binder mode 的硬条件是：

- `sample_type=single_template`。
- `review.review_state=approved`。
- 至少一个 `functionTerms`。
- 恰好一个 `planningRoleTerms`。
- 至少一个 `terrainTerms`。
- `styleTerms` 可为空。

binder source 固定声明 `catalogMode=binder`、`sampleType=single_template`、`allowDebugUnapproved=false`，并携带 `terrasenseRunId`、`profilePath` 和 `vocabularySnapshotPath`。

## 当前跨仓库断点

TerraSense 当前 binder exporter 输出 `terrainTerms`，而 StructureBinder 当前 `CityStructureProfileCatalog` 把 `terrainTerms` 视为退役字段，并要求 `terrainModes`（`SURFACE|EMBEDDED|FLOATING`）。两端 schema 版本虽然都写 v0.2，但字段目前不兼容，binder 产物不能宣称已被 City 正式消费。

在实现统一前，文档不得把以下事项写成完成能力：

- binder 导出可直接进入当前 City D4/D6。
- `terrainTerms` 会被自动映射为 `terrainModes`。
- official configured-structure 导出仍为 City 建筑几何真值。
- TerraSense envelope facts 会覆盖固定 NBT rawSize/hash。

修复时必须由两仓库共同选择并冻结一个字段契约，再增加 exporter -> `CityStructureProfileCatalog` 的真实集成测试；禁止在消费端按文件名或旧 placement term 猜值。

## 事实与语义边界

TerraSense 可以导出扫描硬事实、截图来源、功能、规划角色、地形/拓扑标签、风格和审核状态。当前 City fixed-template 几何只认 Minecraft `StructureTemplateManager` 读取的 NBT hash/rawSize，以及 City template catalog 的旋转、镜像、clearance 和入口；TerraSense 语义不能覆盖这些字段。

AI 初标不是正式真值。正式或 binder 导出必须经过人工 `approved`；debug mode 可保留未审核信息，但 source 必须明确为 debug，不能混入正式 catalog。
