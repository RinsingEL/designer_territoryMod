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
- 一个 `terrainModes`，由 review 的 `terrain_mode` 生成；缺省为 `SURFACE`。
- 至少一个人工批准的 `styleTerms`；功能、规划角色、风格引用必须存在于已批准词表且类型一致。
- 独立 `entrance_review.state=approved`，绑定当前采集文件摘要；需要接路时至少一个合法边缘朝外出口，无需接路时必须明确 intent 和原因。

binder source 固定声明 `catalogMode=binder`、`sampleType=single_template`、`allowDebugUnapproved=false`，并携带 `terrasenseRunId`、`profilePath` 和 `vocabularySnapshotPath`。

## Binder 放置地形契约

TerraSense binder exporter 输出 `terrainModes`，StructureBinder `CityStructureProfileCatalog` 直接消费该字段。数组当前固定为单元素，值为 `SURFACE|EMBEDDED|FLOATING`；Studio 默认 `SURFACE`，只有人工明确选择时才使用另外两种。旧 `terrainTerms` 不得出现在 binder 产物中。

configured/Jigsaw assembly 仍未进入 City active catalog，TerraSense envelope facts 也不会覆盖固定 NBT rawSize/hash。消费端禁止按文件名或旧 placement term 猜放置地形。

## 事实与语义边界

TerraSense 可以导出扫描硬事实、截图来源、功能、规划角色、地形/拓扑标签、风格和审核状态。当前 City fixed-template 几何只认 Minecraft `StructureTemplateManager` 读取的 NBT hash/rawSize，以及 City template catalog 的旋转、镜像、clearance 和入口；TerraSense 语义不能覆盖这些字段。

### 人工接路口 sidecar v1

binder mode 另写 `StructureEntrances.approved.json`，schema=`terrasense_approved_entrances.v1`。`structures` 每行包含 `structureId/contentHash/size/reviewState/intent/note/captureDigest/roadEntrances`；roadEntrances 使用现有 Binder `entranceId/x/z/direction`。原始采集的 y 保留在 workspace，v1 只接受 y=1 的平面出口，不宣称支持立体道路连接。

托管规划加载阶段按完整 templateRef 精确关联，校验 NBT 内容指纹、尺寸、独立审核、边界朝外方向，再将批准入口合并进冻结上下文；不改写原模板目录，不覆盖 NBT、变体、旋转镜像或 clearance。缺 sidecar、缺某模板审核、身份/指纹/尺寸不匹配均在调用模型前阻断。旧目录入口不能兜底。`no_connection` 必须空列表且有作者说明，不得由程序猜测。

管理包必须在同一目录提供 sidecar，且 `TerraSenseStructureProfileSource.binder.json` 与 `.official.json` 只能存在一个，避免歧义。已有规划上下文不会被就地改写；重新规划时才使用新版审核数据。

### 显式旧素材池兼容

默认 `entrancePolicy=reviewed_required`，仍执行上述严格审核。用户明确保留旧目录测试时，可在 source descriptor 配置 `entrancePolicy=legacy_catalog`，仅在没有 sidecar 且未声明 `entranceCatalogPath` 时使用原 template catalog 的入口。功能/风格审核、NBT 可用性及碰撞验收不放宽。上下文 authoringBrief 标明 `entranceAuthority=legacy_catalog_unreviewed`，不会生成 approved 记录。

已安装或已声明的 sidecar 不允许因损坏、缺失或审核失败退回旧入口。已有 sidecar 时仍优先严格核验。未知 policy 直接报错；正式 TerraSense exporter 不自动输出 legacy policy。

AI 初标不是正式真值。正式或 binder 导出必须经过人工 `approved`；debug mode 可保留未审核信息，但 source 必须明确为 debug，不能混入正式 catalog。
