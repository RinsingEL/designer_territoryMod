# City 调试 MCP 接口契约

## 版本

D4 Blueprint compiler v0.6 主线 + D4 阵列候选选择闭环 v0.4/v0.5 + Patch 探索式选址 v0.1 + 建筑驱动 LandUse v0.1 + 关键装饰锚点候选 v0.1 + worldgen 方块观测 v0.1 显式开发接口。

Java HTTP：`127.0.0.1:5000`
Node MCP：`country_designer_mcp`
环境变量：`GEOMANTIA_MC_API_URL`，默认 `http://127.0.0.1:5000`

## 工具总览

| MCP 工具 | HTTP 端点 | 当前语义 |
| --- | --- | --- |
| `city_plan_d2` | `POST /realm/city/plan_d2` | 构建 CitySiteContext。 |
| `city_plan_d3` | `POST /realm/city/plan_d3` | 构建 CityLandformReviewPackage 和 D3 review PNG。 |
| `city_review_d3_site` | `POST /realm/city/review_d3_site` | 对 T4 AI 候选选出的首都显式接受当前 D3 选址或要求回 T4 重选。 |
| `city_prepare_d4_blueprint_context` | `POST /realm/city/prepare_d4_blueprint_context` | 程序冻结完整 D4 只读上下文；不调用模型，AI 城市设计调用计数为 0。 |
| `city_submit_d4_blueprint` | `POST /realm/city/submit_d4_blueprint` | 同一 `contextId` 只消费一次完整 `CityBlueprint v0.4` 提交；每个 Group 必填 `preferredPatchZone=CENTER|NORTH|EAST|SOUTH|WEST`，可选 `connectionPlan`，输出 blueprint/report/trace。 |
| `city_compile_d4_blueprint` | `POST /realm/city/compile_d4_blueprint` | 只读取已接受 Blueprint 与冻结 snapshot；全部 Group 先按 patch 内部方位播种，再按关系图连接。程序自动派生 focus/方向/gap，复用旧连续外扩引擎生成近圈完整阵列候选并整批提交，最后 fill。输出 v0.6 compile trace、Group extent 和标准 D4 anchor，不接受 candidateId，不调用 AI。 |
| `patch_explorer_open` | `POST /realm/patch_explorer/open` | 以 `scopeType=city_d4` 打开 D3 patch 探索会话，返回扣除 hard occupied 后的类型目录。 |
| `patch_explorer_show_candidates` | `POST /realm/patch_explorer/show_candidates` | 按 AI 兴趣类型分页返回每类候选、染色图和仅限当页兴趣候选的稀疏几何关系。 |
| `patch_explorer_select_candidate` | `POST /realm/patch_explorer/select_candidate` | 选择已展示候选并返回确认染色图与 `patchSelectionRef`。 |
| `city_query_structure_catalog` | `POST /realm/city/query_structure_catalog` | 只读检索 TerraSense 结构画像；支持 canonical termId，以及来源冻结词表的中文标签 / alias；不触发 D4-D7 或世界写入。 |
| `city_query_template_metadata` | `POST /realm/city/query_template_metadata` | 从当前游戏的 `StructureTemplateManager` 只读校验给定 `templateRefs[]`，返回实际 NBT 尺寸、content hash 与来源；不加载区块、不放置结构。 |
| `city_create_d4_candidate_session` | `POST /realm/city/create_d4_candidate_session` | legacy/debug：创建逐 slot 候选 session；不属于新的正式 AI 决策边界。 |
| `city_plan_d4_next_candidates` | `POST /realm/city/plan_d4_next_candidates` | D4 v2：只为当前未选择 slot 生成候选，避开已冻结 occupied envelope。 |
| `city_select_d4_candidate` | `POST /realm/city/select_d4_candidate` | D4 v2：选择当前 slot 的一个 candidate，冻结占用并进入下一个 slot。 |
| `city_finalize_d4_candidate_session` | `POST /realm/city/finalize_d4_candidate_session` | D4 v2：所有 slot 选完后生成标准 D4 `StructureAnchorPlan` / `StructureAnchorMap`。 |
| `city_plan_d4_candidates` | `POST /realm/city/plan_d4_candidates` | v0.1 debug batch 入口：一次性生成全部 slot 候选，`planningMode=all_slots_tentative_order_debug`。 |
| `city_plan_d4_array_candidates` | `POST /realm/city/plan_d4_array_candidates` | D4 阵列候选入口：按 patch / envelope facts 生成 3-5 组批量结构候选，组内已做估算防撞，并内嵌可直接交给 `city_plan_d4` 的 `expandedStructureAnchorPlan`。 |
| `city_create_d4_design_loop_state` | `POST /realm/city/create_d4_design_loop_state` | D4 多轮设计 loop state：基于 D3 patch 创建状态 artifact；只写状态，不触发提交阶段。 |
| `city_read_d4_design_loop_state` | `POST /realm/city/read_d4_design_loop_state` | D4 多轮设计 loop state 读取：返回 state、occupied field、zones、patch availability、summary 和 trace。 |
| `city_append_d4_design_loop_round` | `POST /realm/city/append_d4_design_loop_round` | D4 多轮设计 loop 追加一轮：写入本轮 anchors / placed structures / zones，并用 `collisionEnvelope` / `bodyEnvelope` 回写 occupied field。 |
| `city_write_d4_design_loop_state` | `POST /realm/city/write_d4_design_loop_state` | D4 多轮设计 loop state 显式写回：校验并重写 state 及拆分 artifact。 |
| `city_create_d4_array_layout_loop` | `POST /realm/city/create_d4_array_layout_loop` | D4 阵列布局 loop 显式入口：v0.2/v0.3 创建直接执行 state；v0.4 创建候选选择 state，读取关键结构 D4 anchor 作为 occupied。 |
| `city_execute_d4_array_layout_item` | `POST /realm/city/execute_d4_array_layout_item` | D4 v0.2/v0.3：每轮只执行一个 `nextArrayLayoutPlanItem`；v0.3 `composite_array` 可在单 item 内展开 parent zone / subZones / child arrays。 |
| `city_query_d4_array_expansion_space` | `POST /realm/city/query_d4_array_expansion_space` | D4 v0.4 只读外扩空间：常规返回 focus 周边空间；显式新功能区返回全局 patch 候选与入口。 |
| `city_plan_d4_array_expansion_candidates` | `POST /realm/city/plan_d4_array_expansion_candidates` | D4 v0.4/v0.5 默认生成至少 3 组完整阵列候选与预览，不提交 loop state；显式 `minCandidateCount=2` 可返回 2 组完整合法候选供人工选择。 |
| `city_select_d4_array_expansion_candidate` | `POST /realm/city/select_d4_array_expansion_candidate` | D4 v0.4 选择完整候选后原子更新 occupied、array zones、剩余空间和 trace。 |
| `city_finalize_d4_array_layout_loop` | `POST /realm/city/finalize_d4_array_layout_loop` | D4 v0.2/v0.3/v0.4：把 base key anchors + 已提交 array anchors 合并成标准 D4 `StructureAnchorPlan` 并调用 `city_plan_d4`。 |
| `city_plan_d4_structure_cluster_groups` | `POST /realm/city/plan_d4_structure_cluster_groups` | D4 整组候选调试入口：按 `DesignSlotPlan` 一次生成多组完整结构群落脚方案；预览图颜色代表整组，bbox 默认不画在主图里。 |
| `city_select_d4_candidates` | `POST /realm/city/select_d4_candidates` | v0.1 debug batch 选择入口。推荐使用 D4 v2 session。 |
| `city_select_d4_structure_cluster_group` | `POST /realm/city/select_d4_structure_cluster_group` | D4 结构群整组选中入口：按 `groupCandidateId` 取 `expandedStructureAnchorPlan` 并进入标准 D4 artifact。 |
| `city_plan_d4` | `POST /realm/city/plan_d4` | 直接提交 `StructureAnchorPlan`，生成结构 anchor / envelope；保留为调试入口。 |
| `city_plan_d5` | `POST /realm/city/plan_d5` | 读取最终 D4 `StructureAnchorMap`，按 `collisionEnvelope + maskMarginBlocks` 生成轻量 reservation mask 预案；不读 safety 字段，不生成真实道路 operation。 |
| `city_plan_d6` | `POST /realm/city/plan_d6` | 读取最终 D4/D5 与当前世界固定 NBT，复核 identity、三层几何和 owner chunks；不要求 chunk loaded，不改世界。 |
| `city_plan_land_use` | `POST /realm/city/plan_land_use` | 读取 D3 terrain field、D4 group provenance 与 D6 locked footprint，生成 block 级 area plan 和 `city_land_use_surface_print_plan.v0.2`；可选严格 intent v0.3 在本次规划中提供 `uniform|contour_bands` 算法材料默认与 group 例外，不改世界。 |
| `city_query_decoration_catalog` | `GET /realm/city/query_decoration_catalog` | v0.3 返回 catalog hash、content index schema、pose upgrade required / mode、prefab pose summaries 与 style 摘要；不返回原始 NBT。 |
| `city_upgrade_default_decoration_catalog` | `POST /realm/city/upgrade_default_decoration_catalog` | 仅对 managed 且精确匹配旧打包默认的目录显式备份并升级 v0.3；自定义目录拒绝自动改写，停用旧 active plan但保留 ledger / 已落地方块。 |
| `city_plan_decoration_anchor_candidates` | `POST /realm/city/plan_decoration_anchor_candidates` | 为关键单点 prefab 按完整 footprint、clearance 和已知硬障碍生成 1-8 个稳定候选与预览；不采样地形、不加载 chunk，Agent 选中后把相对 `coordinateFramePatch` 回填到最终 DecorationProgram。 |
| `city_plan_city_dressing` | `POST /realm/city/plan_city_dressing` | 通用装饰阵列 v0.3：继承 Shape / Pattern 判别联合，增加严格连续落差 / foundation policy；v0.2 只读兼容，新 artifact 输出 v0.3。 |
| `city_probe_decoration_terrain` | `POST /realm/city/probe_decoration_terrain` | activation 前只读地形探针：读取已编译装饰槽位，只采样当前已加载真实区块，报告高度、邻接高差、未加载覆盖和线性槽位连续带 profile；不生成 chunk、不写世界。 |
| `city_execute_d5` | `POST /realm/city/execute_d5` | 校验并激活 LandUse area + SurfacePrintPlan v0.2 + 当前 palette；LandUse 不读取 catalog / prefab / run。连续 Decoration run 仍用目标 ServerLevel generator 采样冻结，不加载 chunk。批量地表与稀疏 Decoration 职责冲突时 hard fail。 |
| `city_execute_d7` | `POST /realm/city/execute_d7` | 保留入口名，正式路径只查询 worldgen ledger / chunk 状态。 |
| `city_query_worldgen_observations` | `POST /realm/city/query_worldgen_observations` | 按 dimension + chunk 查询 City 写入在 post-features / retry tick / chunk save 回调中的实际 BlockState；只读 sidecar，不加载 chunk。 |
| `city_plan_city_walls` | `POST /realm/city/plan_city_walls` | 读取 D7 ledger、D5 wall reservation 和 actual road mask，生成城墙 plan、preview 和 NBT 模板；v3 可生成结构种子城市外环 hull + 道路聚类裁门；`wallDesignPolicy=v3.2/v3.3` 增加天然边界、道路趋势 / 近路投影开门和独立 gatehouse；`wallVersion=v4` 生成 actualFootprint 优先、D5 cityDomain cell 轻量贴形的陆侧墙图。 |
| `city_execute_city_walls` | `POST /realm/city/execute_city_walls` | 按城墙 plan 使用 vanilla setBlock 后端放置临时石墙 / 塔楼 / gatehouse；v3/v4 可开启 debug scan 输出缺口原因，v4 按 `wallUnits[]` 和 `nodeConnectorUnits[]` 执行。 |
| `city_run_workflow` | `POST /realm/city/run_workflow` | 正式快跑器；D3/site review 后默认进入 Blueprint，缺输入返回 `awaiting_city_blueprint + nextAction`，有效 Blueprint 自动编译并继续 D5-D7。 |

## MCP 调用时间日志

所有 City 工具与其他 MCP 工具共用 [MCP 调用日志契约](../../../../00_nav/MCP调用日志契约.md)。City 不另建一份同名日志或人工计时文档。

## D4 单次 Blueprint 决策边界

正式顺序固定为：

```text
city_prepare_d4_blueprint_context
-> AI/Codex 读取返回的完整 context
-> city_submit_d4_blueprint（一次）
-> city_compile_d4_blueprint（纯程序）
-> 标准 structure_anchor_plan / structure_anchor_map
```

prepare 必填 `runId`、`citySeedId`、`terrasenseProfileSource`、`templateCatalogSource`、`blueprintReferenceCatalog.v0.2`，成功返回 `contextId`、`aiCityDesignCallCount=0` 和完整 `cityBlueprintContext`。submit 必填同一 run/city/contextId 与严格 `city_blueprint.v0.4`；非法提交也消费该 context 的一次 AI 设计预算，失败不得覆盖最后有效 Blueprint。v0.1-v0.3 不做静默迁移。`connectionPlan` 可选覆写 `structurePoolRef/algorithmProfileRef/densityClass/parameters`；MCP schema 严格拒绝坐标、数量、裸 gap 和跨 planner family 参数。

详细字段、枚举、hash 和 reason code 见 [CityBlueprint 数据契约](../数据契约/CityBlueprint数据契约.md)。02 已接通；本文其余 D4 candidate/session/array/manual anchor 接口统一按 legacy/debug 理解，只能由显式旧 mode 调用，不得被正式 Blueprint 主链继续调用。

## city_run_workflow

这是 City 真实验收提速入口，不替代单步调试接口。它按当前 active path 调用现有 endpoint handler，并写出 `city_workflow_report.json`。

必填参数：

- `runId`
- `citySeedId`

正式 Blueprint 首次完整运行不再从 workflow 请求中读取设计 slot 或目录，而是要求案子 01 的 Context/Blueprint 已存在。以下参数只在显式 legacy/debug mode 中需要：

- `terrasenseProfileSource`
- `designSlotPlan`
- `templateCatalogSource`，显式指向 `city_template_catalog.v0.1`

常用可选参数：

- `skipExisting`，默认 `true`。已有且 source identity 仍有效的 artifact 可跳过对应阶段，用于等待 chunk worldgen 后复跑；装饰规划只能以 `city_decoration_planning_complete.json` 判断可跳过，不得以 compiled 文件存在判断。
- 发布失效按依赖链传播：D3 或 D6 成功重算后删除旧 LandUse / Decoration completion；LandUse 成功重算后删除旧 Decoration completion。`skipExisting` 只能依据仍存在且在执行期通过 source hash 校验的 completion，不得复用失效的下游 compiled plan。
- `patchScanPaddingBlocks`，默认 128；首次 D3 会按 city bounds + padding 覆盖多个 GIS region，把结构 bbox 和 v4 城墙 breathing room 需要的外侧 patch context 一并写入 D3 package。D4 候选仍受原 city grid 约束，padding 不是新的城市核心可选域。
- `confirmWorldMutation`，默认 `false`。未传时 workflow 在 execute_d5 前返回 `waiting_for_confirmation`。
- `d4CandidateMode=blueprint|key_then_array|array_layout_loop_v0_2|array_layout_loop_v0_3|sequential_session|structure_cluster_groups`；默认 `blueprint`。默认路径缺 Context 时返回 `awaiting_city_blueprint + nextAction=city_prepare_d4_blueprint_context`，缺已接受 Blueprint 时返回 `awaiting_city_blueprint + nextAction=city_submit_d4_blueprint`，两者均为 `ok=true` 可恢复暂停。其余 mode 必须显式传入并统一视为 legacy/debug。
- `enableLandUseLayer=true|false`；显式请求值优先于 `city_land_use/settings.json.enabledInWorkflow`，bundled 默认关闭。启用后在 D6 locked plan 之后运行 `city_plan_land_use`。
- `landUseIntentPlan`，可选严格 `city_land_use_intent_plan.v0.3`。省略时服务端按 D4 semantic 自动选规则并使用 policy 内置 fallback；显式提交以 `surfaceAlgorithmDefaults[]` 提供本次城市算法材料默认，以 `surfaceOverrides[]` 处理少数 group 例外。未知字段、未知 target / rule、重复算法默认 / surface target、`set_rule` 缺 ruleRef、`exclude` 携带 ruleRef 均 hard fail；旧 v0.2 `global_axis|radial` 不自动迁移。
- `enableDressingLayer=true|false`，默认 `false`；为 `true` 时必须提供 `decorationProgramPlan`，workflow 会在 D6 后调用 `city_plan_city_dressing`，再由 `city_execute_d5` 激活装饰 worldgen 程序。
- `decorationProgramPlan`，`schemaVersion=city_decoration_program_plan.v0.2`；必须带 query 返回的 `catalogHash`、`styleProfileId`、`styleProfileHash`；`programs[]` 使用 Shape / Pattern 判别联合并只引用该风格档案注册的语义 content。
- `dressingBrushPlan`、`dressingLayoutItems[]` 和 v0.1 七种业务 item 已破坏性移除，传入返回 `CITY_DRESSING_LEGACY_SCHEMA_REMOVED`，不得自动转换。
- `roadProvider=auto|roadweaver|worldedit_debug|none`；默认 `auto` 只在 RoadWeaver 存在时注册真实道路，缺 RoadWeaver 时跳过道路，旧 debug 道路必须显式 `worldedit_debug`。
- `planWalls` / `executeWalls`，默认 `false`。
- `wallVersion`、`wallTerrainPolicy`、`wallDesignPolicy` 及对应城墙参数，会透传给 D5 / CityWalls；`wallVersion=v4` 时额外可传 `wallUnitLengthBlocks`、`waterRunMinUnits`、`waterRetreatMaxCells`、`structureWallBreathingRoomBlocks`、`heightDatumClampBlocks`、`localMedianWindowUnits`。
- `debugScan`，执行城墙时默认 `true`。
- `dimensionId` / `playerName`。

语义：

- workflow 会顺序执行：`city_plan_d3` -> site review -> 默认 Blueprint 编译 D4 -> `city_plan_d5` 轻量预案 -> `city_plan_d6` 当前世界 NBT lock -> 可选 `city_plan_land_use` -> 可选 `city_plan_city_dressing` -> `city_execute_d5` locked 激活 -> `city_execute_d7`。正式 D4 只读取冻结 snapshot，不接受本次请求临时替换目录。legacy/debug mode 才读取 `templateCatalogSource/designSlotPlan`。
- `key_then_array` 阶段约束：`placementOrder` 中所有关键结构 slot 必须在任何 `array_fill` 之前；数组阶段后再出现关键结构返回 `D4_KEY_STRUCTURES_MUST_PRECEDE_ARRAYS`；存在阵列但没有关键结构返回 `D4_KEY_STRUCTURE_STAGE_REQUIRED`。
- D3 step 会刷新覆盖 `grid.blockBounds + patchScanPaddingBlocks` 的所有 GIS region；不得只刷新城市中心所在单个 region。
- 若 `confirmWorldMutation=false`，返回 `status=waiting_for_confirmation`，不激活 mask / planned registry。
- 若 D7 返回 `WAITING_FOR_WORLDGEN`，workflow 返回 `status=waiting_for_worldgen`。玩家或 debug command 加载目标 chunk 后，用相同请求复跑；已存在 artifact 会被跳过。
- `planWalls=true` 时 ledger 完整后继续调用 `city_plan_city_walls`。
- `executeWalls=true` 时继续调用 `city_execute_city_walls`；成功完成后 HTTP controller 才请求保存世界。
- 每个 step 都记录 `startedAt`、`endedAt`、`durationMs`、`status`、`reasonCode`、`artifacts`。
- `skipExisting=true` 复跑城墙时，workflow 必须校验已有 `city_wall_plan.json` 的 `wallVersion` / `wallDesignPolicy` / `wallTerrainPolicy` 与请求匹配；不匹配时不得跳过旧 plan。

返回 artifact：

- `city_workflow_<citySeedId>/city_workflow_report.json`
- `city_d4_staged_<citySeedId>/d4_staged_plan.json`
- `city_d4_staged_<citySeedId>/d4_staged_trace.json`
- `city_d4_array_layout_<citySeedId>/d4_array_layout_plan.json`、`d4_array_layout_loop_state.json`、`d4_array_layout_execution_trace.json`、`d4_array_occupied_field.json`、`d4_array_patch_availability.json`、`d4_functional_array_zones.json`、`d4_array_layout_preview.png`（仅显式 `array_layout_loop_v0_2` / `array_layout_loop_v0_3`）
- `city_land_use_<citySeedId>/land_use_terrain_field.json`、`city_land_use_area_plan.json`、`city_land_use_surface_print_plan.json`、`land_use_plan_trace.json`、`land_use_preview.png`、`quality_report.json`、最后发布的 `city_land_use_planning_complete.json`（workflow 开启 LandUse 或单独调用 `city_plan_land_use`）
- `city_decoration_<citySeedId>/city_decoration_program_plan.json`、`city_decoration_compiled_program_plan.json`、`city_decoration_slot_projection.json`、`city_decoration_planning_trace.json`、`quality_report.json`、`city_decoration_preview_index.json`、`city_decoration_preview_<programId>.png`、末尾发布的 `city_decoration_planning_complete.json`（仅显式 `enableDressingLayer=true` 或单独调用 `city_plan_city_dressing`）

质量口径：

- workflow 报告只用于提速和留痕；任何结构越界、重叠、worldgen ledger 不完整、墙体缺口等最终判断仍以各阶段 artifact / trace 为准。
- 不允许 workflow 在正式路径绕过 `city_execute_d5` / `city_execute_d7` 的 worldgen-time placement 规则；不得回退 late paste。

## city_plan_d3

必填参数：

- `runId`
- `citySeedId`

可选参数：

- `cellStepBlocks`，未传时从 run manifest 恢复。
- `patchScanPaddingBlocks`，默认 128。
- `dimensionId`
- `playerName`

语义：

- D3 进入实时 GIS 刷新前，必须读取 run 的 `world_survey_context.json`，并严格比较其中 `worldSeed` / `dimensionId` 与当前 `ServerLevel`。缺少或损坏身份来源时返回 `CITY_RUN_WORLD_IDENTITY_SOURCE_MISSING` / `CITY_RUN_WORLD_IDENTITY_INVALID`；不一致时返回 `CITY_RUN_WORLD_IDENTITY_MISMATCH`。以上拒绝必须发生在创建 D3 / LandUse 目录和刷新 GIS region 之前。
- 同一 guard 适用于后续所有读取或修改实时世界的 City 入口，包括 template metadata、terrain probe、D6、execute D5/D7、城墙规划/执行和 workflow；离线 D2/D4/D5/LandUse 规划仍只消费 artifact，不要求当前世界已加载。
- D3 的 `grid` 仍表示城市核心规划域，D4 候选不得因为 padding 扩大而离开该 grid。
- `patchScanPaddingBlocks` 只扩大 patch 上下文：实现必须刷新覆盖 `grid.blockBounds + padding` 的所有 GIS region，并把这些 region 的 `LandformPatch` / `memberCells` 合并进同一个 `CityLandformReviewPackage`。
- 目的：当 AI 选择靠近城市核心边界的 patch 时，D6 `actualFootprint`、D5/D7 reservation 和 v4 城墙 `structureWallBreathingRoomBlocks` 仍有已扫描 patch 背景，不允许墙体静默长到未知 patch 外。
- D3 package 必须写出 `patchScanPaddingBlocks`、`patchContextBounds`、`refreshedRegions[]`，用于判断 patch coverage 是否足够。
- 若 CitySeed 为 `role=capital` 且 `source.siteSelectionMode=ai_candidate_selection`，D3 必须返回 `siteReviewStatus=awaiting_review`，并删除与新 D3 身份不再匹配的旧审查决策。

## city_review_d3_site

必填参数：`runId`、`citySeedId`、`decision`、`decisionReason`。`decision` 只接受 `accept_selected_site` 或 `reselect_required`。

审查产物 `city_site_review_decision.json` 必须绑定当前 D3 package identity、CitySeed identity 和 T4 `patchSelectionRef`。所有 D4 入口统一校验：

- 缺少决策返回 `CITY_D3_SITE_REVIEW_REQUIRED`。
- 决策为重选返回 `CITY_D3_SITE_RESELECTION_REQUIRED`，下一步回到 T4 Patch 选址。
- D3 或 CitySeed 已变更返回 `CITY_D3_SITE_REVIEW_STALE`。
- 只有当前 identity 下的 `accept_selected_site` 允许进入 D4，不允许默认改变城市原型绕过重选。

## city_plan_city_walls v4

`wallVersion=v4` 为当前 City Walls 新测试路径。

新增 / 关键参数：

- `wallUnitLengthBlocks`：默认 16，墙图基础 unit 长度，和 step 对齐。
- `waterRunMinUnits`：默认 3，连续多少个 unit 命中水体后判定为湖 / 海并尝试陆侧退避。
- `waterRetreatMaxCells`：默认 4，水体退避最多尝试多少个 unit 步长。
- `structureWallBreathingRoomBlocks`：默认 32，以 D7 `actualFootprint` union 为核心外扩生成墙圈。
- `heightDatumClampBlocks`：默认 6，`targetY` 相对全局 `cityWallDatumY` 的夹取范围。
- `localMedianWindowUnits`：默认 3，局部高度 median 采样窗口。

输出要求：

- `schemaVersion=city_wall_plan.v0.4`
- `wallBoundaryMode=actual_footprint_land_ring`
- `wallContourMode=terrain_adaptive_domain_guided_land_ring`
- `terrainContourEvents[]`：记录 unit 因 D5 `cityDomainMask` 外缘 guide 而发生的有限偏移，以及为连接偏移 unit 插入的短 `terrain_contour_link`。
- `wallNodes[]`：节点类型包括 `corner_tower`、`beacon_tower`、`gatehouse`、`terrace_node`、`natural_boundary_endpoint`。
- `wallUnits[]`：16 格左右的短墙 unit；普通墙不得依赖执行层再任意切成长短不一的重叠片。
- `nodeConnectorUnits[]`：墙体到塔 / 门楼 / terrace 的连接单元，输出 `connectorStatus=connected|stepped|blocked|skipped`。
- `cityWallDatumY`：整圈候选墙线的 trimmed median 高度基准。
- `wallGraphValidation`：记录水体退避、mask skip、height break、闭环候选和断点。

v4 行为口径：

- 边界必须包住 D7 `actualFootprint`，不得被 D3 source patch 锁死。
- 规划层先用 `actualFootprint + structureWallBreathingRoomBlocks` 生成保守外圈，再读取 D5 `cityDomainMask[]` 中的 `maskType=city_domain_cell` 外缘作为地形 / 城市域 guide；每个 unit 只允许小幅偏移，且必须仍在 `knownPatchBounds` 内、不能压结构 footprint 或水体。相邻 unit 偏移后用 `terrain_contour_link` 连接，避免预览继续呈现纯四边形。
- D5 `seedPatches[]` 若带 `memberCells[]`，v4 水体判定必须优先按真实成员 cell 判断，不能把大型 water patch 的 envelope 当作整片硬水体；`shore` 不应直接等同于普通墙禁止落点。
- 连续水体 run 达阈值时优先退回陆地侧；退避失败时输出天然水体边界 gap，而不是把普通墙落入湖 / 海。
- `actualRoadMask` 只用于真实道路开门；复跑或实机验收时不得把本系统已放置的石砖 / 圆石 / 安山岩等城墙或结构材料反扫成道路并造成大面积 `ROAD_MASK_GATEHOUSE_OPENING`。
- 相邻节点高差 `<=2` 走普通平墙，`3..6` 走 `stepped_wall_unit` 或 `stair_link`，`>6` 插入 `terrace_node`；仍无法缓解时在 validation 中输出明确 reason。
- 执行层按 `wallUnits[]` / `nodeConnectorUnits[]` 放置，并在地形采样时忽略本系统已经放置的墙 / 塔 / 门楼材料，避免重复执行叠高。

## 已删除接口：city_profile_structure_envelopes

HTTP 与 MCP 路由均已删除。任何旧 profiling 请求、`structureEnvelopeFactsSource`、bbox group 或 envelope sample 输入都必须返回 `CITY_CONFIGURED_STRUCTURE_FLOW_REMOVED`，不生成兼容 artifact。

## city_plan_d4

必填参数：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `templateCatalogSource`
- `structureAnchorPlan`

可选：

- anchor 只允许 `templateId`、可选一致的 `templateRef`、显式 `variant`、rotation / mirror、anchor 和 placement provenance。旧 `structureId(s)`、hash/rawSize 手写值、bbox/envelope 输入均拒绝。

`terrasenseProfileSource` 支持：

- `sourceType=structure_profile_jsonl` + `profilePath`
- `sourceType=debug_catalog` + `debugCatalogPath`
- 可选 `vocabularySnapshotPath`：冻结 TerraSense 词表。`city_query_structure_catalog` 用它解析中文 display label 与 alias；未提供时该接口仍接受画像中存在的 canonical termId。

旧 `patchGroupPlan`、`functionType`、`functionTag`、`function_candidates` 等字段必须失败：`LEGACY_CITY_FUNCTION_ZONE_FLOW_REMOVED`。

返回 artifact：

- `structureAnchorPlan`
- `structureAnchorMap`
- `structureProfileCatalog`
- `structureAnchorPreview`
- `qualityReport`
- `sourceD3Package`

`structureAnchorMap.anchors[]` 输出冻结的 template identity、transformed `actualFootprint`、`collisionEnvelope=exact footprint + clearance` 与 `maskEnvelope=collision + maskMargin`。预览必须分层绘制 body、collision、mask；不得读取 `StructureStart.getBoundingBox()` 作为建筑 body。

## D4 Patch Explorer 接入 v0.1

Patch Explorer 是 D4 现有候选器之前的可选地理探索层，不直接生成 anchor、不写 occupied，也不替代 envelope、阵列完整计数和最终防撞。

推荐调用顺序：

1. 调用 `patch_explorer_open`，传 `runId`、`scopeType=city_d4`、`citySeedId`。
2. AI 从返回的类型目录中选择感兴趣的类型，调用 `patch_explorer_show_candidates`。程序默认每类展示面积前 3 名并返回候选染色图；关系表只描述当前兴趣类型、当页候选之间的相邻、距离、方位和共享边界。
3. AI 可翻页或更换兴趣类型；确定后调用 `patch_explorer_select_candidate`，获得确认染色图和 `patchSelectionRef`。
4. 将 `patchSelectionRef` 放入目标 D4 计划对象。服务端验证同一 D3 scope 后，同时派生 `candidatePatchRefs[]` 搜索依据和内部保留的 `candidateLegalRegion` member-cell 硬边界，再调用既有候选器。

支持消费选择凭证的入口：

| 入口 | `patchSelectionRef` 所在对象 | 服务端交接 |
| --- | --- | --- |
| `city_plan_d4_candidates`、`city_plan_d4_structure_cluster_groups`、`city_create_d4_candidate_session` | `designSlotPlan.slots[]` | 覆盖该 slot 的 `candidatePatchRefs[]`，并注入组件 member-cell 硬边界，再进入原顺序/整组候选器。 |
| `city_plan_d4_array_candidates` | `arrayCandidatePlan` | 覆盖 `candidatePatchRefs[]`，注入组件硬边界，再生成 3-5 组完整阵列。 |
| `city_create_d4_array_layout_loop` | `arrayLayoutPlan.layoutPlans[]` | 为每个带选择凭证 item 覆盖搜索 patch 并注入组件硬边界；复合子阵列继承该边界。 |
| `city_query_d4_array_expansion_space`、`city_plan_d4_array_expansion_candidates` | `arrayExpansionRequest` | 解析为单个 `selectedGlobalPatchRef`、设置 `newFunctionalArea=true`，并把组件硬边界内部传播到 nested layout item。 |

选择凭证必须来自同一 `runId`、同一 `citySeedId` 的 `city_d4` scope，且来源 D3 与已提交 occupied 几何身份仍一致。只读候选会话中的更新时间、质量结果、候选历史和未选择 envelope 不得令凭证 stale，也不得被当作 occupied；真实选择或 finalize 新增的 occupied 几何必须令旧凭证 stale。`candidatePatchRefs[]` 继续负责定位原 D3 patch 与生成搜索点；真正的完整候选范围硬边界是服务端从已验证选择中注入的 `candidateLegalRegion`。anchor、array、layout、cluster、candidate session 和 expansion 的每个实际 `collisionEnvelope` 必须完全落在该 member-cell union 内，越界候选不得生成或必须拒绝。

`candidateLegalRegion` 是 HTTP 边界内部保留字段，调用方不得在根对象、slot、layout item 或 expansion nested item 中手写。任一外部输入携带该字段都返回 `PATCH_SELECTION_D4_RESERVED_FIELD_FORBIDDEN`；只有 resolver 验证 `patchSelectionRef` 后才能注入，避免伪造较大 mask 绕过选择凭证。

D4 v0.5 常规 outward 保持原行为：已有父结构、方向和目标间距时，不要求 `patchSelectionRef`，仍从父结构 body/collision 外缘连续生长并把 D3 patch 作为后置地形过滤。只有 AI 明确先探索地理或创建新功能区时才走上述选择凭证路径。

## city_query_structure_catalog

必填参数：

- `terrasenseProfileSource`：只接受 `structure_profile_jsonl` 或显式 `debug_catalog`，不读取旧 C3.5 catalog、`function_candidates` 或 `functionTags`。

可选参数：

- `allOfTerms[]`：AND，候选必须同时拥有的 term。
- `anyOfTerms[]`：OR，候选至少拥有一个的 term。
- `excludeTerms[]`：拥有任一 term 的候选不返回。
- `limit`：默认 20，范围 1-100。

term 输入优先使用 TerraSense canonical termId，例如 `function.agriculture`。当 source 带 `vocabularySnapshotPath` 时，也接受该冻结词表中唯一对应的 `label`（例如 `农业`）或 `aliases[]`；无词表时 display label / alias 必须返回 `CITY_STRUCTURE_QUERY_TERM_UNRESOLVED`，同名歧义返回 `CITY_STRUCTURE_QUERY_TERM_AMBIGUOUS`，不做 City 自建语义映射。

响应 schema 为 `city_structure_catalog_query.v0.2`，只返回可用于语义筛选的摘要：`semanticProfileId`、`matchedCanonicalTerms`、各类完整 terms、`sourceProfileRef`、`catalogMode` 与 `qualityTerms`。不得返回 `structureId`、fixed footprint / expected area / rotations / clearance 等几何或 configured identity；模板身份和全部几何必须另由显式 `templateCatalogSource` 提供。请求不依赖 `runId`、`citySeedId` 或 D3-D7 artifact，不生成任何 artifact、状态或世界写入；`readOnly=true` 是固定响应字段。

本地运行时导入必须把 `StructureProfile.jsonl`、`StructureVocabulary.snapshot.json` 与正式 source 描述一并复制到 `run/config/structureTemplate/terrasense/<importId>/`，不得在 City 请求中继续引用客户端或 TerraSense 工程目录。接口不自动发现 source；调用方仍须将该描述文件内容作为 `terrasenseProfileSource` 传入。当前 v0.1 的只读查询与 D4/D6 请求工作目录不同，导入 source 的 `profilePath` / `vocabularySnapshotPath` 必须写为 StructureBinder 本地运行配置的绝对路径；不得使用跨 endpoint 的相对路径。

## city_query_template_metadata

必填参数：

- `templateRefs[]`：1-32 个 Minecraft `ResourceLocation`，例如 `geomantia:d6d7_fixture/house`。

可选参数：

- `dimensionId`：省略时使用 `playerName` 当前维度。
- `playerName`：用于解析当前维度。

返回每个模板的 `readable`、`failureCode`、`failureDetail`；可读模板额外返回 `rawSize={width,height,depth}`、`templateHash`、`sourceId`。该接口只能读取当前运行时 `StructureTemplateManager`，不得创建 ticket、加载或生成 chunk，不得执行 D4-D7 或写入世界 / run artifact。它用于在组装 `city_template_catalog.v0.1` 前冻结真实 NBT 尺寸和 hash，不替代 D5 前的身份漂移校验。

## city_plan_d4_array_candidates

必填参数：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `templateCatalogSource`
- `arrayCandidatePlan`

可选参数：

- `occupiedStructureAnchorMapSource`，形如 `{ "anchorMapPath": "city_d4_x/structure_anchor_map.json" }`
- `occupiedEnvelopes[]`

`arrayCandidatePlan` 必填 `schemaVersion=city_d4_array_candidate_plan.v0.1`、`cityId`、`arrayId`、`candidatePatchRefs[]`、`templateIds[]`、每个模板的显式 `variantId`、`arrayCount`。`patterns[]` 缺省为 `loose_cluster`、`patch_axis_band`、`scattered`；显式可传 `compound_cluster`、`grid`、`courtyard`、`l_shape`、`u_shape`、`organic_compact`。可选 `compoundCluster={shape,rows,columns,spacingBlocks}`；template assignment 固定为 `round_robin`。

语义：

- `templateIds[]` 按稳定 round-robin 分配到 `arrayCount` 个 item；传 seeded/weighted random、variant seed 或 weights 返回 `D4_RANDOM_TEMPLATE_SELECTION_REMOVED`。
- `arrayCount` 必须完整满足；容量不足返回 `D4_ARRAY_COUNT_UNSATISFIED`，不输出部分候选组。
- 不读取或生成道路，只输出 item 级 `roadPoint` / `roadAccessIntent` 作为 D7 后处理提示。
- 输出 `d4_array_candidate_set.json`、`d4_array_candidate_preview.png`、`quality_report.json`；每个候选组写 `arrayPattern`、`arrayShape`、`spacingBlocks`，item 也写 `arrayShape` / `spacingBlocks`。
- 每个 `arrayCandidates[]` 内含 `expandedStructureAnchorPlan`，调用方选中整组后直接传给 `city_plan_d4`。
- D4 阵列 hard conflict 只看 `estimatedCollisionEnvelope` 与 occupied collision/body；`estimatedMaskEnvelope`、旧 safety 字段、道路 / 装饰 / 植被 margin 不得撑大 spacing。

## city_create_d4_design_loop_state / city_read_d4_design_loop_state / city_append_d4_design_loop_round / city_write_d4_design_loop_state

这一组接口是 D4 多轮城市设计 loop 的 state / artifact 基础设施。它们只读写 JSON artifact，不搜索候选结构、不自动选结构、不执行阵列形态扩展、不触发 D5 / D6 / dressing / roads / worldgen / D7。

`city_create_d4_design_loop_state` 必填：

- `runId`
- `citySeedId`

可选：

- `planningMode` 或 `designLoopOptions.planningMode`，默认 `d4_multi_round_design_loop_v0_1`。
- `designLoopOptions.cityId`
- `baseStructureAnchorMapSource`，形如 `{ "anchorMapPath": "city_d4_x/structure_anchor_map.json" }`，用于从既有 anchor map 初始化 `anchors[]` 与 `occupiedField`。

`city_read_d4_design_loop_state` 必填：

- `runId`
- `citySeedId`

可选：

- `designLoopStateSource`，形如 `{ "designLoopStatePath": "city_d4_design_loop_x/d4_design_loop_state.json" }`；未传时读取默认路径。

`city_append_d4_design_loop_round` 必填：

- `runId`
- `citySeedId`
- `designLoopRound`

可选：

- `stateId`：与当前 state 不一致时返回 `D4_DESIGN_LOOP_STATE_STALE`。
- `designLoopStateSource`

`designLoopRound` 可含：

- `roundId`
- `anchors[]`
- `placedStructures[]`
- `functionZones` 或 `{zones[]}`
- `arrayZones` 或 `{arrayZones[]}`
- `functionalArrayZones.arrayZones[]`
- `nextAiContextSummary`
- `executionTrace`

规则：

- `anchors[]` / `placedStructures[]` 每项必须有 `collisionEnvelope` 或 `bodyEnvelope`，否则返回 `D4_DESIGN_LOOP_OCCUPIED_ENVELOPE_REQUIRED`。
- `occupiedField.occupied[].envelopeSource` 只能是 `collisionEnvelope` 或 `bodyEnvelope`。
- 输入中若存在退场 envelope 字段，写入 state 时必须剥离，不得进入正式 artifact。

`city_write_d4_design_loop_state` 必填：

- `runId`
- `citySeedId`
- `designLoopState`

可选：

- `stateId`：用于 stale state 校验。

返回 artifact：

- `city_d4_design_loop_<citySeedId>/d4_design_loop_state.json`
- `d4_design_loop_occupied_field.json`
- `d4_design_loop_function_zones.json`
- `d4_design_loop_array_zones.json`
- `d4_design_loop_patch_availability.json`
- `d4_design_loop_next_ai_context_summary.json`
- `d4_design_loop_execution_trace.json`
- `quality_report.json`

## city_create_d4_array_layout_loop / city_execute_d4_array_layout_item / city_finalize_d4_array_layout_loop

D4 v0.2/v0.3 阵列布局 loop 是显式 legacy/debug 路径，不替换默认 Blueprint compiler。

`city_create_d4_array_layout_loop` 必填：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `templateCatalogSource`
- `arrayLayoutPlan`

可选：

- `baseStructureAnchorPlanSource`
- `occupiedStructureAnchorMapSource`

语义：

- 创建 `city_d4_array_layout_<citySeedId>/d4_array_layout_loop_state.json`。
- 若已有 `city_d4_<citySeedId>/structure_anchor_plan.json` / `structure_anchor_map.json`，默认作为 base key anchors 和 occupied。
- `arrayLayoutPlan.schemaVersion=city_d4_array_layout_plan.v0.3` 或 `planningMode=array_layout_loop_v0_3` 时，state / trace 也使用 v0.3 口径。
- `arrayLayoutPlan.schemaVersion=city_d4_array_layout_plan.v0.4` + `planningMode=array_candidate_selection_loop_v0_4` 时，`layoutPlans[]` 必须为空；创建后只能走 v0.4 query / plan / select，`city_execute_d4_array_layout_item` 返回 `D4_ARRAY_LAYOUT_V04_CANDIDATE_SELECTION_REQUIRED`。
- 输出 `d4_array_layout_preview.png`，主图只显示已执行 zone、点、连接线和 RoadWeaver gateway，不绘制 bbox。
- `requiredItems[]`、`featuredItems[]` 或 `fillPool[]` 只允许 `{templateId,variantId,rotation?,mirror?}`；`variantId` 必填，几何从显式 `templateCatalogSource` 冻结。`fillPool` 只允许固定 round-robin，不接受权重或随机 seed。

`city_execute_d4_array_layout_item` 必填：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `templateCatalogSource`
- `nextArrayLayoutPlanItem`

可选：

- `stateId`
- `arrayLayoutLoopStateSource`

语义：

- 每次只接受一个 `nextArrayLayoutPlanItem`。
- `plannerType` 支持 `plaza_ring`、`compound_cluster`、`guide_line_dual_side`、`riverbank_dual_side`、`contour_band`、`composite_array`。
- `layoutPlans[]` 不能直接放进 `nextArrayLayoutPlanItem`；v0.3 只有 `composite_array.childLayoutPlans[]` 可以在同轮展开子阵列。
- `composite_array` 会输出 `zoneKind=parent_composite` 的父 zone、`subZones[]` 和 `zoneKind=child_array` 的子 zone，子阵列结构 anchor 才进入最终 `StructureAnchorPlan`。
- `stateId` 若不是当前 state，返回 `D4_ARRAY_LAYOUT_LOOP_STATE_STALE`。
- required item 失败 hard block；fill item 冲突时跳过，最终必须满足 `countPolicy.minCount`。
- `compound_cluster` 读取 `compoundCluster.shape|rows|columns|spacingBlocks`，支持 `grid`、`courtyard`、`l_shape`、`u_shape`、`organic_compact`；zone / item / trace 写 `arrayShape` 与实际 `spacingBlocks`。
- 防撞只使用 collision envelope / body envelope；occupied 来自 base key anchors 和已执行 array items，profile/debug 结构大小诊断不进入正式 array zone 字段。`maskEnvelope` 可以重叠，不得撑大 D4 anchor 间距。
- 模板 item 以目录中已由 NBT 校验的 `rawSize` 和 `clearanceBlocks` 计算几何；阵列输入只允许 `{templateId,variantId,rotation?,mirror?}`，拒绝 `templateFootprint`、`bbox`、`footprint`、`actualFootprint`、`templateSize` 或 `rawSize` 等调用方几何。D4 输出最小角 `anchorBlock`、`templateRef`、`templateHash`、`variantId`、rotation / mirror、NBT `templateSize` 与派生 closed `actualFootprint`；D6 才补 `lockedActualFootprint`。`templatePlacementPlan.transformed.roadEntrances[]` 与 footprint 均由 `templateSize + transform + anchor` 推导。RoadWeaver 只能消费这组入口，不能从 bbox 或阵列中心反推道路端点。
- 阵列 item 可传 `orientationPolicy={mode:auto_frontage,targetRef,frontageEntranceId?,direction?}`。未显式给 `rotation` 的模板会在原候选位置枚举目录 `allowedRotations[]`，按 `array_center`、`nearest_water` 或 cardinal 目标排序，并继续执行既有 grid / collision 检查；item / anchor / trace 输出 `orientationDecision`。模板显式 `rotation` 时保持原行为并优先于自动策略。

`city_finalize_d4_array_layout_loop` 必填：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `templateCatalogSource`

可选：

- `stateId`
- `arrayLayoutLoopStateSource`

语义：

- 合并 `baseStructureAnchorPlan.anchors[]` 与 `arrayAnchors[]`。
- 调用标准 `city_plan_d4`，最终输出 `structure_anchor_plan.json`、`structure_anchor_map.json`、`structure_anchor_preview.png`。
- 后续 D5/D6/D7 不需要知道 array layout loop 存在。

## D4 阵列候选选择闭环 v0.4

v0.4 是显式 legacy/debug 路径，不加入 `city_run_workflow` 默认 Blueprint compiler，也不改变 v0.2/v0.3 的直接 execute 语义。

共同前提：`city_create_d4_array_layout_loop` 传显式 `templateCatalogSource`、`arrayLayoutPlan.schemaVersion=city_d4_array_layout_plan.v0.4`、`planningMode=array_candidate_selection_loop_v0_4`、空 `layoutPlans[]`；可选 `occupiedStructureAnchorMapSource` 提供已 Plan 的 collision occupied。后续 plan/select/finalize 继续传同一 catalog source，source identity 漂移 hard fail。

`city_query_d4_array_expansion_space` 的 `arrayExpansionRequest` 有两种互斥路径：

- 常规外扩必须传 `focusRef={anchorId|arrayId}`、`direction=north|south|east|west|northeast|northwest|southeast|southwest`、`targetPatchRef`。响应 `searchScope=focus_nearby_expansion`，给出 focus collision、方向可用区、入口、容量和 nearby patch。
- 新功能区必须显式传 `newFunctionalArea=true`，且不传 `focusRef`、`direction`、`targetPatchRef`。响应 `searchScope=explicit_global_new_functional_area`、`selectedGlobalPatchRequired=true`、按可用性后容量排序的 `globalPatchCandidates[]`；每项含 `patchRef`、`remainingCapacity`、`available`、`availabilityReason` 和可用时的 `expansionEntryPoint`。查询不预留任何空间。

`city_plan_d4_array_expansion_candidates` 必须传一个 `nextArrayLayoutPlanItem`（支持 `compound_cluster`、`guide_line_dual_side`、`plaza_ring`、`composite_array`）。常规路径继续使用 focus / direction / target patch；新功能区路径必须传 `newFunctionalArea=true` + 来自 query 的 `selectedGlobalPatchRef`，不接受旧 `targetPatchRef` 代替选择。成功返回 `schemaVersion=city_d4_array_expansion_candidate_set.v0.4`、`sourceStateId`、`arrayCandidates[]`、`expansionSpace` 和 quality。每组候选必须完整、collision 不重叠旧 occupied，候选生成不得修改 loop state、occupied、zones 或剩余空间。

`nextArrayLayoutPlanItem.orientationPolicy` 同样适用于 v0.4 候选；每组候选在原点位上完成旋转选择并写出 `orientationDecision`，select 后才把结果写入标准 anchor。

`city_select_d4_array_expansion_candidate` 默认必须传 `candidateId`；只有显式 `autoSelectHighestScore=true` 时才按最高分选择，trace 必须写 `decisionSource=auto_highest_score_explicit`，默认人工 / AI 选择写 `ai_or_human_selected`。选择后才原子写入 loop state 的 anchors、occupied envelopes、functional array zones、remaining expansion space 和 trace；候选集 `sourceStateId` 不匹配当前 state 返回 stale。

`city_finalize_d4_array_layout_loop` 只合并已经 select 的 array anchors；未选 `arrayCandidates[]` 不得进入标准 `structure_anchor_plan.json` / `structure_anchor_map.json`。

v0.4 artifact：`d4_array_expansion_space.json`、`d4_array_expansion_candidate_set.json`、`d4_array_expansion_candidates.png`、`d4_array_expansion_candidate_quality_report.json`，加既有 loop state / occupied / zones / trace artifact。

关键失败码：`D4_ARRAY_LAYOUT_FOCUS_REQUIRED`、`D4_ARRAY_LAYOUT_FOCUS_NOT_OCCUPIED`、`D4_ARRAY_LAYOUT_TARGET_PATCH_REQUIRED`、`D4_ARRAY_LAYOUT_EXPANSION_DIRECTION_UNAVAILABLE`、`D4_ARRAY_LAYOUT_GLOBAL_PATCH_SELECTION_REQUIRED`、`D4_ARRAY_LAYOUT_GLOBAL_PATCH_UNAVAILABLE`、`D4_ARRAY_LAYOUT_GLOBAL_PATCH_NO_CAPACITY`、`D4_ARRAY_LAYOUT_CANDIDATES_UNSATISFIED`、`D4_ARRAY_LAYOUT_CANDIDATE_SELECTION_REQUIRED`、`D4_ARRAY_LAYOUT_CANDIDATE_SET_STALE`。

## D4 连续外扩候选 v0.5

v0.5 复用 `city_query_d4_array_expansion_space` 与 `city_plan_d4_array_expansion_candidates` 的闭环职责，继续使用 `city_d4_array_layout_plan.v0.4`，不新增 endpoint。

- 常规 outward 只提交父结构引用、方向、阵列方式和 `arrayExpansionRequest.expansionPolicy={actualBodyGapMin,actualBodyGapMax,frontierExpansionStepBlocks?,frontierMaxExpansionRounds?}`；不传 `targetPatchRef` 即进入连续前沿模式。
- `candidateCount` 仍限制为 3-5，缺省为 5；`minCandidateCount` 缺省为 3。仅显式 `minCandidateCount=2` 时可返回 2 组完整合法候选，且不得低于 2 或返回残缺阵列。
- query 的 `expansionSpace` 以父结构 D2 body / collision bbox 为中心，响应 `focusBodyEnvelope`、`expansionMode=continuous_focus_frontier`、`expansionPolicy` 与 `frontierRings[]`。候选响应 `parentBodyEnvelope`、`parentCollisionEnvelope`、`frontierRing`、`actualBodyGapBlocks`、`terrainPatchRefs` 与 `frontierTrace`；候选集另写 `frontierSearchTrace[]`。D3 patch 仅作为命中地形与评分说明，可跨 patch。
- `actualBodyGapBlocks` 固定为候选整组结构的最小方向 body gap。连续 `guide_line_dual_side` 先在目标 gap 放内侧首排，再向外放另一侧，不能因双侧横移把首排推到 gap 之外。
- `expansionPolicy` 的连续前沿按整组 D2 `plannedFootprint` 并集推导，而不是按第一个数组成员；混合尺寸成员均不得回压 `actualBodyGapMin`。
- 近圈全部不可用前不得进入外圈；响应 / trace 必须说明 collision、水体、坡度、member-cell 或容量等跳过原因。
- 候选生成不写 loop state；select / finalize 与 v0.4 保持一致。
- 预览须提供 `d4_array_expansion_candidates.png` 总览、`d4_array_expansion_candidate_detail.png` 候选局部和 `structure_anchor_cluster_preview.png` 最终锚点最密簇局部。调试局部图显示 D2 body / collision / mask；设计主图使用候选短编号，避免长 ID 遮挡。
- 近圈无可用候选时逐圈 `reasonCode` 至少可为 `D4_ARRAY_LAYOUT_FRONTIER_NO_TERRAIN_PATCH`、`D4_ARRAY_LAYOUT_FRONTIER_BODY_GAP_UNSATISFIED`、`D4_ARRAY_LAYOUT_FRONTIER_COMPLETE_CLUSTER_UNAVAILABLE`；所有圈失败返回 `D4_ARRAY_LAYOUT_CONTINUOUS_FRONTIER_UNSATISFIED`。常规 outward 不得再依赖 `D4_ARRAY_LAYOUT_TARGET_PATCH_REQUIRED`。

## city_query_decoration_catalog

- 无必填参数，使用 GET。
- 运行时 `config/geomantia/city_decoration/` 是 catalog 真值。仅当该根目录不存在时，本次查询安装打包基础 `content_index.json`、`styles/medieval_coastal.json` 和 4 个有效 NBT 模板；目录已存在时绝不覆盖、合并或修复，目录不完整或非法仍由后续 catalog 校验失败。
- 返回 `schemaVersion=city_decoration_catalog_query.v0.3`、`contentIndexSchemaVersion`、`contentPoseUpgradeRequired`、`upgradeMode=none|explicit_managed_default_only`、当前 `catalogHash`、`contents[]` 摘要与 `styleProfiles[]`。
- 基础 `medieval_coastal` 的 `semanticRefs[]` 至少含 `crop_tile`、`water_channel_tile`、`field_border`、`gravel_path_tile`。
- content 摘要额外暴露 `groundPlaneLocalY`、`embedDepthBlocks`、`clearanceMode`；不返回原始 NBT、blocks、实体或任意 block operation。
- AI 必须先查询目录，再把返回的 `catalogHash`、`styleProfileId`、`styleProfileHash` 写入 `decorationProgramPlan`；program 内 `contentRef` 只能填写该 profile 的语义键，不能填写 concrete prefab id。

## city_upgrade_default_decoration_catalog

- 仅用于首次 bootstrap 过的 managed 默认目录升级；只接受精确匹配打包 v0.2（可含 / 缺旧 fallback）或 v0.3 pre-fallback 的 index，整体备份后写入 v0.3 pose 字段。无 manifest、非 Geomantia source 或任意用户改写均返回 `CITY_DECORATION_DEFAULT_CATALOG_UPGRADE_UNSAFE`。
- 请求必须是 `{"confirmConfigMutation":true}`。响应给出升级前后 catalog hash、backupPath、是否需要重规划，以及被停用的 active plan 数量。
- 当 `catalogChanged=true` 时，旧 plan hash 不得继续 activation。重新 `city_query_decoration_catalog` 取得新 hash 后，用同一 city 的原始 DecorationProgram intent 调用 `city_plan_city_dressing`，再 `city_execute_d5`；同 city 新 hash 是合法替换，不应手改 active plan 或 ledger。
- 验收必须选择未生成目标 chunk；历史田地、ledger 和已落地方块均不被升级入口回写。

## city_plan_decoration_anchor_candidates

必填参数：

- `runId`
- `citySeedId`
- `decorationProgramPlan`：当前 `city_decoration_program_plan.v0.4`，包含待选单点 program；需要顺序规划多个关键装饰时，还应包含前面已经回填候选 patch 的固定单点 programs。
- `programId`：本次生成候选的 program。

可选参数：

- `candidateCount`：`1..8`，默认 5。

前置约束：

- 目标 program 必须为 `shape.type=rectangle` 且 `minU=minV=maxU=maxV=0`、`pattern.type=grid_repeat`，且该局部点处于 grid 启用相位。pattern 指向的 palette slot 可含多个 prefab entry；每个 world anchor 复用 runtime 确定性内容选择。
- palette layer 的 `required` 值沿用原 DecorationProgram 语义；候选工具不额外要求它必须为 `true`。
- 候选 slot 的 `rotationQuarterTurns` 固定为 0，因此 concrete content 必须允许 0 度；`coordinateFrame.quarterTurns` 可以保留原值，不作为 prefab rotation 拒绝条件。
- catalog / style identity、targetArea 和 program 严格字段校验沿用 `city_plan_city_dressing`。普通 scatter、edge、多点 grid、连续带和批量地表不得调用该工具。

语义：

- 读取 D3 / D4 / D5 / D6、可选 LandUse 和 decoration catalog/style；解析 target ref、resolved target mask 和 concrete prefab 的真实尺寸。
- 每个候选的完整 footprint 以及 prefab comfort margin 与 `conflictPolicy.clearanceBlocks` 合成的 clearance 都必须位于 resolved target mask 内。
- 首版完整 prefab footprint 不得跨 owner chunk；跨 chunk anchor 计入 `crossChunk` rejection。
- 候选避开 D6 locked structure、墙 reservation、gate/gateway、路口、LandUse gate/corridor 等当前 artifact 可证明的 hard obstacles。不得把尚未落地的 RoadWeaver 两端点连线或对角 bbox 猜成道路。
- 同一 plan 内，除目标 program 外已经固定为单点的 Decoration programs 也进入 `fixedDecorationObstacles`；多个关键装饰必须按顺序选择，后一次请求携带前面已回填的 programs，避免相互占位。
- 固定 `terrainSampling=not_performed`。入口不请求 ticket、不加载或生成 chunk，不读取 live height，不改现有 DecorationProgram 规划产物、active registry、ledger 或世界。
- 候选为空是成功诊断：`candidates=[]`，并由 `qualityReport` / `rejectionCounts` 解释；不得生成越界 fallback。

响应至少包含：

- `ok=true`。
- `candidateSet`：`schemaVersion=city_decoration_anchor_candidate_set.v0.1`，含 city/program/catalog identity、targetMaskId、请求/扫描/合法/返回数量、`terrainSampling`、`runtimeTerrainPreflightRequired`、`rotationQuarterTurns=0`、`rejectionCounts`、`fixedDecorationObstacles[]` 和 `candidates[]`。
- 每个 candidate：稳定 `candidateId`、rank、确定性 `contentRef` / `paletteSlotId`、诊断用 world anchor / owner chunk、`localOffsetDelta={u,v}`、完整 footprint、clearance、margin、score breakdown，以及可直接回填的绝对 `coordinateFramePatch={originMode,orientationMode,quarterTurns,offsetUBlocks,offsetVBlocks}`。
- `qualityReport`：`schemaVersion=city_decoration_anchor_candidate_quality.v0.1`，含 passed、请求/返回/合法/扫描数量、rejectionCounts、shortfall warning 和 `terrainSampling=not_performed`。
- `rejectionCounts` 固定为 `outsideTarget`、`hardObstacle`、`crossChunk`、`rotationUnsupported`、`contentNotPrefab`、`decorationConflict`；structure / wall / gate / corridor 等在首版汇总为 `hardObstacle`，具体类型从 source plan 与预览读取。
- `preview`：`schemaVersion`、city/program、`fileName`、绝对 `path`、候选数和 `terrainSampling`；图中显示 target mask、硬障碍、固定装饰、候选 footprint / clearance 和短编号。
- `artifacts`：固定含 `candidateSet`、`qualityReport`、`preview`、`sourceD3Package`、`sourceStructureAnchorMap`、`sourceReservationMaskPlan`、`sourceStructureMaterializationPlan`；按实际输入可增加 `sourceWallReservationPlan`、`sourceLandUseAreaPlan`、`sourceLandUsePlanningComplete`。

候选产物目录为 `city_decoration_<citySeedId>/anchor_candidates/<safe programId>/`，写 `decoration_anchor_candidate_set.json`、`quality_report.json` 和 `city_decoration_anchor_candidates_<safe programId>.png`。

后置步骤：

- Agent 只选择 `candidateId`，把对应 `coordinateFramePatch` 合并回原 program，再把完整计划提交给 `city_plan_city_dressing`。
- `coordinateFramePatch` 只允许现有 `originMode`、`orientationMode`、`quarterTurns`、`offsetUBlocks`、`offsetVBlocks`；world anchor 只是响应诊断字段，不得写入最终 AI-facing intent。
- 本工具不新增 selection state，也不替代 `city_probe_decoration_terrain` 和运行期 terrain validator。

常见 reason code：

- `CITY_DECORATION_CANDIDATE_PROGRAM_ID_REQUIRED`
- `CITY_DECORATION_CANDIDATE_PROGRAM_UNKNOWN`
- `CITY_DECORATION_CANDIDATE_COUNT_INVALID`
- `CITY_DECORATION_ANCHOR_CANDIDATE_POINT_SHAPE_REQUIRED`
- `CITY_DECORATION_ANCHOR_CANDIDATE_GRID_PATTERN_REQUIRED`
- `CITY_DECORATION_ANCHOR_CANDIDATE_GRID_POINT_INACTIVE`

## city_probe_decoration_terrain

必填参数：

- `runId`
- `citySeedId`

可选参数：

- `dimensionId`：省略时使用 run 已记录的维度；该记录不可用时再按当前 player / server 解析。
- `playerName`：仅用于定位当前 player 所在维度，不参与槽位或地形计算。

语义：

- 只读取同一 `city_decoration_<citySeedId>/` 内的 `city_decoration_compiled_program_plan.json` 与 `city_decoration_slot_projection.json`；两者的 projection schema、cityId 与 catalogHash 必须一致，否则返回 `CITY_DECORATION_TERRAIN_PROBE_PLAN_INCOMPLETE`。
- `loadedChunksOnly=true` 是固定模式：只检查服务器当前已加载 chunk，不申请 ticket、不调用会 load / generate chunk 的 API；`mutatesWorld=false`，不改世界、不执行 worldgen、不激活 registry、不写 ledger 或 artifact。
- 顶层返回 overall coverage、`activationRecommendation` 和 `reasonCodes[]`。每个 `programs[]` 与 `paletteSlots[]` 至少返回 `projectedSlotCount`、`sampledSlotCount`、`loadedSlotCount`、`unavailableSlotCount`、`coverageRatio`、`heightMin`、`heightMax`、`heightSpread`、`adjacentPairCount`、`maxAdjacentHeightDelta`、`activationRecommendation` 和 `reasonCodes[]`。`cross_section_repeat` 与 `parallel_rows` 的每个 palette slot 另返回通用 `continuousBandProfiles[]`，项为 `programId`、`paletteSlotId`、`continuationAxis`、`projectedSlotCount`、`loadedSlotCount`、`unavailableSlotCount`、`expectedAdjacentPairCount`、`loadedAdjacentPairCount`、`unavailableAdjacentPairCount`、`maxAdjacentHeightDelta`、`continuousLoadedSegmentCount` 和 `reasonCodes[]`；调用方再按内容语义判断水渠、田垄或其他长带风险。
- 未加载槽位必须计入 `unavailableSlotCount`，其地形事实为 unknown；不得以 D3 patch、预览 raster、上次 probe 或默认地表补值。`activationRecommendation=ready_for_activation|review_terrain_before_activation|await_chunk_load|no_projected_slots` 仅供人工决定是否继续，不自动调用 `city_execute_d5`。
- 响应 schema 为 `city_decoration_terrain_probe.v0.1`。重复 probe 不得写入、覆盖或改变 decoration plan、active plan、ledger 或任何 artifact。

常见 reason code：

- `CITY_DECORATION_TERRAIN_PROBE_PLAN_INCOMPLETE`
- `CITY_DECORATION_TERRAIN_CHUNK_UNAVAILABLE`
- `CITY_DECORATION_TERRAIN_SLOPE_REVIEW_REQUIRED`
- `CITY_DECORATION_CONTINUOUS_BAND_SLOPE_RISK`
- `CITY_DECORATION_CONTINUOUS_BAND_UNAVAILABLE`

## city_plan_city_dressing

必填参数：

- `runId`
- `citySeedId`
- `decorationProgramPlan`

可选参数：

- `d4FunctionalArrayZonesSource`
- `roadCorridorSource`
- `dimensionId`
- `playerName`

语义：

- 读取 D3 / D4 / D5 / D6 artifact，以及可选 D4 `functionalArrayZones`。
- 从 `config/geomantia/city_decoration/content_index.json`、`templates/*.nbt` 和 `styles/*.json` 建立 Decoration prefab 目录与风格档案；冻结 `catalogHash` 和所选 `styleProfileHash`。该目录只约束 Decoration-owned 内容；LandUse 农田、水渠和铺装地表直接消费 SurfacePrintPlan v0.2，不引用此 catalog 或 tile NBT。
- 当前 AI 输入 `decorationProgramPlan.schemaVersion=city_decoration_program_plan.v0.4`，编译结果 program 为 `city_decoration_compiled_program.v0.4`；v0.3 及更旧 intent 不自动迁移，schema 不匹配 hard fail。
- `Shape` 首期只接受 `target_mask`、`rectangle`、`ellipse`、`ring`、`polygon`；`Pattern` 首期只接受 `uniform_fill`、`cross_section_repeat`、`parallel_rows`、`edge_repeat`、`grid_repeat`、`deterministic_scatter`。
- Shape / Pattern 按 `type + params` 判别联合校验；首期 Content 只接受 `contentKind=prefab`。AI 只引用 style profile 的语义 `contentRef`；规划阶段才解析为 config catalog 的 concrete prefab，不得提交 block operation、内联 NBT 路径或 block state。
- AI-facing program 接受 `targetArea.sourceType=patch|land_use_area`；后者 `ref` 必须命中同一 City 已定稿的 `LandUseAreaPlan.areaId`。程序解析后才生成内部 `targetMask.memberBounds[]` 与世界 `coordinateFrame.origin/axisU/axisV`，MCP 不接受 `targetBounds/memberBounds` 或 AI 手写 world coords。
- prefab NBT 禁止实体；规划时发现 `entities[]` 非空 hard fail。
- `terrainDropFallbackContentRef` 允许普通 `1x1 -> 1x1` tile，也允许保持一个水平横截面不变、只沿连续 run 轴等长或加长的 prefab fallback；placement mode 与 replace policy 必须一致。该规则只约束独立 Decoration prefab；LandUse v0.2 `contour_bands` 水槽直接消费冻结 role spans，不引用 lined straight / end-cap。
- RoadWeaver 在 Decoration 规划期只有 transformed endpoints 与抽象 connection graph，没有真实路径；不得把 connection 两端的对角 bbox 或直线猜测为 hard corridor。`city_plan_city_dressing` 只为每个 endpoint 生成 `planned_road_gateway`，当前固定保护入口点 `±4` 格；真实道路后写并拥有最终覆盖权。
- 输出规范化语义 DecorationProgram intent、只含 concrete prefab 的 compiled program、slot projection、planning trace、style resolution trace、quality report 和按 program 裁切的意图预览；不注册结构，不注册 RoadWeaver endpoint。
- 全部产物成功写完后最后写 `city_decoration_planning_complete.json`：`schemaVersion=city_decoration_planning_complete.v0.2`，含 `cityId`、`catalogHash`、`styleProfileId`、`styleProfileHash`、`completedAt`。
- `city_execute_d5` 先按完整连续 pattern 投影冻结 run / slot outcome / foundation；worldgen chunk compiler 消费同一快照并做局部复检，多方块 prefab 使用统一 pose datum。
- `dressingBrushPlan`、`dressingLayoutItems[]` 或 v0.1 artifact 进入 v0.2 时 hard fail，不自动兼容。

返回 artifact：

- `decorationProgramPlan`
- `compiledDecorationProgramPlan`
- `slotProjection`
- `planningTrace`
- `styleResolution`
- `qualityReport`
- `decorationPreviewIndex`
- `planningComplete`
- `artifacts`

常见 reason code：

- `CITY_DECORATION_PROGRAM_PLAN_REQUIRED`
- `CITY_DECORATION_PLAN_INCOMPLETE`
- `CITY_DRESSING_LEGACY_SCHEMA_REMOVED`
- `CITY_DECORATION_SHAPE_TYPE_UNSUPPORTED`
- `CITY_DECORATION_SHAPE_FIELD_UNSUPPORTED`
- `CITY_DECORATION_PATTERN_TYPE_UNSUPPORTED`
- `CITY_DECORATION_PATTERN_FIELD_UNSUPPORTED`
- `CITY_DECORATION_CONTENT_REF_UNKNOWN`
- `CITY_DECORATION_CATALOG_HASH_MISMATCH`
- `CITY_DECORATION_STYLE_PROFILE_UNKNOWN`
- `CITY_DECORATION_STYLE_PROFILE_HASH_MISMATCH`
- `CITY_DECORATION_STYLE_SEMANTIC_REF_UNKNOWN`
- `CITY_DECORATION_PREFAB_ENTITY_NBT_FORBIDDEN`
- `CITY_DECORATION_TARGET_AREA_EMPTY`
- `CITY_DECORATION_TERRAIN_SLOT_SKIPPED`
- `CITY_DECORATION_COLLISION_CONFLICT`

## city_plan_d4_structure_cluster_groups / city_select_d4_structure_cluster_group

`city_plan_d4_structure_cluster_groups` 必填参数：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `templateCatalogSource`
- `designSlotPlan`

可选参数：

- `groupCount`，默认 5。
- `candidatesPerSlot`，默认 5。
- `beamWidth`，默认 `groupCount * candidatesPerSlot`。

语义：

- 读取与 D4 v2 session 相同的 `DesignSlotPlan`。
- 这是显式调试 / 整城构图实验入口，不是 workflow 默认路径；正式默认是 `city_run_workflow d4CandidateMode=blueprint`。
- 内部复用顺序候选 session 的 `planNext/selectSession/finalizeSession` 规则做 beam search；每扩展一个 slot，就用 fixed-template exact body + clearance collision 冻结 occupied。
- 只输出完整组；若无法生成任何完整非重叠组，返回 `D4_STRUCTURE_CLUSTER_GROUP_UNSATISFIED`。
- 输出 `structure_cluster_group_candidate_set.json`、`structure_cluster_group_candidates.png`、`quality_report.json`。
- `structure_cluster_group_candidates.png` 是给 AI 选择用的主图：一种颜色代表一整组候选，点标签是 slot 简写，不绘制 bbox / mask / collision envelope。bbox 仍保留在 JSON 里供 debug 和验证使用。
- 每个 `groupCandidates[]` 内含 `items[]`、`groupCollisionEnvelope` / `groupMaskEnvelope`、`scoreBreakdown`、`risks[]` 和 `expandedStructureAnchorPlan`。

`city_select_d4_structure_cluster_group` 必填参数：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `templateCatalogSource`
- `groupCandidateId`

可选参数：

- `structureClusterGroupCandidateSetSource`，形如 `{ "candidateSetPath": "..." }` 或 `{ "structureClusterGroupCandidateSetPath": "..." }`；未传时读取当前 run/city 默认产物。

语义：

- 读取 `structure_cluster_group_candidate_set.json`，按 `groupCandidateId` 找到整组候选。
- 取该组 `expandedStructureAnchorPlan` 调用标准 `city_plan_d4`，输出 `structure_anchor_plan.json`、`structure_anchor_map.json`、`structure_anchor_preview.png` 等标准 D4 artifact。
- 后续 D5/D6/D7 不需要知道候选层存在。

## city_create_d4_candidate_session / city_plan_d4_next_candidates / city_select_d4_candidate / city_finalize_d4_candidate_session

D4 v2 推荐使用顺序候选 session：

```text
city_create_d4_candidate_session
city_plan_d4_next_candidates
city_select_d4_candidate
... repeat until all slots selected ...
city_finalize_d4_candidate_session
```

`city_create_d4_candidate_session` 必填参数：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `templateCatalogSource`
- `designSlotPlan`

可选：

- `sessionId`

`city_plan_d4_next_candidates` 必填参数：

- `runId`
- `citySeedId`

语义：

- 每次只返回当前 `currentSlotId` 的候选。
- 候选基于 session 中已经冻结的 `selectedAnchors[]` / `occupiedEnvelopes[]` 重新生成。
- slot 只提交 `templateId/templateIds` 与显式 `variantId`；服务端从 session 冻结的 `templateCatalogSource` 读取 hash、rawSize、入口和 clearance。TerraSense 只提供语义标签，不自动发现 companion catalog。
- 返回 `slot_candidate_set.json`、`anchor_candidate_preview.png`、`d4_candidate_session_trace.json`。
- `anchor_candidate_preview.png` 必须叠加 D3 patch member-cell 底图；已冻结 anchor 用 `S1/S2...` 标注，当前 slot 候选用 `C1/C2...` 标注，候选完整 id / score / role 放入右侧 legend，避免把同一 slot 的多个候选重叠误读为最终落地重叠。

`city_select_d4_candidate` 必填参数：

- `runId`
- `citySeedId`
- `slotId`
- `candidateId`

可选：

- `sessionId`
- `anchorId`
- `selectionReason`
- `quickPreflight`

语义：

- `slotId` 必须等于当前 session `currentSlotId`，否则返回 `D4_SLOT_ORDER_VIOLATION`。
- 选择成功后冻结 `estimatedCollisionEnvelope` 作为 `occupiedEnvelopes[].blockBounds`；后续 slot 候选必须避开该 collision envelope，不再写入 `estimatedSafetyEnvelope`。
- 本轮 `quickPreflight` 只记录请求，返回 `quickPreflightStatus=deferred_to_d6`；当前世界 NBT identity 与 exact geometry 复核仍由 D6 负责。
- 每次 selection 会累计 `agentThinkTimeMs`。

`city_finalize_d4_candidate_session` 必填参数：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `templateCatalogSource`

可选：

- `sessionId`

语义：

- 必须所有 placementOrder slot 都已选择，否则返回 `D4_SESSION_NOT_FINALIZABLE`。
- finalize 会把 session `selectedAnchors[]` 转换为标准 `StructureAnchorPlan`，并调用现有 D4 hard validation。
- 输出 `structure_anchor_plan.json`、`structure_anchor_map.json`、`structure_anchor_preview.png`、`d4_design_time_report.json`。
- `structure_anchor_preview.png` 同样必须叠加 D3 patch 底图，用于复核最终 anchor 与 patch / 水岸 / 山脊 / 崖壁等地形关系。

新增 artifacts：

- `d4_candidate_session.json`
- `slot_candidate_set.json`
- `d4_candidate_session_trace.json`
- `d4_design_time_report.json`

`d4_design_time_report.json` 至少包含：

- `totalWallClockMs`
- `toolRuntimeMs`
- `agentThinkTimeMs`
- `stepTimings[]`
- `failureReasons`

## city_plan_d4_candidates / city_select_d4_candidates

`city_plan_d4_candidates` 必填参数：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `templateCatalogSource`
- `designSlotPlan`

语义：

- 这是 v0.1 debug batch path；active 推荐路径是 D4 v2 session。
- 返回 `planningMode=all_slots_tentative_order_debug`。
- `slotId` / `displayRole` 只表示本次设计槽位，不是 City 全局功能枚举。
- `candidatePatchRefs` 始终只是候选搜索依据。未传 `patchSelectionRef` 时沿用既有 D4 grid / patch / collision 行为；传入并验证选择凭证后，服务端内部注入的 `candidateLegalRegion` 是候选 `collisionEnvelope` 的额外硬边界，任何调用方手写同名字段均拒绝。D6 actual footprint 校验仍是后续物化硬门，不取代此处 D4 候选约束。
- slot 只使用 `templateId` 或 `templateIds[]`，并显式指定 `variantId`；旧 `structureId(s)` 返回 `CITY_CONFIGURED_STRUCTURE_FLOW_REMOVED`。
- 每个 slot 默认输出最多 5 个候选，候选包含 `candidateKind`、`anchorBlock`、`estimatedCollisionEnvelope`、`estimatedMaskEnvelope`、`scoreBreakdown`、`placementReason`、`risks`。
- `candidateId` 在同一 slot 内稳定且唯一，用于 `city_select_d4_candidates` 精确回选。
- `distanceBand` 首版固定为 `near=32-96`、`medium=96-224`、`far=>224` blocks；`targetAnchorId` 只引用已选 anchor，`targetSlotId` 只作为软提示。

返回 artifact：

- `designSlotPlan`
- `anchorCandidateSet`
- `anchorCandidatePreview`
- `qualityReport`
- `sourceD3Package`

`city_select_d4_candidates` 必填参数：

- `runId`
- `citySeedId`
- `terrasenseProfileSource`
- `templateCatalogSource`
- `anchorSelectionPlan`

可选：

- `anchorCandidateSetSource`，形如 `{ "candidateSetPath": "..." }`；未传时读取当前 run/city 默认候选产物。

语义：

- 读取 `anchor_candidate_set.json`，把 `selectedCandidates[]` 转换为标准 `StructureAnchorPlan`。
- 转换后立即复用 `city_plan_d4` 的硬校验与 artifact 输出；后续 D5/D6/D7 不需要知道候选层存在。
- 旧 `patchGroupPlan`、`functionType`、`functionTag`、`function_candidates` 等字段同样必须失败：`LEGACY_CITY_FUNCTION_ZONE_FLOW_REMOVED`。

## city_plan_d5 / city_execute_d5

`city_plan_d5` 无 AI payload，只读取 D3 / 最终 D4 artifact；D4 design loop state 不能作为正式输入。

返回 artifact：

- `reservationMaskPlan`
- `wallReservationPlan`
- `roadAccessPlan`
- `buildOperationPlan`
- `reservationMaskPreview`
- `wallReservationPreview`
- `qualityReport`
- `sourceStructureAnchorMap`

可选参数：

- `wallVersion=v3|v2|v1_debug`，默认 `v2`；`v3` 生成结构种子 patch region hull，`v2` 生成 D3 patch 贴边 wall reservation，`v1_debug` 保留旧矩形调试墙。
- `wallMarginBlocks`，默认 24。
- `segmentLengthBlocks`，默认 15。
- `wallCorridorHalfWidthBlocks`，默认 4。
- `wallBreathingRoomBlocks`，v3 默认 24。
- `patchExpansionMaxRounds`，v3 默认 4。
- `concavityOpeningMaxBlocks`，v3 默认 64。
- `concavityDepthRatioMin`，v3 默认 0.6。

`city_execute_d5` required：

- `runId`
- `citySeedId`
- `confirmWorldMutation=true`

可选：

- `roadProvider=auto|roadweaver|worldedit_debug|none`，默认 `auto`。

执行语义：

- 必须已存在完整 D6 locked `structure_materialization_plan.json`；每项必须有固定 template identity、`actualFootprint`、`lockedActualFootprint`、`lockedCollisionEnvelope`、`maskEnvelope`、`ownerChunks[]`、`terrainPosePolicy=structure_start_beard_thin` 与 `templateDatumPolicy=generator_base_height_motion_blocking_no_leaves`。出现 `pieceBoxes`、signature、bbox group 或 envelope sample 时按旧 configured artifact 拒绝。
- `city_decoration_compiled_program_plan.json` 与 `city_decoration_planning_complete.json` 必须同时存在；缺一返回 `CITY_DECORATION_PLAN_INCOMPLETE`。两者均不存在时按 dimension + city 注销旧 active decoration plan。
- `city_dressing_<citySeedId>/` 中的 v0.1 artifact 必须显式拒绝 `CITY_DRESSING_LEGACY_SCHEMA_REMOVED`，不得参与激活或跳过判断。
- 激活 server-root `geomantia_city_masks/active_reservation_mask_plan.json`。
- `city_land_use_area_plan.json`、`city_land_use_surface_print_plan.json` 与 `city_land_use_planning_complete.json` 必须共同校验当前 schema、city、area hash、surface hash、ruleProfileHash 与 sourceD6Hash；缺 SurfacePrintPlan 返回 `CITY_LAND_USE_SURFACE_PRINT_PLAN_MISSING`，schema 不是 v0.2 明确拒绝。LandUse 产物均不存在时按 dimension + city 注销 active plan。旧 completion、active registry 和 ledger 不读取、不迁移，升级前必须清理并重规划。几何区域不得自动复制为全域植被 mask。
- LandUse activation 前先由当前 AreaPlan + SurfacePrintPlan 编译 owner fragment，只读检查实际包含 surface 或 boundary 操作的 owner；微整地 mask 只是 surface 操作的上下文，不能单独令 owner relevant，`PRESERVE + OPEN` 等零写入区域不进入预检。任一待写 owner 的 loaded / disk chunk 已到 FEATURES 返回 `CITY_LAND_USE_CHUNK_ALREADY_AT_FEATURES`，region NBT 读取失败或状态未知返回 `CITY_LAND_USE_CHUNK_STATUS_UNKNOWN`；不得申请 chunk ticket、加载或生成目标 chunk，且整体预检通过前不得改 active registry。
- decoration compiled plan、slot projection、completion 完整存在时，D5 必须校验 projection 的 schema / city / catalog / program / slot 身份，并与 compiled plan 的确定性投影逐项一致。随后每个有 slot 的 program 以实际 slot min/max 包络额外进入该 active plan 的 `noVegetationMask` 和 `noVanillaStructureMask`，两者均为 `maskType=decoration_projection`；前者抑制植被，后者阻止普通原版 / 模组结构起始。不得扩大为整块 patch；分别返回 `decorationVegetationMaskCount`、`decorationStructureMaskCount`。
- `cross_section_repeat` / `parallel_rows` 必须在 activation 使用目标 `ServerLevel` 的 `ChunkGenerator.getBaseHeight/getBaseColumn` 编译完整 run；不得加载 / 生成 chunk。缺 level 返回 `CITY_DECORATION_TERRAIN_SAMPLER_LEVEL_REQUIRED`。同一 frozen plan 写 D5 artifact 并进入 active registry。
- 同步激活 `active_planned_structure_registry.json`，registry 只写固定 template identity、三层几何、owner chunks 和冻结的 terrain policy。
- hook 不可用 hard fail：`CITY_MASK_HOOK_UNAVAILABLE` / `CITY_WORLDGEN_STRUCTURE_HOOK_UNAVAILABLE`。
- active path 不执行 `build_operation_plan.json`，返回 skipped / deferred 的 `worldMutationReport`，避免提前生成目标 chunk。
- RoadWeaver 存在且 `roadProvider=auto|roadweaver` 时，D5 生成 `city_roadweaver_connection_plan.v0.2` 并反射调用 `RoadNetworkApi.registerStructureEndpoint` / `ensureConnection(..., generateImmediately=false)`。计划固定使用 `connectionStrategy=group_spatial_mst`：先按 D4/D6 `placementGroupId` 对组内真实入口生成 Manhattan 距离最小生成树，再从每对 group 的最近真实入口候选生成组间最小生成树；不得按局部 priority 把不同功能区交替串成全城长链。顶层报告 `placementGroupCount`、`intraGroupConnectionCount`、`interGroupConnectionCount`，连接项报告 `connectionScope`、两端 group 与 `distanceBlocks`。worldgen 先由 LandUse v0.2 直接消费冻结 FIELD / CHANNEL role spans并写 FIELD-only CROP / channel-aware BOUNDARY，再执行稀疏 Decoration，最后由 RoadWeaver 真实道路后写；道路拥有最终地表覆盖权。
- RoadWeaver 缺失且 `roadProvider=roadweaver` 时 hard fail `ROADWEAVER_UNAVAILABLE`。
- RoadWeaver 缺失且 `roadProvider=auto` 时跳过道路并写入 `road_provider_state.json`，状态为 `skipped` / `ROADWEAVER_UNAVAILABLE` / `useWorldEditDebugFallback=false`。
- 只有显式 `roadProvider=worldedit_debug` 时才允许 D7 WorldEdit debug fallback。
- 响应包含 `activePlannedStructureCount`、`plannedStructureRegistryPath`、`worldgenPlacementMode=true`、`decorationVegetationMaskCount`、`requiresLockedMaterializationPlan=true`、`roadPlanningStage=d7_after_worldgen_ledger`、`roadProvider`、`roadWeaverAvailable`。

返回 artifact 增加：

- `roadWeaverConnectionPlan`
- `roadWeaverRegistrationReport`
- `roadProviderState`
- `frozenDecorationTerrainPlan`
- `decorationTerrainActivationTrace`
- `decorationActivationPreviewIndex`

## city_plan_d6

必填参数：

- `runId`
- `citySeedId`

可选：

- `dimensionId`
- `playerName`

不得传旧 `terrasenseProfileSource`、`structureChoicePlan`、`fixedPlacementSelectionPlan`、`plannedFixedPlacementMap`、`structurePoolMap`。

返回 artifact：

- `structureMaterializationPlan`
- `placedStructureLedger`
- `structureMaterializationTrace`
- `inferredFunctionAreaMap`
- `structureMaterializationPreview`
- `qualityReport`

未生成 chunk 时 response 为 `status=planned_worldgen` / `reasonCode=WAITING_FOR_WORLDGEN`；这不是结构失败。

chunk 已经生成到 `FEATURES` 或之后且没有 ledger 时，返回 `STRUCTURE_CHUNK_ALREADY_GENERATED`，不得继续走 active placement。

D6 使用当前世界 `StructureTemplateManager` non-mutating 重新读取 NBT，校验 template hash、rawSize、rotation、mirror、exact footprint、collision、mask 和 owner chunks。输出只保留 `locked=true`、固定 template identity、`actualFootprint`、`lockedActualFootprint`、`lockedCollisionEnvelope`、`maskEnvelope`、`ownerChunks[]` 与冻结 terrain policy；不创建或探测 `StructureStart`。

D6 trace 记录 NBT identity 复核、变换、`actualFootprint`、`lockedCollisionEnvelope`、`maskEnvelope` 和 owner chunks。任何 identity 或几何漂移 hard fail；尤其不得把 collision 覆写成裸 footprint。

## city_plan_land_use

必填参数：

- `runId`
- `citySeedId`

可选参数：

- `landUseIntentPlan`：严格 `city_land_use_intent_plan.v0.3`；完整字段见 `../数据契约/CityLandUseAreaPlan数据契约.md`。省略时使用 policy 内置 fallback；不同城市应在本次请求的 `surfaceAlgorithmDefaults[]` 传入各自材料。

语义：

- 必须已有 D3 `land_use_terrain_field.json`、最终 D4 provenance、D5 轻量预案和 D6 locked `structure_materialization_plan.json`。
- 显式 group / array / composite group 作为一个竞争主体，未分组 anchor 各自成为主体；最终 footprint 排除只认 D6 locked plan。
- `landUseIntentPlan` 只能指定稳定 group / anchor、`ruleRef`、算法级运行时材料默认和 group 例外；不得提交面积、行动力、成本、64 格连接阈值、逐 block 路径或 mask。`algorithmAnchor` 是唯一允许的可选 block 坐标，只用于 `contour_bands` 平地回退和相位基准，不定义区域边界。
- 调用只做规划与 artifact 写入，不加载 chunk、不写世界、不激活 registry。独立调用本身视为显式规划，不受 workflow 默认关闭影响。
- RoadWeaver 最终路线不进入本接口的几何猜测；真实道路后写并可覆盖 LandUse surface。

返回 artifact：

- `landUseTerrainField`
- `landUseAreaPlan`
- `landUsePlanTrace`
- `landUsePreview`
- `qualityReport`
- `planningComplete`

固定输入、rules version 和 seed salt 必须生成相同 `planHash`、spans、boundary loops 与 claim trace。未知 target / `ruleRef`、group 成员冲突、city 不一致或 D6 未锁定必须 hard fail；仅无法自动解析的结构语义可 warning 并跳过该主体。

## city_execute_d7

必填参数：

- `runId`
- `citySeedId`

可选：

- `executeStructurePlacement`，默认 false。
- `dimensionId`
- `playerName`

语义：

- `executeStructurePlacement=false`：只查看 worldgen ledger / 当前 chunk 状态。
- `executeStructurePlacement=true`：正式路径仍只查看 worldgen ledger / 当前 chunk 状态，不 late paste。
- 当所有 planned structures 都有 ledger 时，若 RoadWeaver 已注册，D7 不再覆盖 RoadWeaver 道路；若显式 `worldedit_debug`，D7 基于 ledger 真实 `actualFootprint` 生成调试道路 / 边界后处理，避障使用 `actualFootprint + roadAvoidanceMarginBlocks`，默认 3；若 `auto` 缺 RoadWeaver，则跳过道路并报告 `ROADWEAVER_UNAVAILABLE`。
- `debugLateMaterialize` 已删除；传入时返回 `CITY_CONFIGURED_STRUCTURE_FLOW_REMOVED`，不会执行任何 late paste。

返回 artifact：

- `placedStructureLedger`
- `structureMaterializationTrace`
- `inferredFunctionAreaMap`
- `placedStructurePreview`
- `qualityReport`
- `sourceStructureMaterializationPlan`

响应 / report 增加：

- `roadPostprocessSource=worldgen_ledger_actual_footprint`
- `roadAvoidanceMarginBlocks`
- `roadBlockedByStructureCount`
- `boundarySource=actual_footprint_union`
- `roadProviderState`
- `terrainAdaptationReport`

## city_query_worldgen_observations

必填参数：

- `dimensionId`
- `chunkX`
- `chunkZ`

可选参数：

- `phase=post_features|post_retry_tick|chunk_save`
- `limit=1..100`，默认 10
- `includeBlocks`，默认 true

非法 dimension、phase 或 limit 必须拒绝，不得静默改写。语义：只读取 server-root `geomantia_city_masks/worldgen_block_observations/.../chunk_<x>_<z>.jsonl`、尚未刷盘的 observation 队列和当前内存中的待 save 检查标记。不得读取 region NBT，不得申请 ticket，不得加载或生成 chunk，不得修改世界。

完整字段与 ledger/现场证据边界见 [CityWorldgenBlockObservation 数据契约](../数据契约/CityWorldgenBlockObservation数据契约.md)。

## city_plan_city_walls / city_execute_city_walls

`city_plan_city_walls` 必填参数：

- `runId`
- `citySeedId`

可选：

- `wallVersion=v3|v2|v1_debug`，默认 `v2`。
- `wallBoundaryMode=structure_seeded_patch_region_hull`，v3 兼容字段。
- `wallMarginBlocks`，默认 24。
- `segmentLengthBlocks`，默认 15。
- `gateWidthBlocks`，默认 9。
- `roadScanMarginBlocks`，默认 8。
- `roadProtectionMarginBlocks`，默认 2。
- `maxFoundationDepthBlocks`，默认 8。
- `maxSegmentHeightDeltaBlocks`，默认 7。
- `gateClusterRadiusBlocks`，v3 默认 24。
- `terrainFitUnitLengthBlocks`，v3 默认 5。
- `wallTerrainPolicy=v3|v3.1`，v3 城墙执行层地形策略，默认 `v3`。
- `wallDesignPolicy=v3|v3.2|v3.3`，v3 城墙规划层设计策略，默认 `v3`；`v3.2` 启用天然边界、道路趋势开门、独立 gatehouse 和可用塔节点；`v3.3` 增加近路投影开门。
- `minGateSpacingBlocks`，v3.2 / v3.3 城门最小间距，默认 48。
- `minGateRoadLengthBlocks`，v3.2 / v3.3 道路趋势最小长度，默认 24。
- `roadProjectionMaxDistanceBlocks`，v3.3 近路投影开门最大距离，默认 32。
- `naturalWaterBoundaryMinAreaBlocks`，v3.2 / v3.3 大片水体天然边界最小 patch 面积，默认 4096。
- `flatMaxDeltaBlocks`，v3.1 默认 7。
- `steppedMaxDeltaBlocks`，v3.1 默认 16。
- `mountainProbeDistanceBlocks`，v3.1 默认 6。
- `naturalBoundaryMinDeltaBlocks`，v3.1 默认 17。
- `embeddedSlopeTower`，v3.1 默认 true。

语义：

- 默认 `wallVersion=v2`，读取 D5 `wall_reservation_plan.json`、D7 `placed_structure_ledger.json` 和世界实际方块。
- `wallVersion=v3` 读取 v3 wall reservation 的 `cityDomainMask` / `outerWallRing`，对 actual road mask 进行 road component 分类，内部路不裁门，外部入城路按 cluster 裁门。
- `wallTerrainPolicy=v3.1` 不改变 v3 外环边界，只改变执行层地形策略：8-16 高差生成阶梯墙，高差更大时尝试嵌坡或标记天然峭壁边界。
- `wallDesignPolicy=v3.2` 不改变 v3 外环边界或 v3.1 地形策略，只改变规划层设计语义：大片水体 / shore / cliff 可生成 `natural_boundary` 段并跳过连续墙；外部道路必须满足趋势和长度才生成 `gatehouse`；贴墙 / 擦边 / 碎路进入 `roadTrendSkippedIntersections[]`；城门按 `minGateSpacingBlocks` 合并。
- `wallDesignPolicy=v3.3` 继承 v3.2；外部道路未真正穿墙但靠近墙体、距离不超过 `roadProjectionMaxDistanceBlocks` 且能投影到墙段时，生成 `WALL_GATE_FROM_ROAD_PROJECTION` gatehouse；内部道路仍不裁门，touch-only 碎路仍跳过。
- v2 扫描 wall corridor 附近 actual road mask，按 road-wall intersection 生成 `generatedGates[]`，墙段不得覆盖真实道路。
- `wallVersion=v1_debug` 才使用 v0.1 的 `actualFootprint` union 外扩矩形城墙。
- 输出 `actual_road_mask.json`、`city_wall_plan.json`、`city_wall_preview.png` 和 `city_wall_templates/*.nbt`。
- v3 / v3.1 的 `wallSegments[]` 必须带 `wallAxis=X|Z`，作为执行层拆 unit、生成阶梯切片、判断墙体厚度和嵌坡方向的唯一主轴来源。
- v3.2 的 `wallSegments[]` 允许出现 `segmentType=gatehouse` 和 `segmentType=natural_boundary`；`gatehouse` 使用 `gatehouse_9` / `gatehouse_13`，`natural_boundary` 使用 `natural_water_boundary` / `natural_cliff_boundary` 空模板作为 artifact 标记，不放连续墙。
- v3.3 的 `city_wall_plan.json` 额外包含 `projectedRoadGateCandidates[]`、`roadProjectionSkippedIntersections[]` 和 `roadProjectionMaxDistanceBlocks`；没有直接门或投影门时，fallback 原因为 `NO_VALID_GATE_CANDIDATE_AFTER_FILTER`。

返回 artifact：

- `cityWallPlan`
- `actualRoadMask`
- `cityWallPreview`
- `cityWallTemplateDirectory`
- `sourcePlacedStructureLedger`

`city_execute_city_walls` 必填参数：

- `runId`
- `citySeedId`
- `confirmWorldMutation=true`

可选：

- `dimensionId`
- `playerName`
- `debugScan`，v3 调试开关，默认 false。
- `debugScanStepBlocks`，默认 1。

语义：

- 使用 `city_wall_plan.json` 放置临时石砖城墙、可用塔节点、gate gap 或 v3.2 独立 gatehouse。
- 后端为 `vanilla_setblock`，不依赖 WorldEdit。
- 默认 v2 硬保护 `actualRoadMask`、gate gap 和 structure `actualFootprint`，不覆盖 RoadWeaver 道路或建筑。
- v3 按 `wallAxis` 和 `terrainFitUnitLengthBlocks` 把墙段拆成小 unit，按 unit/column 采样地形，输出 `placementUnitResults[]` 与 `terrainFitMode`，避免因局部高差整段消失；执行层不得用拆碎后的 unit 长宽反推朝向。
- `wallTerrainPolicy` 从 `city_wall_plan.json.terrainFitPolicy.policyVersion` 读取；`v3.1` report 额外输出 `terrainPolicyVersion`、`terrainDeltaBand`、`stepSlices[]`、`mountainProbe` 和 debug sample 的 `policyDecision`。
- `segmentType=natural_boundary` 必须跳过连续墙并在 gap debug 中说明 `NATURAL_WATER_BOUNDARY` / `NATURAL_CLIFF_BOUNDARY`；`segmentType=gatehouse` 必须清出完整门洞并放置石木混合门楼。
- `debugScan=true` 时输出 `wall_terrain_debug_scan.json`、`wall_mask_conflict_report.json`、`wall_gap_debug_report.json`，用于手工 TP 复核缺口原因。

返回 artifact：

- `cityWallPlan`
- `cityWallPlacementReport`
- `wallTerrainDebugScan`
- `wallMaskConflictReport`
- `wallGapDebugReport`

## 推荐调用流程

```text
city_run_workflow {
  runId,
  citySeedId,
  terrasenseProfileSource,
  templateCatalogSource,
  designSlotPlan,
  patchScanPaddingBlocks: 128,
  skipExisting: true,
  d4CandidateMode: "key_then_array",
  confirmWorldMutation: false
}
检查 d4_staged_plan.json / d4_staged_trace.json 和 structure_anchor_map.json
city_run_workflow { 同上, confirmWorldMutation: true, roadProvider: "auto" }
若 status=waiting_for_worldgen，按 D7 trace / workflow report TP 到目标 chunk 外侧加载
city_run_workflow { 同上, confirmWorldMutation: true, roadProvider: "auto", planWalls: true, executeWalls: true }
```

真实执行如果返回 `WAITING_FOR_WORLDGEN`，从目标 chunk 外侧靠近 / TP 触发 chunk 首次生成；生成后重复 `city_execute_d7 { executeStructurePlacement: true }` 查询 ledger。若返回 `STRUCTURE_CHUNK_ALREADY_GENERATED`，说明该 chunk 已错过生成期，正式路径不得补贴结构。
