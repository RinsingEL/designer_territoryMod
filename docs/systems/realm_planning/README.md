# 国度规划系统文档入口

国度规划系统负责承接 W 阶段世界粗扫结果和 GIS 粗尺度地貌事实，生成国度配置、国度落脚、首都种子、国度扩张结果、城市名册和城市生成条件。

它对应主线 workflow 中的 T 阶段。它不负责城市内部边界、功能区、道路网络、结构池预算或 jigsaw / prefab 物化；这些属于后续 City 和 Materialization 链路。

## 阅读顺序

1. `10_product/T阶段国度与城市种子方案.md`
2. `10_product/功能设计/W-T阶段主流程设计.md`
3. `10_product/开发计划-v1.1-W粗Patch与T阶段重建.md`
4. `20_contracts/数据契约/W-T阶段数据契约.md`
5. `20_contracts/接口契约/W-T阶段MCP接口.md`
6. `30_code_guide/代码导览.md`
7. `40_tests/测试入口.md`
8. `40_tests/真实游玩验收计划.md`

## 当前状态

- 当前已有 T 阶段方案、v1.1 W / T 重建开发计划、主流程设计、数据契约、MCP 接口契约、代码导览、测试入口和真实游玩验收计划。
- v1.1 最小实现已接入实现仓库，提供 W / T 主链、HTTP / MCP / Forge 调试入口、JVM 测试和 Forge GameTest 验收。
- 后续如扩展 C 阶段消费、城市内部规划或结构物化，应在新系统 / 新阶段文档中另起计划，不塞回当前 T4。

## 核心产物

| 产物 | 说明 |
| --- | --- |
| RealmProfile | 国度风格、生活偏好、材料、宗教、产业、地貌偏好、结构池倾向。 |
| RealmCandidateMapPackage | 带网格坐标的国度落脚候选图、patch 摘要、禁用区域和坐标说明。 |
| RealmCoordinateSelection | AI 从候选图返回的网格坐标、坐标转换、校验结果和选择理由。 |
| RealmSeed | 国度扩张核心点和扩张参数。 |
| CapitalCitySeed | 首都一定存在的城市种子。 |
| RealmTerritoryMap | 多国度统一扩张后的势力范围。 |
| CitySeedRegistry | 城市名册、城市数量、理论规模、生成条件和触发方式。 |

## 上下游

- 上游：W 阶段 WorldSurveyContext、GIS 按消费层传入 `cellStepBlocks` 生成的粗地貌事实、粗 WorldPatchMap、地貌图集和带网格坐标预览图。
- 下游：C 阶段 City / FunctionZone / Materialization 链路。

## 目录说明

| 目录 | 内容 |
| --- | --- |
| `10_product/` | 系统方案、v1.1 开发计划和 W / T 主流程设计。 |
| `20_contracts/` | W / T 阶段结构化产物契约和 MCP 接口契约。 |
| `30_code_guide/` | 当前实现仓库入口、主调用链和 review 检查点。 |
| `40_tests/` | 结构校验、fixture、未来自动测试入口和真实游玩验收计划。 |
