# 06 SafetyEnvelope 退场验收卡

## 修改目的

将 `safetyEnvelope` 从 City 结构落地正式链路中退场。结构大小范围继续保留在 profile facts / debug 统计事实中，但正式 D4 / D5 / D6 / D7 artifact、registry、dressing 输入和 MCP 契约不再输出或消费 `safetyEnvelope`、`estimatedSafetyEnvelope`、`groupSafetyEnvelope`。

## 验收卡 1：D4 AnchorMap 不再输出 safetyEnvelope

### 验收目标

标准 D4 `structure_anchor_map.json` 的 `anchors[]` 只保留 `plannedFootprint`、`collisionEnvelope`、`maskEnvelope` 和 envelope profile 选择信息，不再输出 `safetyEnvelope`。

### 必须检查

- `CityStructureAnchorPlanner`
- D4 `structure_anchor_map.json`
- D4 anchor preview
- `CityStructureLandingFlowTest`

### 通过条件

1. `structureAnchorMap.anchors[]` 不含 `safetyEnvelope`。
2. `reservedEnvelope` 若仍保留兼容语义，必须等同或指向 `collisionEnvelope`，不得恢复旧 safety 语义。
3. D4 preview 不绘制 safety 层，不用灰色 safety 层暗示结构间距。
4. D4 测试不得再断言 `safetyEnvelope` 存在。

### 禁止事项

- 禁止把 `safetyEnvelope` 改名后继续作为 D4 anchor 正式边界输出。
- 禁止让 `maxObservedEnvelope` 直接进入 D4 hard collision 判断。

## 验收卡 2：D4 Candidate / Array 不再输出 estimatedSafetyEnvelope

### 验收目标

D4 候选点、阵列候选和 array layout loop 的 item 只输出 `estimatedCollisionEnvelope` 与 `estimatedMaskEnvelope`。结构尺寸波动只能通过 profile facts / bbox group / debug trace 表达。

### 必须检查

- `CityStructureCandidateEnvelope`
- `CityStructureAnchorCandidatePlanner`
- `CityStructureArrayCandidatePlanner`
- `CityStructureArrayLayoutLoopPlanner`
- `CityStructureClusterGroupCandidatePlanner`
- D4 candidate / array candidate / array loop artifact

### 通过条件

1. `slotCandidates[].candidates[]` 不含 `estimatedSafetyEnvelope`。
2. `arrayCandidates[].items[]` 不含 `estimatedSafetyEnvelope`。
3. `functionalArrayZones.arrayZones[]` 不含 `groupSafetyEnvelope`。
4. `occupiedEnvelopes[].blockBounds` 只来自 collision / body envelope。
5. collision 不重叠、旧 safety 可能重叠的结构仍可被 D4 放置。

### 禁止事项

- 禁止用 `estimatedSafetyEnvelope` 做过渡字段继续写进 JSON。
- 禁止用 `groupSafetyEnvelope` 给 dressing、roads 或 D5 提供区域依据。

## 验收卡 3：D5 / Mask 链路不消费 safetyEnvelope

### 验收目标

D5 reservation mask 只从 `collisionEnvelope + maskMarginBlocks` 派生 `maskEnvelope`，不读取、不继承、不信任任何 safety 字段。

### 必须检查

- `CityReservationMaskPlanner`
- D5 `reservation_mask_plan.json`
- D5 `active_mask_summary.json`
- D5 相关测试

### 通过条件

1. D5 输入里即使存在旧 `safetyEnvelope`，输出 mask 也不受其影响。
2. D5 `noVegetationMask`、`noVanillaStructureMask` 等结构保护 mask 由 `collisionEnvelope + maskMarginBlocks` 得到。
3. `maskMarginBlocks` 默认在 5 到 10 格范围内，当前默认 8 格可接受。
4. 测试覆盖旧输入带超大 `safetyEnvelope` 时，D5 mask 仍按 collision 小边距生成。

### 禁止事项

- 禁止用 `safetyEnvelope` 作为 D5 mask fallback。
- 禁止用 `vegetationMarginBlocks` 重新撑大结构间距。

## 验收卡 4：D6 / D7 / Registry 不再读写 safetyEnvelope

### 验收目标

D6 locked plan、planned structure registry、worldgen ledger 和 D7 placed artifact 不再输出 `safetyEnvelope`。真实落地阶段使用 `actualFootprint`、`lockedActualFootprint`、`lockedCollisionEnvelope`、`maskEnvelope` 和 `pieceBoxes`。

### 必须检查

- `CityStructureMaterializationPlanner`
- `CityReservationMaskRegistry`
- D6 `structure_materialization_plan.json`
- active planned structure registry
- D7 `placed_structure_ledger.json`
- D7 placed preview

### 通过条件

1. D6 `plannedWorldgenStructures[]` 不含 `safetyEnvelope`。
2. active planned structure registry 不含 `safetyEnvelope`。
3. D7 ledger / placed artifact 不含 `safetyEnvelope`。
4. `maskEnvelope` 由 `lockedCollisionEnvelope + maskMarginBlocks` 派生。
5. `pieceBoxes`、`actualFootprint`、`lockedActualFootprint` 继续保留，用于解释真实生成大小。

### 禁止事项

- 禁止为了兼容旧 artifact 在新输出中继续写 `safetyEnvelope`。
- 禁止把 `lockedCollisionEnvelope` 扩成旧 safety 范围。

## 验收卡 5：DecorationProgram 不再依赖 groupSafetyEnvelope

### 验收目标

City decoration 的 hard obstacles 只能来自结构 / 阵列的 collision、mask、actual footprint 或装饰自身策略，不得读取 `groupSafetyEnvelope`。

### 必须检查

- `CityDecorationProgramPlanner`
- `city_decoration_compiled_program_plan.json`
- `city_decoration_planning_trace.json`
- decoration planner / chunk compiler tests

### 通过条件

1. decoration 解析 array zone 时只使用 `groupMaskEnvelope` 或 `groupCollisionEnvelope`。
2. compiled plan、planning trace 和 hard obstacles 不含 `groupSafetyEnvelope`。
3. 装饰 body 不与结构 collision / locked actual footprint / road corridor 重叠。
4. 需要装饰缓冲时，由 conflict / content policy 声明 margin，不借 safety 字段。

### 禁止事项

- 禁止继续使用 `groupSafetyEnvelope` 生成 decoration hard obstacle。
- 禁止让 decoration margin 反向修改 D4 结构 anchor。

## 验收卡 6：Preview 不再显示 safety 层

### 验收目标

所有 D4 / D5 / D6 / D7 结构落地预览不再绘制 safety envelope。冲突颜色只代表 collision conflict。

### 必须检查

- `CityStructureLandingPreviewRenderer`
- D4 anchor preview
- D4 candidate preview
- D4 array layout preview
- D6 materialization preview
- D7 placed preview

### 通过条件

1. 图例不再出现 `safety`。
2. 红色冲突只表示 collision / body overlap。
3. mask 可以作为橙色或其他弱提示显示，但不得表现为结构间硬间距。
4. 若需要 profile debug overlay，字段名必须是 `diagnosticMaxObservedEnvelope` 或同类 debug 名称，且默认不作为主图冲突层。

### 禁止事项

- 禁止保留灰色 safety 外框作为默认显示层。
- 禁止在 label / legend 中继续使用 safety 解释结构间距。

## 验收卡 7：契约与 MCP schema 删除 safety 正式字段

### 验收目标

文档仓库与 MCP 工具说明不再把 safety 作为正式字段或诊断字段推荐使用；结构大小范围归入 profile facts。

### 必须检查

- `country_designer_mcp/src/realm/tools.ts`
- `docs/systems/city/20_contracts/接口契约/City调试MCP接口.md`
- `docs/systems/city/20_contracts/数据契约/结构落地交接契约.md`
- `docs/systems/city/30_code_guide/代码导览.md`
- `docs/systems/city/40_tests/测试入口.md`

### 通过条件

1. MCP 描述不再提 `estimatedSafetyEnvelope`、`groupSafetyEnvelope` 或 `safetyEnvelope` 作为输出字段。
2. 数据契约不再要求或推荐 D4/D5/D6/D7 artifact 输出 safety 字段。
3. 代码导览明确：正式结构边界只有 collision / mask，尺寸统计在 profile facts。
4. 测试入口明确新增无 safety 链路回归。

### 禁止事项

- 禁止写成 “safety 仅诊断保留”。
- 禁止把 `maxObservedEnvelope` 描述成新的规划边界。

## 验收卡 8：兼容旧输入但新输出无 safety

### 验收目标

为了避免旧 artifact 直接崩溃，读取层可以短期兼容旧 `safetyEnvelope` 输入，但任何新产物都不得继续输出 safety 字段。

### 必须检查

- D4 finalize
- D5 plan
- D6 plan
- execute_d5
- D7 ledger check
- 回归测试夹具

### 通过条件

1. 旧输入若带 `safetyEnvelope`，读取层不会崩溃。
2. 新输出不再包含 `safetyEnvelope`。
3. 旧 `safetyEnvelope` 不参与 collision、mask、occupied、dressing、road、wall 的任何硬判断。
4. 测试覆盖旧输入 safety 超大但新输出无 safety 的完整链路。

### 禁止事项

- 禁止为了兼容而把旧 `safetyEnvelope` copy 到新 artifact。
- 禁止在 task record 中宣称 safety 已删除，但契约或输出仍保留。

## 最终验收

### 必跑验证

1. `./gradlew test --tests com.rinsing.geomantia.systems.city.CityStructureLandingFlowTest`
2. `./gradlew test --tests com.rinsing.geomantia.systems.city.CityStructureArrayLayoutLoopPlannerTest`
3. `./gradlew test --tests com.rinsing.geomantia.platform.http.CityPlanningEndpointHandlerTest`
4. `npm run build`，工作目录为 `country_designer_mcp`
5. `git diff --check`

### 全局搜索验收

实现仓库允许出现 `safetyEnvelope` 的位置仅限：

1. 历史 `dev_docs`。
2. 旧输入兼容测试的 fixture 文本。
3. 明确标注 legacy input compatibility 的读取 fallback。

文档仓库允许出现 `safetyEnvelope` 的位置仅限：

1. 历史案子。
2. 本验收卡中作为禁止项 / 退场目标出现。
3. `结构Envelope瘦身-v0.1` 的背景说明。

### 提交要求

1. 这是独立提交，不混入 D2 profile cache、D4 AI loop 或阵列形态继续开发。
2. 实现仓库提交标题建议：`城市系统-v0.1.40版本-移除结构SafetyEnvelope正式字段`。
3. 文档仓库若同步契约，单独提交，标题建议：`文档仓库-v0.1.66版本-同步结构SafetyEnvelope退场口径`。
