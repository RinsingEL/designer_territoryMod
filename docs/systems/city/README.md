# City 系统文档入口

City 系统承接 T 阶段输出的 `CitySeedRegistry` / `CitySiteCandidate`，在城市候选范围内生成可 review、可验证、可真实落地的城市结构规划。

## 当前 Active 主线

当前 City D3-D6 已按破坏性重构切换为：

```text
D3 地形 patch 真值
  -> configured structure envelope profiling
  -> D4 key_then_array 分阶段主流程（关键结构逐个定锚 / 冻结 occupied，再按阵列填充批量结构）
  -> 可选 D4 v2 顺序候选 session（逐 slot 生成 / 选择 / 冻结）
  -> 可选 D4 结构群整组候选 / 整组选定（整城构图调试路径）
  -> 可选 D4 阵列候选组（批量结构候选组，输出标准 StructureAnchorPlan）
  -> 可选 D4 阵列布局 loop v0.3（composite_array 父分区 / subZones / child arrays）
  -> D4 StructureAnchorPlan / StructureAnchorMap
  -> city_plan_d5 轻量 reservation mask 预案（只读最终 D4 collision + maskMargin，含 D3 patch 贴边 wall reservation）
  -> city_plan_d6 planned_worldgen probe-and-lock（锁定 actualFootprint / pieceBoxes / lockedCollisionEnvelope）
  -> 可选 plan_city_dressing 校验 DecorationProgram v0.2、按 style profile 将语义内容解析为 prefab、冻结 content / style hash 并生成意图预览
  -> 可选 city_probe_decoration_terrain 只读已加载真实地形、人工审阅高度 / 连续带 profile / 未加载覆盖
  -> execute_d5 以 D6 locked collision 激活 active mask / planned structure 生成期注册 / 装饰 worldgen 程序
  -> Minecraft worldgen createStructures 阶段写入 StructureStart
  -> city_execute_d7 查询 worldgen ledger
  -> 根据已落结构 ledger 反推 inferred function area
  -> RoadWeaver 道路；旧 debug 道路仅允许显式 `worldedit_debug`
  -> city walls v2/v3/v4/v5 扫描真实道路并规划 / 放置城墙
```

### 当前主线模板建筑迁移状态

在 City active 主建筑范围内，当前主路径已锁定为 `StructureTemplate` NBT：D2 读取模板目录与 NBT 尺寸 / hash，D4 选择并冻结 `templateRef`、`templateHash`、`variant`、`rotation`、`mirror`、`footprint`，D5 可通过 City 自己的 active template placement registry 交接到 worldgen；模板建筑不查询 `Registries.STRUCTURE`、不生成 `StructureStart`、不使用 Jigsaw pool。

D2 / D4 / D6 / D7 对同一建筑必须携带同一模板 identity 和 footprint。D5 的 RoadWeaver 注册只使用模板 transformed `roadEntrances[]`，不使用 bbox 外侧伪入口；缺 mod 时 `auto` 跳过、`roadweaver` hard fail，旧 debug road 仅在显式 `worldedit_debug` 下可用。既有 StructureStart / Jigsaw 主线文字继续保留作历史信息和历史测试保护，不作为模板建筑 active 解释。

`city_run_workflow` 是当前调试 / 验收快跑入口，用于串联上述阶段、记录每步耗时和暂停原因；它不改变单步接口的真值，也不允许绕过 worldgen-time placement 或 D5/D7 状态检查。

城墙 v0.2 仍是默认兼容口径；v0.3 已接入显式 `wallVersion=v3` 开发路径，从结构 actualFootprint / sourcePatch 出发生成城市外环 hull，填掉凹陷和内部道路口袋，并增加 step=1 地形 / mask debug 扫描。`wallTerrainPolicy=v3.1` 是 v3 的执行层地形策略，用于把 8-16 高差转成阶梯墙、更大高差转成嵌坡或天然峭壁边界；`wallDesignPolicy=v3.2/v3.3` 是 v3 的规划层设计策略，用于把大片水体 / 峭壁转成天然边界、按道路趋势或近路投影生成独立 gatehouse、限制城门密度并使用可用 5x5 塔节点。`wallVersion=v4` 是当前新增测试路径：D5 仍产出 reservation/mask 上下文，D7 ledger 后以 `actualFootprint` 为硬约束生成 `actual_footprint_land_ring` 墙图，并用 D5 `cityDomainMask` 的 cell 外缘做小幅 `terrain_adaptive_domain_guided_land_ring` 轮廓适配；输出 `wallNodes[]`、`wallUnits[]`、`nodeConnectorUnits[]`、`cityWallDatumY`、`terrainContourEvents[]` 和 `wallGraphValidation`，并对连续水体做陆侧退避、对高度差生成 stepped/terrace connector。`wallVersion=v5` 是显式实验路径：必须从 D5 v5 reservation 开始，D7 后只读取 D5 `wallLine` 做高度适配和落地 / 跳过判断；若前序 D5 不是 v5，`WALL_V5_REQUIRES_D5_V5_RESERVATION` 应 hard stop，不得自动退回 v4。

旧的“先画功能区再塞结构”主链不再是当前真值。active endpoint 不再默认产出或消费：

- `function_zone_map.json`
- `buildable_area_map.json`
- `planned_fixed_placement_map.json`
- `structure_pool_map.json`
- `start_candidate_set.json`

旧 `FunctionZoneMap` / `BuildableAreaMap` / bounded jigsaw 多 start 面积补偿相关代码和文档只作为历史参考；如果旧 payload 或旧 artifact 进入 active endpoint，应返回 `LEGACY_CITY_FUNCTION_ZONE_FLOW_REMOVED`，不得静默兼容。

## 阅读顺序

1. `10_product/案子/README.md`
2. `10_product/案子/D3-D6结构落地驱动城市重构-v0.1/README.md`
3. `20_contracts/数据契约/结构落地交接契约.md`
4. `20_contracts/接口契约/City调试MCP接口.md`
5. `30_code_guide/代码导览.md`
6. `40_tests/测试入口.md`

历史方案可读但不作为当前实现依据：

- `10_product/系统概述.md`
- `10_product/过程设计/C1-C4城市规划过程.md`
- `10_product/过程设计/C5-C8结构落地交接过程.md`
- `10_product/案子/城市构造流程-v0.1/README.md`
- `10_product/案子/C5锚点与保留区-v0.1/README.md`
- `10_product/案子/D6结构池规划-v0.1/README.md`
- `10_product/案子/D7条件包装结构生成-v0.1/README.md`
- `10_product/案子/D7剩余结构起点候选-v0.1/README.md`
- `10_product/开发计划-v0.2~v0.5-*`

已并入主线和后续待做的分阶段小案子：

- `10_product/案子/D4设计构图候选闭环-v0.1/README.md`：让 AI 提交城市结构 slot 和通用空间关系，程序按 D3 patch / envelope facts 生成少量安全候选点，避免 AI 直接手算 anchor。
- `10_product/案子/D4设计构图候选闭环-v0.2/README.md`：已完成并入主线；将 v0.1 批量候选升级为逐 slot session：每选定一个 anchor 后冻结 occupied set，再为下一个 slot 重新生成候选，降低 D6 才发现碰撞后的回退成本。`key_then_array` 的关键结构阶段复用该 session；v0.1 批量候选仅保留为 debug / 兼容入口。
- D4 key_then_array：`city_run_workflow` 默认路径；`placementStrategy=key_structure|single_ai_selected` 的关键结构必须先走逐 slot session，选中后冻结 occupied envelope；`placementStrategy=array_fill` 的填充结构随后逐组调用阵列候选，并读取上一阶段 `StructureAnchorMap` 避让已落结构。
- `10_product/案子/D4阵列布局AgentLoop-v0.2-v0.3/README.md`：D4 阵列布局同一版本线；v0.2 已接入显式阵列层开发路径，v0.3 已补 `composite_array` 嵌套阵列能力。AI 每轮仍只提交一个 `nextArrayLayoutPlanItem`，但该 item 可用 `childLayoutPlans[]` 描述父 zone 内的子阵列；程序同轮生成 parent zone、subZones、child zones、occupied field 和 preview。当前不切默认，需显式调用三段 endpoint 或 `d4CandidateMode=array_layout_loop_v0_3`。
- `10_product/案子/D4阵列候选选择闭环-v0.4/README.md`：已接入显式候选选择闭环：create 后常规外扩查询以已 Plan collision occupied 的 focus、方向和 target patch 划定外侧可用区；显式 `newFunctionalArea=true` 不需要这三项，先返回按容量 / 可用性排序的全局 patch 和入口，再由 `selectedGlobalPatchRef` 生成候选。候选不提交 state，整组选中才原子写 occupied / zones / 剩余空间；默认不自动选择，`composite_array` 父子区继续保留。当前不切默认。
- `10_product/案子/D4连续外扩候选-v0.5/README.md`：当前开发路径。常规外扩不预选 patch，改以父结构 D2 body / collision bbox、方向和目标实体间距产生近中远连续候选；D3 patch 后置用于地形筛选 / 评分，可跨 patch，近圈不可用才有原因地扩大搜索。
- D4 结构群整组候选：显式调试路径；读取同一 `DesignSlotPlan`，用顺序候选生成 / 选择规则做 beam search，一次输出多组完整 slot 落脚方案；预览图中颜色代表整组，不代表建筑或 slot，bbox 默认不画在主图里。
- `10_product/案子/City通用装饰阵列系统-v0.2/README.md`：当前装饰开发真值。`plan_city_dressing` 只接受 AI-facing `city_decoration_program_plan.v0.2`，首期只引用 D3 patch，并用 `type + params` Shape / Pattern 判别联合组合通用布局，程序再编译 member bounds / 世界坐标。含 offset 的 Pattern 从 Shape 局部起始边界计相位，不能受世界坐标或 chunk 边缘影响。`ContentPalette` 的 `contentRef` 是 `market_stall` 等风格语义键，`config/geomantia/city_decoration/styles/*.json` 才映射到 content index / templates 中的具体 prefab；规划冻结 `catalogHash` 和 `styleProfileHash`，worldgen 重载时两者任一漂移均拒绝旧计划。`city_probe_decoration_terrain` 是 activation 前人工审阅入口，只读已加载区块，输出每个槽位的地形覆盖、高度和线性阵列连续带 profile，不生成 chunk 或写世界。农田 / 水渠 / 石路使用 tile NBT；worldgen 每次回调只写当前 owner chunk 的 fragment，并先登记该 fragment 的植被 mask，跨 chunk 连续性由同一 program / seed / coordinate frame 保证，多方块 prefab 使用统一 datum。v0.1 七种业务 item 破坏性退场，不自动兼容。
- `10_product/案子/City装饰填充层Plan-v0.1/README.md`：历史参考；记录旧七种业务 item、提前展开 surface operation 和内置测试模板方案，不再作为 active 输入契约。
- `10_product/案子/结构Envelope精修-v0.1/README.md`：缩紧稳定结构 bbox，区分 actual / collision / mask。
- `10_product/案子/结构语义重标记-v0.1/README.md`：整理 TerraSense 结构语义白名单，不恢复 City 自建枚举。
- `10_product/案子/RoadWeaver结构连接-v0.1/README.md`：已接入 optional RoadWeaver adapter，D5 execute 阶段注册结构道路端点；`auto` 缺 mod 时跳过道路并标记 `ROADWEAVER_UNAVAILABLE`，旧 debug 道路只允许显式 `worldedit_debug`。
- `10_product/案子/结构地形兼容适配-v0.1/README.md`：已加入 terrain adaptation / Beardifier 诊断 trace，用于判断浮空等问题来源。
- `10_product/案子/城市边界与城墙-v0.1/README.md`：已加入 D7 ledger 后的临时城墙 plan / execute 闭环，输出石墙 NBT artifact。
- `10_product/案子/城市边界与城墙-v0.2/README.md`：已进入当前默认城墙口径，D5 早期生成 D3 patch 贴边 wall reservation mask，RoadWeaver 真实道路生成后扫描 actual road mask 并裁出城门，最后放墙 / 塔 / foundation；v0.1 矩形墙仅保留为 `wallVersion=v1_debug`。
- `10_product/案子/城市边界与城墙-v0.3/README.md`：已接入显式 `wallVersion=v3` 开发路径；从结构种子和 D3 patch 邻接图生成城市外环 hull，填充小凹陷 / 小洞 / 内部道路口袋，聚类外部道路裁门，并为墙体缺口输出 step=1 地形扫描、mask 冲突坐标和 gap debug report；`wallTerrainPolicy=v3.1` 增加阶梯墙 / 嵌坡 / 天然峭壁边界执行策略；`wallDesignPolicy=v3.2` 增加天然水体边界、道路趋势开门、独立门楼和可用塔节点。
- `10_product/案子/城市边界与城墙-v5/README.md`：草案；将城墙职责收紧为 D5 决定平面和 mask、worldgen 保护 corridor 并记录真实地表、D7 后城墙只做高度适配和落地判断；顶部“给下一个 AI 的短口径”是后续 agent 优先阅读的 v5 防跑偏说明。
- `10_product/案子/City结构风格化换皮-v0.1/README.md`：在结构真实落地后按国度 / 城市 palette 做材料主题化替换。

## 当前产物

| 阶段 | 当前产物 |
| --- | --- |
| D2 | `citySiteContext` |
| D3 | `city_landform_review_package.json`、`landform_review_map.png`；patch 含 `biomeSummary` 群系摘要 |
| envelope profiling | `structure_envelope_facts.json`、`structure_envelope_profile_preview.png`、`quality_report.json` |
| D4 design loop state | `city_d4_design_loop_<citySeedId>/d4_design_loop_state.json`、`d4_design_loop_occupied_field.json`、`d4_design_loop_function_zones.json`、`d4_design_loop_array_zones.json`、`d4_design_loop_patch_availability.json`、`d4_design_loop_next_ai_context_summary.json`、`d4_design_loop_execution_trace.json` |
| D4 staged workflow | `d4_staged_plan.json`、`d4_staged_trace.json`；关键结构阶段复用 D4 v2 session artifact，阵列阶段按 `arrayId` 输出独立阵列候选 artifact，最终仍写标准 `structure_anchor_plan.json` / `structure_anchor_map.json` |
| D4 structure cluster groups | `design_slot_plan.json`、`structure_cluster_group_candidate_set.json`、`structure_cluster_group_candidates.png`、`quality_report.json` |
| D4 candidates | `design_slot_plan.json`、`anchor_candidate_set.json`、`anchor_candidate_preview.png`、`quality_report.json` |
| D4 array candidates | `d4_array_candidate_plan.json`、`d4_array_candidate_set.json`、`d4_array_candidate_preview.png`、`quality_report.json` |
| D4 array layout loop | `city_d4_array_layout_<citySeedId>/d4_array_layout_plan.json`、`d4_array_layout_loop_state.json`、`d4_array_layout_execution_trace.json`、`d4_array_occupied_field.json`、`d4_array_patch_availability.json`、`d4_functional_array_zones.json`、`d4_array_layout_preview.png` |
| D4 array candidate selection v0.4 | 同一 loop 目录中的 `d4_array_expansion_space.json`、`d4_array_expansion_candidate_set.json`、`d4_array_expansion_candidates.png`、`d4_array_expansion_candidate_quality_report.json`；候选集含 `sourceStateId`、`arrayCandidates[]`、全局搜索时的 `globalPatchCandidates[]`，只有 select 后 loop state / occupied / zones 才改变 |
| D4 continuous outward v0.5 | 沿用 `d4_array_expansion_space.json` / `d4_array_expansion_candidate_set.json` / `d4_array_expansion_candidates.png`，新增 `d4_array_expansion_candidate_detail.png` 和 `structure_anchor_cluster_preview.png`；记录近 / 中 / 远候选、每圈跳过原因和命中 patch 解释。 |
| D4 | `structure_anchor_plan.json`、`structure_anchor_map.json`、`structure_profile_catalog.json`、`structure_anchor_preview.png`、`quality_report.json` |
| City decoration | `city_decoration_<citySeedId>/city_decoration_program_plan.json`、`city_decoration_compiled_program_plan.json`、`city_decoration_slot_projection.json`、`city_decoration_planning_trace.json`、`city_decoration_style_resolution.json`、`quality_report.json`、`city_decoration_preview_index.json`、多张 `city_decoration_preview_<programId>.png`，最后写 `city_decoration_planning_complete.json`；素材源为 server config 下 content index / templates，语义到 prefab 的映射来自同级 `styles/*.json` |
| D5 | `reservation_mask_plan.json`、`wall_reservation_plan.json`、`wall_reservation_preview.png`、`road_access_plan.json`、`build_operation_plan.json`、`reservation_mask_preview.png`、`quality_report.json`；road/build 为 D7 后处理占位 |
| execute_d5 | 激活 server-root `active_reservation_mask_plan.json`、`active_planned_structure_registry.json`、可选 `geomantia_city_masks/active_city_decoration_program_plans.json`，写跳过式 `world_mutation_report.json`、`active_mask_summary.json`、`active_city_decoration_summary.json`、`roadweaver_connection_plan.json`、`road_provider_state.json`；worldgen 成功片段另写 `geomantia_city_masks/city_decoration_worldgen_ledger.json` |
| D6 | `structure_materialization_plan.json`（`plannedWorldgenStructures[]`，含 locked actual footprint / bbox group / collision envelope / signature）、空 `placed_structure_ledger.json`、`structure_materialization_trace.json`、`inferred_function_area_map.json`、`structure_materialization_preview.png` |
| execute_d7 | `placed_structure_ledger.json`、`structure_materialization_trace.json`、`inferred_function_area_map.json`、`placed_structure_preview.png`，ledger 完整后生成 RoadWeaver-aware road report 与 terrain adaptation report |
| city walls | `actual_road_mask.json`、`city_wall_plan.json`、`city_wall_preview.png`、`city_wall_templates/*.nbt`、`city_wall_placement_report.json`；v3.2+ 额外要求 `gatehouse_9.nbt` / `gatehouse_13.nbt` / `watchtower_5x5.nbt` / `beacon_5x5.nbt`；v4 计划额外输出 `wallNodes[]` / `wallUnits[]` / `nodeConnectorUnits[]` / `cityWallDatumY` / `terrainContourEvents[]` / `wallGraphValidation` |
| workflow | `city_workflow_<citySeedId>/city_workflow_report.json`，记录 D3 -> D7 / 可选城墙阶段的时间戳、耗时、artifact、暂停 / 失败原因 |

## 上下游

| 方向 | 系统 | 交接内容 |
| --- | --- | --- |
| 上游 | 国度规划系统 | `CitySeedRegistry`、城市候选坐标、国度归属。 |
| 上游 | GIS / TerraSense | D3 地形 patch 真值、TerraSense `StructureProfile.jsonl` / debug catalog、TerraSense tag 白名单。 |
| 本系统 | City | 顶层 configured structure envelope facts、结构 anchor、locked actual footprint、reservation mask、planned structure registry、worldgen ledger、RoadWeaver endpoint plan、terrain trace、D3 patch wall reservation、actual-road gated wall boundary。 |
| 下游 | 世界生成 / Materialization | feature / vanilla structure 抑制 hook、planned structure worldgen hook、原版 `StructureStart` 生成期落地、ledger 与 trace。 |

## 目录说明

| 目录 | 内容 |
| --- | --- |
| `10_product/` | 当前方案、历史方案和开发计划。 |
| `20_contracts/` | 阶段输入输出、artifact、MCP/HTTP 参数和失败口径。 |
| `30_code_guide/` | Java / MCP 当前实现入口。 |
| `40_tests/` | 自动测试、真实游玩验收和调试图验收入口。 |
