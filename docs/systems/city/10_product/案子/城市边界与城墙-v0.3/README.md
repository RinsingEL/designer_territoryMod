# City 案子：城市边界与城墙 v0.3

## 状态

已接入显式 `wallVersion=v3` 开发路径，待真实游玩验收。v0.3 是对 v0.2 真实验收暴露问题的下一版方案；默认路径仍保留 v2 作为对照，直到 v3 完成真实验收后再考虑切默认。

v0.2 已证明两件事：

- 墙带必须早于世界生成进入 mask，否则植被和自然结构会抢占墙体区域。
- 城门必须晚于 RoadWeaver 真实道路生成后裁剪，否则墙会砍断道路。

但 v0.2 的默认边界仍然过度贴合 D3 patch 外露边，容易形成锯齿、凹陷和内部道路穿墙；执行层遇到坡地时会整段跳过，现场会出现“莫名其妙少一块”。v0.3 的目标是把城墙升级为 **结构种子驱动的城市外环墙**，并增加精确 debug 扫描能力，让每个缺口都能追溯到坐标和原因。

## 核心结论

v0.3 不再把 D3 patch 外缘直接当最终墙线。正确口径是：

```text
结构 actualFootprint / sourcePatch
  -> 在 D3 patch 邻接图上扩张城市占地区域
  -> 填掉小凹陷 / 小洞 / 内部道路口袋
  -> 生成单一城市外环 hull
  -> D5 早期预留 wallReservationMask
  -> RoadWeaver 生成真实道路
  -> D7 按真实道路聚类裁门
  -> execute 墙体按短段 / step 适配地形
  -> debug 扫描输出所有缺口坐标和地形 / mask 原因
```

D3 patch 仍是地形事实和扩张单位，但 patch 外露边只是候选边界，不是最终墙线真值。

## 问题背景

真实测试中看到三类问题：

1. **凹陷过深**
   - 城墙沿 patch 边界凹进城市内部。
   - 凹陷中已有内部道路和结构连接点。
   - 结果是同一条内部道路被当成多次穿墙，生成过多 gate / tower / skip。

2. **墙线太碎**
   - v0.2 逐 cell 外露边生成 centerline。
   - 即使拓扑上可闭合，视觉上仍然是锯齿边、局部袋状凹陷和过多短墙段。
   - 它更像“patch 边界图”，不是“城市外壳”。

3. **缺口原因不够可验收**
   - `WALL_TERRAIN_TOO_STEEP` 能解释整段跳过，但现场小缺口可能来自 road mask / structure footprint 逐格保护。
   - 当前 report 没有记录每个被保护坐标、每个 step=1 地形采样点、foundation 到底补了多少。
   - 用户手工飞过去验收时，很难判断是地形报错、mask 抢占、道路保护，还是 planner 本身开了门。

## v0.3 目标

- 生成一个更像城市边界的外环，而不是直接沿 patch 锯齿边放墙。
- 小凹陷、小洞和内部道路口袋默认并入城内。
- 内部道路不再触发城门；只有从外部进入城市的道路才裁门。
- 城墙执行时按更小单元处理地形，避免长段因为局部高差整段消失。
- 对所有缺口输出可手工复核的坐标、mask 类型、地形采样和 reason code。

## City Domain Hull

### 1. 结构种子

输入来自 D6 / D7：

- planned / placed structure `actualFootprint`
- D4 `sourcePatchIds`
- D6 locked collision envelope
- RoadWeaver endpoint / connection plan
- D3 patch member cells、landform type、neighbor patch graph

每个结构先映射到一个或多个 seed patch，再把 `actualFootprint + wallBreathingRoomBlocks` 覆盖到 patch cell grid 上，形成初始城市域。

默认参数：

```text
wallBreathingRoomBlocks = 24
patchExpansionMaxRounds = 4
```

### 2. Patch 扩张评分

从 seed patch 出发，沿 D3 patch 邻接图扩张。扩张不是无脑 BFS，而是按收益决定是否吸收邻接 patch。

通用评分项：

- `structureCoverageGain`：是否能更好包住结构和道路端点。
- `compactnessGain`：是否减少细长触手、锯齿边和墙长。
- `concavityClosureGain`：是否填掉窄口深凹陷。
- `roadPocketGain`：是否把内部结构连接路纳入城内。
- `terrainPenalty`：是否落到过陡山体 / 深水 / 大悬崖。
- `naturalBoundaryBonus`：水岸、崖壁、山脊等是否可作为外侧天然边界。

输出每个被吸收或拒绝 patch 的 reason：

```text
PATCH_SEED_STRUCTURE
PATCH_ABSORBED_COMPACTNESS
PATCH_ABSORBED_CONCAVITY_CLOSURE
PATCH_ABSORBED_INTERNAL_ROAD
PATCH_REJECTED_TERRAIN_STEEP
PATCH_REJECTED_DEEP_WATER
PATCH_REJECTED_LOW_GAIN
```

### 3. 凹陷填充

对 patch-expanded city domain 做 morphology / hull 规整：

- 填掉面积小于阈值的洞。
- 填掉开口窄、深度大的凹陷。
- 去掉细长触手。
- 只保留主连通城市域。

建议首版规则：

```text
concavityOpeningMaxBlocks = 64
concavityDepthRatioMin = 0.6
holeFillMaxAreaBlocks = 4096
appendageWidthMaxBlocks = 32
```

一个凹陷满足以下任意强条件时，应并入城内：

- 内部存在 actualRoadMask。
- 内部靠近两个以上 structure actualFootprint。
- 填充后 wallLength 明显下降。
- 填充后 gateCount 下降。

输出：

```text
concavityFillEvents[]
holeFillEvents[]
appendageTrimEvents[]
```

### 4. 外环生成

从 cleaned city domain 生成最终墙线：

- 只取最大外环。
- 不取内部洞边界。
- 简化短锯齿。
- snap 到 `segmentLengthBlocks`。
- 保留天然边界标记，后续可决定是城墙、栅栏、岸堤还是不放墙。

输出：

```text
cityDomainMask[]
cityDomainHull[]
outerWallRing[]
wallCenterline[]
wallCorridorMask[]
```

## D5 Wall Reservation

v0.3 仍然在 D5 早期生成 wall reservation mask，但来源改为 city domain hull，而不是 patch 外露边。

`wall_reservation_plan.json` 升级为：

```text
schemaVersion = city_wall_reservation_plan.v0.3
boundarySource = structure_seeded_patch_region_hull
```

新增字段：

- `seedPatches[]`
- `patchExpansionTrace[]`
- `cityDomainMask[]`
- `domainCleanupReport`
- `outerWallRing[]`
- `wallCorridorMask[]`
- `wallReservationDebug`

D5 继续把 `wallCorridorMask` 合入：

- `noVegetationMask`
- `vegetationLimitedMask`
- `noVanillaStructureMask`

## RoadWeaver 裁门 v0.3

v0.3 的道路裁门先区分内部道路和外部道路。

### 道路分类

扫描 actual road mask 后，把道路 component 分类：

- `insideRoad`：主要位于 city domain 内，用于连接内部结构，不裁门。
- `externalApproachRoad`：从 city domain 外部进入，才裁门。
- `parallelWallRoad`：沿墙外侧或墙内侧平行，不裁门；必要时 shift wall 或 skip。
- `ambiguousRoad`：分类不确定，进入 debug report。

分类依据：

- road component 与 city domain 的内外穿越次数。
- road component 的端点是否在 domain 外。
- road 与 structure actualFootprint / RoadWeaver endpoint 的连接关系。
- road crossing 与 outerWallRing 的交点聚类。
- 后续 v3.2 不应只看道路方块是否碰到墙，而应拟合 road component 的趋势：只有道路主体从外部进入内部、且穿越距离足够时才开门；贴墙、擦边、零散路面点只进入 debug / skip。

### 城门聚类

v0.2 的问题是每个 segment 命中 road mask 都开门。v0.3 必须先聚类：

```text
road-wall raw intersections
  -> cluster by distance / same road component
  -> one cluster = one gate
```

默认参数：

```text
gateClusterRadiusBlocks = 24
gateWidthBlocks = 9
maxGateCountSoft = 6
```

输出：

- `rawRoadWallIntersections[]`
- `gateClusters[]`
- `generatedGates[]`
- `insideRoadIgnoredIntersections[]`

## 墙体地形适配 v0.3

v0.2 的执行策略是整段采样地形，高差超过阈值就跳过。v0.3 改成短段 / 单列适配。

### 放置单元

执行前把墙段拆成更小 placement units：

- 直墙按 `terrainFitUnitLengthBlocks=3~5` 切段。
- 每个 unit 单独采样地形。
- unit 内高差小则整体放置。
- unit 间允许 step up / step down。

### 地形策略

每个 unit 输出 `terrainFitMode`：

```text
FLAT_PLACED
STEPPED_PLACED
FOUNDATION_FILLED
EMBEDDED_IN_SLOPE
SKIPPED_TOO_STEEP
SKIPPED_FOUNDATION_TOO_DEEP
SKIPPED_PROTECTED_MASK
```

默认不再因为整段某个局部高差过大就跳过完整 segment。

### wallTerrainPolicy v3.1

`wallVersion=v3` 只表示城市外环 hull / 道路聚类裁门这条边界算法。`wallTerrainPolicy=v3.1` 是 v3 的执行层地形策略，不重命名、不替换 v3 边界。

默认阈值：

```text
flatMaxDeltaBlocks = 7
steppedMaxDeltaBlocks = 16
mountainProbeDistanceBlocks = 6
naturalBoundaryMinDeltaBlocks = 17
embeddedSlopeTower = true
```

执行口径：

- 高差 `<=7`：沿用 `FLAT_PLACED` / `FOUNDATION_FILLED` / 低坡 stepped 行为。
- 高差 `8-16`：生成 `STEPPED_WALL_PLACED`，按 2-5 格 step slice 分级落地，不再输出 `WALL_UNIT_SKIPPED_TERRAIN`。
- 高差 `>16` 且一侧 6 格内判定为连续山体：输出 `WALL_EMBEDDED_IN_SLOPE`，墙端嵌入山体并放塔楼或石砌封头。
- 高差 `>16` 且无法嵌坡：输出 `NATURAL_CLIFF_BOUNDARY`，不放连续墙，只放边界塔 / 石砌标记；这类天然边界不应作为普通 gap 处理。

保护优先级不变：`actualRoadMask`、gate gap 和 structure `actualFootprint` 高于任何地形策略；阶梯墙 / 嵌坡墙不得覆盖道路或建筑。

v3.1 的执行层必须使用 `city_wall_plan.wallSegments[].wallAxis` 作为墙段长度主轴。`terrainFitUnit` 和 `stepSlices[]` 都沿该主轴切分，墙体厚度、山体侧 probe 和嵌坡封头也以该主轴为准。不得在 unit 拆碎后再用 unit 的长宽推断主轴，因为 9x8 这类近方形 unit 会把厚度方向误判为长度方向，现场表现为墙上叠墙、错朝向墙片、墙体缺洞和局部悬空。

v3.1 的 foundation 有效深度应覆盖中等坡策略：当 `steppedMaxDeltaBlocks=16` 时，执行层至少能向下补到 16 格，避免 8-16 高差的阶梯墙合法放置但低侧悬空。地形采样还应忽略本轮临时城墙材料的连续顶部，避免重复执行同一 plan 时把旧墙当作地面继续向上叠。

v3.1 report 扩展：

- `terrainPolicyVersion`
- `terrainDeltaBand=LOW|MID|HIGH`
- `terrainFitMode=FLAT_PLACED|FOUNDATION_FILLED|STEPPED_WALL_PLACED|EMBEDDED_IN_SLOPE|NATURAL_CLIFF_BOUNDARY|SKIPPED_UNSUITABLE`
- `stepSlices[]`
- `mountainProbe`
- debug scan 的 `policyDecision`

### Foundation

foundation 从“统一 baseY 向下补”升级为按 column / unit 补：

- 每列记录 surfaceY。
- 每列记录 foundationDepth。
- 超过 `maxFoundationDepthBlocks` 的列只跳过该 unit，或报告需要 terrain work。

## Debug 扫描

v0.3 必须提供可开关的 debug scan。目的不是正式生成依赖，而是让现场缺口可以被复盘。

### 触发方式

`city_execute_city_walls` 增加可选参数：

```json
{
  "debugScan": true,
  "debugScanStepBlocks": 1,
  "debugScanIncludePlacedUnits": true,
  "debugScanIncludeSkippedUnits": true
}
```

首版暂不新增单独调试入口，先通过 `city_execute_city_walls debugScan=true` 输出 debug artifact。后续如需不重新放墙的扫描，可再扩展：

```text
city_debug_scan_city_walls
```

输入：

- `runId`
- `citySeedId`
- `wallPlanSource`
- 可选 `scanBounds`
- 可选 `segmentIds[]`

### Terrain Debug Scan

对每个 skipped / suspicious unit 做 step=1 扫描：

- `x`
- `z`
- `surfaceY`
- `heightDeltaToNeighbors`
- `topBlock`
- `isSolidBelow`
- `isWater`
- `isLeavesOrVegetation`
- `foundationDepthRequired`
- `maxFoundationDepthBlocks`
- `terrainFitDecision`

输出：

- `wall_terrain_debug_scan.json`
- `wall_terrain_debug_preview.png`

### Mask Debug Scan

对所有 protected / skipped 坐标记录：

- `x`
- `z`
- `yRange`
- `maskType`
- `maskId`
- `sourceArtifact`
- `reasonCode`
- `overlappedRoadMaskId`
- `overlappedStructureId`
- `overlappedGateId`

输出：

- `wall_mask_conflict_report.json`
- `wall_mask_conflict_preview.png`

### Gap Debug Report

把最终墙线中不连续、没放、被跳过、被保护的片段统一汇总：

- `gapId`
- `gapBounds`
- `nearestSegmentIds[]`
- `gapLengthBlocks`
- `primaryReason`
- `secondaryReasons[]`
- `manualInspectTp`
- `terrainSampleSummary`
- `maskConflictSummary`

输出：

- `wall_gap_debug_report.json`

## Artifacts

新增 / 升级：

- `wall_reservation_plan.json`
- `wall_reservation_preview.png`
- `city_domain_hull_debug.json`
- `city_domain_hull_preview.png`
- `actual_road_mask.json`
- `city_wall_plan.json`
- `city_wall_preview.png`
- `city_wall_placement_report.json`
- `wall_terrain_debug_scan.json`
- `wall_mask_conflict_report.json`
- `wall_gap_debug_report.json`
- `wall_terrain_debug_preview.png`
- `wall_mask_conflict_preview.png`

## Reason Codes

新增：

```text
PATCH_ABSORBED_CONCAVITY_CLOSURE
PATCH_ABSORBED_INTERNAL_ROAD
PATCH_REJECTED_LOW_GAIN
DOMAIN_HOLE_FILLED
DOMAIN_CONCAVITY_FILLED
DOMAIN_APPENDAGE_TRIMMED
ROAD_CLASSIFIED_INSIDE
ROAD_CLASSIFIED_EXTERNAL_APPROACH
ROAD_CLASSIFIED_PARALLEL_WALL
GATE_CLUSTER_FROM_EXTERNAL_ROAD
WALL_UNIT_STEPPED_PLACED
WALL_UNIT_FOUNDATION_FILLED
WALL_UNIT_EMBEDDED_IN_SLOPE
WALL_UNIT_SKIPPED_TERRAIN
WALL_UNIT_SKIPPED_MASK
STEPPED_WALL_PLACED
WALL_EMBEDDED_IN_SLOPE
NATURAL_CLIFF_BOUNDARY
WALL_UNIT_SKIPPED_UNSUITABLE
WALL_GAP_DEBUG_TERRAIN_CONFIRMED
WALL_GAP_DEBUG_MASK_CONFIRMED
WALL_GAP_DEBUG_PLANNER_CONFIRMED
```

保留并细化：

```text
WALL_TERRAIN_TOO_STEEP
WALL_FOUNDATION_TOO_DEEP
WALL_ROAD_PROTECTED
WALL_STRUCTURE_FOOTPRINT_PROTECTED
WALL_GATE_GAP
```

## 接口口径

复用现有主入口：

- `city_plan_d5`
- `city_plan_city_walls`
- `city_execute_city_walls`

新增可选参数：

```json
{
  "wallVersion": "v3",
  "wallBoundaryMode": "structure_seeded_patch_region_hull",
  "wallBreathingRoomBlocks": 24,
  "patchExpansionMaxRounds": 4,
  "concavityOpeningMaxBlocks": 64,
  "concavityDepthRatioMin": 0.6,
  "holeFillMaxAreaBlocks": 4096,
  "appendageWidthMaxBlocks": 32,
  "gateClusterRadiusBlocks": 24,
  "terrainFitUnitLengthBlocks": 5,
  "wallTerrainPolicy": "v3.1",
  "flatMaxDeltaBlocks": 7,
  "steppedMaxDeltaBlocks": 16,
  "mountainProbeDistanceBlocks": 6,
  "naturalBoundaryMinDeltaBlocks": 17,
  "embeddedSlopeTower": true,
  "debugScan": false,
  "debugScanStepBlocks": 1
}
```

调试入口可选：

- `city_debug_scan_city_walls`（后续可选）

## 验收标准

- D5 wall reservation 仍能进入 noVegetation / noVanillaStructure mask。
- 预览图能显示：
  - D3 patch 底图
  - seed patch
  - patch expansion
  - filled concavity / filled hole
  - final city domain hull
  - outerWallRing
  - actual road mask
  - gate clusters
  - skipped / debug gaps
- 红框类“窄口深凹陷 + 内部道路”应被并入城内，不再产生一串小 gate。
- 内部结构连接道路不裁门；外部进入城市的道路才裁门。
- gate 数量经过聚类后明显少于 v0.2。
- 城墙不覆盖 RoadWeaver 道路和 structure actualFootprint。
- 城墙遇小坡能 stepped / foundation 放置，不因整段高差超过阈值整段消失。
- 显式 `wallTerrainPolicy=v3.1` 时，8-16 高差应生成 `STEPPED_WALL_PLACED`；高差更大处应输出 `WALL_EMBEDDED_IN_SLOPE` 或 `NATURAL_CLIFF_BOUNDARY`，而不是继续产生大量 `WALL_UNIT_SKIPPED_TERRAIN`。
- 每个最终缺口都能在 `wall_gap_debug_report.json` 中找到：
  - 坐标范围
  - 主原因
  - TP 坐标
  - 地形 step=1 扫描摘要或 mask 冲突摘要
- 用户手工飞到缺口位置时，能用 report 解释是地形、mask、gate、planner 还是执行器造成。

## Test Plan

自动测试：

- domain hull：结构 seed patch 能扩张成主连通城市域。
- domain cleanup：窄口深凹陷被填充，小洞被填充，细长触手被剪掉。
- road classification：内部道路不生成 gate，外部穿墙道路生成 gate cluster。
- gate clustering：多个相邻 raw intersections 合并成一个 gate。
- terrain fit：长墙段切成 placement units，小高差 stepped 放置，不整段跳过。
- terrain policy v3.1：8-16 高差生成阶梯墙；高差更大时优先嵌坡，失败后标记天然峭壁边界。
- debug scan：terrain / mask / gap 三类 report 均输出坐标和 reason。
- preview：v3 preview 包含 D3 patch、domain hull、gate cluster、debug gap 图层。

真实游玩测试：

```text
D3
-> envelope profiling
-> D4 v2 candidate session / selection
-> D6 probe-and-lock
-> D5 wall reservation v3
-> execute_d5 激活 mask / RoadWeaver / planned structure
-> 玩家加载新区块
-> D7 ledger
-> plan city walls v3
-> execute city walls v3 with debugScan=true
```

重点验收：

- 城市外环比 v0.2 更完整，少锯齿和少内部凹陷。
- 墙不会围出奇怪口袋，也不会让内部道路反复穿墙。
- 少块时能直接从 debug report 找到坐标和原因。
- v3.1 中等坡应变成阶梯墙；极端坡应能看到嵌山体封头 / 边界塔，或在 report 中标记天然峭壁边界。
- 当前 gate 仍是裁洞式结果，验收时只要求道路不被完全砍断；若出现外侧已开、内侧未开全，记录为后续独立城门结构问题。

## 暂不处理

- 不做最终美术级城门楼。
- 不做护城河和完整防御玩法。
- 不做复杂曲线墙体模板。
- 不把 RoadWeaver 内部 graph API 作为必须依赖；首版仍可扫描真实路面。
- 不把 city domain hull 恢复成旧功能区真值；它只服务墙体、mask 和边界。

## v3.2 后续设计口径

v3.1 的目标是让墙体能在复杂地形上稳定落地。v3.2 的目标应转向“边界系统设计感”：墙不再是唯一边界，城门和塔也不再是墙段副产物，而是独立节点。

### 天然边界

大片水体、海湾、湖泊和高峭崖壁应作为天然屏障，不强行筑连续石墙。v3.2 应把外环边界段分类为：

```text
STONE_WALL
NATURAL_WATER_BOUNDARY
NATURAL_CLIFF_BOUNDARY
QUAY_OR_SEAWALL
BRIDGE_OR_WATER_GATE
```

设计规则：

- 大湖 / 海湾：默认不筑墙，只在码头、桥、浅滩、渡口放 gate / tower / quay。
- 河流穿城：可作为内部运河，不因河岸生成连续城墙。
- 河流穿过外边界：在桥、渡口或道路穿越处生成 `BRIDGE_OR_WATER_GATE`。
- 狭窄溪流：可忽略、涵洞化或短桥化，不额外制造碎墙。

### 可用塔节点

当前 v3.1 的小塔 / 烽火台仍可能退化成一两片墙柱。v3.2 应废弃“碎片塔”，改成有独立 footprint 和内部空间的节点模板：

```text
watchtower_5x5
watchtower_7x7
beacon_5x5
beacon_7x7
slope_cap_tower
```

最小可用塔应至少有 5x5 footprint、内部 3x3 可站立空间、入口或梯子 / 楼梯。空间不足时宁可不放塔，也不放一两片违和墙柱。塔的触发点应限于：外环角点、长墙间隔、城门两侧、天然边界端点、陡坡封头。

### 独立城门结构

城门不应继续只是裁洞式 gate。v3.2 应把城门变成独立结构模板，负责完整切断墙段、保护道路通廊、生成木制 / 石制混合门楼、门洞高度、门侧塔楼和内外道路衔接。

首批模板建议：

```text
gatehouse_9
gatehouse_13
bridge_gate
water_gate
harbor_gate
```

验收重点：不能再出现外侧已开、内侧未开全；门洞必须覆盖道路在城墙厚度方向上的完整穿越范围。

### 道路趋势与门密度

v3.2 的开门逻辑应从“方块命中”升级为“道路趋势”：

- 扫描 road mask 后做连通域。
- 对每个 road component 拟合主方向和穿越向量。
- 只有 component 从 domain 外部进入内部，且在墙两侧都有足够长度支撑时，才生成 gate candidate。
- 多条道路在城墙附近交汇时合并成一个 gate cluster。
- 引入 `minGateSpacingBlocks`，避免城门太密。
- 贴墙平行、擦边、只有少量方块触碰墙的道路，不开门，只记录 `WALL_ROAD_TANGENT_SKIP` / `WALL_ROAD_TOUCH_ONLY_SKIP`。

## 后续方向

- 独立城门结构：城门不再只是墙段裁洞，而是独立 gate template / gatehouse，负责内外两侧完整开口、门洞高度、门侧塔楼和道路衔接。
- 城门楼模板、转角模板、斜墙模板。
- 城墙风格化换皮，与 City palette 联动。
- 天然边界类型：水岸防波堤、崖壁不筑墙、木栅栏农区边界。
- RoadWeaver graph API 深度读取道路拓扑，替代方块扫描。
- 墙体玩法：巡逻、守卫、入口检查、破损修复。
