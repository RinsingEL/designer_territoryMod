# City 案子：景观主体与 Parcel 联合布局 v0.7

## 状态

进入 active path。v0.7 将景观从 required/fill 建筑各自产生的小地块改为显式 `Landscape` 主体。按最新《City景观约束松绑》修订：AI 提交目标实例数和每实例 Parcel 数；required 建筑先按城市构图落位，景观再由 owner 种子向外按地形生长。实际数量、位置、面积和轮廓服从地形，完全长不出时警告，不再让整城失败。

当前只完成区域几何、阶段占比承载和稳定候选选择。AI 自主组合阶段、有效使用多候选权重，以及按 `contentWeights` 落地多作物、多花种和多树种尚未形成执行闭环，属于功能缺口，不归类为既有功能的 bug。

## 核心分层

城市户外固定按以下顺序编译和执行：

```text
D6 locked structure footprint
-> 单一城市基础地板
-> 显式景观 Parcel 覆盖
-> 稀疏景观装饰
-> 已确认外部长距道路可选后写覆盖与清障
```

各层职责：

1. 城市基础地板只回答“整座城市的通用建设地表在哪里”，不规划道路。
2. 农田、花田、绿化带、林场、池塘等景观先形成独立 Parcel，再在 Parcel mask 内按选中的接力填充方案逐格生成主题区、间隔带、水、地面等内部角色。
3. D4 `streetBands[]` 只冻结服务真实目的地的 City 区内街巷和城市主路，D6 后由 SurfacePrint 精确执行；功能区关系和距离本身不产生道路。RoadWeaver 只可执行另行确认、两端具有真实交通出口的外部长距道路。
4. 建筑结构本身继续由 D6 locked footprint 排除，Beardifier 继续负责结构地形融合。

## 单一城市基础域

`CityBlueprint` 在 `outdoorPlan.foundationProfileRef` 选择冻结的基础地板 Profile。程序收集全部纳入城市主体的 D6 footprint，按 Profile 的建筑外扩和形态闭合参数生成一个单一连续执行域，并使用同一 Surface recipe 铺地。D6/ Foundation 规划只确定城市覆盖范围与几何连接，不得以 D3 的水体、坡度或局部起伏把城市域切碎或拒绝整座城市。

Foundation 的地形兼容由 owner-chunk 执行层处理：城区建设面先按《City城市基面与路网形态-v0.1》冻结的邻域主高程形成分级平台，削平孤立小凸起并填实小坑洼，较大平台边缘做挡土收边；不得把地板逐列贴回原始微地形。D4 仍必须先拒绝完整占地不可承载的建筑位置，台基只处理整地后剩余的建筑局部高差。Landscape 按自身自然地形规则覆盖 Foundation，不进入城区整地，也不改变 D6 locked footprint。

基础域禁止使用：

- 模板 `roadEntrances[]`；
- 入口外伸 corridor；
- 组内建筑中心连线或最小连接树；
- `HIERARCHY|CONNECTION|ADJACENCY` 关系直线；
- 为通过连通验收而生成的细长地板桥。

算法允许先得到多个建筑影响组件，但正式结果必须收敛为一个连续城市域。配置允许的最大闭合范围内仍不连续时，规划明确失败并返回 D4 布局不适合单城的原因；不得把多个组件静默解释成多个城镇。未来港区、庄园、前哨等卫星区必须另立显式契约，默认不启用。

基础域内部除结构 footprint 和明确的不可写执行排除外，不得留下原群系洞。所有 SpatialGround 共享同一基础地板材质；其共享空间类型和层级只保留建筑学语义，不再拥有独立铺地配方。

## 景观主体与 Parcel 图

景观不是一次连续面积洪泛。每个 landscape 由一组稳定、可追踪的 Parcel 组成，每个 Parcel 保留独立 mask、边界和 Surface recipe。

每个景观必须显式声明语义和来源：`FUNCTIONAL|COMPOSITIONAL|AMBIENT` 表示用途；`ATTACHED` 精确绑定 `groupId + requiredStructureRef`，`FREE_STANDING` 通过 placement domain 声明城市剩余空间、建筑边缘、组间或沿水域。fill/connectivity 建筑永远不拥有景观，也不得进入 required 景观预留区。

AI 提交目标 `instanceCount` 和每实例目标 `parcelCount`；`ATTACHED` 的实例数固定为 1。Profile 规定 AI 可选的数量和面积范围；程序可因地形减少实际 Parcel 数或面积。

每个非零实例形成可追踪的父子树。`ATTACHED` owner 只提供根种子和外向方向；近地受阻时根 Parcel 可以离开建筑门口，到周边好地生长。每个非根 Parcel 从父 Parcel 真实外边界接力。Parcel 最终 mask 互斥，但同实例或不同实例都允许直接接壤；相邻不等于合并，各 Parcel 仍保留独立 Area 身份。

required 建筑先按功能区、阵列和道路构图落位，景观不得为了规划完整性反向迫使建筑换位。景观从 owner 附近和周边好地中比较方向、父子拓扑与逐格外形，优先保留更多非零景观和更大实际面积；同面积时再比较距离、长宽比、树深、方向覆盖和分叉。目标 Parcel 放不满就按地形缩减，完全零格写警告；fill/connectivity 只避让实际冻结的景观 spans。

每个 Parcel 的外轮廓必须从唯一根 seed 以四邻接 frontier 逐格生长。`preferredAreaBlocks` 是可用空间充足时的正常完成目标；`maxAreaBlocks` 只是不允许突破的防御上限，不能因为周围仍有空地就继续长满上限。若地形、规划边界、结构或其他 Parcel 提前封闭 frontier，实际面积可以小于目标；只要存在可用格就保留实际结果，完全零格才警告。不允许用扩大到 max 或固定图形补偿其他 Parcel。

frontier 的逐格排序必须共同消费 D3 地形代价、局部同 Parcel 邻接聚合、Blueprint 稳定 seed 派生的多尺度连续扰动，以及 `TOWARD_REFERENCE|AWAY_FROM_REFERENCE|ALONG_WATER` 方向关系。它们决定同一面积下的凹凸、偏移和伸展，但不赋予 AI 逐格坐标。禁止用全局最短路距离场、曼哈顿半径或欧氏半径直接决定整块外壳；固定输入必须复现，改变稳定 seed 或真实地形必须能够改变外轮廓。

LandUse 只执行 D4 按地形冻结的实际非零 Parcel；D6 footprint、主体身份或容量漂移仍明确失败，不在 D6 重新选地或补固定图形。D4 零格 warning 原样保留。optional `FREE_STANDING` 仍逐实例探测，一个 optional 实例失败不影响其他实例。

每次扩张必须校验 D6 footprint、D4 容量、规划边界、地形可通行性和当前占用。候选轮廓可以在搜索时冲突，最终格只能有一个 owner；禁止重叠补数或离开容量兜底。

相邻 Parcel 不合并成一个 Area。父子共享边界由 child 单侧占一格并执行一次；跨 Landscape 优先使用非 `OPEN` 一侧，双方均非 `OPEN` 时按规范化实例 ID 决定唯一 owner。归属和材料必须冻结到计划，禁止依赖 chunk 或执行顺序去重。

## Parcel 内部区域接力生长

每个景观 Parcel 只有一个稳定根起点。第一块区域从根起点逐格扩张；每一块后继区域必须从其父区域的局部边界选取一个相邻格作为新起点，再以自身 frontier 逐格扩张。程序在完整 `memberSpans - exclusionSpans` 上一次性冻结所有区域；输入 mask、方案和 seed 相同，输出 region spans 必须相同，跨 chunk 只裁切冻结结果，不能重新起步。

三条硬契约：

1. 所有被填充格都必须有扩张来源。禁止用圆、菱形、矩形、距离环、预制 mask 或其他固定几何公式生成角色；同样禁止把它们用作快速路径或失败保底。
2. 目标能力中，多样性由 AI 提交的方案权重、角色占比、角色生长偏置和内容权重驱动，但 AI 不接触逐格几何；当前只完成方案引用、角色阶段和占比对区域几何的驱动，内容权重尚未驱动世界内容。
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

## 功能缺口报告：AI 组合与内容权重未闭环

### 分类

这是未完成的产品能力，不是故障修复项。区域接力算法能够消费有序 `roleShares[]` 并逐格扩张，但当前目录、AI 决策和执行层组合后，实际体验仍接近预设模板。

### 当前已完成

- Blueprint 允许每个 Landscape 提交一个或多个 `fillSelection.variants[]`，每个候选携带 `selectionWeight`。
- `roleShares[]` 的顺序、重复角色、`targetShare` 和 `PATCH|CORRIDOR` 会进入 Parcel 内区域接力并影响区域面积与 frontier 偏置。
- 程序按 Parcel 身份和稳定 seed 选择候选；相同输入保持确定性。
- AI 不提交逐格坐标、mask 或固定几何。

### 当前缺口

1. Catalog 同时给出完整角色序列和完整数值示例，现有真实 Blueprint 直接复制示例的阶段顺序、占比与内容权重，没有体现一次城市决策中的重新组合。
2. 只有一个候选的 `variants[]` 仍可填写任意 `selectionWeight`，但单候选必然以 100% 命中，该权重不产生任何差异。首批配置中除农田有两个兼容 Profile 外，花田和林场都只有一个 Profile，方案权重缺少实际选择空间。
3. `contentWeights[]` 目前只被校验并写入 Blueprint、trace 和 SurfacePrintPlan。LandUse worldgen 仍从 Surface Recipe 读取单一 `cropBlockId` 或固定 material slot，没有按权重选择作物、花或树。
4. Decoration 尚未消费 Landscape fill 的 `contentWeights[]`。因此 `crop:wheat/carrot/potato`、`flower:poppy/dandelion/cornflower`、`tree:oak/birch/spruce` 等语义权重不会改变对应 Landscape 的最终多内容分布。
5. 当前自动测试只证明字段可解析、可冻结和区域阶段可扩张，没有证明改变候选权重或内容权重会改变最终选择与世界方块。

### 完成标准

- Catalog 负责给出合法角色、占比范围、生长形式和内容白名单；示例只用于解释，不得成为 AI 必须照抄的唯一序列。
- AI 必须能够在合法范围内重新排列或重复阶段、调整各阶段占比，并在存在多个兼容 Profile 时给出有实际意义的候选权重。
- 单候选权重在契约和 trace 中明确规范化为 100%，不得用 `70/40/50` 等互不相干的数值制造已经发生跨 Landscape 抽样的假象。
- `contentWeights[]` 必须由明确的执行层消费：批量作物/花地表归 LandUse，稀疏树木/灌木归 Decoration；同一内容不得由两层重复铺设。
- 固定 Blueprint、Parcel 和 seed 下内容选择稳定；改变权重后统计分布应发生可验证变化，且仍满足主题内容明显强于间隔内容。
- 自动测试必须覆盖多候选稳定选择、单候选规范化、非示例阶段组合、内容权重到执行操作的映射，以及真实新区块中的多作物、多花种和多树种观测。

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

AI 只在一次 Blueprint 中选择 foundation/landscape Profile、景观用途与来源、目标实例/Parcel 数、自由景观 placement domain，以及填充候选权重、按序角色占比、`PATCH|CORRIDOR` 生长偏置和内容权重。AI 不提交 block ID、逐块坐标、mask、固定形状、方向或道路。程序按地形生成实际几何。

prepare 不注入隐藏默认目录。调用方必须提交完整 `landscapeFillProfiles[]`；服务原样校验、冻结并放入 Context 供 AI 阅读。示例属于 Profile 正式字段，不是提示词外的口头约定。

## RoadWeaver 边界

LandUse 不读取或猜测 RoadWeaver 最终路径。City 自有区内路、城市主路和窄宽 transition 必须先通过真实目的地与临街使用校验，再由 D4 冻结为精确 bands，并在 SurfacePrint v0.7 中转成 slab/curb feature cells；这不是缺 RoadWeaver 时的兜底。RoadWeaver 在景观之后只覆盖 Blueprint 另行确认的外部长距 corridor；缺少 RoadWeaver 时只影响该条已确认连接，不删除 City 自有路。

## 破坏性规则

- 旧 CityBlueprint、引用目录、户外意图和完成标记不自动迁移。
- `SpatialGround.landUseRuleRef`、`SpatialGround.surfaceRecipeRef`、关系骨架 seed 和正式路径 `autoConnect` 删除。
- 正式 workflow 只接受当前冻结 Blueprint/catalog；旧字段 hard fail。
- 旧任务产物和 server-root active LandUse 状态必须清理后重规划，不提供存档版本控制或静默兼容。

## 验收

- 全城只有一个连续基础地板主体，且所有基础地板使用同一冻结配方。
- 基础域无入口线、MST 线、跨组关系线或其他道路状 LandUse 几何。
- 城市基础域内部无未解释原群系洞。
- D4 对完整结构占地执行 `water/slope/localRelief/elevation range` 门禁，不可承载时在同一规划范围内改选；合法城市硬质区域的小坑、沟槽和流体被补平，小凸起被削平，未改高度列不得漏铺 Foundation 地表或边界。
- required 建筑先按城市构图落位；景观不得反向迫使建筑换位，目标数量或面积可按地形缩减，零格只警告；fill/connectivity 只避让实际容量。
- 存在多个完整可行容量方案时不得固定接受首个候选；大型多 Parcel 景观优先形成二维、多方向父子构图，同分方案随稳定 seed 可改变方位但固定输入必须复现。
- required 景观在近地受阻时能离开 owner 与 preferred Patch 找好地；实际 Parcel 数和面积可小于 Blueprint 目标，零格有明确 warning；optional 实例空间不足以零占地 `skipped_insufficient_space` 退出。
- 可用空间充足时每个 Parcel 的实际面积等于自身 `preferredAreaBlocks` 而非统一长到 `maxAreaBlocks`；同面积 Parcel 的外轮廓由稳定 seed、地形和方向关系逐格形成，不得退化为固定圆、菱形或距离球。
- 每个非零实例形成父子树，根由主体种子向外选择地形，不强制紧贴；非根来自父 Parcel 真实边界；固定输入重复编译 hash 一致。
- 各 Parcel 保留独立 Area 和边界，不因同类型或相邻而合并。
- AI 可为同一景观提供多个填充候选及选择权重；固定输入下每个 Parcel 的候选选择稳定。
- 角色目标占比会改变各接力区域的目标面积，`PATCH|CORRIDOR` 只影响 frontier 偏置，不定义固定轮廓或固定宽度。
- 区域接力覆盖 `member - exclusions` 恰好一次；根起点必须是合法格，后继起点必须邻接父区域，断开或无法完成时 hard fail，跨 chunk 不重启。
- `land_use_preview.png` 叠加冻结的区域边界、接力起点、父界面以及主题、田埂、水和地面角色，可直接审阅 Parcel 内部形态与 provenance。
- 花田、绿化带、林场和农田都能通过目录 Profile 选择，不需要修改 Java。
- City 自有区内路/城市主路与已确认的 RoadWeaver 外部长距道路职责分离，双方各自拥有冻结几何并按顺序清理冲突景观；距离或功能区关系不能自动造路。
