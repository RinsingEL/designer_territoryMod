# City 系统文档入口

City 系统负责承接 T 阶段输出的 `CitySeedRegistry` / `CitySiteCandidate`，在城市候选范围内生成可 review、可验证、可交给结构落地层消费的城市规划图层。

当前系统只承接 C1-C4 的城市规划过程：局部地貌事实、城市语法、功能区落图、边界处理与道路网络。C5 之后的 anchor、约束场、结构池预算和 jigsaw / prefab 物化属于结构落地过程，当前先在本系统中记录交接口径，后续实现时可迁入独立的 Materialization 系统。

## 阅读顺序

1. `10_product/系统概述.md`
2. `10_product/过程设计/C1-C4城市规划过程.md`
3. `10_product/过程设计/C5-C8结构落地交接过程.md`
4. `20_contracts/数据契约/城市规划数据契约.md`
5. `20_contracts/数据契约/结构落地交接契约.md`
6. `30_code_guide/代码导览.md`
7. `40_tests/测试入口.md`

## 当前状态

- 本系统处于方案与契约设计阶段，尚未在实现仓库建立新的 City 主链实现。
- 旧 C1-C9 资料只作为 `docs/90_archive/` 下的历史参考，不迁回当前真值。
- 本轮文档按“大过程”组织，不把 C1-C8 拆成八个独立开发阶段。

## 上下游

| 方向 | 系统 | 交接内容 |
| --- | --- | --- |
| 上游 | 国度规划系统 | `CitySeedRegistry`、`CitySiteCandidate`、国度风格、城市功能类型、城市理论规模、候选选址条件。 |
| 上游 | GIS | 城市局部 `TerrainPatchMap`、地貌指标、坡度、水体、岸线、patch 摘要和预览图。 |
| 本系统 | City | `CityGrammarPlan`、`FunctionZoneMap`、`BoundaryTreatment`、`RoadNetwork`。 |
| 下游 | Materialization / 结构落地 | `StructureLandingIntent`、anchor 需求、保留区、道路与功能区边界、结构池倾向和预算输入。 |

## 目录说明

| 目录 | 内容 |
| --- | --- |
| `10_product/` | City 系统边界、C1-C4 城市规划过程、C5-C8 结构落地交接口径。 |
| `20_contracts/` | 阶段间传递对象、核心字段、状态和版本口径。 |
| `30_code_guide/` | 当前尚未实现；用于记录未来实现入口和 review 边界。 |
| `40_tests/` | 未来自测、真实游玩验收和调试图验收入口。 |
