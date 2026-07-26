# W-T 主链实现指南

本文说明当前国度规划系统的 W / T 主链如何在实现仓库中执行。它面向开发和 review，不重新定义阶段职责或字段契约；产品真值见 `../../10_product/`，数据与接口契约见 `../../20_contracts/`。

## 适用范围

适用于以下入口触发的同一条主链：

- MCP 工具 `realm_run_acceptance`
- `POST /realm/acceptance/run`
- Forge 命令 `/geomantia realm acceptance [planningRadiusBlocks] [cellStepBlocks]`
- Forge GameTest `RealmPlanningGameTests.realmPlanningPriorAcceptance`
- JVM 测试中直接调用 `RealmPlanningService`

也适用于拆阶段调试：

- `realm_w_refresh`
- `realm_t1_prepare`
- `realm_t2_select_coordinate`
- `realm_t3_expand`
- `realm_t4_build_registry`

不适用于 C 阶段城市内部规划、结构池选择、道路生成、jigsaw / prefab 物化或生产级长期地图存储。

## 入口与触发方式

| 入口 | 代码 | 输入来源 | 输出 |
| --- | --- | --- | --- |
| MCP | `country_designer_mcp/src/realm/tools.ts`、`handlers.ts` | MCP tool arguments | 格式化 JSON 文本和 artifact 路径 |
| HTTP | `RealmPlanningHttpController` | JSON body、在线玩家或显式中心点 | JSON 响应、`run/realm_debug/<runId>/` |
| Forge 命令 | `GisPlatformEvents.realmAcceptance` | 命令参数、命令源位置和维度 | 聊天提示、debug 产物 |
| GameTest | `RealmPlanningGameTests.realmPlanningPriorAcceptance` | 真实 `ServerLevel` | GameTest 断言和 debug 产物 |
| JVM 测试 | `RealmPlanningServiceTest` | 合成 GIS refresh / WorldSurveyResult | 临时目录下阶段产物和断言 |

HTTP 入口必须通过 `callOnServerThread` 回到 Minecraft server thread 后，再读取玩家、维度、世界种子和 prior sampler。

## 前置条件

- W 阶段需要 `planningRadiusBlocks` 或兼容字段 `radiusChunks`。
- `cellStepBlocks` 默认 `128`，用于国度规划粗 cell。
- `microSampleStrideBlocks` 和 `localSlopeRadiusBlocks` 用于 W runner 内真实 micro-sampling；分片 W survey 会输出 `world_feature_grid.json` 并在 `WorldPatchMap.cells[]` 内嵌稳健统计。
- `resumePolicy` 默认 `use_cache`，可复用同 run 目录下的 W tile snapshot。
- T1 / T2 / T3 / T4 拆阶段运行时，必须使用同一个 `runId` 找回内存中的 `RealmRun`。
- 真实 acceptance 默认 `qualityMode=strict`；GameTest 可使用 `smoke` 覆盖真实链路。

## 主调用链

端到端 acceptance 当前主链：

```text
MCP realm_run_acceptance
  -> POST /realm/acceptance/run
  -> RealmPlanningHttpController.handleAcceptance
  -> callOnServerThread
  -> runWorldSurvey
  -> WorldSurveyRunner.run
  -> RealmPlanningService.runAcceptance
  -> runW
  -> prepareT1
  -> selectT2
  -> expandT3
  -> buildT4
  -> acceptance_report.json + score_manifest.json
```

拆阶段主链：

```text
realm_w_refresh
  -> runWorldSurvey
  -> RealmPlanningService.runW

realm_t1_prepare
  -> RealmPlanningService.prepareT1

realm_t2_select_coordinate
  -> RealmPlanningService.selectT2

realm_t3_expand
  -> RealmPlanningService.expandT3

realm_t4_build_registry
  -> RealmPlanningService.buildT4
```

## 步骤明细

### 1. 参数归一与服务端上下文

| 字段 | 内容 |
| --- | --- |
| 目标 | 把 MCP / HTTP / 命令输入转换为世界扫描配置和执行上下文。 |
| 输入 | `runId`、`planningRadiusBlocks`、`radiusChunks`、`cellStepBlocks`、`microSampleStrideBlocks`、`localSlopeRadiusBlocks`、`sampleMode`、`resumePolicy`、`playerName`、`dimensionId`、`centerBlockX/Z`。 |
| 输出 | `WorldSurveyRunner.Config`、`ServerLevel`、`MinecraftPriorAtlasSampler`。 |
| 允许读 | Minecraft server、在线玩家、世界边界、维度、玩家位置、请求 JSON。 |
| 允许写 | HTTP/MCP 错误响应、命令提示、调试日志。 |
| 禁止事项 | 入口层不得复制 W / T 业务逻辑，不得在 MCP 层持有 T 阶段状态。 |
| 失败处理 | 参数错误返回 400；未知玩家或维度显式报错；运行异常返回 500。 |
| 测试锚点 | MCP `realm_status`、`realm_run_acceptance`；HTTP `/realm/acceptance/run`。 |

当前实现说明：

- `planningRadiusBlocks` 未传入时，用 `radiusChunks * 16` 兼容旧参数。
- 没有在线玩家且未传中心点时，HTTP 当前回落到 `(0,0)`；真实验收建议显式传中心或指定玩家。
- `RealmPlanningHttpController.runWorldSurvey` 始终创建 `WorldSurveyRunner` 并使用 `MinecraftPriorAtlasSampler`。

### 2. W 分片扫描与缓存

| 字段 | 内容 |
| --- | --- |
| 目标 | 按配置范围枚举 GIS Region tile，逐 tile 扫描或复用缓存。 |
| 输入 | `WorldSurveyRunner.Config`、`AtlasSampler`、`GisSampleConfig.withCellStepBlocks(cellStepBlocks)`。 |
| 输出 | `WorldSurveyResult`、`world_survey_manifest.json`、`world_feature_grid.json`、`tiles/region_<x>_<z>.json`。 |
| 允许读 | tile snapshot、GIS sample/classifier 配置、prior sampler。 |
| 允许写 | run 目录、tile snapshot、tile debug 目录、survey manifest。 |
| 禁止事项 | W runner 不应直接生成 RealmProfile、RealmSeed、Territory 或 CitySeed。 |
| 失败处理 | 单 tile 失败按 `resumePolicy` 决定重扫或记录 failed；最终 `sealed=false` 时抛错。 |
| 测试锚点 | `world_survey_manifest.json.stats`、`WorldSurveyResult.sealed`、恢复扫描缓存命中数。 |

当前实现说明：

- `WorldSurveyRunner.run` 用 `SurveyBounds` 对齐扫描范围，并按 region 坐标生成 `TilePlan`。
- tile 扫描复用 GIS `GisRefreshService.run`，再通过 `AtlasRegionSnapshotIo.write` 写缓存，并写入配置 hash meta。
- `resumePolicy=use_cache` 时优先读 snapshot；损坏缓存或配置 hash 不一致时按策略重扫或失败。
- sealed tile 汇总后，`WorldSurveyRunner` 会用 `microSampleStrideBlocks` 和 `localSlopeRadiusBlocks` 对每个 coarse cell 执行 micro-sampling，写 `heightStats`、`slopeStats`、`waterFrac`、`biomeHist` 和 `microSampleCount`。
- `world_feature_grid.json` 的配置 hash 一致时可直接复用，恢复扫描无需重复 micro-sampling。
- 只有 `failedTileCount=0` 且 tile 数量完整时，`WorldSurveyResult.sealed=true`。

### 3. W 汇总为 WorldPatchMap

| 字段 | 内容 |
| --- | --- |
| 目标 | 把 sealed W survey 转成 T 阶段可消费的世界粗图。 |
| 输入 | `WorldSurveyResult.regions()`、GIS Cell、GIS Patch。 |
| 输出 | `WorldSurveyContext`、`WorldPatchMap`、continent / patch 摘要、W 预览图。 |
| 允许读 | `AtlasRegion`、`AtlasCell`、`LandformPatch`、survey bounds。 |
| 允许写 | `RealmRun.worldCells`、`worldCellsByKey`、`patchSummaries`、`continentSummaries`、W 产物文件。 |
| 禁止事项 | W 汇总不应创建国度、不应提前选择首都、不应生成城市种子。 |
| 失败处理 | 无可分配大陆时抛错；未 ready cell 会被跳过。 |
| 测试锚点 | `world_survey_context.json`、`world_patch_map.json`、`w_manifest.json`、`world_patch_preview.png`。 |

当前实现说明：

- `RealmPlanningService.runW(WorldSurveyResult, worldTheme)` 创建 `RealmRun` 并调用 `buildWorld`。
- `buildWorld` 只收集 `LANDFORM_READY` 且位于扫描范围内的 cell。
- `assignContinents` 对可分配陆地做四邻接 BFS，生成 `continent_<n>`。
- `buildPatchSummaries` 从 cell `patchId` 和 GIS patch 摘要聚合 WorldPatchMap patch。
- 当前 `baseLandform`、`landformTags`、`heightStats`、`slopeStats` 来自 W 粗 cell 与 `WorldFeatureGrid` 聚合；`cliff` 作为 tag 参与 steep / barrier 语义，不再默认作为大面积主地貌。

### 4. T1 国度配置与候选图包

| 字段 | 内容 |
| --- | --- |
| 目标 | 生成或接收国度配置，并为每个国度准备带网格坐标的候选图包。 |
| 输入 | `realmProfiles[]`、`realmCount`、`targetContinentId`、W patch / continent 摘要。 |
| 输出 | `RealmProfile[]`、`RealmCandidateMapPackage[]`、每国候选图、`t1_manifest.json`。 |
| 允许读 | `RealmRun.worldCells`、`patchSummaries`、`continentSummaries`。 |
| 允许写 | `run.profiles`、`run.candidatePackages`、T1 产物文件。 |
| 禁止事项 | T1 不应生成 RealmSeed，不应替 AI 选最终坐标，不应创建城市。 |
| 失败处理 | 目标大陆不存在或没有候选 cell 时抛错。 |
| 测试锚点 | `candidate_map_packages.json`、`realm_profiles.json`、候选图 `candidates/*.png`。 |

当前实现说明：

- `prepareT1` 若收到 `realmProfiles[]` 就解析为 `RealmProfile`；否则按 `realmCount` 生成 debug profile。
- `buildCandidatePackage` 当前把目标大陆内可分配 patch 全部纳入 allowed set。
- `candidateScore` 根据地貌偏好、水距、海岸、山地亲和等选一个 suggested point。
- `exportCandidateMap` 用 world preview 加网格并高亮 allowed patch。

### 5. T2 坐标选择与种子落盘

| 字段 | 内容 |
| --- | --- |
| 目标 | 校验 AI / 自动流程选择的 grid 坐标，并生成可扩张种子。 |
| 输入 | `runId`、`realmId`、`gridX/Z`、`alternates[]`、`selectionReason`、`selectedBy`、`allowSnap`。 |
| 输出 | `RealmCoordinateSelection`、`RealmSeed`、`CapitalCityIntent`、`t2_report.json`。 |
| 允许读 | T1 `CandidatePackage`、`RealmProfile`、`worldCellsByKey`、已占用 seeds。 |
| 允许写 | `run.selections`、`run.seeds`、`run.capitalIntents`、T2 产物文件。 |
| 禁止事项 | 不得静默跨大陆、跨海、跨禁用 patch；不得在 rejected 坐标上继续 T3。 |
| 失败处理 | 非法坐标返回 rejected selection；允许 snap 时只在小半径内找合法 cell。 |
| 测试锚点 | `realm_coordinate_selections.json`、`realm_seeds.json`、`capital_city_intents.json`。 |

当前实现说明：

- `selectT2` 先用 `validateSelection` 校验原坐标。
- `allowSnap=true` 时，`trySnap` 在附近 cell 中寻找合法候选。
- accepted 后生成 `RealmSeed.from(profile, selection, cell)` 和无坐标 `CapitalCityIntent.from(profile, selection)`。
- rejected 会写入 selections 和 T2 report，但不会生成 seed / capital。

### 6. T3 国度扩张

| 字段 | 内容 |
| --- | --- |
| 目标 | 根据所有 accepted RealmSeed 生成国度势力范围。 |
| 输入 | `runId`、`normalizationGroup`、`allowUnclaimedLand`、`qualityMode`、`expansionModel`。 |
| 输出 | `RealmTerritoryMap`、`t3_report.json`、`territory_repair_log.json`、`territory_preview.png`。 |
| 允许读 | `run.profiles`、`run.seeds`、`worldCells`、`scalePlan`、`expansionStyle`。 |
| 允许写 | `run.territory`、T3 产物文件、score 中的 T3 指标。 |
| 禁止事项 | 不得接受 rejected seed；不得跨 run / 维度共享状态；不得在 T3 创建城市实例。 |
| 失败处理 | 缺 seed、无 land cell、无 frontier 时抛错或写 repair / warning。 |
| 测试锚点 | `realm_territory_map.json`、`t3_report.json`、`score_manifest.subScores.T3`。 |

当前实现说明：

- `expandT3` 调用 `buildTerritory`，按 normalizationGroup 过滤参与国度和 land cell。
- `normalizeScales` 仍记录 `scalePlan.targetAreaRatio`，但在 `action_budget` 中作为软目标和评分信号，不直接决定硬面积。
- `expansionModel=quota_frontier` 保留旧多源 frontier / quota / repair / rebalance 逻辑，供 smoke 和对照使用。
- `expansionModel=action_budget` 为 strict 默认：程序从 `scalePlan.priority` 和 `expansionStyle` 派生 `ExpansionBudget` 与 `TerrainCostProfile`。
- action frontier 携带 `cumulativeCost`、`pathLength` 和 parent cell；扩张被行动力、单格成本、屏障、跨海策略和竞争压力共同限制。
- T3 输出 `owned / wild / contested / blocked / unreachable` 状态，`t3_report.json` 记录预算使用率、地形成本分布、停止原因和状态比例。
- action model 下不再用 rebalance 强行吃满全部陆地；后处理只用于旧 quota 对照模型。

### 7. T4 城市种子名册

| 字段 | 内容 |
| --- | --- |
| 目标 | 基于 T3 领土和国度配置生成有限城市种子名册。 |
| 输入 | `run.territory`、`run.profiles`、`run.capitals`、W 地貌事实。 |
| 输出 | `CitySeedRegistry`、`realm_city_candidate_packages.json`、`t4_report.json`、`city_seed_preview.png`。 |
| 允许读 | T3 领土 cell、每国 stats、城市间图距离、国度 profile。 |
| 允许写 | `run.registry`、T4 产物文件、score 中的 T4 指标。 |
| 禁止事项 | 不得生成城市内部边界、道路、功能区、建筑落点或 chunk 加载 opportunistic 城市。 |
| 失败处理 | 缺 T3 territory 时抛错；不满足间距的候选会被跳过。 |
| 测试锚点 | `city_seed_registry.json`、`realm_city_candidate_packages.json`、`score_manifest.subScores.T4`。 |

当前实现说明：

- `buildRegistry` 每国保留首都，并按条件尝试港口、矿业镇、边境堡等城市种子。
- `bestCityCandidate` 在本国领土内按角色 scorer 选候选。
- `citySpacingOk` 和 `nearestCityDistance` 用本国图距离和规模半径约束城市间距。
- `realm_city_candidate_packages.json` 记录每国候选图包、已选城市和 chunk pregen 规则说明。

### 8. 验收报告与评分

| 字段 | 内容 |
| --- | --- |
| 目标 | 汇总 W / T1 / T2 / T3 / T4 是否完成，并把结果质量写成可阻断报告。 |
| 输入 | `RealmRun` 当前所有阶段状态和产物路径。 |
| 输出 | `acceptance_report.json`、`score_manifest.json`、HTTP/MCP response。 |
| 允许读 | `run.artifacts`、`run.registry`、`run.territory`、W/T3/T4 stats。 |
| 允许写 | 验收报告、score manifest、response 中的 `passed`。 |
| 禁止事项 | 不得只因链路跑通就忽略 hardBlocks；不应把 smoke 结果当 strict 质量通过。 |
| 失败处理 | 缺 CitySeedRegistry、缺首都或 hard block 会使 `passed=false`。 |
| 测试锚点 | `acceptance_report.json.passed`、`score_manifest.hardBlocks`、MCP `realm_run_acceptance` 返回。 |

当前实现说明：

- `buildT4` 会调用 `exportScoreManifest`。
- `acceptanceReport` 用结构完成状态和 `scoreManifest.passed` 共同决定最终 `passed`。
- W 子分当前会因 `cliffRatio`、`singletonPatchRatio` 和 micro-sampling 缺口降分。
- T3 子分检查连通性、detached area、自然边界贴合，并在 action model 下检查 `budgetCoherenceScore`、`terrainIdentityScore`、`wildlandScore`、`contestedReasonabilityScore` 和 `overExpansionPenalty`。
- T4 子分检查首都数量、seed 数、同格冲突和 spacing violation。

## 状态推进

端到端 acceptance 阶段状态：

```text
W survey sealed
  -> runW completed
  -> T1 candidate packages completed
  -> T2 accepted seeds completed
  -> T3 territory completed
  -> T4 CitySeedRegistry completed
  -> score manifest completed
  -> acceptance report completed
```

`RealmRun` 当前是内存态对象，按 `runId` 存在于 `RealmPlanningService.RUNS`。debug JSON 是验收产物和复查依据，不是长期生产存储。

## 读写边界

| 模块 | 允许写 | 不应写 |
| --- | --- | --- |
| MCP / HTTP / Forge 入口 | 参数校验、响应、错误消息 | W/T 算法状态、业务对象内部字段 |
| `WorldSurveyRunner` | tile cache、survey manifest、`WorldSurveyResult` | RealmProfile、RealmSeed、Territory、CitySeed |
| W 汇总 | WorldSurveyContext、WorldPatchMap、预览图 | 国度坐标、国境、城市 |
| T1 | RealmProfile、CandidatePackage、候选图 | RealmSeed、Territory、CitySeed |
| T2 | Selection、RealmSeed、CapitalCityIntent | 国境、最终首都坐标、城市名册 |
| T3 | RealmTerritoryMap、repair log、territory preview | 城市内部结构、C 阶段对象 |
| T4 | CitySeedRegistry、城市候选包、city seed preview | 城市实例、道路、功能区、建筑点 |
| Score / acceptance | score_manifest、acceptance_report | 反向修改 W/T 主数据 |

## 失败处理

- 参数错误应在入口层返回 400 或命令失败消息。
- W tile 失败必须进入 `world_survey_manifest.json`，sealed 失败不得进入正式 T。
- T1 无候选、T2 坐标非法、T3 缺 seed、T4 缺 territory 都应结构化失败。
- strict 模式下 `score_manifest.hardBlocks[]` 不为空时，端到端 `passed=false`。
- GameTest 可使用 smoke 模式验证真实 server 链路，但不能替代 strict 真实游玩验收。

## 调试与产物

| 阶段 | 产物 |
| --- | --- |
| W survey | `world_survey_manifest.json`、`tiles/region_<x>_<z>.json` |
| W | `world_survey_context.json`、`world_patch_map.json`、`world_patch_preview.png`、`grid_overlay_preview.png`、`w_manifest.json` |
| T1 | `realm_profiles.json`、`candidate_map_packages.json`、`candidates/*_candidate_map.png`、`t1_manifest.json` |
| T2 | `realm_coordinate_selections.json`、`realm_seeds.json`、`capital_city_intents.json`、`t2_report.json` |
| T3 | `realm_territory_map.json`、`territory_preview.png`、`t3_report.json`、`territory_repair_log.json` |
| T4 | `city_seed_registry.json`、`city_seed_preview.png`、`t4_report.json`、`realm_city_candidate_packages.json` |
| 验收 | `score_manifest.json`、`acceptance_report.json` |

## 测试锚点

- `./gradlew.bat test`
- `./gradlew.bat runGameTestServer`
- `country_designer_mcp` 下 `npm run build`
- MCP `realm_run_acceptance`
- MCP `realm_w_refresh` + `realm_t1_prepare` + `realm_t2_select_coordinate` + `realm_t3_expand` + `realm_t4_build_registry`
- 真实 client integrated server 验收产物

## 常见改动路径

| 想改什么 | 优先改哪里 | 必须同步检查 |
| --- | --- | --- |
| W 扫描范围 / 缓存 | `WorldSurveyRunner`、`RealmPlanningHttpController.runWorldSurvey` | MCP 接口、真实验收计划、缓存 manifest。 |
| W 粗图字段 | `RealmPlanningService.buildWorld`、`WorldCell.asJson` | 数据契约、score manifest、preview。 |
| T1 候选策略 | `buildCandidatePackage`、`candidateScore` | 候选图包契约、T2 校验、候选图。 |
| T2 坐标校验 | `validateSelection`、`trySnap` | MCP 错误返回、T2 report、非法坐标测试。 |
| T3 扩张算法 | `buildTerritory`、`buildFrontierTerritory`、`buildActionBudgetTerritory`、`frontierMoveCost`、`actionEdgeCost`、repair / rebalance 方法 | T3 数据契约、score manifest、真实验收预览。 |
| T4 城市种子 | `buildRegistry`、`bestCityCandidate`、`citySpacingOk` | CitySeedRegistry 契约、城市候选包、T4 report。 |
| 评分阻断 | `scoreManifest`、`wQualityScore`、`t3QualityScore`、`t4QualityScore` | 真实游玩验收计划、测试入口、GameTest smoke/strict 边界。 |
