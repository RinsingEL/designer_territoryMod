# GIS 主链 Review 清单

本文用于人工 review GIS 主链 PR。它不是测试入口替代品，而是帮助 reviewer 判断代码有没有越界、状态有没有错写、调试逻辑有没有混入主链。

Review 前建议同时打开：

- `../flows/半径刷新实现指南.md`
- `../../20_contracts/数据契约/AtlasCell.md`
- `../../20_contracts/数据契约/RefreshJob.md`
- `../../20_contracts/数据契约/LandformPatch.md`
- `../../40_tests/测试入口.md`

## 总体检查

- 本次改动属于哪个阶段：入口、规划、采样、指标、分类、Patch、预览、测试、MCP/HTTP。
- 是否同步更新了受影响的 `10_product/`、`20_contracts/`、`30_code_guide/` 或 `40_tests/`。
- 是否新增了状态、字段、接口参数或返回字段，却没有更新契约。
- 是否把调试逻辑、临时代码或 fallback 写进默认主链。
- 是否绕过 `GisRefreshService` 复制了一条独立业务流程。
- 是否能用自动测试、MCP/HTTP 结果或 debug 产物证明改动。

## 入口层

适用代码：

- `GisPlatformEvents`
- `GeomantiaHttpServer`
- `GisHttpController`
- `country_designer_mcp/src/gis/*`

检查点：

- 输入是否按契约校验，例如 `radiusChunks` 范围、`sampleMode` 枚举、中心点成对出现。
- HTTP 入口是否回到 server thread 后再读取玩家、维度和执行刷新。
- MCP handler 是否只做参数整理和 HTTP 转发，不持有 GIS 业务状态。
- 命令、HTTP、MCP 是否都调用同一条 `GisRefreshService` 主链。
- 错误是否能在命令失败消息、HTTP 400/500 或 MCP `isError` 中看见。
- 临时客户端辅助是否有明确 TEMP 标记、启用条件和移除条件。

常见风险：

- 在 HTTP controller 中复制采样、指标或分类逻辑。
- 默认吞掉未知 `sampleMode`，导致调用方以为跑了 observed/verify。
- 无玩家时偷偷用 `(0,0)` 做中心，产生误导性结果。

## RefreshJob 与 Region

适用代码：

- `GisRefreshService.refresh`
- `RefreshJob`
- `AtlasRegionStore`
- `AtlasRegion`

检查点：

- jobId、center、radius、dependencyMargin、cellStep、sampleMode 是否来自契约字段。
- `completed` 是否只表示本次半径刷新完成，不暗示跨 Region 缝合完成。
- `dirtyRegions` 是否记录本次实际影响的 Region。
- RegionStore 是否仍是内存组织，不被描述为生产级持久层。
- 修改 Region 状态时是否符合 `EMPTY -> SAMPLED -> METRICS_PARTIAL -> READY`。

常见风险：

- 过早把 Region 标记为 ready。
- 把轻量 JSON snapshot 当成正式缓存。
- 跨 Region 行为没有实现，却在返回值或文档里暗示已经缝合。

## 半径规划

适用代码：

- `RadiusRefreshPlanner`
- `GisSampleConfig`

检查点：

- `radiusChunks` 到 cell 半径的换算是否使用 `cellStepBlocks`。
- `dependencyMarginCells` 是否只扩展采样范围，不改变消费者稳定区语义。
- planned cells 排序是否稳定，避免测试和 preview 随机抖动。
- stable 与 dependency margin 是否能正确标记 edgeDirty。
- Planner 是否保持纯规划，不写 Cell 数据。

常见风险：

- 使用 chunk 坐标和 block 坐标时混淆单位。
- 把圆形距离、方形 ring、Region 边界的含义写混。
- 边界依赖不足时直接失败，而不是标记 edgeDirty。

## 采样层

适用代码：

- `AtlasSampler`
- `MinecraftPriorAtlasSampler`
- `SyntheticAtlasSampler`
- `SampleMode`

检查点：

- prior 是否只调用生成器接口，不主动生成 chunk。
- sample 写入是否只覆盖基础字段和 `SAMPLED` flag。
- `observedIfLoaded` 或 `verifySurface` 若新增实现，是否明确小范围和触发条件。
- sampleSource 是否真实反映数据来源，不能所有模式都假装 verified。
- 合成 sampler 是否只用于测试，不进入真实世界默认路径。

常见风险：

- 为了拿真实表面大范围加载或生成 chunk。
- 在 sampler 内直接写指标、分类或 patch。
- `SampleMode` 契约更新后 MCP/HTTP、测试用例没有同步。

## 指标层

适用代码：

- `AtlasMetricsComputer`
- `GisSampleConfig`

检查点：

- 未 `SAMPLED` 的 Cell 是否跳过。
- 小邻域和大邻域缺失时是否标记 `EDGE_DIRTY`。
- `METRICS_READY_SMALL` 和 `METRICS_READY_LARGE` 是否只在对应指标写入后设置。
- waterDistance 是否对未采样区域保持不可用或边界标记，不伪造稳定值。
- 指标计算是否不写 landform、patch 或消费者评分。

常见风险：

- 只算了一部分指标却设置 large ready。
- 为避免 unknown 大面积出现而放宽状态约束。
- 把 debug 默认值当成真实指标。

## 分类层

适用代码：

- `LandformClassifier`
- `GisClassifierConfig`
- `LandformType`

检查点：

- 只有 `SAMPLED`、small metrics ready、large metrics ready 的 Cell 才分类。
- 分类顺序是否符合方案：water/shore 优先，极端坡度，再 TPI，再 plain/slope。
- `UNKNOWN` 是否保留为真实不确定状态，不被强行压成 plain。
- GIS 是否仍不输出通用 buildability。
- 阈值变化是否同步配置表、测试样例和 preview 验收。

常见风险：

- 为了视觉好看把 unknown 全部归类为某个地貌。
- 在分类层做消费者偏好判断。
- 改阈值后只看单张图，不跑合成测试。

## Patch 合并

适用代码：

- `PatchMerger`
- `LandformPatch`
- `PatchFlag`

检查点：

- 当前 v1 是否仍按四邻接、同类型合并；若改变邻接或近似合并，是否同步文档。
- `PATCH_READY` 是否只给参与 patch 的 Cell。
- Patch 摘要字段是否来自成员 Cell，而不是 bbox 或默认值硬填。
- PatchEnvelope 是否只作为成员 Cell 派生出的外接范围，不反向决定成员 Cell。
- `patchId`、PatchShape、`memberCells` 或 `cellPatchIndex` 是否能从 Cell 精确追溯所属 Patch。
- `fragment`、`edgeDirty`、`crossRegionCandidate` 是否按真实条件设置。
- 未实现成员 Cell 持久化、真实轮廓、跨 Region 缝合时，不应在接口中暗示已支持。

常见风险：

- Patch 只看 bbox 导致摘要和成员不一致。
- 用 PatchEnvelope 作为最终命中结果，而不是先返回 candidate 再用 PatchShape 精查。
- 小碎片吸收改变语义，却没有测试和契约说明。
- patch preview 视觉优化被误写成主数据结构变更。

## Preview、Progress 与 Snapshot

适用代码：

- `ProgressExporter`
- `PreviewExporter`
- `AtlasRegionSnapshotIo`
- `AtlasJson`

检查点：

- progress 是否在关键状态变更后写出。
- preview 图层是否和 `PreviewManifest` 一致。
- preview/export 是否不反向修改主数据。
- `patch.png` 是否使用 Cell/PatchShape 表达真实成员形状，而不是用 PatchEnvelope 画形状。
- snapshot 是否写入 `snapshotPurpose` 和 `productionPersistence=false`。
- 快照读写字段是否和 AtlasCell/AtlasRegion/LandformPatch 契约保持一致。

常见风险：

- 图层文件存在但 manifest 没登记。
- debug JSON 被消费者当主数据读。
- 为了测试复现加入的字段没有明确非生产语义。

## HTTP/MCP 返回

适用代码：

- `GisHttpController.refreshResponse`
- `country_designer_mcp/src/gis/handlers.ts`
- `GIS调试MCP接口.md`

检查点：

- 返回字段是否和接口契约一致。
- `ok` 的语义是否清楚：refresh 为 `status == completed`，test_run 为 `passed`。
- `runDirectory`、artifacts 是否能定位实际产物。
- 失败时是否给出可读 error，而不是空响应。
- MCP timeout 是否覆盖真实 refresh 耗时。

常见风险：

- 改 Java HTTP 返回但忘了 MCP handler 或契约。
- 把本地调试接口当 G8 消费者查询接口使用。
- 在 MCP 层吞掉 HTTP 错误，导致验收误判。

## 测试与验收

最低检查：

- `./gradlew.bat test`
- `country_designer_mcp` 下 `npm run build`

涉及 Forge/runtime 行为时：

- `./gradlew.bat runGameTestServer`
- `/geomantia gis test_run mixed`
- MCP `gis_test_run {"caseId":"mixed"}`

涉及真实世界 prior 采样时：

- 启动真实 client/server。
- MCP 或 HTTP 调 `gis_status`。
- MCP 或 HTTP 调 `gis_refresh {"radiusChunks":8,"sampleMode":"prior"}`。
- 检查 `progress_manifest.json`、`preview_manifest.json`、`landform.png`、`patch.png`。

涉及 preview 表达时：

- 必须人工打开对应图层。
- 说明图层是证据还是真值。
- 如果视觉怪但数据合理，要指出是 preview 层、分类层还是 patch 合并层的问题。

## 必须暂停请用户判断

出现以下情况不要直接实现到底：

- 想把 GIS 输出通用 buildability。
- 想把 verifySurface 变成大范围默认刷新。
- 想引入生产级持久层或改变 `atlasVersion`。
- 想改变 Patch 语义，例如近似地貌合并、碎片吸收、跨 Region 缝合。
- 想改变主流程阶段顺序。
- 自动测试通过但 preview 或真实世界结果明显不符合预期审美/设计。
