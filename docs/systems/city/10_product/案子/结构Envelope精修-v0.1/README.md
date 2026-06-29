# City 案子：结构 Envelope 精修 v0.1

## 定位

本案是 `D3-D6结构落地驱动城市重构-v0.1` 之后的第一阶段优化。目标是解决当前结构之间视觉距离偏远、preview 中 bbox 过于保守的问题。

本案只处理 envelope / bbox 策略，不扩展新的城市功能区、不接入 Road Weaver、不做结构地形适配。道路只做一处必要调整：D5 不再提前固定道路，D7 在 worldgen ledger 完整后按真实 `actualFootprint` 生成调试道路 / 边界。

## 核心判断

当前问题不需要先拆成很多结构类别。先用两个口径处理：

1. 固定大小结构的问题是“朝向包络过大”。
2. 非固定大小结构的问题是“固定 depth / size 配置下的生成范围统计”。

## 口径一：固定大小结构的朝向包络

固定大小结构或近固定大小结构，本体大小通常已经明确。当前 bbox 偏大的主要原因不是结构本身不稳定，而是 profiling 把不同朝向 / 不同 chunk seed 下的 bbox 合成了一个全方向包络。

这会导致：

- preview 中红框明显大于建筑本体。
- D4 防撞过于保守。
- ship / farm / cottage 等看起来可以更近的结构被推远。

### 目标策略

对固定大小结构，不再只使用全方向合并 P95。

优先使用：

```text
selectedPlacementBBox + smallClearance
```

或至少使用：

```text
orientationSpecificBBox + smallClearance
```

其中：

- `selectedPlacementBBox` 来自 D6 preflight 对当前 anchor chunk / seed 的实际 bbox。
- `orientationSpecificBBox` 来自 profiling 时按实际朝向或 bbox 形态分组后的 bbox。
- `smallClearance` 初始建议从 2、4、6 三档实测。

### 关键要求

- profiling 需要记录每个样本的实际 bbox，而不是只输出合并 envelope。
- 如果无法手动控制 configured structure rotation，也要能按“本次实际生成形态”使用 bbox。
- D4 preview 必须区分建筑 actual bbox、collision bbox、mask bbox。
- D6 preflight 仍然负责最终确认 actual bbox 未越界。

## 口径二：非固定大小结构的固定 depth 回归

村庄、jigsaw 或其他会扩展的 configured structure，本体大小不是固定值。它们需要在固定配置下做回归统计。

这里的固定配置包括：

- configured structure id。
- jigsaw size / depth。
- max distance from center。
- 结构包自身 generation config。
- City 侧输入的 anchor chunk / seed 策略。

### 目标策略

对非固定大小结构，继续使用统计 envelope：

```text
collisionEnvelope = fixedDepthP95 + clearance
maskEnvelope      = fixedDepthP99 + vegetationMargin
safetyEnvelope    = maxObserved 或 max_distance_from_center
```

### 关键要求

- profiling trace 必须记录 depth / size / max distance 等生成参数。
- 同一结构不同 depth 配置应视为不同 envelope facts。
- P95 / P99 用于布局，不承诺覆盖全部长尾。
- D6 preflight 和 worldgen signature gate 负责拦截长尾越界。

## Key Changes

- `structure_envelope_facts.json` 保留每个 sample 的 actual bbox / piece count / area。
- 增加固定结构的 `validSamples[]` 和 `bboxGroups[]`：
  - `validSamples[]` 记录 `sampleIndex`、`localBounds`、`pieceCount`、`areaBlocks`、`bboxGroupKey`。
  - `bboxGroups[]` 按 `localBounds + pieceCount` 分组，记录 `groupKey`、`sampleCount`、`ratio`、`localEnvelope` 和示例 sample。
- 增加 `generationConfigHash`，把结构 id、profile 类型、footprint 模式、固定尺寸、期望面积、max distance、结构配置来源纳入 facts 匹配。
- D4 对固定大小结构使用 `bboxGroups[]` 生成 collision envelope。
- D4 对非固定大小结构继续使用 fixed-depth P95 / P99。
- D4 输出 `envelopeMode`：
  - `fixed_bbox_group`：固定或近固定结构，使用选中的 bbox group。
  - `fixed_depth_statistics`：非固定结构，使用 P95 / P99 / maxObserved。
- D4/D7 preview 同时展示：
  - actual bbox
  - collisionEnvelope
  - maskEnvelope
  - safetyEnvelope

## 实施口径

### 固定 / 近固定结构

固定结构识别优先级：

1. TerraSense profile 明确标记 `footprintMode=fixed_footprint`。
2. profiling 显示 piece count 稳定，且 bbox group 数量有限，可视为近固定结构。

首轮实现不在 D4 直接调用 MC registry 做当前 anchor 的 dry-run，也不做 D6 preflight 后重排。D4 只使用 profiling 产出的 bbox group facts。

默认选择样本数最多的 dominant bbox group。调用方可在 anchor 上显式指定 `envelopeGroupKey`。若指定的 group 不存在，D4 返回明确错误，不回退到大半径 envelope。

固定结构 envelope：

```text
collisionEnvelope = selected bboxGroup.localEnvelope + smallClearanceBlocks
maskEnvelope      = selected bboxGroup.localEnvelope + vegetationMarginBlocks
safetyEnvelope    = maxObservedEnvelope 或结构 profile 的保守范围
```

默认值：

```text
smallClearanceBlocks = 4
```

该值只用于 `fixed_bbox_group`，不再被旧的 `DEFAULT_CLEARANCE_BLOCKS=8` 强制放大。

### 非固定结构

非固定结构继续使用固定生成配置下的统计范围。

```text
collisionEnvelope = localEnvelopeP95 + clearanceBlocks
maskEnvelope      = localEnvelopeP99 + vegetationMarginBlocks
safetyEnvelope    = maxObservedEnvelope 或 max_distance_from_center
```

同一结构在不同 depth / size / max distance / 结构配置来源下必须得到不同 `generationConfigHash`。D4 读取 facts 时需要校验 profile hash 和 generation config hash，避免拿旧统计套新配置。

### D6 Probe-And-Lock

D6 preflight 生成实际 bbox / piece boxes / start signature，但不改变世界。D6 是最终防撞准入点，会把本次实际生成形态锁进 `structure_materialization_plan.json`：

- `lockedActualFootprint`
- `lockedBBoxGroupKey`
- `lockedCollisionEnvelope`
- `expectedStartSignature`

如果实际 bbox group 与 D4 dominant group 不一致，只要 facts 中存在该 group，且 `actualFootprint + collisionClearanceBlocks` 与本轮其他结构 / 既有 ledger 不重叠，D6 锁定实际 group，不再直接失败。

若 locked collision 与其他结构或 ledger 重叠，D6 返回结构化失败原因，并在 trace 中写明：

- `envelopeMode`
- `selectedEnvelopeGroupKey`
- `lockedBBoxGroupKey`
- actual bbox
- actual bbox group key
- collisionEnvelope
- lockedCollisionEnvelope
- maskEnvelope
- safetyEnvelope

首轮不做 D6 后重排。防撞失败时由调用方调整 anchor、clearance 或 envelope group 后重新规划。

### D7 真实边界道路

D5 的 road / build operation 只保留占位，标记 `roadPlanningStage=d7_after_worldgen_ledger`。所有 planned structure 都有 worldgen ledger 后，D7 基于真实 `actualFootprint` 聚合边界，并用 `actualFootprint + roadAvoidanceMarginBlocks` 作为道路避障，默认 `roadAvoidanceMarginBlocks=3`。

该道路后处理仍是调试级能力，后续可替换为 Road Weaver；但从本案开始，正式路径不得再用 D5 预先猜出的路线穿过房顶、墙体或结构 body。

## 验收

- Trek 当前测试结构中，ship / farm / cottage 等固定或近固定结构的 collision bbox 明显缩小。
- ship 与 agriculture farm 的实际视觉距离比上一轮测试更近。
- 固定大小结构不会因为全方向合并 envelope 被过度推远。
- 非固定大小结构在固定 depth 配置下能输出 P95 / P99 / maxObserved。
- D6 locked collision envelope 不重叠，且不与既有 ledger 重叠。
- worldgen actual bbox 全部落在 D6 locked collision envelope 内。
- D7 道路基于真实 actual footprint 避障，不上房顶、不穿墙、不穿结构 body。
- mask 仍能抑制结构范围内的植被。
- trace 能解释某个结构走的是“固定结构朝向 bbox”还是“非固定结构 fixed-depth 统计 bbox”。

## 暂不处理

- 不要求本案实现手动指定 configured structure rotation。
- 不接入 Road Weaver。
- 不做台基、削坡、填土。
- 不重新整理 TerraSense 语义标签。
- 不引入 Stable / Variable / Unstable 等额外结构分类作为首轮实现前提。

## 待定

- 后续是否在 D4 增加当前 anchor 的 dry-run，用 `selectedPlacementBBox` 替代 dominant bbox group。
- 后续是否支持手动控制 configured structure rotation。
- `smallClearanceBlocks=4` 是否需要按结构包或结构类型微调。
- bbox group 是否需要从 `localBounds + pieceCount` 升级为 piece layout signature。
