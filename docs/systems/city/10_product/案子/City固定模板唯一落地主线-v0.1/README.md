# City 案子：固定模板唯一落地主线 v0.1

## 状态

当前实现与契约真值。configured structure / Jigsaw / 动态 bbox 主线已完成破坏性删除；Trek B0.6 的 20 个固定 NBT 已由离线工具导入目标存档。运行时 metadata catalog、潮汐王冠 13 模板重算和真实 `beard_thin` GameTest 仍属于现场验收项，未完成前不得宣称目标城市已落地。

## 一、架构决策

City active 建筑只允许使用固定 NBT `StructureTemplate` 落地。这里保留的是 Minecraft 对结构模板 NBT 的读取、旋转、镜像和方块粘贴能力，不保留 Minecraft worldgen configured structure 系统。所有进入 City catalog 的模板都强制归一为 `terrainPosePolicy=structure_start_beard_thin`。它不查询或选择 configured structure，不进入 Jigsaw，start 内只有一个 exact-footprint City 固定模板 piece；`StructureStart` 的 terrain-adaptation bbox 只供 Minecraft Beardifier 内部使用。

本案从 City active path 删除：

- `Registries.STRUCTURE` / configured structure 查询与选择。
- 外部 `StructureStart` 创建、注入、签名和 piece boxes；唯一保留的是 City 自有单-piece terrain start。
- Jigsaw pool、随机展开、depth / `max_distance_from_center` 规模控制。
- `/place structure` 等价落地和 `StructureStart.placeInChunk` 调试 fallback。
- P50 / P90 / P95 / P99 / maxObserved envelope 多次采样。
- configured structure 与固定模板之间的自动 fallback、自动转换和双轨兼容。

旧字段、旧 artifact 或旧 payload 进入 template-only active endpoint 时必须明确 hard fail，不允许猜测模板、自动查询同名 configured structure，或静默退回旧主线。

## 二、为什么删除 configured structure

Jigsaw 本质上是一套隐藏在资源包中的随机局部规划器：它根据 pool、connector、depth 和随机种子临时决定建筑组合。City 已经有更强的显式 D4 设计层，可以控制关键建筑、阵列、group、间距、方向、道路入口和 LandUse provenance；继续保留 Jigsaw 等于在 D4 之后再运行一次不可完整 review 的弱规划器。

configured structure 带来的额外成本包括：

- D4 只能用统计 envelope 猜测最终范围，不能直接使用精确几何。
- D6 必须再次 dry-run 并锁定 signature / piece boxes，仍要防随机长尾。
- 道路入口难以稳定获得，容易退化为 bbox 外侧伪入口。
- 同一个结构 ID 在不同 seed 下可能得到不同 footprint，影响防撞、LandUse 和城市构图复现。
- `StructureStart` 注入、原版结构引用、生成阶段和 ledger 形成另一套复杂生命周期。
- 外部结构包的随机计划与 City group / array 计划重叠，却缺少 City 的候选、预览、选择和失败解释。

固定模板把“建筑内部长什么样”冻结在 NBT，把“建筑之间如何构成城市”全部交给 City。D4 必须显式给出 `templateId/templateRef + variant`；模板变体不再在 planner 内随机抽样。随机性只允许存在于不会改写建筑 identity 与几何的候选排序或装饰权重中。

## 三、目标主流程

```text
W / T 城市种子
-> D3 城市局部地形与 LandUseTerrainField
-> CityTemplateCatalog 读取 NBT 精确尺寸、hash、旋转、镜像、入口和语义
-> D4 关键模板逐个选点 + 模板阵列 / group 构图
-> D5 按精确 transformed footprint 生成 reservation / wall 轻量预案
-> D6 校验并锁定模板 identity、精确 footprint、collision、mask 和 owner chunks
-> LandUseAreaPlan 从模板建筑 / group 扩张
-> DecorationProgram 引用 LandUseAreaPlan
-> confirmWorldMutation=false 人工 review
-> execute_d5 激活 template placement / mask / LandUse / Decoration / RoadWeaver 计划
-> `ChunkGenerator.createStructures` 注入 City 单-piece template start
-> 原版 structure 阶段按 owner chunk 粘贴固定模板
-> LandUse surface / boundary
-> Decoration fragment
-> template / LandUse / Decoration ledger
-> RoadWeaver 与城墙后续处理
```

City 模板只通过 `ChunkGenerator.createStructures` 写入 City 注册的单-piece start。`tryGenerateStructure` 只保留原版 / 模组自然结构 mask 抑制，不生成 City 建筑；FEATURES 阶段也不再存在 direct-template 补贴或 late materialization。

## 四、输入真值

### 4.1 模板几何真值

每个模板的唯一几何真值是 `StructureTemplateManager` 读取到的 NBT：

```text
rawSize + rotation + mirror + anchor
= exact transformed world footprint
```

任何配置、TerraSense profile 或历史 artifact 都不能覆盖 NBT 尺寸。D4、D5、D6、worldgen 和 ledger 必须由同一模板 identity 复算完全一致的 closed footprint。

### 4.2 模板目录真值

`CityTemplateCatalog` 至少登记：

- `templateId`、`templateRef`、`contentHash` 和 `variantId`。
- 允许的 rotations / mirrors。
- 本地 `roadEntrances[]` 与方向；旋转、镜像后转换为世界入口。
- `clearanceBlocks`、terrain pose / support policy。
- TerraSense 语义引用或可追溯 tag source。

目录 loader 必须从 NBT 重新校验 hash 和尺寸。外部素材接入时，工具可自动扫描客观字段；人工只负责语义 tag、入口和少量不能由 NBT 推导的策略。

### 4.3 TerraSense 职责

TerraSense 保留为语义与检索真值：住宅、农业、商业、市政、地标、风格和用途等 tag 仍由它提供。TerraSense 不再为 City active 建筑提供 footprint、P95/P99 envelope 或 configured structure registry identity。

## 五、阶段职责调整

### 5.1 D2 / 模板导入

- 读取模板目录和 NBT，输出可检索的模板 facts。
- 校验 template identity、精确尺寸、hash、旋转、镜像和道路入口。
- 不调用 `city_profile_structure_envelopes`，不做随机采样。

### 5.2 D3

D3 地貌 patch、城市 review package 和 LandUseTerrainField 保持不变。D3 不读取建筑 NBT，也不选择模板。

### 5.3 D4

- 关键建筑、普通建筑和 array / composite group 全部选择 `templateId` / `variantId`。
- 候选防撞只使用精确 transformed footprint + `clearanceBlocks`。
- 自动 spacing 由模板实际宽深和 clearance 推导；显式 spacing 仍需通过精确 collision 校验。
- D4 保留 placement group、array zone、设计 slot、方向和道路入口 provenance。
- 领域名 `StructureAnchorPlan` 可以暂时保留为“建筑锚点”的通用名，但其中不得再出现 Minecraft configured `structureId` 语义。

对于 4-5 栋紧凑住宅，推荐 `minCount=4`、`targetCount=5`、`maxCount=5`；每栋 `clearanceBlocks=5` 时，两栋实际 footprint 之间可形成约 10 格净空。容量不足时只允许按显式 count policy 降到 4 栋，不能重叠或缩小 clearance。

### 5.4 D5

- `collisionEnvelope = transformedFootprint + clearanceBlocks`。
- `maskEnvelope = collisionEnvelope + maskMarginBlocks`。
- reservation、植被、自然结构和城墙上下文全部来自精确模板几何。
- RoadWeaver 只读取 transformed `roadEntrances[]`；缺入口必须 hard fail 或由调用方显式 `roadProvider=none`，不得生成 bbox 伪入口。

### 5.5 D6

D6 保留“最终锁定”职责，但删除随机结构 probe：

- 重新读取 NBT 并校验 template hash / raw size。
- 校验 rotation / mirror / anchor 和精确 transformed footprint。
- 检查模板之间、模板与既有 ledger 的 collision。
- 检查 owner chunks 尚未进入禁止阶段。
- 锁定 placement identity、datum policy、road entrances、collision / mask 和 owner range。

D6 不再输出 `pieceBoxes`、`expectedStartSignature`、`lockedBBoxGroupKey` 或任何 envelope sample 引用。

### 5.6 Worldgen 与 ledger

- 由 City 自己的 active template placement registry 驱动 `MinecraftCityWorldgenStructurePlacer`。
- anchor owner 首次进入 `createStructures` 时按锁定 identity 读取 NBT，以 generator base height 冻结 datum 并创建唯一单-piece start；piece 再按 owner chunk 确定性粘贴。
- ledger 记录 template identity、世界 anchor、rotation / mirror、datumY、精确 footprint、hash 和 appliedAt。
- 重复 hook、重启和 chunk 生成顺序不能导致重复粘贴或不同结果。
- `city_execute_d7` 若继续保留，只负责读取 template ledger、汇总 actual placement 和驱动道路 / 城墙后处理，不再创建或补放建筑。

## 六、破坏性契约变化

实现时必须同步更新 City 数据契约、MCP 接口、代码导览、测试入口和影响面。

必须删除或退场：

- MCP / HTTP `city_profile_structure_envelopes`。
- `terrasenseProfileSource + configured structureIds[]` 作为 D4 建筑几何输入的路径。
- `materializationMode=minecraft_place_structure|bounded_jigsaw`。
- D6 `plannedWorldgenStructures[]` 中的 registry structure、piece、signature 和 bbox group 字段。
- configured structure active registry、worldgen placement ledger 字段和相关 reason codes。
- `debugLateMaterialize` 与 `worldedit_debug` 之外的建筑 late paste；道路 debug provider 不受此条影响。

必须新增或锁定：

- template-only 的 D4 key / array 输入，只接受模板目录 identity。
- template-only D6 placement plan / completion marker。
- active template placement registry 与 template placement ledger 的唯一 schema。
- 旧 configured payload 的统一 hard fail，例如 `CITY_CONFIGURED_STRUCTURE_FLOW_REMOVED`。

不要求为了删除旧分支而重命名所有包含 `Structure` 的通用领域类；只有确实表达 Minecraft configured structure / `StructureStart` 的类型、字段和 artifact 才必须删除或改名。

## 七、实现删除面

### 7.1 直接删除

- `CityStructureEnvelopeProfiler`。
- `CityStructureEnvelopeFacts`。
- `MinecraftCityStructureEnvelopeSampler`。
- `MinecraftCityStructureMaterializationBackend` 旧 late materialize backend。
- `city_profile_structure_envelopes` 的 HTTP、MCP handler、tool schema、artifact 和测试。
- configured structure 专用稳定性测试、sample cache 和 preview。

### 7.2 拆除 configured 分支后保留模板能力

- `CityStructureProfileCatalog`：只保留与模板语义检索仍有明确价值的部分，否则由 `CityTemplateCatalog` 替代。
- `CityStructureCandidateEnvelope`：删除 P95/P99 / max distance 分支，只从 `CityTemplatePlacementGeometry` 构造精确 envelope。
- `CityStructureMaterializationPlanner`：删除 configured / jigsaw mode，只生成 template placement。
- `CityReservationMaskRegistry`：删除 planned configured structure registry；模板 placement registry 应独立命名、独立 schema。
- `MinecraftCityWorldgenStructurePlacer`：删除 configured / 外部 `StructureStart` 分支，只保留 City 注册单-piece terrain start。
- `ChunkGeneratorStructureMaskMixin`：`tryGenerateStructure` 只做自然结构 mask；`createStructures` 只注入冻结的 City template start；FEATURES 只处理 LandUse / Decoration 与观测。
- D4 key、array、continuous expansion planner：删除 `structureIds[]` configured 分支，只消费模板 selections。

### 7.3 保留

- `CityTemplateCatalog` / `CityTemplateCatalogLoader`。
- `MinecraftCityTemplateReader`。
- `CityTemplatePlacementGeometry`。
- `CityTemplateRuntimeTransform`。
- D3、LandUse、Decoration、RoadWeaver、城墙和原版自然结构抑制能力。

## 八、开发阶段

### 阶段 A：契约与入口切换

- 锁定 template-only payload、artifact 和 reason codes。
- 从默认 workflow 删除 envelope profiling step。
- 旧 configured 请求统一 hard fail，不再写兼容 artifact。

### 阶段 B：D4 模板唯一规划

- key candidate session、array fill、array loop、continuous expansion 全部改用模板目录。
- 自动 spacing、occupied field、group provenance 只认精确模板 footprint。
- 补 4-5 栋住宅、10 格净空、旋转 / 镜像和混合模板阵列测试。

### 阶段 C：D5 / D6 精确锁定

- D5 只使用 exact collision / mask。
- D6 删除随机 probe、piece 和 signature，改为 template identity 复算与 chunk preflight。
- RoadWeaver 入口只来自模板目录。

### 阶段 D：Worldgen 模板落地

- 激活独立 template placement registry。
- `createStructures` 注入单-piece start，原版 structure owner chunk 确定性粘贴模板并写 ledger。
- template -> LandUse -> Decoration 的执行顺序、事务边界和幂等性明确可测。

### 阶段 E：物理删除与文档收口

- 删除 configured / envelope / 外部 StructureStart / Jigsaw 代码与测试；保留并独立验收目录配置驱动的 City terrain start。
- 更新代码导览、测试入口、影响面、City README 和案子状态索引。
- 将旧 D3-D6 configured 主线降为历史参考，固定模板唯一落地主线升为当前真值。

## 九、验收

### 自动测试

- NBT raw size、hash、rotation、mirror 与 transformed footprint 全链一致。
- D4 五栋住宅 group 可按精确 footprint 排布；`clearanceBlocks=5` 时实际房体净空不小于 10 格。
- 容量只够四栋时，只有显式 `minCount=4` 才允许降级；否则 hard fail。
- D5 mask 与 D6 locked footprint 都能由模板 identity 复算，禁止第二份 bbox 真值。
- D6 不产出 piece / signature / bbox group 字段。
- worldgen template placement 幂等，ledger 写失败不提前标记成功。
- 旧 `structureId`、configured mode、bounded jigsaw 和 envelope source 输入全部 hard fail。
- active City 代码不查询外部 configured `Registries.STRUCTURE`，不读取 Jigsaw pool；所有 City catalog 模板在规划期强制冻结为 `terrainPosePolicy=structure_start_beard_thin`，且只能构造 City 注册的单-piece `StructureStart`。

### 真实游玩

1. 在全新未生成区域放置 1 个市政模板和 4-5 个住宅模板。
2. 人工检查住宅紧凑、净空约 10 格、旋转与入口方向可读。
3. 同一住宅 group 只生成一个连续 `residential` LandUse 区域。
4. RoadWeaver 从模板真实入口接路，结构距离采用 RoadWeaver 自身配置。
5. LandUse 与 Decoration 在首次 owner chunk worldgen 落地，ledger 完整且重启不重复。
6. 日志、trace 和 artifact 不出现 configured structure profiling、外部 StructureStart 或 Jigsaw 执行；启用 `structure_start_beard_thin` 的试验模板只允许出现 City 注册的单-piece start 和 `beard_thin`。

### 删除门槛

实现仓库 active City 源码中，对下列内容的引用必须归零；历史归档和明确的 legacy rejection 常量除外：

- `CityStructureEnvelopeProfiler`
- `MinecraftCityStructureEnvelopeSampler`
- 范围外模板的 `StructureStart`
- `bounded_jigsaw`
- `minecraft_place_structure`
- `debugLateMaterialize`
- `city_profile_structure_envelopes`

## 十、不做

- 不自动把任意 configured structure 或 Jigsaw pool 转换成模板。
- 不保留 Trek configured structure 作为正式验收 fallback。
- 不支持旧 chunk 建筑回填。
- 不让模板内部再运行随机 Jigsaw。
- 不在本案开发素材编辑器、模板市场或自动建筑生成器。
- 不因删除 configured structure 而重做 D3、LandUse、Decoration、RoadWeaver 或城墙算法。

## 十一、完成定义

只有在默认 `city_run_workflow` 不再执行 envelope profiling、D4-D6 只消费固定模板、所有 catalog 模板都冻结为 `structure_start_beard_thin`、旧 configured payload 全部明确拒绝，并完成“五栋住宅 + 10 格净空 + group LandUse + RoadWeaver”真实游玩验收后，本案才算完成。City terrain start 仍需按地形适配试验完成真实游玩验收。
