# City 案子：结构 Envelope 精修 v0.1

## 定位

本案是 `D3-D6结构落地驱动城市重构-v0.1` 之后的第一阶段优化。目标是解决当前结构之间视觉距离偏远、preview 中 bbox 过于保守的问题。

本案只处理 envelope / bbox 策略，不扩展新的城市功能区、不改道路系统、不做结构地形适配。

## 核心目标

- 固定大小或近固定大小结构，使用接近本体的紧 bbox。
- 非固定大小结构，例如村庄、jigsaw 扩展结构，继续走统计回归 envelope。
- D4 preview 同时展示 actual / collision / mask 三类范围，避免把 mask 误读成建筑本体。
- 真实验收时，结构之间距离比当前 P95 全方向合并框更紧，但仍不重叠、不越界。

## 结构分类

### Stable Structure

适用于 piece count 和 bbox 分布高度稳定的结构。

判定信号：

- `pieceCount.p95 == pieceCount.p50` 或波动很小。
- `localEnvelopeP95` 与 `maxObservedEnvelope` 差距很小。
- 多次采样的实际 bbox 面积波动很小。

默认策略：

```text
collisionEnvelope = observedActualP95 + smallClearance
maskEnvelope      = observedActualP99 + vegetationMargin
safetyEnvelope    = maxObserved + diagnosticMargin
```

### Variable Structure

适用于会扩展、会抽样不同组合、会因 seed/order 产生明显差异的结构。

默认策略：

```text
collisionEnvelope = statisticalP95 + clearance
maskEnvelope      = statisticalP99 + vegetationMargin
safetyEnvelope    = maxObserved 或 max_distance_from_center
```

### Unstable Structure

适用于采样 invalid ratio 高、bbox 长尾过大或结构包行为不稳定的结构。

默认策略：

- D4 可以 hard fail 或要求人工确认。
- 不能静默回退到旧大半径。
- trace 必须说明为什么不可用于紧凑布局。

## Key Changes

- `structure_envelope_facts.json` 增加 `stabilityClass`。
- profiling 输出 `bboxVariance`、`pieceCountVariance`、`actualAreaVariance` 等稳定性指标。
- D4 对 `Stable Structure` 使用紧 `collisionEnvelope`。
- D4 对 `Variable Structure` 保留 P95 / P99 统计 envelope。
- D6 preflight 继续作为真实 bbox / signature gate，不因 D4 紧 bbox 而取消。
- preview 中用不同颜色或线型区分：
  - actual bbox
  - collisionEnvelope
  - maskEnvelope
  - safetyEnvelope

## 验收

- Trek 当前测试结构中，ship / farm / cottage 等近固定结构的 collision bbox 明显缩小。
- ship 与 agriculture farm 的实际视觉距离比上一轮测试更近。
- 四区结构实际 bbox 不重叠。
- actual bbox 全部落在 collisionEnvelope / reservedEnvelope 内。
- mask 仍能抑制结构和道路范围内的植被。
- trace 能解释某个结构为什么被判为 stable / variable / unstable。

## 暂不处理

- 不实现手动指定 configured structure rotation。
- 不接入 Road Weaver。
- 不做台基、削坡、填土。
- 不重新整理 TerraSense 语义标签。

## 待定

- Stable 判定阈值是否按结构包全局统一，还是允许 TerraSense Studio 人工覆盖。
- 是否把 orientation-specific envelope 纳入本案，还是拆成后续案子。
- `smallClearance` 默认值建议从 2、4、6 三档实测。
