# City 案子：D3-D6 结构落地驱动城市重构 v0.1

## 定位

本文是 City 当前 active 主线真值，替代“先画功能区再塞结构”的方向。它记录核心目的、阶段职责、接口和验收口径。

## 破坏性重构口径

本案按破坏性重构处理，不再为旧的“功能区优先 -> 结构填充”主链做兼容。

需要直接切断的旧逻辑：

- 旧式预设功能区边界驱动结构选择。
- City 侧 `functionTag` / `functionType` / `structureRole` 等自建语义枚举和隐藏映射。
- `function_candidates` / compat catalog 等旧结构筛选字段。
- 通过多 start 追 D6 面积占比的默认路径。
- D4 dry-run 后 D6 重新随机 place，却假装复用同一份结果的流程。

新主线只承认：

- D3 地形 patch 真值。
- TerraSense tag 白名单和结构画像。
- D4 结构落脚点、`reservedEnvelope` 和道路 / 接入意图。
- D5 feature / vanilla structure 抑制 mask，以及生成期 planned structure registry。
- D6/D7 worldgen-time ledger、actual bbox / pieces / inferred function area。

如果旧字段或旧流程仍被调用，应显式失败并暴露错误，不允许静默回退、自动补兼容或把旧逻辑藏在新接口后面。

## 核心目的

D3 已经产出足够多的地形 patch、指标、标签和成员 cell，后续阶段不再重复做地形识别，也不再先生成硬功能区边界。

新主线：

```text
D3 地形 patch 真值
  -> configured structure envelope profiling
  -> D4 结构落脚点规划
  -> D5 结构保留 mask / planned structure 生成期注册
  -> D6 worldgen 计划校验
  -> chunk 首次生成时由 worldgen hook 写入 StructureStart
  -> city_execute_d7 查询 worldgen ledger
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
- 非固定大小 configured structure 优先使用 envelope facts 的 P95/P99 bbox 做防撞和 mask。
- 输出结构规划、保留范围、道路 / 水岸接入意图和后续功能区归类线索。
- 禁止同一城市范围内原版自然结构生成抢占 D4 已规划区域。
- active endpoint 名称继续复用 `city_plan_d4`，但 required payload 改为 `runId`、`citySeedId`、`terrasenseProfileSource`、`structureAnchorPlan`。

输出：

- `structure_anchor_plan.json`
- `structure_anchor_map.json`
- `structure_profile_catalog.json`
- `structure_anchor_preview.png`
- `quality_report.json`

D4 不做：

- 不重新划分功能区。
- 不重复标注地形。
- 不在 City 侧创建新的结构语义 tag 枚举，也不把 TerraSense tag 转成另一套 City functionTag / functionType 白名单。
- 不默认 dry-run jigsaw 再交给后续阶段重新 place。
- 不要求非固定结构精确等于最终 bbox。

## Structure Envelope Facts

在 Trek 等结构包测试链路中，D4 前先对顶层 configured structure 做非写世界 bbox 采样，产出 `structure_envelope_facts.json`。这里的“顶层”指可通过 `/place structure <id>` 触发的 `worldgen/structure/*.json` registry entry，不把 `trek:village/.../houses|streets|decor` 等子模板当作 D4 anchor。

当前测试套件先固定为：

| 分区 | configured structures |
| --- | --- |
| 农业区 | `trek:overworld/medium/farm`、`trek:overworld/medium/plains_cottage`、`trek:overworld/medium/beehive_house` |
| 居住区 | `trek:overworld/medium/spruce_cottage`、`trek:overworld/common/mushroom_house`、`trek:overworld/medium/dirt_hut` |
| 商业港口区 | `trek:overworld/medium/dark_oak_trade`、`trek:overworld/medium/small_red_trade`、`trek:overworld/medium/ship_pillager` |
| 行政区 | `trek:overworld/rare/villager_castle`、`trek:overworld/medium/fort`、`trek:overworld/medium/square_tower` |

默认布局意图：

- 行政城堡居中或高点，作为视觉核心。
- 居住区贴近行政区。
- 农业区放在开阔缓坡外圈。
- 商业港口区沿水岸。
- D5 / D7 后处理连接行政区到港口的主轴路，并给农业 / 居住区生成支路。

`city_profile_structure_envelopes` 默认每结构采样 256 次，不写世界，输出：

- `localEnvelopeP50/P90/P95/P99`。
- `maxObservedEnvelope`。
- piece count / area 的统计区间。
- invalid ratio、failure summary。
- TerraSense profile hash、structure config hash、source pack hash。
- `structure_envelope_profile_preview.png`。

使用规则：

- `collisionEnvelope = localEnvelopeP95 + clearanceBlocks`，用于 D4 防撞。
- `maskEnvelope = localEnvelopeP99 + vegetationMarginBlocks`，用于 D5 禁植被 / 禁自然结构。
- `safetyEnvelope = maxObservedEnvelope` 或结构自身 max distance 兜底，用于 trace / 越界诊断。
- 对本轮 Trek 测试结构，facts 缺失或 hash 不匹配必须 hard fail，不回退到旧大半径。
- P95 是布局防撞用的统计 envelope，不承诺覆盖全部长尾；D6 preflight 和 worldgen signature gate 负责兜住实际长尾。

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

### 非固定结构 envelope 策略

有 envelope facts 时，非固定大小结构使用统计 envelope：

```text
collisionEnvelope = P95 local bbox + clearance
maskEnvelope      = P99 local bbox + vegetationMargin
safetyEnvelope    = maxObserved 或 max_distance_from_center 兜底
```

没有 envelope facts 的非 Trek 结构，才允许使用保守 envelope 防撞：

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
- worldgen hook 真实落地后，用实际 bbox / pieces 更新 ledger，但不能突破 D4 的 collision envelope。

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
- `road_access_plan.json` / `build_operation_plan.json`：道路围绕结构 envelope 和入口连接生成，不围绕功能区边界生成。
- `reservation_mask_preview.png`：展示结构保留区、禁植被区和禁自然结构区。
- `city_execute_d5` 激活 server-root `geomantia_city_masks/active_reservation_mask_plan.json` 和 `active_planned_structure_registry.json`，并要求 `confirmWorldMutation=true`。
- active path 不主动执行 WorldEdit 道路 / 清理操作，避免 D5 自己提前生成目标 chunk；这些 operation 作为后处理计划保留。
- D5 mask 优先使用 D4 `maskEnvelope`，道路 corridor 也进入 noVegetation mask。
- hook 或 registry 不可用时必须 hard fail，reasonCode 为 `CITY_WORLDGEN_STRUCTURE_HOOK_UNAVAILABLE` / `CITY_MASK_HOOK_UNAVAILABLE`。

D5 不负责：

- 不清理已经生成出来的半截树。
- 不决定结构最终长成什么样。
- 不把 mask 当成功能区硬边界。

## D6/D7 Worldgen-Time 结构落地

当前 active path 不再在已生成 chunk 上 late paste 结构。结构必须在 Minecraft worldgen 的 `STRUCTURE_STARTS` / `ChunkGenerator.createStructures(...)` 阶段注入，随后由原版 `createReferences` 和 `FEATURES` 流程继续处理。

职责：

- `city_plan_d6` 读取 D4 `structure_anchor_map.json` 和 D5 `reservation_mask_plan.json`，输出 `plannedWorldgenStructures[]`、anchor chunk、reserved envelope 和 required chunk range。
- `city_plan_d6` 不写世界，不要求目标 chunk loaded；未执行 `city_execute_d5` 时也可以先产出 planned_worldgen preflight 计划。
- `city_plan_d6` 对 selected anchor 使用 configured structure registry 做 non-mutating preflight，记录 actual bbox、piece boxes 和 `expectedStartSignature`。
- 若目标 chunk 已经到 `FEATURES` 或之后且 worldgen ledger 没有记录，返回 `STRUCTURE_CHUNK_ALREADY_GENERATED`，不得继续走 active placement。
- `city_execute_d7 executeStructurePlacement=true` 默认只检查 worldgen ledger / chunk 状态，不调用 `StructureStart.placeInChunk`。
- 生成期 hook 在 planned anchor chunk 命中时，用 configured structure registry 生成 `StructureStart`，校验 bbox 不突破 D4 `reservedEnvelope` 后写入 `ChunkAccess.setStartForStructure(...)`。
- 生成期 hook 必须校验 `expectedStartSignature`，不一致时记录 `START_SIGNATURE_MISMATCH`，不得写入成功 ledger。
- hook 记录 `worldgen_placement_ledger.json`，包含 actual bbox、piece boxes、`startSignature`、anchor、TerraSense terms 和生成 chunk。
- `city_execute_d7` 看到 ledger 后写 `placed_structure_ledger.json`、`structure_materialization_trace.json`、`inferred_function_area_map.json`、`placed_structure_preview.png`。
- 所有 planned structure 均已有 worldgen ledger 后，`city_execute_d7` 可执行 deferred road surface / clear operations；这只属于道路后处理，不允许 paste structure。
- `debugLateMaterialize=true` 是显式开发诊断入口，才允许旧 `StructureStart.placeInChunk` 路径；trace 必须标记 `lateMaterialization=true`，不得作为正式验收通过。

关键原则：

- active path 不支持“森林已经生成后再补贴结构”。
- D5 只激活生成期 mask / planned structure registry，不主动触发目标 chunk 生成。
- 植被处理只保留生成期 feature 抑制，不新增清树兜底。
- 若 worldgen hook 无法稳定写入 structure start storage，必须 hard fail `CITY_WORLDGEN_STRUCTURE_HOOK_UNAVAILABLE`，不能静默退回 late paste。

## 原版生成顺序依据

1.20.1 中 chunk 生成顺序包含：

```text
STRUCTURE_STARTS
STRUCTURE_REFERENCES
BIOMES / NOISE / SURFACE / CARVERS
FEATURES
```

`FEATURES` 阶段会先按 structure generation step 调用 `StructureStart.placeInChunk(...)`，之后再放 biome features。原版并不是提供一个通用“结构区禁树 mask”，而是结构先写入后，很多 feature 因为方块和地面条件自然失败。

因此本案保留 D5 mask，并把 planned structure 注册提前到 `createStructures` 阶段，避免道路、clearance、未来接入区被植被抢占。

## 首轮成功标准

- D3 作为已完善的地形 patch 真值层被复用，不重复实现。
- D4 能基于 D3 patch 直接规划结构和 anchor，不再生成预设功能区边界。
- D4 只消费 TerraSense tag 白名单和结构画像，不创建新的 City 语义 tag 枚举。
- 固定结构用 footprint 防撞，非固定结构用 `reservedEnvelope` 防撞。
- Trek 测试结构使用 P95 collision envelope、P99 mask envelope；facts 缺失或 hash 不匹配必须 hard fail。
- jigsaw 结构的 depth / max distance 能进入 reservedEnvelope 推导。
- D5 能在新生成 chunk 中阻止城市保留区生成植被和自然结构，并激活 planned structure registry。
- D6 输出 `plannedWorldgenStructures[]`、actual bbox、piece boxes、`expectedStartSignature`，未生成 chunk 进入 `WAITING_FOR_WORLDGEN`，已生成 chunk 拒绝 late paste。
- chunk 首次生成时 worldgen hook 能记录 actual bbox / pieces；D7 只消费 ledger 并反推功能区。
- `city_plan_d4` / `city_plan_d5` / `city_plan_d6` / `city_execute_d7` 遇到旧字段或旧 artifact 必须显式失败：`LEGACY_CITY_FUNCTION_ZONE_FLOW_REMOVED`。
- 预览图能看到 anchor envelope、mask、planned worldgen structures、piece boxes 和 worldgen ledger。
- trace 能回答为什么等待、失败、重叠、越界或签名不一致。
