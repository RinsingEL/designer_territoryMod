# City MCP 接口契约

## 定位

本文件只维护当前公开工具、阶段职责和破坏性调用边界。字段级 JSON Schema 的实现真值是实现仓库 `country_designer_mcp/src/realm/tools.ts`，HTTP 路由真值是 `RealmPlanningHttpController`；修改工具字段时必须同步更新本文件和对应 Node/Java 测试。

Provider 自动规划使用宿主范围锁定的决策适配器，其工具定义由 ProviderPlanningToolCatalog 同时供内嵌模型和 Hermes 的认证桥读取；Hermes 不再误用原始分阶段 MCP schema。完整 validationReport（含负结论）不属于桥接传输故障，仍保留 ok=false 和原校验反馈；同错三次停止由宿主控制。已有同 Context、非空设计会话续跑不重复注入整包目录和图片。

公开 City MCP 工具调用本地 `/realm/city/<snake_case_action>` HTTP 入口。常规阶段调用至少使用 `runId`、`citySeedId` 定位任务；需要世界上下文的入口可再使用 `dimensionId` 或 `playerName`。

Provider 的 D3 选址复核初始资料使用地貌类型计数、首批非排名摘要和实际地图，不装入整包网格。宿主专用只读工具 `city_inspect_d3_patches` 直接查询本轮已锁定城市的完整 D3 快照，无独立 HTTP 路由，不接受 runId、cityId 或文件路径；支持 `landformType`、精确 `landformPatchId`、零起始 `page` 和 `pageSize`（默认 8，范围 1–16）。每页保留完整地貌块记录及 memberCells，返回 totalMatched/hasMore/nextPage；按需查证，不要求遍历全部页面。原始 D3 产物不变。

程序自动执行步骤请求 `X-Geomantia-Host-Result` 回执，不生成模型展示或嵌入图片，失败证据仍完整返回。模型展示和 Hermes 初始输入不再使用 90000/262144 字符门槛，也不截断作者资料；实际 HTTP 请求体、响应传输及图片安全限制独立保留，不代表模型上下文容量。

## 正式主链工具

冒险家地图右上角提供“重试当前城市”，位于 Agent 过程左侧。客户端仅在具名当前城市 `blocked_by_program` 且未加载/提交时启用；通过冒险家地图网络协议 v5 的 C2S 请求发送 runId/cityId（各最多256字符），由服务端验证单人存档主人或2级管理员权限、当前服务器、队列当前城市/状态/nextAction，再调用与 HTTP `city_post_d4_auto_compile_retry` 相同的入口。过期页面不得重试旧城市，已运行或等待AI修订不得作为程序重试；不清空方案、失败预算或世界扫描。S2C 回执显示提交、状态变化、权限不足、服务未就绪或失败并刷新地图；客户端10秒无回执只刷新和提示，不自动重发。重试功能依赖当前服务器已启动的规划服务，不从客户端固定连接 localhost。

编译候选穷尽返回具体必需建筑的修订证据并按既有预算进入 needs_agent；不得跳过必需项后继续填充。终审失败摘要优先报告最终 qualityReport/compilationAcceptance.hardBlocks，不能使用无关的最后一次填充失败覆盖最终原因。仅有明确缺失设计关系的终审证据可进入设计修订；搜索上限、资源缺口、未知安全错误或编译成功后出现必需内容缺失仍归宿主处理，保留方案和预算，不把通用终审码一律归设计。

| 工具 | HTTP | 职责 |
| --- | --- | --- |
| `city_plan_d2` | `/realm/city/plan_d2` | 建立 CitySiteContext 与模板检索上下文。 |
| `city_design_queue_refresh` | `/realm/city/design_queue/refresh` | 从当前 CitySeedRegistry 建立或合并持久化城市设计队列。 |
| `city_design_queue_status` | `/realm/city/design_queue/status` | 返回队列状态、唯一当前城市和下一动作。 |
| `city_plan_d3` | `/realm/city/plan_d3` | 生成局部地貌 review、patch 和 LandUse terrain field；site review 完成后自动打开 `city_d4` Patch Explorer，并返回 Top Patch 复核下一动作。 |
| `city_review_d3_site` | `/realm/city/review_d3_site` | 冻结需要人工复核的 D3 选址结论。 |
| `city_prepare_d4_blueprint_context` | `/realm/city/prepare_d4_blueprint_context` | 在当前 D3 Top Patch 复核完成后输出 Context v0.10、snapshot v0.10、Reference Catalog v0.9 与 5 次程序编译失败预算。 |
| `city_submit_d4_blueprint` | `/realm/city/submit_d4_blueprint` | 提交完整设计或哈希绑定的 replace-only blueprintPatch；支持省略宿主身份字段和显式 RELATIVE_WEIGHTS，最终仍严格验证完整 canonical v0.12。校验拒绝不计预算；接受后默认自动编译，可用 autoAdvanceAfterD4=false 关闭。 |
| `city_post_d4_auto_compile_status` | `/realm/city/post_d4_auto_compile_status` | 查询 D4 后队列持久化状态；`waiting_for_generation` 正常完成，`needs_agent` 返回 `failureCount/retryAllowed/nextAction` 和允许 Agent 使用的恢复 artifacts。 |
| `city_post_d4_auto_compile_retry` | `/realm/city/post_d4_auto_compile_retry` | 仅在 Blueprint 不变且程序或环境原因已修复时重跑后半段；需要修改设计时改用 `city_submit_d4_blueprint` 提交 revision。 |
| `city_compile_d4_blueprint` | `/realm/city/compile_d4_blueprint` | 编译当前 accepted Blueprint；仅设计归属失败计入预算，程序/明确 frontage 元数据缺口阻塞并保留方案。有结构化 anchor 结果就渲染总览及功能区图，失败证据保留；验收依据 compilationAcceptance 和最终质量报告。 |
| `city_plan_d5` | `/realm/city/plan_d5` | 生成结构 reservation、mask 和可选 wall reservation 预案。 |
| `city_plan_d6` | `/realm/city/plan_d6` | 从当前世界 NBT 锁定模板 identity、geometry 和 owner chunks。 |
| `city_plan_land_use` | `/realm/city/plan_land_use` | 显式规划 LandUse；正式 workflow 在 D6 后由 Blueprint outdoorPlan 驱动。 |
| `city_execute_d5` | `/realm/city/execute_d5` | 激活结构 mask、locked structure registry 与 LandUse 生成期计划。 |
| `city_execute_d7` | `/realm/city/execute_d7` | 查询并汇总落地 ledger，执行允许的后处理。 |
| `city_query_worldgen_observations` | `/realm/city/query_worldgen_observations` | 只读查询 post-features / chunk-save 方块观测。 |
| `city_plan_city_walls` | `/realm/city/plan_city_walls` | 按所选 wallVersion 生成城墙计划。 |
| `city_execute_city_walls` | `/realm/city/execute_city_walls` | 经确认后放置墙段和塔楼。 |
| `city_run_workflow` | `/realm/city/run_workflow` | 串联已冻结步骤；可复用既有 artifact，并在需要确认或等待 worldgen 时停止；响应 artifacts 返回统一 `testRunManifest` / `testRunPackage`。 |

### 作者资料与设计上下文

- 正式 `city_prepare_d4_blueprint_context` 只接收 `runId/citySeedId`。`terrasenseProfileSource/templateCatalogSource/blueprintReferenceCatalog` 由宿主绑定，调用方传入时返回 `PLANNING_SOURCE_HOST_OWNED`，不得由模型拼装或替换目录。
- 来源使用作者显式配置的 `geomantia.providerPlanningSourceDir`；未配置时只接受安装目录中唯一的完整 bundle，多份时返回 `PROVIDER_MANAGED_CITY_SOURCES_AMBIGUOUS`，不按修改时间挑选。
- 可引用结构必须有作者 `approved` 的非空 `functionTerms/styleTerms`，模板目录仍要求 `buildingSemantic/style`。缺标返回 `PLANNING_AUTHOR_ANNOTATION_REQUIRED` 并指出结构引用；真实模板 NBT/hash/rawSize 预检仍保留。
- Context 增加 `designGuide`，依据实际 Reference Catalog 说明设计流程、建筑阵列、功能区组合、道路目的与修订边界。它是能力说明，不生成固定蓝图、不代替作者标注。
- MCP 和内置 Provider 共用模型视图与真正的图片内容；详见 [W/T 通用返回约定](../../../realm_planning/20_contracts/接口契约/W-T阶段MCP接口.md)。完整 Context/Snapshot 的身份与 hash 不因展示压缩改变。

### D4 后自动编译队列契约

- `city_submit_d4_blueprint` 成功且 `autoAdvanceAfterD4` 未显式设为 `false` 时，将该城市加入单线程持久化队列；提交响应的 `postD4AutoCompile` 返回初始状态。
- 自动队列调用 `city_run_workflow` 时不得提交已删除的 `d4CandidateMode`；正式工作流始终且只走 CityBlueprint。显式提交旧字段必须在开始 D3 前返回 `D4_WORKFLOW_MODE_REMOVED`。
- 队列只处理已接受 D4 后的程序阶段：编译 D4、D5、D6、Blueprint outdoor/LandUse 规划与 D5 激活，终点固定为 `waiting_for_generation`，不主动执行 D7 区块生成。
- 状态写入 `<runId>/automation/post_d4/<citySeedId>.json`。重启恢复 queued/running；可修订设计冲突写 needs_agent + city_submit_d4_blueprint；程序失败写 blocked_by_program，保留 Blueprint 与错误，不唤醒模型也不自动重复失败任务。预算耗尽保留 stop_for_human_review。
- blocked_by_program 在仅修复程序/环境、冻结资料不变时使用 city_post_d4_auto_compile_retry。作者目录实际改变时，允许当前城市通过 city_prepare_d4_blueprint_context 正式重建 Context：仍须作者审批、NBT 预检和有效 D3 review，拒绝在途/完成任务、其他城市及预算耗尽；资料未变返回 CITY_BLUEPRINT_AUTHOR_SOURCES_UNCHANGED。成功后旧 Context、snapshot、accepted Blueprint/trace/报告及预算保存到 steps/blueprint/context_history，旧失败任务保存到 automation/post_d4/history；旧 accepted 文件不删除但不再匹配新 Context。原 failureCount/failures 原样迁移，不清零；后半段任务改为 needs_agent + city_submit_d4_blueprint，重启不再被旧阻塞覆盖，也不直接启动编译。GLM 收到旧方案作为参考，必须按新 Context 完整提交；不能使用旧哈希补丁。普通设计修订仍用同一 contextId 完整输入或哈希绑定局部补丁，上层队列不跳过当前城。

### D4 Blueprint 失败预算契约

- 当前 Context 的 `maximumFailureCount` 固定为 `5`。提交参数、schema、枚举、引用、关系或 stale 校验拒绝不增加 `failureCount`，也不得覆盖当前 accepted Blueprint。
- 可操作的设计冲突才原子增加 failureCount；明确的 REQUIRED_STRUCTURE_SEARCH_LIMIT_EXHAUSTED、LANDSCAPE_SEARCH_LIMIT_EXHAUSTED、INTERNAL_SAFETY_LIMIT_REACHED 及 COMPILED_ANCHOR_FINALIZATION_FAILED 保留当前计数，failureOwner=program，nextAction=city_post_d4_auto_compile_retry。第 1～4 次设计失败允许修订，第五次停止请求人工处理。
- failure ledger 与 active revision 发布只允许短原子写入；不得用“同一时间只允许一个 Blueprint 编译”的长锁替代失败预算。
- Agent Loop 只允许使用工具响应和工具明确返回的 artifacts 恢复；不得读取服务端源码、项目文档或未返回的原始 run 文件。

### 城市设计调度队列契约

- 每次单国 T4 finalize 即建立/合并 `<runId>/automation/city_design_queue.json`，无需等待其他国度首都。自动调度先处理当前已登记城市，完成后再开启下一国 T4。
- 默认 `orderingMode=realm_grouped`：队列内先按各国首都到 `0,0` 的距离分组，再按城市到世界 `0,0` 的距离排序，稳定 tie-break 为 `realmId + citySeedId`。`global_radial` 保留为显式兼容配置。自动 T4 finalize 固定使用 `realm_grouped`；Provider 在国度尚未建立城市前使用 RealmSeed 核心距原点决定下一国。
- 整合包默认值写在 `config/geomantia/city_design_queue.json`，schema 为 `geomantia_city_design_queue_config.v0.1`，字段为 `enabled` 和 `orderingMode`。T4/refresh 请求可为单个 run 覆盖 ordering mode，不改全局配置。
- 队列一次只暴露一个 `currentCity`。正式 D2、D3、D3 review、D4 Context 和 D4 submit 请求若不是当前城市，返回 `CITY_DESIGN_QUEUE_OUT_OF_ORDER`；没有 Registry 的旧调试 run 不受该门禁影响。
- 当前状态为 `waiting_for_agent` 时 Agent 从 `currentCity` 开始完成 D3/D4；D4 接受后转 `post_d4_running`。后半段进入 `waiting_for_generation` 后，上层队列自动把下一项变为当前城市。
- 后半段失败时当前城市保持 `needs_agent`，后续城市全部保持 `pending`，不得跳过失败城市继续推进。当前已登记城市全部进入 `waiting_for_generation` 后队列状态为 `completed`；仍有国度未完成 T4 时不代表全世界规划完成，宿主继续安排下一国。

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
| Worldgen observation | `city_worldgen_block_observation.v0.1` |

同一链路中的 `cityId`、D3 hash、catalog hash、Blueprint hash、D6 hash、plan hash 和 schema 必须完整匹配。当前 parser 明确拒绝的旧 artifact 不迁移、不猜字段、不静默降级。

`city_compile_d4_blueprint.artifacts` 在 anchor 终审成功或失败时均返回 `structureAnchorPreview`，并以 `groupStructurePreviews.<groupId>` 返回每个功能区局部 PNG。终审失败不得在 renderer 前提前返回；局部图必须同时绘制已提交结构、功能区实际 claims、该区景观和 `selections[].attempts[].failedAttemptPositions[]` 中的失败位置与 reasonCode。

## 修改世界与配置

- `city_execute_d5` 必须显式传 `confirmWorldMutation=true`；否则拒绝激活。
- `city_execute_city_walls` 必须显式传 `confirmWorldMutation=true`；否则拒绝放置。
- `city_run_workflow` 未确认时返回 `waiting_for_confirmation`，不得代替用户确认。
- plan、query、probe、preview 类接口不得修改世界。



## 运行与日志

Node handler 为每次调用记录统一 `callId`、started/completed、UTC 时间、单调耗时和 timeout 分类。外层超时不等于 Java 端没有继续执行，复查时必须用 call log 与 artifact identity 对齐，不能仅凭客户端等待时间判断阶段状态。

City artifact 不再按阶段散落在 `<runId>/` 根目录。新测试统一写入 `<runId>/city_test_runs/<citySeedId>/steps/`，包根 `test_run_manifest.json` 保存 `latestRequest`、`status`、`nextAction` 和追加式 `attempts[]`。MCP call log 仍只解释调用边界，运行包清单才是恢复一次 City 测试的入口。

`city_run_workflow` 可通过 `skipExisting` 复用身份匹配的冻结 artifact。它必须在以下边界停止并返回明确状态：D3 需要复核、Blueprint 尚未提交、世界修改未确认、目标 chunk 尚未 worldgen、hash/schema 漂移或下游 artifact 不完整。
