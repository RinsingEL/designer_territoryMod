# City 案子：统一城市基底与景观地块 v0.3

## 状态

进入 active path。v0.3 破坏性替换 v0.2 的“SpatialGround 关系骨架铺地”，不保留入口、组内最小连接树、跨组关系线或 LandUse 自动连接作为正式城市地表几何。

## 核心分层

城市户外固定按以下顺序编译和执行：

```text
D6 locked structure footprint
-> 单一城市基础地板
-> 显式景观 Parcel 覆盖
-> 稀疏景观装饰
-> RoadWeaver 道路后写覆盖与清障
```

各层职责：

1. 城市基础地板只回答“整座城市的通用建设地表在哪里”，不规划道路。
2. 农田、花田、绿化带、林场、池塘等景观以独立 Parcel 覆盖基础地板或向城市外缘扩展。
3. RoadWeaver 是建筑入口连接、组内道路和跨组道路的唯一权威；LandUse 不产生替代道路。
4. 建筑结构本身继续由 D6 locked footprint 排除，Beardifier 继续负责结构地形融合。

## 单一城市基础域

`CityBlueprint` 在 `outdoorPlan.foundationProfileRef` 选择冻结的基础地板 Profile。程序收集全部纳入城市主体的 D6 footprint，按 Profile 的建筑外扩和形态闭合参数生成一个单一连续域，并使用同一 Surface recipe 铺地。

基础域禁止使用：

- 模板 `roadEntrances[]`；
- 入口外伸 corridor；
- 组内建筑中心连线或最小连接树；
- `HIERARCHY|CONNECTION|ADJACENCY` 关系直线；
- 为通过连通验收而生成的细长地板桥。

算法允许先得到多个建筑影响组件，但正式结果必须收敛为一个连续城市域。配置允许的最大闭合范围内仍不连续时，规划明确失败并返回 D4 布局不适合单城的原因；不得把多个组件静默解释成多个城镇。未来港区、庄园、前哨等卫星区必须另立显式契约，默认不启用。

基础域内部除结构 footprint 和明确的不可写执行排除外，不得留下原群系洞。所有 SpatialGround 共享同一基础地板材质；其共享空间类型和层级只保留建筑学语义，不再拥有独立铺地配方。

## 景观 Parcel 图

景观不是一次连续面积洪泛。每个 landscape 由一组稳定、可追踪的 Parcel 组成，每个 Parcel 保留独立 mask、边界和 Surface recipe。

农业附着建筑按 D4 provenance 分级：

- `required`：核心来源，默认 Profile 可配置为每栋生成 `5..10` 个 Parcel。
- `fill`：填充来源，默认 Profile 可配置为每栋生成 `1..3` 个 Parcel。
- `connectivity_growth`：道路/连接结构，默认不生成景观 Parcel。

第一个 Parcel 从来源建筑外缘选择合法方向。后续 Parcel 可从原建筑重新分叉，也可从任一已有 Parcel 的可用外缘继续生长；选择由 Blueprint `generationSeed`、landscape ID、anchor ID 和 Parcel ordinal 稳定派生。固定输入必须得到固定图形。

每次扩张必须校验 D6 footprint、规划边界、地形可通行性、Parcel 间距和当前占用。失败时按稳定顺序更换方向或父节点；达到重试上限后记录短缺，不允许重叠补数。总 Parcel 数仍受城市规模和 Profile 硬上限保护，防止大量 fill 建筑造成无界增长。

相邻 Parcel 不合并成一个 Area。它们可以共享或贴近边界，但必须保持独立边界身份，使围栏农田继续呈现“一块一块”的建筑景观层次。

## 配置职责

引用目录冻结三类配置：

- Foundation Profile：LandUse rule、Surface recipe、建筑外扩、闭合半径和最大允许接合距离。
- Landscape Profile：景观类型、规则、配方、规模基准和 ParcelStyle。
- Surface Recipe：地表材料、作物、水渠、边界材料以及等高线条带宽度。

首批正式景观 Profile：

- 围栏混合农田：`FARMLAND`；独立小地块、耕作、作物、水渠和围栏。
- 花田：`MEADOW`；小至中型成片花卉地表，允许开放或低边界。
- 绿化带：`COMMON_GREEN`；城市基底上的狭长软覆盖，不承担道路连通。
- 林场：`WOODLAND`；较大 Parcel、保留或补充树木、只在片区外缘形成边界。

AI 只在一次 Blueprint 中选择 foundation/landscape Profile、附着 Group、总体规模、连续性和地形关系。AI 不提交 block ID、确切 Parcel 数、逐块坐标、方向或道路。程序完全消费冻结 Profile 生成实际几何。

## RoadWeaver 边界

LandUse 不读取或猜测 RoadWeaver 最终路径。RoadWeaver 在景观之后执行，并对自己的道路 corridor 拥有覆盖权：清除冲突作物、景观装饰和边界方块，再落正式道路与入口。缺少 RoadWeaver 或道路入口数据时，道路按既有 provider 规则明确跳过或失败，不得由 LandUse 画线兜底。

## 破坏性规则

- 旧 CityBlueprint、引用目录、户外意图和完成标记不自动迁移。
- `SpatialGround.landUseRuleRef`、`SpatialGround.surfaceRecipeRef`、关系骨架 seed 和正式路径 `autoConnect` 删除。
- 正式 workflow 只接受当前冻结 Blueprint/catalog；旧字段 hard fail。
- 旧任务产物和 server-root active LandUse 状态必须清理后重规划，不提供存档版本控制或静默兼容。

## 验收

- 全城只有一个连续基础地板主体，且所有基础地板使用同一冻结配方。
- 基础域无入口线、MST 线、跨组关系线或其他道路状 LandUse 几何。
- 城市基础域内部无未解释原群系洞。
- 农田核心建筑与填充建筑的 Parcel 数分别落在 Profile 配置范围内。
- Parcel 可从建筑或已有 Parcel 分叉，固定输入重复编译 hash 一致。
- 各 Parcel 保留独立 Area 和边界，不因同类型或相邻而合并。
- 花田、绿化带、林场和农田都能通过目录 Profile 选择，不需要修改 Java。
- RoadWeaver 是唯一道路来源，并能覆盖清理冲突景观。
