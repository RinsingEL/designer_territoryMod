# City 案子：统一城市基底与景观地块 v0.6

## 状态

进入 active path。v0.6 在 v0.5 区域接力基础上把 Parcel 数量收口为 Landscape/Group 总预算，并增加核心优先与可选准入。景观内部仍只能通过逐格 frontier 扩张形成区域，后继区域必须从父区域局部边界接力；固定图形和失败保底继续禁止。

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
2. 农田、花田、绿化带、林场、池塘等景观先形成独立 Parcel，再在 Parcel mask 内按选中的接力填充方案逐格生成主题区、间隔带、水、地面等内部角色。
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

农业附着建筑按 D4 provenance 提供起点，但数量预算属于整个 Landscape/Group，不按 anchor 数倍增：

- `required`：核心来源；`coreParcelCountMin..Max` 是全组优先准入的核心 Parcel 总量，多个核心 anchor 只共同提供起点。
- `fill`：填充来源；`fillParcelCountMin..Max` 是全组共享的额外 Parcel 总量，多个 fill anchor 不复制配额。
- `connectivity_growth`：道路/连接结构，默认不生成景观 Parcel。

第一个 Parcel 从来源建筑外缘选择合法方向。后续 Parcel 可从原建筑重新分叉，也可从任一已有 Parcel 的可用外缘继续生长；选择由 Blueprint `generationSeed`、landscape ID、anchor ID 和 Parcel ordinal 稳定派生。固定输入必须得到固定图形。

LandUse 先让全部核心 Parcel 竞争并冻结位置；任一核心 Parcel 低于 `max(parcelAreaMinBlocks, stageCount)` 时 hard fail。随后按稳定顺序逐个探测可选 Parcel：只有能够完整达到同一最小可执行面积才正式准入并冻结，否则零占地跳过并记录 `skipped_insufficient_space`。不得让可选 Parcel 长到一半后带着碎片进入 SurfacePrint，也不得缩减 AI 阶段。

每次扩张必须校验 D6 footprint、规划边界、地形可通行性、Parcel 间距和当前占用。失败时按稳定顺序更换方向或父节点；不允许重叠补数。Group 总预算防止大量 fill 建筑造成无界增长。

相邻 Parcel 不合并成一个 Area。它们可以共享或贴近边界，但必须保持独立边界身份，使围栏农田继续呈现“一块一块”的建筑景观层次。

## Parcel 内部区域接力生长

每个景观 Parcel 只有一个稳定根起点。第一块区域从根起点逐格扩张；每一块后继区域必须从其父区域的局部边界选取一个相邻格作为新起点，再以自身 frontier 逐格扩张。程序在完整 `memberSpans - exclusionSpans` 上一次性冻结所有区域；输入 mask、方案和 seed 相同，输出 region spans 必须相同，跨 chunk 只裁切冻结结果，不能重新起步。

三条硬契约：

1. 所有被填充格都必须有扩张来源。禁止用圆、菱形、矩形、距离环、预制 mask 或其他固定几何公式生成角色；同样禁止把它们用作快速路径或失败保底。
2. 多样性由 AI 提交的方案权重、角色占比、角色生长偏置和内容权重驱动，但 AI 不接触逐格几何。
3. 每个后继区域必须记录父区域及局部接力界面。若精确 mask 断开、起点非法或 frontier 无法完成目标，规划 hard fail；不得静默重播种或用 bbox 补齐。

填充 Profile 分离三类职责：

- 目录定义唯一 `algorithm=SINGLE_SOURCE_REGION_RELAY`、`relayOrigin=PARENT_REGION_LOCAL_BOUNDARY`、可用角色、`materialRole`、每个角色允许的 `growthForm`、占比范围、内容白名单和面向 AI 的示例。
- AI 在 Blueprint 中提交一个或多个候选 Profile、候选选择权重，以及按接力顺序排列的 `roleShares[]`；每项包含角色、`growthForm=PATCH|CORRIDOR` 和目标占比，另可提交内容权重。
- 程序按 Parcel 身份稳定选择候选，将占比换算为各区域目标面积，冻结 `regionId/parentRegionId/start/sourceFrontier/targetArea/actualArea`、region spans 与内容权重。

典型目录示例：

- 灌溉农田：`CULTIVATED/PATCH -> BANK/CORRIDOR -> WATER/CORRIDOR -> BANK/CORRIDOR -> CULTIVATED/PATCH`，耕地占主要比例，田埂与水渠只作为局部间隔，不形成完整闭环。
- 旱作拼田：`CULTIVATED/PATCH -> GROUND/CORRIDOR -> CULTIVATED/PATCH`，以土路或石子地面打断大块耕地。
- 花田叶带：`FLOWER/PATCH -> LEAF_BREAK/CORRIDOR -> FLOWER/PATCH`，生成大小不同且由局部叶带接力的花片。
- 林场：`TREE_GROVE/PATCH -> SHRUB_BREAK/PATCH|CORRIDOR -> TREE_GROVE/PATCH -> GRAVEL_PATH/CORRIDOR`；树、花具体品种的多内容随机落点仍由 Decoration 消费，不在 SurfacePrint 中伪装为已落地。

角色不直接携带方块 ID。目录的 `materialRole=PRIMARY_CONTENT|BANK|WATER|GROUND` 决定使用 Surface Recipe 的哪个材料槽；AI 只能引用角色和内容白名单。`contentWeights` 本版进入 Blueprint、规划 trace 和 SurfacePrint 冻结产物，但 SurfacePrint 只执行地表/作物材料槽，树种、花种的多内容随机落点仍由 Decoration 后续接入。

## 配置职责

引用目录冻结四类配置：

- Foundation Profile：LandUse rule、Surface recipe、建筑外扩、闭合半径和最大允许接合距离。
- Landscape Profile：景观类型、规则、配方、规模基准和 ParcelStyle。
- Surface Recipe：地表材料、作物、水渠、边界材料以及等高线条带宽度。
- Landscape Fill Profile：兼容景观类型、区域接力算法、接力来源、主题角色、允许生长偏置、角色占比范围、内容白名单和示例。

首批正式景观 Profile：

- 围栏混合农田：`FARMLAND`；独立小地块、耕作、作物、水渠和围栏。
- 花田：`MEADOW`；小至中型成片花卉地表，允许开放或低边界。
- 绿化带：`COMMON_GREEN`；城市基底上的狭长软覆盖，不承担道路连通。
- 林场：`WOODLAND`；较大 Parcel、保留或补充树木、只在片区外缘形成边界。

AI 只在一次 Blueprint 中选择 foundation/landscape Profile、附着 Group、总体规模、连续性、地形关系，以及每个 landscape 的填充候选权重、按序角色占比、`PATCH|CORRIDOR` 生长偏置和内容权重。AI 不提交 block ID、底层算法名、带宽、确切 Parcel 数、逐块坐标、mask、固定形状、方向或道路。程序完全消费冻结 Profile 生成实际几何。

prepare 不注入隐藏默认目录。调用方必须提交完整 `landscapeFillProfiles[]`；服务原样校验、冻结并放入 Context 供 AI 阅读。示例属于 Profile 正式字段，不是提示词外的口头约定。

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
- 每个 Landscape/Group 的核心 Parcel 总量与可选 Parcel 总量分别落在 Profile 配置范围内，增加 fill anchor 不得线性放大数量。
- 核心 Parcel 必须先满足最小可执行面积；空间不足的可选 Parcel 必须以零占地 `skipped_insufficient_space` 退出，已准入 Parcel 不得缺 stage。
- Parcel 可从建筑或已有 Parcel 分叉，固定输入重复编译 hash 一致。
- 各 Parcel 保留独立 Area 和边界，不因同类型或相邻而合并。
- AI 可为同一景观提供多个填充候选及选择权重；固定输入下每个 Parcel 的候选选择稳定。
- 角色目标占比会改变各接力区域的目标面积，`PATCH|CORRIDOR` 只影响 frontier 偏置，不定义固定轮廓或固定宽度。
- 区域接力覆盖 `member - exclusions` 恰好一次；根起点必须是合法格，后继起点必须邻接父区域，断开或无法完成时 hard fail，跨 chunk 不重启。
- `land_use_preview.png` 叠加冻结的区域边界、接力起点、父界面以及主题、田埂、水和地面角色，可直接审阅 Parcel 内部形态与 provenance。
- 花田、绿化带、林场和农田都能通过目录 Profile 选择，不需要修改 Java。
- RoadWeaver 是唯一道路来源，并能覆盖清理冲突景观。
