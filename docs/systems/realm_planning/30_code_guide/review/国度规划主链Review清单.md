# 国度规划主链 Review 清单

本文用于人工 review 国度规划系统 W / T 主链改动。它不是测试入口替代品，而是帮助 reviewer 判断代码有没有越界、阶段状态有没有错写、调试逻辑有没有混入正式主链。

Review 前建议同时打开：

- `../flows/W-T主链实现指南.md`
- `../../10_product/功能设计/W-T阶段主流程设计.md`
- `../../20_contracts/数据契约/W-T阶段数据契约.md`
- `../../20_contracts/接口契约/W-T阶段MCP接口.md`
- `../../40_tests/测试入口.md`
- `../../40_tests/真实游玩验收计划.md`

## 总体检查

- 本次改动属于哪个阶段：W survey、W 汇总、T1、T2、T3、T4、score、HTTP/MCP/Forge、测试。
- 是否同步更新了受影响的 `10_product/`、`20_contracts/`、`30_code_guide/` 或 `40_tests/`。
- 是否新增字段、接口参数、返回字段或产物文件，却没有更新契约。
- 是否绕过 `RealmPlanningService` 复制了一条独立业务流程。
- 是否把临时 debug 逻辑、自动选点、smoke 放进 strict 正式验收语义。
- 是否能用自动测试、MCP/HTTP 响应、debug 产物或真实预览图证明改动。

## 入口层

适用代码：

- `RealmPlanningHttpController`
- `GisPlatformEvents`
- `country_designer_mcp/src/realm/*`
- `DevAutoLoadClient`

检查点：

- HTTP 是否回到 server thread 后再读取玩家、维度、世界种子和 prior sampler。
- MCP handler 是否只做参数整理和 HTTP 转发，不持有业务状态。
- `planningRadiusBlocks`、`radiusChunks`、`cellStepBlocks`、`resumePolicy`、`qualityMode` 是否按契约校验。
- 无玩家时使用 `(0,0)` 的行为是否只用于调试，并在真实验收中显式指定中心或玩家。
- Forge 命令和自动客户端 smoke 是否有明确开发启用条件。
- 错误是否能在 HTTP 400/500、MCP `isError` 或命令失败消息中看见。

常见风险：

- 在 controller 中复制 T1/T2/T3/T4 逻辑。
- MCP schema 新增参数但 Java HTTP 未读取，或 Java 已读取但 MCP 未暴露。
- 自动客户端辅助默认启用，污染正常游玩。

## W 分片扫描

适用代码：

- `WorldSurveyRunner`
- `WorldSurveyResult`
- `AtlasRegionSnapshotIo`
- `GisRefreshService`

检查点：

- scan bounds 是否由 `planningRadiusBlocks` 和 `cellStepBlocks` 可追溯计算。
- tile cache 是否只在同 run 目录下复用，`resumePolicy` 语义是否清楚。
- 读缓存失败时是否按策略 rescan 或记录 failed。
- `sealed` 是否只在所有 tile 成功时为 true。
- `world_survey_manifest.json` 是否记录 tile 数、缓存命中、失败数、耗时、数据量和配置。
- `microSampleStrideBlocks`、`localSlopeRadiusBlocks`、`microSampleCount`、`world_feature_grid.json` 和 `microSamplingImplemented=true` 是否能互相印证；不得只写字段不采样。
- tile cache 和 feature grid cache 是否校验 `configHash`，不同 seed / step / stride / 范围不得误复用。

常见风险：

- 不同 seed、维度、step 或 bounds 误复用旧 tile。
- W 未 sealed 就进入 T1 / T2 / T3。
- 长 W 扫描未考虑 MCP timeout 或异步 job 需求。

## W 汇总与 WorldPatchMap

适用代码：

- `RealmPlanningService.runW`
- `buildWorld`
- `assignContinents`
- `buildPatchSummaries`
- `buildContinentSummaries`
- W preview/export 方法

检查点：

- 只消费 `LANDFORM_READY` 且在 survey bounds 内的 cell。
- grid 坐标、block 坐标、`gridOriginBlock`、`cellStepBlocks` 是否一致。
- continent id 是否按可分配陆地四邻接生成，不把水体和 unknown 混入陆地大陆。
- patch 摘要是否能从 cell `patchId` 和 GIS patch 追溯。
- W 预览图是否只是调试图，不反向改变 WorldPatchMap。
- cliff / steep 当前过量的问题是否进入 `score_manifest` warning 或 W 子分。

常见风险：

- 把 GIS Region 内 patch id 当成跨 tile 全局 clean patch id。
- preview 看起来像主数据，但 manifest / JSON 无法解释。
- W 地貌粗分类质量差，却只看 T3/T4 通过就放行。

## T1 候选图包

适用代码：

- `RealmPlanningService.prepareT1`
- `RealmProfile.fromJson`
- `buildCandidatePackage`
- `exportCandidateMap`

检查点：

- AI 输入的 `RealmProfile` 是否结构化校验，而不是直接信任文本。
- 默认 debug profile 是否只用于未传 profile 的调试场景。
- 候选图包是否包含 grid legend、originBlock、cellStep、允许 patch、候选图路径。
- allowed patch 是否限制在目标大陆 / 大区内。
- T1 是否没有生成 RealmSeed、国境或城市种子。

常见风险：

- 候选图缺坐标说明，导致 T2 无法可信选点。
- T1 重新引入旧“AI 填底层参数、选簇、选方向”流程。
- 默认 profile 混入正式国度设定。

## T2 坐标选择

适用代码：

- `RealmPlanningService.selectT2`
- `validateSelection`
- `trySnap`
- `RealmSelection`
- `RealmSeed`
- `CapitalCitySeed`

检查点：

- 坐标是否合法必须按 continent、patch、水体、禁用规则和占用冲突校验。
- rejected selection 是否写明 `errors[]`，且不会生成 seed / capital。
- snap 是否小范围、可追溯，不跨大陆、跨海或跨禁用 patch。
- accepted seed 是否继承 `scalePlan` 和 `expansionStyle`。
- 首都 seed 是否一定存在且稳定 ID。

常见风险：

- 非法坐标被静默修正到远处。
- 多国度选择同一 cell 但没有冲突记录。
- T2 直接创建除首都外的城市。

## T3 国度扩张

适用代码：

- `RealmPlanningService.expandT3`
- `buildTerritory`
- `normalizeScales`
- `quotas`
- `buildFrontierTerritory`
- `frontierMoveCost`
- `repairDetachedComponents`
- `rebalanceAreaQuotas`
- `RealmTerritoryMap`

检查点：

- 所有参与国度必须已有 accepted `RealmSeed`。
- land cell 必须来自同一 `normalizationGroup` / 目标大陆。
- 扩张必须是 per-run 状态，不共享 legacy 静态全局状态。
- frontier 扩张只能从已有边界向邻接 cell 推进，不能退回全图静态抢格子。
- repair log 是否记录未归属挂接、飞地修复、quota rebalance 等后处理。
- `t3_report.json` 是否记录面积、目标面积、连通块、detached ratio、邻国、主要地貌。
- strict 下 hard block 是否能阻断明显拓扑坏结果。

当前已知设计风险：

- `strict` T3 默认应使用 `action_budget`；`quota_frontier` 只作为 smoke / 对照模型。
- action model 下 `scalePlan.targetAreaRatio` 是软目标和评分信号，不应通过 rebalance 强行拉回 quota。
- `wild / contested / blocked / unreachable` 必须进入 territory cell 状态、T3 report 和 score manifest。
- Review 应重点看行动力预算、地形消耗、停止原因、荒野比例和国度特色是否进入报告。

常见风险：

- 为了面积接近 quota 破坏连通性。
- rebalance 把边界修复变成强行填满世界。
- T3 通过后误以为 W 地貌质量和扩张模型都已经合理。

## T4 城市种子名册

适用代码：

- `RealmPlanningService.buildT4`
- `buildRegistry`
- `bestCityCandidate`
- `citySpacingOk`
- `nearestCityDistance`
- `cityCandidatePackagesJson`
- `CitySeedRegistry`

检查点：

- T4 必须在 T3 territory 存在后运行。
- 首都必须保留，其他城市按角色候选和约束生成。
- 城市种子 ID 是否稳定唯一。
- 城市间是否按规模半径和本国图距离约束。
- `realm_city_candidate_packages.json` 是否逐国说明候选、已选 seed 和 chunk pregen 规则。
- CitySeed 是否不包含道路、功能区边界、结构落点或 jigsaw 参数。

常见风险：

- 又退回 chunk 加载时 opportunistic 创建有限城市。
- 城市全部靠近世界中心或玩家首加载区域。
- T4 直接进入 C 阶段细规划。

## Score、报告与预览

适用代码：

- `acceptanceReport`
- `scoreManifest`
- `wQualityScore`
- `t3QualityScore`
- `t4QualityScore`
- preview export 方法

检查点：

- `score_manifest.json` 是否在 T4 后写出，并进入 artifacts。
- `acceptance_report.passed` 是否同时看结构完成和 score manifest。
- strict 与 smoke 的差异是否明确；GameTest smoke 不等于正式质量通过。
- W / T3 / T4 的 warning 和 hardBlocks 是否可解释。
- previewSet 中的图是否真实存在，且图例 / 坐标能帮助人工复查。

常见风险：

- `passed=true` 只表示链路跑通，忽略 hardBlocks。
- 总分达标但 warning 说明核心能力未实现，却在文档中宣称完成。
- preview 文件存在但内容和 JSON 字段无法对上。

## 测试与验收

最低检查：

- `./gradlew.bat test`
- `country_designer_mcp` 下 `npm run build`

涉及真实 Forge / ServerLevel 行为时：

- `./gradlew.bat runGameTestServer`

涉及真实世界 prior 采样和 MCP 控制时：

- 启动真实 client/server。
- MCP 或 HTTP 调 `realm_status`。
- MCP 调 `realm_run_acceptance`，明确 `planningRadiusBlocks`、`cellStepBlocks`、`qualityMode`。
- 检查 `world_survey_manifest.json`、`t3_report.json`、`t4_report.json`、`score_manifest.json`。
- 人工打开 `world_patch_preview.png`、`territory_preview.png`、`city_seed_preview.png`。

涉及 T3 扩张模型时：

- 不只看 `passed=true`。
- 必须看每国面积、连通性、repair log、是否吃满全部陆地、是否存在合理荒野。
- 如果行动力模型尚未实现，应在验收说明中明确当前只是 quota 过渡模型。

## 必须暂停请用户判断

出现以下情况不要直接实现到底：

- 想把 `scalePlan.targetAreaRatio` 继续作为最终面积硬配额。
- 想把 `allowUnclaimedLand=false` 固定为真实开放世界默认。
- 想让 T4 或 chunk pregen 动态新增有限城市名额。
- 想让 AI 填底层 terrain cost、阈值或 Dijkstra 裸参数。
- 想让 W 未 sealed 或有 failed tile 时进入正式 T。
- 自动测试通过但真实预览图明显不符合世界规划直觉。
