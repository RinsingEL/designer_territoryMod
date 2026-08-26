# City MCP 接口契约

## 定位

本文件只维护当前公开工具、阶段职责和破坏性调用边界。字段级 JSON Schema 的实现真值是实现仓库 `country_designer_mcp/src/realm/tools.ts`，HTTP 路由真值是 `RealmPlanningHttpController`；修改工具字段时必须同步更新本文件和对应 Node/Java 测试。

所有 City MCP 工具调用本地 `/realm/city/<snake_case_action>` HTTP 入口。常规阶段调用至少使用 `runId`、`citySeedId` 定位任务；需要世界上下文的入口可再使用 `dimensionId` 或 `playerName`。

## 正式主链工具

| 工具 | HTTP | 职责 |
| --- | --- | --- |
| `city_plan_d2` | `/realm/city/plan_d2` | 建立 CitySiteContext 与模板检索上下文。 |
| `city_plan_d3` | `/realm/city/plan_d3` | 生成局部地貌 review、patch 和 LandUse terrain field。 |
| `city_review_d3_site` | `/realm/city/review_d3_site` | 冻结需要人工复核的 D3 选址结论。 |
| `city_prepare_d4_blueprint_context` | `/realm/city/prepare_d4_blueprint_context` | 输出 Context v0.10、snapshot v0.10 和 Reference Catalog v0.9。 |
| `city_submit_d4_blueprint` | `/realm/city/submit_d4_blueprint` | 一次提交完整 CityBlueprint v0.11；支持 Group 关系位置和父阵列编排。 |
| `city_compile_d4_blueprint` | `/realm/city/compile_d4_blueprint` | 编译已接受 Blueprint；不进行第二次 AI 设计。无论最终 quality 成败，只要 D4 已形成结构化 anchor 结果，就必须渲染整城总览与每个功能区局部图；失败尝试位置及原因必须进入局部图。是否可验收仍必须读取 `compilationAcceptance` 和最终 D4 quality。 |
| `city_plan_d4` | `/realm/city/plan_d4` | 生成标准 anchor/group artifact。正式 workflow 使用 Blueprint mode。 |
| `city_plan_d5` | `/realm/city/plan_d5` | 生成结构 reservation、mask 和可选 wall reservation 预案。 |
| `city_plan_d6` | `/realm/city/plan_d6` | 从当前世界 NBT 锁定模板 identity、geometry 和 owner chunks。 |
| `city_plan_city_dressing` | `/realm/city/plan_city_dressing` | 规划稀疏 DecorationProgram。 |
| `city_plan_decoration_anchor_candidates` | `/realm/city/plan_decoration_anchor_candidates` | 为 required 单点装饰计算完整 footprint/clearance 候选。 |
| `city_plan_land_use` | `/realm/city/plan_land_use` | 显式规划 LandUse；正式 workflow 在 D6 后由 Blueprint outdoorPlan 驱动。 |
| `city_execute_d5` | `/realm/city/execute_d5` | 激活结构、LandUse、Decoration 与 RoadWeaver 生成期计划。 |
| `city_execute_d7` | `/realm/city/execute_d7` | 查询并汇总落地 ledger，执行允许的后处理。 |
| `city_query_worldgen_observations` | `/realm/city/query_worldgen_observations` | 只读查询 post-features / chunk-save 方块观测。 |
| `city_plan_city_walls` | `/realm/city/plan_city_walls` | 按所选 wallVersion 生成城墙计划。 |
| `city_execute_city_walls` | `/realm/city/execute_city_walls` | 经确认后放置墙段和塔楼。 |
| `city_run_workflow` | `/realm/city/run_workflow` | 串联已冻结步骤；可复用既有 artifact，并在需要确认或等待 worldgen 时停止；响应 artifacts 返回统一 `testRunManifest` / `testRunPackage`。 |

## 目录与诊断工具

| 工具 | HTTP | 是否写状态 |
| --- | --- | --- |
| `city_query_structure_catalog` | `/realm/city/query_structure_catalog` | 否；查询固定模板目录。 |
| `city_query_template_metadata` | `/realm/city/query_template_metadata` | 否；从当前世界模板管理器读取 hash、rawSize 等事实。 |
| `city_query_decoration_catalog` | `/realm/city/query_decoration_catalog` | 否；查询 Decoration content/style。 |
| `city_upgrade_default_decoration_catalog` | `/realm/city/upgrade_default_decoration_catalog` | 是；仅在 `confirmConfigMutation=true` 时升级受管理默认目录并备份旧配置。 |
| `city_probe_decoration_terrain` | `/realm/city/probe_decoration_terrain` | 否；只采样已加载 FULL chunk，不写 artifact 或世界。 |

## D4 legacy/debug 工具

下列接口仍在代码中，用于显式候选、阵列、loop 和 session 调试，不属于默认 Blueprint workflow：

- 候选：`city_plan_d4_candidates`、`city_select_d4_candidates`。
- 阵列：`city_plan_d4_array_candidates`、`city_create_d4_array_layout_loop`、`city_query_d4_array_expansion_space`、`city_plan_d4_array_expansion_candidates`、`city_select_d4_array_expansion_candidate`、`city_finalize_d4_array_layout_loop`。
- 设计轮次：`city_create_d4_design_loop_state`、`city_read_d4_design_loop_state`、`city_append_d4_design_loop_round`、`city_write_d4_design_loop_state`。
- cluster group：`city_plan_d4_structure_cluster_groups`、`city_select_d4_structure_cluster_group`。
- sequential session：`city_create_d4_candidate_session`、`city_plan_d4_next_candidates`、`city_select_d4_candidate`、`city_finalize_d4_candidate_session`。

这些工具不得被文档描述成正式 workflow 的保底路径。正式 Blueprint 失败时应修正 Blueprint 或编译错误，不自动切换到固定图形、array loop 或 sequential session。

## 当前关键 schema

| Artifact | 当前 schema |
| --- | --- |
| Blueprint Context | `city_blueprint_context.v0.10` |
| Blueprint | `city_blueprint.v0.11` |
| Catalog Snapshot | `city_blueprint_catalog_snapshot.v0.10` |
| Reference Catalog | `city_blueprint_reference_catalog.v0.9` |
| Validation / Submission | `city_blueprint_validation_report.v0.4` / `city_blueprint_submission_trace.v0.4` |
| Compile Trace / Group Extent | `city_generation_compile_trace.v0.13` / `group_extent_map.v0.10` |
| Structure Anchor Plan / Map | `city_structure_anchor_plan.v0.3` / `city_structure_anchor_map.v0.3` |
| Template Catalog / Placement / Ledger | `v0.1` 系列 |
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

`city_execute_d5` 的 `roadProvider` 为 `auto|roadweaver|worldedit_debug|none`。RoadWeaver plan v0.2 只允许 `long_distance_inter_group_mst`：禁止 intra-group 边，SIMPLE 仅保留距离 >=128 blocks 的组间边；HIERARCHICAL `cityMainRoadPlan=planned` 时 `delegatedToCityMainRoad=true/connectionCount=0`。`auto` 缺 Mod 只跳过该长距层，不启用 WorldEdit fallback。

`city_execute_d5` 写出的 `active_planned_structure_registry.json` 必须包含 `activationProvenance`：schema、D5 plan hash、D6 plan hash、LandUse completion hash、Decoration completion hash 与规范化 `roadProvider`。`city_run_workflow skipExisting=true` 只有在这些身份全部与当前输入一致时才能跳过 D5；任一来源变化或旧 artifact 缺 provenance 都必须重新执行激活。

RoadWeaver endpoint 必须同时保留模板冻结的 `entrancePoint` 与实际注册使用的 `roadPoint`。存在 `lockedActualFootprint` 时，`roadPoint` 必须沿冻结入口方向投影到 footprint 外一格，`coordinateSource=directional_gateway_outside_locked_footprint`；不得把 footprint 内的门点直接交给长距道路作为首段起点。

## 运行与日志

Node handler 为每次调用记录统一 `callId`、started/completed、UTC 时间、单调耗时和 timeout 分类。外层超时不等于 Java 端没有继续执行，复查时必须用 call log 与 artifact identity 对齐，不能仅凭客户端等待时间判断阶段状态。

City artifact 不再按阶段散落在 `<runId>/` 根目录。新测试统一写入 `<runId>/city_test_runs/<citySeedId>/steps/`，包根 `test_run_manifest.json` 保存 `latestRequest`、`status`、`nextAction` 和追加式 `attempts[]`。MCP call log 仍只解释调用边界，运行包清单才是恢复一次 City 测试的入口。

`city_run_workflow` 可通过 `skipExisting` 复用身份匹配的冻结 artifact。它必须在以下边界停止并返回明确状态：D3 需要复核、Blueprint 尚未提交、世界修改未确认、目标 chunk 尚未 worldgen、hash/schema 漂移或下游 artifact 不完整。
