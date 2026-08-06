# City 案子：单次蓝图城市空间织体 v0.2

## 状态

已进入 active path。v0.2 是对 v0.1 LandUse 方案的破坏性替换，不保留逐建筑占地或城市内部自然残余回退。

## 设计对象

建筑是城市的实体，户外空间是建筑之间的共同负空间。程序的基本对象不是“一栋建筑周围的一圈地”，而是一个完整功能组团以及它与其他组团的关系。

城市空间固定分为四级：

1. 城市主脉：由核心 Group、`HIERARCHY`、`CONNECTION` 和 `ADJACENCY` 关系形成全城骨架。
2. 功能组团：同一 Group 的全部 D6 建筑共同围合一个空间主体。
3. 共享空间：广场、市场街、住宅庭院、农庄场院或通用城市地表。
4. 建筑门槛：每个入口只负责接入共享空间，不拥有独立地板或环形边界。

验收关系为：

```text
建筑入口 -> 组团共享空间 -> 次级连接 -> 城市主脉 -> 其他组团
```

## 单次 Blueprint

`city_blueprint.v0.6` 一次冻结结构和户外语义。D4 的 `groups[]`、阵列构图、`relations[]` 同时成为 D6 后的城市空间骨架。

`outdoorPlan.spatialGrounds[]` 对每个结构 Group 声明 LandUse rule、Surface recipe、`sharedSpaceType`、`hierarchyLevel=PRIMARY|SECONDARY|LOCAL` 和 membership。AI 不提交坐标、面积、缓冲距离、逐建筑增长方向、自动连接开关或 residual 分类。

## 程序编译

组团编译器以入口、组内建筑最小连接树和跨组关系线生成共享空间骨架，再结合 Group 的 extent、priority、composition 和层级派生面积。单栋建筑没有完整外缘 seed，因此不会自然生成铺地环。

城市共享空间统一使用 `boundaryPolicy=OPEN`。围栏、树篱和矮墙只能来自明确景观或真正的外缘设计，不能沿每个建筑或每个不连通组件自动生成。

城市包络内部的所有非结构、非走廊单元必须归属一个城市空间组。旧面积上限不能让残余回退为原群系；`explicitResidualBlocks` 与 `unknownResidualBlocks` 都必须为 0。自然地形若要保留，必须以 `landscapes[]` 中的显式景观进入设计。

农业景观是完整农庄/田野片区。多个附属农业建筑共享总预算并各自提供入口或 seed；程序负责公平展开和连通，只在整个农业片区的外缘生成边界。

## 执行边界

SurfacePrintPlan、区块 owner、作物、等高线、Beardifier 和回滚机制仍是纯执行层，继续消费编译后的最终几何，不重新解释城市层级。

## 破坏性规则

- `city_blueprint.v0.5`、`structureGrounds`、`residualPolicy` 直接拒绝。
- 正式 workflow 只接受 v0.6 Blueprint，不从请求级 LandUse intent 回退。
- `city_outdoor_intent_plan.v0.2` 与 `city_land_use_planning_complete.v0.3` 绑定全部输入 identity；旧产物必须重规划。

## 验收

- 同一冻结输入重复编译 hash 一致。
- 每个 Group 恰好一个 SpatialGround。
- 每个建筑入口可达组团共享空间，所有城市组团可达城市主脉。
- 城市空间无逐建筑铺地环、无逐组件围栏、无未解释原群系洞。
- 农业附属建筑均得到田野覆盖，边界只位于农业片区外缘。
- 预览直接显示最终城市地表、空间层级与显式景观。
