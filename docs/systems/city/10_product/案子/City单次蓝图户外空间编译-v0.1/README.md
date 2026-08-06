# City 案子：单次蓝图户外空间编译 v0.1

## 状态

已完成并入 active path。本文定义 CityBlueprint 一次完成结构与户外设计决策、D6 后由程序确定性编译地表和景观的首个完整切片。

## 要解决的问题

当前结构 Blueprint 已是一次提交，但 LandUse 仍可在 workflow 请求中接收第二份 `landUseIntentPlan`。这会形成两个设计权威，也让地表和景观无法随 Blueprint 一起冻结。现有 LandUse 还有两个几何问题：

- 同组每栋建筑分别贡献完整增长预算，农业建筑越多，农田总面积近似线性膨胀。
- `unclaimedSpans` 只是整个 D3 规划范围的补集，无法区分城市内部遗漏、显式自然保留和城市外部荒野。

## 核心决策

一次 AI 提交 `city_blueprint.v0.5`，根级同时携带结构 `groups[]` 和 `outdoorPlan`。二者属于同一个设计决定，但由两个程序编译阶段消费：

```text
D3 地形与冻结目录
-> 一次 CityBlueprint v0.5
   -> groups / relations -> D4 结构编译 -> D5 -> D6 locked footprint
   -> outdoorPlan + D6 -> 户外意图投影 -> LandUse / Landscape / UrbanSpace
-> SurfacePrintPlan
-> execute_d5 / 首次 owner-chunk worldgen
```

结构 `groups[]` 继续只允许 `STRUCTURE`。景观不进入结构阵列排序、required/fill、collision 或关系图施工，避免让结构编译器承担连续面域职责。

## Blueprint 负责的决定

`outdoorPlan` 必须完整回答：

- 本城是生成户外空间还是显式保持原貌。
- 城市包络的紧凑程度。
- 每个结构 Group 使用哪条 LandUse 规则、地表 recipe、范围档位、连接策略和城市/景观 membership。
- 哪些独立或附属景观存在，它们依附哪些结构 Group、偏好哪些 D3 patch、范围和内容密度档位、连续性与生长关系。
- 城市包络内的小封闭洞、狭缝、中型空地、大型空地和外部连通空间如何收口。

Blueprint 不提交世界坐标、逐格边界、方块 ID、裸面积、行动力、成本、田垄位置或树木位置。所有这些值由冻结 profile、D3 地形、D6 footprint、入口和 `generationSeed` 推导。

## 户外编译

### 结构地表

每个结构 Group 在 `GENERATE` 模式下恰好对应一份 structure ground。程序把该 Group 的 D6 anchors 汇总为一个空间主体，按 footprint 总面积和 extent 档位生成共享预算，不再为每栋建筑重复叠加 rule extra area。

`AWAY_FROM_REFERENCE` 与 `TOWARD_REFERENCE` 只表达关系。程序从来源 Group 和参考 Group 的 locked footprint 质心计算方向，并从合适的 footprint 外缘派生 seed。

### 景观

每个 landscape 使用冻结 `landscapeProfileRef`。profile 决定 LandUse rule、Surface recipe、三个 extent 基准面积和 membership；Blueprint 决定具体 extent、intensity、continuity、terrain policy 与关系。

首个真实执行类型是农田：全部附属农业建筑共享一份 landscape 总预算；程序再按 `CONTINUOUS|MULTI_PARCEL|PATCHY` 把这份预算守恒地编译为 1、最多 2 或最多 4 个 parcel growth region。增加农业 anchor 只增加 seed，不增加总面积。现有 `CONTOUR_BANDS` 继续负责不规则最终 mask 内的 FIELD、BANK、WATER、END_CAP 和 FIELD-only 作物，不重写作物执行器。

`COMMON_GREEN`、`WOODLAND`、`MEADOW`、`POND` 首版至少拥有正式区域所有权和 residual / preview 语义；只有 profile 声明可执行 Surface recipe 时才进入 worldgen 写入。连续内容不得退回旧通用 Decoration。

### 城市包络与剩余空间

城市包络只由 `membership=URBAN` 的地表 claim、locked structure footprint 和已冻结 corridor/gate 支撑。外围农田、林场和池塘不得扩大城市包络。

最终扩张后，程序在紧凑局部栅格上生成 envelope，并对 `envelope - claims - footprints - corridors` 的所有连通分量分类。小孔和窄缝可吸收进相邻 urban area；中大型空地按 Blueprint 冻结为 common green、service ground 或 natural reserve；水体、陡坡和未采样事实只能进入显式自然类型。

验收恒等式：

```text
UrbanEnvelope
= StructureFootprint
 + CorridorOrRoadReservation
 + LandUseOrLandscapeAssignment
 + ExplicitNaturalReserve
```

`unknownResidualBlocks` 必须为 0。整个 planning bounds 的 `unclaimedSpans` 继续只作外部补集，不能再充当城市漏洞指标。

## 权威与兼容

- `city_blueprint.v0.4`、旧 context、旧 snapshot 不自动迁移，必须重新 prepare 和提交。
- 正式 Blueprint workflow 禁止再传请求级 `landUseIntentPlan` 或开关覆写户外设计。
- legacy/debug D4 仍可显式调用独立 LandUse intent，但不属于一次 Blueprint 主线。
- 户外 completion 必须绑定 Blueprint、D6、D3 terrain field 和冻结 outdoor catalog identity；任一漂移都要求重编。

## 不做事项

- 不让 AI 输出逐格景观或物件坐标。
- 不把景观放进结构 `groups[]`。
- 不修改 Beardifier 建筑地形融合。
- 不重写农田等高线与作物落地链。
- 不恢复通用 Decoration 作为景观中间层。
- 不为旧 Blueprint 或旧户外产物做静默迁移。

## 验收

- 同一 Blueprint、D3、D6 和冻结目录重复编译得到相同 hash。
- 正式 workflow 的 AI 城市设计提交计数仍为 1。
- 每个结构 Group 的地表决定来自 Blueprint，不从请求临时覆写。
- 多个农业 anchor 不再线性放大农田总预算，农田能按关系向城市外侧生长。
- 城市包络内 `unknownResidualBlocks=0`，自然地表只能以显式类型存在。
- 现有 SurfacePrint、ContourBand、crop、boundary、chunk owner 和 rollback 测试全部通过。
- 预览能区分 urban area、landscape、absorbed residual、explicit natural 与非法 unknown。
