# 国度规划系统文档入口

国度规划系统负责承接 W 阶段世界粗扫结果和 GIS 粗尺度地貌事实，生成国度配置、国度落脚、首都种子、国度扩张结果、城市名册和城市生成条件。

它对应主线 workflow 中的 T 阶段。它不负责城市内部边界、功能区、道路网络、结构池预算或 jigsaw / prefab 物化；这些属于后续 City 和 Materialization 链路。

## 阅读顺序

1. `10_product/T阶段国度与城市种子方案.md`
2. `10_product/功能设计/W-T阶段主流程设计.md`
3. `10_product/开发计划-v1.1-W粗Patch与T阶段重建.md`
4. `10_product/开发计划-v1.2-W粗扫T3T4质量重构.md`
5. `10_product/开发计划-v1.3-Dregora标准W粗扫与GIS指标聚合.md`
6. `10_product/开发计划-v1.4-T3行动力国度扩张模型.md`
7. `10_product/开发计划-v1.5-高步长局部指标封装与地貌判定修正.md`
8. `10_product/开发计划-v1.6-多尺度GIS地貌特征栈与面域验收.md`
9. `20_contracts/数据契约/W-T阶段数据契约.md`
10. `20_contracts/接口契约/W-T阶段MCP接口.md`
11. `30_code_guide/代码导览.md`
12. `30_code_guide/flows/W-T主链实现指南.md`
13. `30_code_guide/review/国度规划主链Review清单.md`
14. `30_code_guide/diagrams/国度规划W-T代码流程图.md`
15. `40_tests/测试入口.md`
16. `40_tests/真实游玩验收计划.md`

## 当前状态

- 当前已有 T 阶段方案、v1.1 W / T 重建开发计划、主流程设计、数据契约、MCP 接口契约、代码导览、测试入口和真实游玩验收计划。
- v1.1 最小实现已接入实现仓库，提供 W / T 主链、HTTP / MCP / Forge 调试入口、JVM 测试和 Forge GameTest 验收。
- v1.2 计划已根据真实世界验收复盘补充，重点修复 W 地貌分类 / patch 粒度、T3 国境连通性、T4 城市种子分布和质量评分阻断。
- v1.2 验收后补齐 `30_code_guide` 代码过程导览；v1.4 已让 strict T3 默认使用 action budget 行动力扩张模型，旧 quota frontier 仅作为 smoke / 对照模型保留。
- v1.3 计划以 Dregora 体感世界为标准，目标 `planningRadiusBlocks=16384`；当前实现已在 W runner 内落地 `metricSampleStrideBlocks` / `localSlopeRadiusBlocks` 的真实 micro-sampling 聚合与 feature grid 缓存。
- v1.4 计划聚焦 T3 行动力扩张模型；当前 strict 默认已由行动力预算、地形消耗、竞争压力和 wild / contested / blocked / unreachable land 共同决定国度范围。
- 2026-06-12 已完成 v1.3 / v1.4 Dregora 标准档真实验收：`planningRadiusBlocks=16384`、`cellStepBlocks=128`、`microSampleStrideBlocks=32`、`expansionModel=action_budget`，最终 `acceptance_report.passed=true`、`score_manifest.totalScore=82.95`、`hardBlocks=[]`。
- v1.5 计划聚焦高步长局部指标封装和地貌判定修正：保护低 step GIS 主链，同时让 `cellStepBlocks=128` 的 W 粗扫使用 micro 局部证据确认 `cliff` / `steep` / `shore` 等局部标签。
- v1.6 计划吸收 GIS 地貌识别研究结论，聚焦多尺度特征栈、`ridge` / `plateau` / `lowland` 面域语义、Tag Audit cell reference 和后续 PCG suitability 适配；当前首版已落地 `terrainMetrics` / `landformEvidence` / `landformConfidence`、代表点抽样、point / cell reference 审计和扫描边界水体降级诊断。
- 后续如扩展 C 阶段消费、城市内部规划或结构物化，应进入 `systems/city/README.md` 或后续 Materialization 系统，不塞回当前 T4。

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
| ScoreManifest | W / T3 / T4 结果质量评分、硬阻断和人工 review 清单。 |

## 上下游

- 上游：W 阶段 WorldSurveyContext、GIS 按消费层传入 `cellStepBlocks` 生成的粗地貌事实、粗 WorldPatchMap、地貌图集和带网格坐标预览图。
- 下游：City 系统 C1-C4 城市规划链路，以及后续 Materialization 结构落地链路。

## 目录说明

| 目录 | 内容 |
| --- | --- |
| `10_product/` | 系统方案、v1.1 最小闭环计划、v1.2 质量重构计划、v1.3 Dregora 标准 W 粗扫计划、v1.4 T3 行动力扩张计划、v1.5 高步长局部指标封装计划、v1.6 多尺度 GIS 地貌特征栈计划和 W / T 主流程设计。 |
| `20_contracts/` | W / T 阶段结构化产物契约和 MCP 接口契约。 |
| `30_code_guide/` | 当前实现仓库入口、主调用链、代码过程图和 review 检查点。 |
| `40_tests/` | 结构校验、fixture、未来自动测试入口和真实游玩验收计划。 |
