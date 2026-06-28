# City 案子：D3-D6 结构落地驱动城市重构 v0.1

## 定位

本文是 City 新主线草案，替代“先画功能区再塞结构”的方向。它先记录核心目的和阶段职责，暂不展开完整契约。

## 核心目的

D3 已经产出足够多的地形 patch、指标、标签和成员 cell，后续阶段不再重复做地形识别，也不再先生成硬功能区边界。

新主线：

```text
D3 地形 patch 真值
  -> D4 结构落脚点规划
  -> D5 结构保留 mask / feature 抑制
  -> D6 chunk 加载后真实结构落地
  -> 根据已落结构群反推功能区
```

## D3 地形 patch 真值

D3 负责提供结构选址所需的地形事实。当前实现已经具备这层能力，本案不要求重写 D3：

- 地形 patch、memberCells、面积和边界。
- 水岸、平地、坡地、高点、森林 / 植被密度、已有占用等标签或指标。
- 局部高度、坡度、水体、连通性和 patch 邻接关系。

D3 之后的阶段消费这些事实，不重新识别地形。

## D4 结构落脚点规划

D4 直接根据 D3 patch 信息选择合适的结构和落脚点。

职责：

- 由 AI / review 过程基于 D3 地形 patch 选择结构类型和 anchor。
- 消费 TerraSense 导出的结构画像、tag 白名单和 placement / terrain / feature terms。
- 固定大小结构使用自身 footprint + clearance 做防撞。
- 非固定大小 jigsaw 结构使用 `reservedEnvelope` 做防撞。
- 输出结构规划、保留范围、道路 / 水岸接入意图和后续功能区归类线索。
- 禁止同一城市范围内原版自然结构生成抢占 D4 已规划区域。

D4 不做：

- 不重新划分功能区。
- 不重复标注地形。
- 不在 City 侧创建新的结构语义 tag 枚举，也不把 TerraSense tag 转成另一套 City functionTag / functionType 白名单。
- 不默认 dry-run jigsaw 再交给后续阶段重新 place。
- 不要求非固定结构精确等于最终 bbox。

### TerraSense tag 真值

D4 的结构选择必须以 TerraSense 输出为 tag 真值来源：

- 允许消费 TerraSense 已有 tag 白名单、结构画像、结构尺寸、入口类型、placement terms、terrain terms 和 feature terms。
- AI 可以阅读这些 tag 和 D3 地形 patch 事实来选择结构与落脚点。
- City 只负责把 TerraSense tag 原样带入 trace / preview / scoring，不再发明新的结构语义枚举。

禁止：

- 禁止在 City 代码中新增大量 `functionTag`、`functionType`、`structureRole` 等语义枚举来重新解释 TerraSense。
- 禁止把 TerraSense tag 映射成另一套隐藏白名单后再参与结构筛选。
- 禁止因为某个结构没有命中 City 自定义枚举就把它过滤掉。
- 禁止让 D4/D6 的结构选择依赖旧式硬编码功能区类型。

### 非固定结构 reservedEnvelope

非固定大小结构先用保守 envelope 防撞：

```text
reservedEnvelope =
  startTemplateFootprint
  + jigsawMaxExpansionRadius
  + clearance
  + roadAccessMargin
```

防撞规则：

- 两个结构的 `reservedEnvelope` 默认不得重叠。
- 固定结构的 `footprint + clearance` 不得进入其他结构的 `reservedEnvelope`。
- D4 可以接受结构之间比实际需要更远，以换取稳定性。
- D6 真实落地后，用实际 bbox / pieces 更新 ledger，但不能突破 D4 的保留策略。

### depth 与规模稳定

Jigsaw configured structure 自身有 `size` / maxDepth 和 `max_distance_from_center` 这类规模参数。D4 可以把它们作为 `reservedEnvelope` 的来源：

- `size` / maxDepth 控制 jigsaw 最多展开多少层，能让结构规模更稳定。
- `max_distance_from_center` 是更直接的水平扩展上限，适合推导保守半径。
- terrain adaptation 可能额外扩 bbox，保守半径要把这部分算进去。

注意：

- depth 不是精确面积开关，只是展开上限。
- 防撞不能只靠 depth，仍以 `reservedEnvelope` 为准。
- 如果结构包的 profile 缺少可靠半径，宁可保守放大，接受更稀疏。

## D5 结构保留 mask / feature 抑制

D5 根据 D4 的结构规划，把每个结构和道路 / 接入区往外扩一圈生成 mask。

目标：

- 对新生成 chunk 或尚未跑 biome decoration 的 chunk，阻止城市保留区内生成树、草、花、藤蔓、灌木等 feature。
- 让道路、结构落地区、clearance 和水岸接入区在植被生成前被保护。

输出：

- `noVegetationMask`：禁止树和软植被生成。
- `vegetationLimitedMask`：允许低风险装饰，但不允许树干 / 树冠进入。
- `noVanillaStructureMask`：阻止原版自然结构抢占 D4 规划区域。
- `reservationReason`：记录 mask 来自结构、道路、clearance、水岸接入还是已有占用。

D5 不负责：

- 不清理已经生成出来的半截树。
- 不决定结构最终长成什么样。
- 不把 mask 当成功能区硬边界。

## D6 道路生成与真实结构落地

D6 在相关 chunk 加载到位后执行道路生成和真实结构落地。

职责：

- 检查 D4 规划的 anchor / envelope / mask 是否仍有效。
- 复用当前道路生成能力，围绕 D4 / D5 的结构保留区外圈生成道路、接入口和结构群之间的连接路。
- 对固定结构按固定 footprint 直接放置。
- 对非固定 jigsaw 结构调用原版 configured structure 生成和落地。
- 真实落地后记录 actual bbox / piece footprint。
- 结构群落地后，根据 footprint、clearance、influence area、道路和水岸关系反推功能区。

当前可复用能力：

- `CityRoadBoundaryPlanner` 的节点、主路 / 支路和 A* 网格寻路能力。
- `RoadIntent` / `BoundaryIntent` / `BuildOperationPlan` 的结构化输出。
- `BuildableAreaMapBuilder` 对道路、边界和 reserved footprint 的栅格扣除能力。

重构方向：

- 旧输入是 `FunctionZoneMap`。
- 新输入应改为 D4 结构规划、`reservedEnvelope`、D5 mask、结构群中心和接入口。
- 道路不再服务预设功能区边界，而是服务已规划结构：外圈路、入口路、结构间连接路、水岸 / 高点接入路。
- 道路本身也应进入 D5 mask，避免新 chunk feature 把路线上长满树。

关键原则：

- D4 如果没有持久化同一份 `StructureStart`，D6 就不能假装复用 D4 dry-run 结果。
- 初版默认不在 D4 做精确 dry-run；D4 只做保守 envelope 规划。
- D6 落地时可以生成真实 `StructureStart`，但实际结果必须被 ledger 记录并用于后续结构避让和功能区归类。

## 原版生成顺序依据

1.20.1 中 chunk 生成顺序包含：

```text
STRUCTURE_STARTS
STRUCTURE_REFERENCES
BIOMES / NOISE / SURFACE / CARVERS
FEATURES
```

`FEATURES` 阶段会先按 structure generation step 调用 `StructureStart.placeInChunk(...)`，之后再放 biome features。原版并不是提供一个通用“结构区禁树 mask”，而是结构先写入后，很多 feature 因为方块和地面条件自然失败。

因此本案仍保留 D5 mask，避免道路、clearance、未来接入区被植被抢占。

## 首轮成功标准

- D3 作为已完善的地形 patch 真值层被复用，不重复实现。
- D4 能基于 D3 patch 直接规划结构和 anchor，不再生成预设功能区边界。
- D4 只消费 TerraSense tag 白名单和结构画像，不创建新的 City 语义 tag 枚举。
- 固定结构用 footprint 防撞，非固定结构用 `reservedEnvelope` 防撞。
- jigsaw 结构的 depth / max distance 能进入 reservedEnvelope 推导。
- D5 能在新生成 chunk 中阻止城市保留区生成植被和自然结构。
- D6 能复用现有道路生成能力，为结构保留区外圈和结构间连接生成道路 mask / operation。
- D6 真实落地后能记录 actual bbox / pieces，并反推功能区。
