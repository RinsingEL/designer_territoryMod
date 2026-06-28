# City 系统文档入口

City 系统承接 T 阶段输出的 `CitySeedRegistry` / `CitySiteCandidate`，在城市候选范围内生成可 review、可验证、可真实落地的城市结构规划。

## 当前 Active 主线

当前 City D3-D6 已按破坏性重构切换为：

```text
D3 地形 patch 真值
  -> D4 StructureAnchorPlan / StructureAnchorMap
  -> D5 reservation mask / planned structure 生成期注册
  -> D6 planned_worldgen 校验
  -> Minecraft worldgen createStructures 阶段写入 StructureStart
  -> city_execute_d7 保留入口名，查询 worldgen ledger
  -> 根据已落结构 ledger 反推 inferred function area
```

旧的“先画功能区再塞结构”主链不再是当前真值。active endpoint 不再默认产出或消费：

- `function_zone_map.json`
- `buildable_area_map.json`
- `planned_fixed_placement_map.json`
- `structure_pool_map.json`
- `start_candidate_set.json`

旧 `FunctionZoneMap` / `BuildableAreaMap` / bounded jigsaw 多 start 面积补偿相关代码和文档只作为历史参考；如果旧 payload 或旧 artifact 进入 active endpoint，应返回 `LEGACY_CITY_FUNCTION_ZONE_FLOW_REMOVED`，不得静默兼容。

## 阅读顺序

1. `10_product/案子/D3-D6结构落地驱动城市重构-v0.1/README.md`
2. `20_contracts/数据契约/结构落地交接契约.md`
3. `20_contracts/接口契约/City调试MCP接口.md`
4. `30_code_guide/代码导览.md`
5. `40_tests/测试入口.md`

历史方案可读但不作为当前实现依据：

- `10_product/案子/D6结构池规划-v0.1/README.md`
- `10_product/案子/D7条件包装结构生成-v0.1/README.md`
- `10_product/开发计划-v0.2~v0.5-*`

## 当前产物

| 阶段 | 当前产物 |
| --- | --- |
| D2 | `citySiteContext` |
| D3 | `city_landform_review_package.json`、`landform_review_map.png` |
| D4 | `structure_anchor_plan.json`、`structure_anchor_map.json`、`structure_profile_catalog.json`、`structure_anchor_preview.png`、`quality_report.json` |
| D5 | `reservation_mask_plan.json`、`road_access_plan.json`、`build_operation_plan.json`、`reservation_mask_preview.png`、`quality_report.json` |
| execute_d5 | 激活 server-root `active_reservation_mask_plan.json`、`active_planned_structure_registry.json`，写跳过式 `world_mutation_report.json`、`active_mask_summary.json` |
| D6 | `structure_materialization_plan.json`（`plannedWorldgenStructures[]`）、空 `placed_structure_ledger.json`、`structure_materialization_trace.json`、`inferred_function_area_map.json`、`structure_materialization_preview.png` |
| execute_d7 | `placed_structure_ledger.json`、`structure_materialization_trace.json`、`inferred_function_area_map.json`、`placed_structure_preview.png` |

## 上下游

| 方向 | 系统 | 交接内容 |
| --- | --- | --- |
| 上游 | 国度规划系统 | `CitySeedRegistry`、城市候选坐标、国度归属。 |
| 上游 | GIS / TerraSense | D3 地形 patch 真值、TerraSense `StructureProfile.jsonl` / debug catalog、TerraSense tag 白名单。 |
| 本系统 | City | 结构 anchor、reserved envelope、reservation mask、planned structure registry、worldgen ledger。 |
| 下游 | 世界生成 / Materialization | feature / vanilla structure 抑制 hook、planned structure worldgen hook、原版 `StructureStart` 生成期落地、ledger 与 trace。 |

## 目录说明

| 目录 | 内容 |
| --- | --- |
| `10_product/` | 当前方案、历史方案和开发计划。 |
| `20_contracts/` | 阶段输入输出、artifact、MCP/HTTP 参数和失败口径。 |
| `30_code_guide/` | Java / MCP 当前实现入口。 |
| `40_tests/` | 自动测试、真实游玩验收和调试图验收入口。 |
