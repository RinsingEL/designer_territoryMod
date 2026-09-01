# City MCP 接口契约

## 定位

本文件只维护当前公开工具、阶段职责和破坏性调用边界。字段级 JSON Schema 的实现真值是实现仓库 `country_designer_mcp/src/realm/tools.ts`，HTTP 路由真值是 `RealmPlanningHttpController`；修改工具字段时必须同步更新本文件和对应 Node/Java 测试。

所有 City MCP 工具调用本地 `/realm/city/<snake_case_action>` HTTP 入口。常规阶段调用至少使用 `runId`、`citySeedId` 定位任务；需要世界上下文的入口可再使用 `dimensionId` 或 `playerName`。

## 正式主链工具

| 工具 | HTTP | 职责 |
| --- | --- | --- |
| `city_plan_d2` | `/realm/city/plan_d2` | 建立 CitySiteContext 与模板检索上下文。 |
| `city_design_queue_refresh` | `/realm/city/design_queue/refresh` | 从当前 CitySeedRegistry 建立或合并持久化城市设计队列。 |
| `city_design_queue_status` | `/realm/city/design_queue/status` | 返回队列状态、唯一当前城市和下一动作。 |
| `city_plan_d3` | `/realm/city/plan_d3` | 生成局部地貌 review、patch 和 LandUse terrain field；site review 完成后自动打开 `city_d4` Patch Explorer，并返回 Top Patch 复核下一动作。 |
| `city_review_d3_site` | `/realm/city/review_d3_site` | 冻结需要人工复核的 D3 选址结论。 |
| `city_prepare_d4_blueprint_context` | `/realm/city/prepare_d4_blueprint_context` | 在当前 D3 Top Patch 复核完成后输出 Context v0.10、snapshot v0.10、Reference Catalog v0.9 与 5 次程序编译失败预算。 |
| `city_submit_d4_blueprint` | `/realm/city/submit_d4_blueprint` | 提交完整 CityBlueprint v0.12 revision；校验拒绝不增加 `failureCount`，编译失败且仍有预算时可用同一 `contextId` 修正重提。接受后默认加入 D4 后自动编译队列，可用 `autoAdvanceAfterD4=false` 关闭。 |
| `city_post_d4_auto_compile_status` | `/realm/city/post_d4_auto_compile_status` | 查询 D4 后队列持久化状态；`waiting_for_generation` 正常完成，`needs_agent` 返回 `failureCount/retryAllowed/nextAction` 和允许 Agent 使用的恢复 artifacts。 |
| `city_post_d4_auto_compile_retry` | `/realm/city/post_d4_auto_compile_retry` | 仅在 Blueprint 不变且程序或环境原因已修复时重跑后半段；需要修改设计时改用 `city_submit_d4_blueprint` 提交 revision。 |
| `city_compile_d4_blueprint` | `/realm/city/compile_d4_blueprint` | 编译当前 accepted Blueprint revision；真实编译/终审失败原子增加 `failureCount`。无论最终 quality 成败，只要 D4 已形成结构化 anchor 结果，就必须渲染整城总览与每个功能区局部图；失败尝试位置及原因必须进入局部图。是否可验收仍必须读取 `compilationAcceptance` 和最终 D4 quality。 |
| `city_plan_d5` | `/realm/city/plan_d5` | 生成结构 reservation、mask 和可选 wall reservation 预案。 |
| `city_plan_d6` | `/realm/city/plan_d6` | 从当前世界 NBT 锁定模板 identity、geometry 和 owner chunks。 |
| `city_plan_city_dressing` | `/realm/city/plan_city_dressing` | 规划稀疏 DecorationProgram。 |
| `city_plan_decoration_anchor_candidates` | `/realm/city/plan_decoration_anchor_candidates` | 为 required 单点装饰计算完整 footprint/clearance 候选。 |
| `city_plan_land_use` | `/realm/city/plan_land_use` | 显式规划 LandUse；正式 workflow 在 D6 后由 Blueprint outdoorPlan 驱动。 |
| `city_execute_d5` | `/realm/city/execute_d5` | 激活结构、LandUse 与 Decoration 生成期计划。 |
| `city_execute_d7` | `/realm/city/execute_d7` | 查询并汇总落地 ledger，执行允许的后处理。 |
| `city_query_worldgen_observations` | `/realm/city/query_worldgen_observations` | 只读查询 post-features / chunk-save 方块观测。 |
| `city_plan_city_walls` | `/realm/city/plan_city_walls` | 按所选 wallVersion 生成城墙计划。 |
| `city_execute_city_walls` | `/realm/city/execute_city_walls` | 经确认后放置墙段和塔楼。 |
| `city_run_workflow` | `/realm/city/run_workflow` | 串联已冻结步骤；可复用既有 artifact，并在需要确认或等待 worldgen 时停止；响应 artifacts 返回统一 `testRunManifest` / `testRunPackage`。 |

### D4 后自动编译队列契约

- `city_submit_d4_blueprint` 成功且 `autoAdvanceAfterD4` 未显式设为 `false` 时，将该城市加入单线程持久化队列；提交响应的 `postD4AutoCompile` 返回初始状态。
- 自动队列调用 `city_run_workflow` 时不得提交已删除的 `d4CandidateMode`；正式工作流始终且只走 CityBlueprint。显式提交旧字段必须在开始 D3 前返回 `D4_WORKFLOW_MODE_REMOVED`。
- 队列只处理已接受 D4 后的程序阶段：编译 D4、D5、D6、Blueprint outdoor/LandUse 规划与 D5 激活，终点固定为 `waiting_for_generation`，不主动执行 D7 区块生成。
- 状态写入 `<runId>/automation/post_d4/<citySeedId>.json`。服务重启后恢复 `queued` / `running` 项；失败写 `needs_agent`、原因码与错误信息，不继续吞错。
- `needs_agent` 若只需在 Blueprint 不变的前提下重跑已修复的程序/环境阶段，使用 `city_post_d4_auto_compile_retry`；若 `retryAllowed=true` 且需要修改设计或改选已审查 Patch，则使用同一 `contextId` 调用 `city_submit_d4_blueprint` 提交新的完整 revision。

### D4 Blueprint 失败预算契约

- 当前 Context 的 `maximumFailureCount` 固定为 `5`。提交参数、schema、枚举、引用、关系或 stale 校验拒绝不增加 `failureCount`，也不得覆盖当前 accepted Blueprint。
- 只有程序化 D4 编译或终审明确失败才原子增加 `failureCount`。第 1～4 次失败返回 `retryAllowed=true`、`nextAction=city_submit_d4_blueprint`；第 5 次返回 `retryAllowed=false` 并停止请求人工处理。
- failure ledger 与 active revision 发布只允许短原子写入；不得用“同一时间只允许一个 Blueprint 编译”的长锁替代失败预算。
- Agent Loop 只允许使用工具响应和工具明确返回的 artifacts 恢复；不得读取服务端源码、项目文档或未返回的原始 run 文件。

### 城市设计调度队列契约

- T4 CitySeedRegistry 覆盖全部国度首都后自动建立 `<runId>/automation/city_design_queue.json`。单国 T4 finalize 尚未覆盖其他国度时返回 `cityDesignQueueStatus=awaiting_remaining_realms`，不得提前启动 City。
- 默认 `orderingMode=global_radial`：按 `anchorBlock` 到世界 `0,0` 的距离升序，稳定 tie-break 为 `realmId + citySeedId`。`realm_grouped` 先按各国首都到 `0,0` 的距离排序国度，再按城市到本国首都的距离排序。
- 整合包默认值写在 `config/geomantia/city_design_queue.json`，schema 为 `geomantia_city_design_queue_config.v0.1`，字段为 `enabled` 和 `orderingMode`。T4/refresh 请求可为单个 run 覆盖 ordering mode，不改全局配置。
- 队列一次只暴露一个 `currentCity`。正式 D2、D3、D3 review、D4 Context 和 D4 submit 请求若不是当前城市，返回 `CITY_DESIGN_QUEUE_OUT_OF_ORDER`；没有 Registry 的旧调试 run 不受该门禁影响。
- 当前状态为 `waiting_for_agent` 时 Agent 从 `currentCity` 开始完成 D3/D4；D4 接受后转 `post_d4_running`。后半段进入 `waiting_for_generation` 后，上层队列自动把下一项变为当前城市。
- 后半段失败时当前城市保持 `needs_agent`，后续城市全部保持 `pending`，不得跳过失败城市继续推进。全部城市进入 `waiting_for_generation` 后队列状态为 `completed`。

### city_plan_d3 固定采样契约

- `cellStepBlocks` 是兼容字段，只允许省略或传 `16`；其他值返回 `CITY_D3_CELL_STEP_FIXED`。D3 不用该字段覆盖 W 来源 step。
- `preferGeneratorNativeTerrain` 可选，默认 `true`。RTF 可用时走二维 Heightmap fast path；未安装或运行时不可用时整次 D3 回退 Minecraft prior，响应和 review package 的 `terrainProvider` 必须说明实际来源。
- 响应 `artifacts` 至少包含 `landformReviewMap`、`biomeOverview`、`cityLandformReviewPackage`、`landUseTerrainField`。`biomeOverview` 使用 D3 16-block cell 的最终 Minecraft biome id。
- D3 采样、Patch 分析、PNG 和 artifact 写入必须在 API worker 执行，不得把完整 handler 包入服务器线程。响应返回 `executionMode=api_worker`、`serverThreadBlocked=false` 与 `durationMs`；workflow 同样只把确实需要世界读写的后续步骤送回服务器线程。

### city_execute_d7 在线队列契约

- `executeStructurePlacement=true` 不得同步遍历城市 owner 或调用阻塞式 `level.getChunk(...)`。缺失 LandUse owner 进入服务器 tick 队列，以异步 FULL chunk future 逐块请求。
- 每个服务器 tick 全局最多启动一次 chunk 请求或执行一个 owner 事务；队列进行中返回 `status=waiting_for_worldgen`、`reasonCode=CITY_LAND_USE_D7_BACKFILL_IN_PROGRESS`，调用方以同一 `runId + citySeedId` 轮询。
- `landUseOwnerCompletion` 使用 `city_land_use_owner_completion.v0.2`，必须返回 `status`、`maxOwnerActionsPerTick=1`、`synchronousChunkLoads=false`、可选 `currentOwner`，并保留全部 identity、计数、missing 与 failure 字段。
- 单 owner 仍使用完整预检、快照、写入、rollback 与 ledger 事务；队列只改变调度，不得把 owner 事务拆成无回滚的小写入。

## 目录与诊断工具

| 工具 | HTTP | 是否写状态 |
| --- | --- | --- |
| `city_query_structure_catalog` | `/realm/city/query_structure_catalog` | 否；查询固定模板目录。 |
| `city_query_template_metadata` | `/realm/city/query_template_metadata` | 否；从当前世界模板管理器读取 hash、rawSize 等事实。 |
| `city_query_decoration_catalog` | `/realm/city/query_decoration_catalog` | 否；查询 Decoration content/style。 |
| `city_upgrade_default_decoration_catalog` | `/realm/city/upgrade_default_decoration_catalog` | 是；仅在 `confirmConfigMutation=true` 时升级受管理默认目录并备份旧配置。 |
| `city_probe_decoration_terrain` | `/realm/city/probe_decoration_terrain` | 否；只采样已加载 FULL chunk，不写 artifact 或世界。 |

## 当前关键 schema

| Artifact | 当前 schema |
| --- | --- |
| Blueprint Context | `city_blueprint_context` |
| Blueprint | `city_blueprint` |
| Catalog Snapshot | `city_blueprint_catalog_snapshot` |
| Reference Catalog | `city_blueprint_reference_catalog` |
| Validation / Submission | `city_blueprint_validation_report` / `city_blueprint_submission_trace` |
| Failure Budget | `city_blueprint_failure_budget` |
| Compile Trace / Group Extent | `city_generation_compile_trace` / `group_extent_map` |
| Structure Anchor Plan / Map | `city_structure_anchor_plan` / `city_structure_anchor_map` |
| Template Catalog | `city_template_catalog` |
| LandUse Intent / Area / Terrain Field | `v0.3` / `v0.1` / `v0.1` |
| SurfacePrintPlan | `city_land_use_surface_print_plan.v0.7` |
| Decoration content / program / active / ledger | `v0.4` 系列；只读旧版兼容以代码 parser 为准 |
| Worldgen observation | `city_worldgen_block_observation.v0.1` |

同一链路中的 `cityId`、D3 hash、catalog hash、Blueprint hash、D6 hash、plan hash 和 schema 必须完整匹配。当前 parser 明确拒绝的旧 artifact 不迁移、不猜字段、不静默降级。

`city_compile_d4_blueprint.artifacts` 在 anchor 终审成功或失败时均返回 `structureAnchorPreview`，并以 `groupStructurePreviews.<groupId>` 返回每个功能区局部 PNG。终审失败不得在 renderer 前提前返回；局部图必须同时绘制已提交结构、功能区实际 claims、该区景观和 `selections[].attempts[].failedAttemptPositions[]` 中的失败位置与 reasonCode。

## 修改世界与配置

- `city_execute_d5` 必须显式传 `confirmWorldMutation=true`；否则拒绝激活。
- `city_execute_city_walls` 必须显式传 `confirmWorldMutation=true`；否则拒绝放置。
- `city_run_workflow` 未确认时返回 `waiting_for_confirmation`，不得代替用户确认。
- `city_upgrade_default_decoration_catalog` 必须显式传 `confirmConfigMutation=true`。
- plan、query、probe、preview 类接口不得修改世界。

`city_execute_d5` 只接收当前结构、LandUse 与 Decoration 激活参数。城区显式 `CONNECTION`、区内道路和桥均由 City 自有计划拥有；旧沙砾道路、外部道路 provider 和 D7 延迟道路后处理均已删除。

`city_execute_d5` 写出的 `active_planned_structure_registry.json` 必须包含 `activationProvenance`：D5 plan hash、D6 plan hash、LandUse completion hash 与 Decoration completion hash。`city_run_workflow skipExisting=true` 只有在这些身份全部与当前输入一致时才能跳过 D5；任一来源变化或旧 artifact 缺 provenance 都必须重新执行激活。

## 运行与日志

Node handler 为每次调用记录统一 `callId`、started/completed、UTC 时间、单调耗时和 timeout 分类。外层超时不等于 Java 端没有继续执行，复查时必须用 call log 与 artifact identity 对齐，不能仅凭客户端等待时间判断阶段状态。

City artifact 不再按阶段散落在 `<runId>/` 根目录。新测试统一写入 `<runId>/city_test_runs/<citySeedId>/steps/`，包根 `test_run_manifest.json` 保存 `latestRequest`、`status`、`nextAction` 和追加式 `attempts[]`。MCP call log 仍只解释调用边界，运行包清单才是恢复一次 City 测试的入口。

`city_run_workflow` 可通过 `skipExisting` 复用身份匹配的冻结 artifact。它必须在以下边界停止并返回明确状态：D3 需要复核、Blueprint 尚未提交、世界修改未确认、目标 chunk 尚未 worldgen、hash/schema 漂移或下游 artifact 不完整。
