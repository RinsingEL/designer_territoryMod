# City 系统文档入口

City 系统承接 T 阶段输出的 `CitySeedRegistry` / `CitySiteCandidate`，在城市候选范围内生成可 review、可验证、可真实落地的城市结构规划。

## 当前 Active 主线

当前 City D3-D6 已按破坏性重构切换为：

```text
D3 地形 patch 真值
  -> configured structure envelope profiling
  -> D4 设计 slot 候选生成 / 候选选择（推荐路径）
  -> D4 StructureAnchorPlan / StructureAnchorMap
  -> D5 reservation mask 预案（含 D3 patch 贴边 wall reservation）
  -> D6 planned_worldgen probe-and-lock
  -> execute_d5 激活 locked planned structure 生成期注册
  -> Minecraft worldgen createStructures 阶段写入 StructureStart
  -> city_execute_d7 查询 worldgen ledger
  -> 根据已落结构 ledger 反推 inferred function area
  -> RoadWeaver / debug fallback 道路
  -> city walls v2 扫描真实道路并按 D3 patch 贴边墙带裁门 / 放墙
```

城墙 v0.2 仍是当前默认口径；v0.3 已接入显式 `wallVersion=v3` 开发路径，目标是从结构 actualFootprint / sourcePatch 出发生成城市外环 hull，填掉凹陷和内部道路口袋，并增加 step=1 地形 / mask debug 扫描，待真实游玩验收后再考虑切默认。

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
- `10_product/案子/D4设计构图候选闭环-v0.2/README.md`：将 v0.1 批量候选升级为逐 slot session：每选定一个 anchor 后冻结 occupied set，再为下一个 slot 重新生成候选，降低 D6 才发现碰撞后的回退成本。
- `10_product/案子/结构Envelope精修-v0.1/README.md`：缩紧稳定结构 bbox，区分 actual / collision / mask。
- `10_product/案子/结构语义重标记-v0.1/README.md`：整理 TerraSense 结构语义白名单，不恢复 City 自建枚举。
- `10_product/案子/RoadWeaver结构连接-v0.1/README.md`：已接入 optional RoadWeaver adapter，D5 execute 阶段注册结构道路端点；缺 mod 时保留 debug fallback 并在 trace 中标明。
- `10_product/案子/结构地形兼容适配-v0.1/README.md`：已加入 terrain adaptation / Beardifier 诊断 trace，用于判断浮空等问题来源。
- `10_product/案子/城市边界与城墙-v0.1/README.md`：已加入 D7 ledger 后的临时城墙 plan / execute 闭环，输出石墙 NBT artifact。
- `10_product/案子/城市边界与城墙-v0.2/README.md`：已进入当前默认城墙口径，D5 早期生成 D3 patch 贴边 wall reservation mask，RoadWeaver 真实道路生成后扫描 actual road mask 并裁出城门，最后放墙 / 塔 / foundation；v0.1 矩形墙仅保留为 `wallVersion=v1_debug`。
- `10_product/案子/城市边界与城墙-v0.3/README.md`：已接入显式 `wallVersion=v3` 开发路径，待真实验收；从结构种子和 D3 patch 邻接图生成城市外环 hull，填充小凹陷 / 小洞 / 内部道路口袋，聚类外部道路裁门，并为墙体缺口输出 step=1 地形扫描、mask 冲突坐标和 gap debug report。
- `10_product/案子/City结构风格化换皮-v0.1/README.md`：在结构真实落地后按国度 / 城市 palette 做材料主题化替换。

## 当前产物

| 阶段 | 当前产物 |
| --- | --- |
| D2 | `citySiteContext` |
| D3 | `city_landform_review_package.json`、`landform_review_map.png` |
| envelope profiling | `structure_envelope_facts.json`、`structure_envelope_profile_preview.png`、`quality_report.json` |
| D4 candidates | `design_slot_plan.json`、`anchor_candidate_set.json`、`anchor_candidate_preview.png`、`quality_report.json` |
| D4 | `structure_anchor_plan.json`、`structure_anchor_map.json`、`structure_profile_catalog.json`、`structure_anchor_preview.png`、`quality_report.json` |
| D5 | `reservation_mask_plan.json`、`wall_reservation_plan.json`、`wall_reservation_preview.png`、`road_access_plan.json`、`build_operation_plan.json`、`reservation_mask_preview.png`、`quality_report.json`；road/build 为 D7 后处理占位 |
| execute_d5 | 激活 server-root `active_reservation_mask_plan.json`、`active_planned_structure_registry.json`，写跳过式 `world_mutation_report.json`、`active_mask_summary.json`、`roadweaver_connection_plan.json`、`road_provider_state.json` |
| D6 | `structure_materialization_plan.json`（`plannedWorldgenStructures[]`，含 locked actual footprint / bbox group / collision envelope / signature）、空 `placed_structure_ledger.json`、`structure_materialization_trace.json`、`inferred_function_area_map.json`、`structure_materialization_preview.png` |
| execute_d7 | `placed_structure_ledger.json`、`structure_materialization_trace.json`、`inferred_function_area_map.json`、`placed_structure_preview.png`，ledger 完整后生成 RoadWeaver-aware road report 与 terrain adaptation report |
| city walls | `actual_road_mask.json`、`city_wall_plan.json`、`city_wall_preview.png`、`city_wall_templates/*.nbt`、`city_wall_placement_report.json` |

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
