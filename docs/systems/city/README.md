# City 系统文档入口

City 系统负责承接 T 阶段输出的 `CitySeedRegistry` / `CitySiteCandidate`，在城市候选范围内生成可 review、可验证、可交给结构落地层消费的城市规划图层。

当前系统承接 C1-C4 的城市规划过程：局部地貌事实、城市语法、功能区落图、道路 / 边界 / 缓冲区规划，以及 D5 首版通过 WorldEdit 后端完成的基础世界落地。D6 是 City 侧的结构选择与固定落点规划：程序消费 TerraSense 导出快照并归一为结构画像，再按真实入口、尺寸、footprint、可建区和地形摘要过滤候选，同时把 D4 功能区 `semanticTerms` 与结构 TerraSense term 交给 AI 判断语义适配；固定大小结构不配置占比，由程序提供预选落地点并由 AI 选择 `landingCandidateId`；非固定结构才配置剩余可见面积占比。D7 进入 Overworld 内选择性接管原版结构生成，优先完整放置固定结构，再以条件包装结构、CityPlanIndex、validator 和 jigsaw 边界策略生成剩余结构；实现仓库当前提供 D7 最小可玩执行入口和 trace / 预览产物。

## 阅读顺序

1. `10_product/系统概述.md`
2. `10_product/过程设计/C1-C4城市规划过程.md`
3. `10_product/过程设计/C5-C8结构落地交接过程.md`
4. `10_product/案子/城市构造流程-v0.1/README.md`
5. `10_product/案子/C5锚点与保留区-v0.1/README.md`
6. `10_product/案子/D6结构池规划-v0.1/README.md`
7. `10_product/案子/D7条件包装结构生成-v0.1/README.md`
8. `10_product/案子/D7剩余结构起点候选-v0.1/README.md`
9. `10_product/开发计划-v0.1-City城市构造最小闭环.md`
10. `10_product/开发计划-v0.2-D7受控Jigsaw物化.md`
11. `10_product/开发计划-v0.3-D7计划驱动Jigsaw拓展.md`
12. `10_product/开发计划-v0.4-D7受控Jigsaw真实粘贴与验收.md`
13. `10_product/开发计划-v0.5-D7Jigsaw落地拦截与规则增强.md`
14. `20_contracts/数据契约/城市规划数据契约.md`
15. `20_contracts/数据契约/结构落地交接契约.md`
16. `30_code_guide/代码导览.md`
17. `40_tests/测试入口.md`
18. `40_tests/D6-D7临时真实结构测试配置.md`

## 当前状态

- 实现仓库已落地 City D2-D7 最小闭环：D2 城市上下文、D3 地貌审查图包、D4 功能区实体化、D5 道路 / 边界 / 缓冲区计划与 WorldEdit 执行入口、D6 结构选择与固定落点规划、D7 固定结构优先放置与剩余结构起点候选 / trace 执行入口。
- D7+ 下一阶段主线是受控 jigsaw 物化：不全局 mixin 原版 jigsaw，也不为每个外部结构手写 `geomantia:*` wrapper；而是在 City D7+ 专用路径中读取外部 configured structure / pool / template，逐 piece 通过城市约束场后再写入世界。
- v0.3 进一步把下一步工程路线收束为计划驱动 D7：以 `CityMaterializationJob`、chunk waiting、真实 ledger、`CityConstraintField` 和 bounded jigsaw solver 作为主线，保持与玩家 TP / 预加载 mod 的 chunk 生命周期协同。当前实现已接入 MC start pool 适配、子 pool 发现和首版 connector 对齐。
- v0.4 聚焦 D7 受控 jigsaw 的真实粘贴闭环：当前实现切片已把 `BoundedJigsawPlan.pieces[]` / `acceptedPieces[]` 中通过 validator 的 pieces 解析回真实 MC runtime piece source，等待 chunk 覆盖后以 `accepted_piece_template_paste` 写入世界，并同步 trace 与 piece ledger；真实游玩验收仍需在原版 / vanilla-like 测试存档中确认。
- v0.5 聚焦 D7 bounded jigsaw 的规则增强：不为每个外部结构手写 `geomantia:*` wrapper，也不全局 mixin 原版自然结构生成器；主线是在 City D7 自己发起的 bounded jigsaw 任务中，把每个 `PieceCandidate` 在真实 paste 前交给 `CityJigsawRulePipeline` 判定，只有 accepted piece 能写世界，rejected / stopped piece 必须写 trace。
- 旧 C1-C9 资料只作为 `docs/90_archive/` 下的历史参考，不迁回当前真值。
- 本轮文档按“大过程”组织，不把 C1-C8 拆成八个独立开发阶段。

## 上下游

| 方向 | 系统 | 交接内容 |
| --- | --- | --- |
| 上游 | 国度规划系统 | `CitySeedRegistry`、`CitySiteCandidate`、国度风格、城市功能类型、城市理论规模、候选选址条件。 |
| 上游 | GIS | 城市局部 `TerrainPatchMap`、地貌指标、坡度、水体、岸线、patch 摘要和预览图。 |
| 本系统 | City | `FunctionZoneMap`、`RoadIntent`、`BoundaryIntent`、`BuildOperationPlan`、`WorldMutationReport`、`StructureProfileCatalog`、`FilteredStructureCatalog`、`PlannedFixedPlacementMap`、`StructurePoolMap`、`StartCandidateSet`、`PlacedStructureMap`、`StructureGenerationTrace`。 |
| 下游 | Materialization / 结构落地 | `PlannedFixedPlacementMap`、`StructurePoolMap`、保留区、道路与功能区边界、剩余可见面积预算、真实放置结果和结构落地约束。 |

## 目录说明

| 目录 | 内容 |
| --- | --- |
| `10_product/` | City 系统边界、C1-C4 城市规划过程、C5-C8 结构落地交接口径，以及具体案子计划。 |
| `20_contracts/` | 阶段间传递对象、核心字段、状态和版本口径。 |
| `30_code_guide/` | D2-D7 当前实现入口、HTTP/MCP 入口和 review 边界。 |
| `40_tests/` | 自动测试、真实游玩验收和调试图验收入口。 |
