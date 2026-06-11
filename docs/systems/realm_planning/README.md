# 国度规划系统文档入口

国度规划系统负责承接 W 阶段世界粗扫结果和 GIS 粗尺度地貌事实，生成国度配置、国度落脚、首都种子、国度扩张结果、城市名册和城市生成条件。

它对应主线 workflow 中的 T 阶段。它不负责城市内部边界、功能区、道路网络、结构池预算或 jigsaw / prefab 物化；这些属于后续 City 和 Materialization 链路。

## 阅读顺序

1. `10_product/T阶段国度与城市种子方案.md`

## 当前状态

- 当前只有方案文档，尚未进入实现迁移。
- 后续真正开始实现时，再补齐 `20_contracts/`、`30_code_guide/` 和 `40_tests/`。
- 不在实现仓库预建空 package。

## 核心产物

| 产物 | 说明 |
| --- | --- |
| RealmProfile | 国度风格、生活偏好、材料、宗教、产业、地貌偏好、结构池倾向。 |
| RealmLandingCandidate | 国度落脚候选簇或候选方向。 |
| RealmSeed | 国度扩张核心点和扩张参数。 |
| CapitalCitySeed | 首都一定存在的城市种子。 |
| RealmTerritoryMap | 多国度统一扩张后的势力范围。 |
| CitySeedRegistry | 城市名册、城市数量、理论规模、生成条件和触发方式。 |

## 上下游

- 上游：W 阶段 WorldSurveyContext、GIS `world_coarse` profile、粗 WorldPatchMap、地貌图集和带网格坐标预览图。
- 下游：C 阶段 City / FunctionZone / Materialization 链路。
