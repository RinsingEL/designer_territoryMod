# 01 Envelope 瘦身

## 修改目的

删除 `safetyEnvelope` 在 City 结构落地链路中的规划语义，不再让它参与 D4 候选过滤、D4 阵列避让、D5 保留区计算或预览图的主要判断。

## 方案

### 1. 删除 safetyEnvelope 规划语义

`safetyEnvelope` 不再作为结构规划硬边界。后续链路只保留 `collisionEnvelope` 与 `maskEnvelope` 两层边界。

### 2. 收敛为 collisionEnvelope / maskEnvelope 两层边界

`collisionEnvelope` 成为结构间防撞的唯一硬边界，用于保证结构本体不会相撞。

`maskEnvelope` 成为世界生成保护边界，由 `collisionEnvelope` 向外扩小边距得到，默认控制在 5 到 10 格范围内，用于 D5 reservation mask、植被清理、vanilla structure 避让、必要地表过渡和后续道路 / 装饰避让。

### 3. D4 只检查 collisionEnvelope

D4 阵列布局只检查 `collisionEnvelope` 之间是否重叠。阵列中的建筑可以按 `maskEnvelope` 的小边距自然贴近，使结构与结构之间形成更接近真实聚落的 5 到 10 格视觉间距，而不是被旧式 safety 余量撑开。

## 可验收提交点

1. 删除 D4 候选过滤和阵列避让中对 `safetyEnvelope` 的硬依赖，提交 D4 防撞口径和测试。
2. 删除 D5 mask 计算中对 `safetyEnvelope` 的硬依赖，提交 D5 小边距 `maskEnvelope` 口径和测试。
3. 调整预览图和 debug artifact，让 `safetyEnvelope` 不再作为主要判断层，提交预览和测试。

## 验收需求

1. D4 候选点和阵列执行只因 `collisionEnvelope` 重叠而拒绝结构，不得因为 `safetyEnvelope` 重叠拒绝结构。
2. D5 输出的 `maskEnvelope` 必须由 `collisionEnvelope` 小边距扩展得到，默认边距保持在 5 到 10 格范围内。
3. 标准 D4 / D5 artifact 中不得再把 `safetyEnvelope` 作为规划硬边界；若临时保留 debug 字段，也必须标记为非规划依据。
4. 预览图必须能清楚显示 `collisionEnvelope` 与 `maskEnvelope`，不得用 `safetyEnvelope` 误导结构间距判断。
5. 回归用例必须覆盖两个结构 `safetyEnvelope` 重叠但 `collisionEnvelope` 不重叠时仍可放置的场景。
