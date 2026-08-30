# City 案子：关键装饰锚点候选 v0.1

## 状态

当前已实现能力。它在现有 DecorationProgram 意图与 `city_plan_city_dressing` 之间提供只读候选步骤，不修改最终 intent、compiled program 或 worldgen 契约。

## 目的

喷泉、雕像、水井、纪念物、大型树等关键单点 prefab 不再由 AI 穷举世界坐标或猜 `offsetUBlocks/offsetVBlocks`。程序负责把 resolved target mask、真实 prefab 尺寸、comfort/conflict margin 与现有硬障碍合并为少量合法候选；Agent 只比较候选并选择。palette layer 的 `required` 仍沿用 DecorationProgram 原语义，不是本工具额外增加的硬门槛。

普通 `deterministic_scatter`、`edge_repeat`、多点 `grid_repeat` 等装饰仍由现有 Pattern 直接投影，不进入本工具。

## 流程

```text
Agent 提交一个关键单点 DecorationProgram 意图
  -> city_plan_decoration_anchor_candidates
  -> 解析 target / style / concrete prefab
  -> 用完整 footprint + clearance 扫描 resolved target mask
  -> 排除 D6 结构、墙、门、路口、LandUse gate 等 hard obstacles
  -> 稳定排序并返回 1-8 个候选、质量摘要和预览
  -> Agent 选择 candidateId
  -> 复制该候选的 coordinateFramePatch 到最终 DecorationProgram
  -> city_plan_city_dressing
  -> city_probe_decoration_terrain
  -> city_execute_d5 / worldgen
```

候选工具不写 active registry，不执行 worldgen，也不替 Agent 自动选择。候选为空是合法诊断结果；必须返回拒绝统计和原因，不能伪造一个越界或冲突锚点。

## 首版输入边界

首版只接受满足以下条件的单个 program：

- `shape.type=rectangle`，且 `minU=minV=maxU=maxV=0`。
- `pattern.type=grid_repeat`，该局部 `(0,0)` 点必须处于启用相位，规划后只表达一个 slot。
- pattern 指向一个 palette slot；该 slot 可以有多个 concrete prefab entry，每个 world anchor 使用与 runtime 相同的确定性选择得到 content 和尺寸。
- 候选 slot 固定 `rotationQuarterTurns=0`，因此所选 concrete content 必须允许 0 度；`coordinateFrame.quarterTurns` 仍保留原 intent 值，两者不是同一个概念。
- `candidateCount` 为 `1..8`，默认 5。

多点 grid、scatter、edge、连续带、批量地表，以及不允许 0 度放置的 content 都明确拒绝或计入 rejection，不静默降级。首版还要求完整 prefab footprint 不跨 owner chunk；跨 chunk anchor 进入 `crossChunk` 拒绝统计。

## 候选合法性

每个候选都必须同时满足：

1. concrete prefab 的完整水平 footprint 位于 resolved target mask 内。
2. prefab comfort margin 与 program `conflictPolicy.clearanceBlocks` 合成的 clearance 范围也位于 mask 内。
3. footprint 与 clearance 均避开当前规划产物中可知的 D6 locked structure、D5 wall reservation、gate/gateway、路口与 LandUse gate/corridor 等 hard obstacles。
4. 同一 plan 内已经回填候选 patch 的其他单点 Decoration programs 作为 `fixedDecorationObstacles` 参与 clearance 避让。
5. 候选之间稳定去重；同一输入重复调用得到相同 candidateId 和排序。

RoadWeaver 尚未落地的真实路线不可被猜成对角矩形或直线障碍；候选阶段只使用已经冻结且可证明的 gateway / corridor。真实地形也不在此阶段伪造：响应固定 `terrainSampling=not_performed`，运行期 terrain validator 仍是最终守门。

## 评分与输出

评分只解释规划几何，不宣称地形安全。首版至少考虑 target 中心接近度、到 hard obstacle 的余量和可用 clearance；分项与总分必须进入候选集，排序规则固定。

输出包括：

- `candidateSet`：候选 ID、诊断用 world anchor / `localOffsetDelta`、完整 footprint、clearance、score 和可直接回填的绝对 `coordinateFramePatch`。
- `qualityReport`：请求数量、合法数量、是否足够以及 `terrainSampling=not_performed`。
- `rejectionCounts`：按 `outsideTarget`、汇总 `hardObstacle`、`crossChunk`、`rotationUnsupported`、`contentNotPrefab` 和 `decorationConflict` 计数；具体硬障碍类型仍从 plan 与预览查看。
- `preview`：显示 target mask、hard obstacles、候选短编号、footprint 与 clearance；预览必须标明没有真实地形采样。

`coordinateFramePatch` 只包含现有相对坐标字段，例如 `originMode`、`orientationMode`、`quarterTurns`、`offsetUBlocks`、`offsetVBlocks`。world anchor 只用于诊断与预览，不得复制进最终 intent；本案不把世界坐标引入 DecorationProgram 契约。

## AI 职责

Agent 决定目标区域、装饰语义、候选数量和最终 `candidateId`。Agent 不枚举世界点、不手工试 offset，也不得在候选为空时绕过工具提交世界坐标。

多个关键装饰按顺序选。后一次候选请求必须携带前面已回填 `coordinateFramePatch` 的单点 programs，程序把它们视为固定装饰障碍；不得为每个关键装饰各自独立生成候选后再一起提交。

选择后，Agent 只把所选项的 `coordinateFramePatch` 合并回原 program，再调用现有 `city_plan_city_dressing`。最终规划、terrain probe、激活和 worldgen 仍沿用原链。

## 非目标

- 不做真实 terrain sampling、逐列高度适配或 chunk load/generation。
- 不新增 candidate selection 持久化状态或自动提交 endpoint。
- 不替代普通 Pattern 算法。
- 不解决 prefab 朝向枚举、面向目标或长椅朝向。
- 不改变 `city_decoration_program_plan.v0.4` schema。

## 验收

- 5x5 喷泉在不规则 plaza mask 中只返回完整 footprint 与 clearance 均在 mask 内的候选。
- centroid 落在 mask 空洞或紧邻建筑时不得仍返回原点；拒绝统计可解释原因。
- 候选避开 D6 structure、wall、gate/gateway 和 LandUse gate/corridor。
- `candidateCount=1` 与 `8` 合法，0、9 失败；MCP 输入继续由 strict schema 拒绝未知字段，原始 HTTP 顶层沿用现有 City endpoint 的兼容口径。palette 多 prefab entry 仍按 runtime 确定性选择。
- 无合法位置时成功返回空 candidates、明确 `qualityReport` / rejectionCounts 和预览，不制造 fallback。
- 重复输入的 candidateId、排序与 `coordinateFramePatch` 完全一致。
- endpoint 不加载/生成 chunk，不改 decoration artifact、active registry、ledger 或世界方块。
- 选中 patch 回填后，`city_plan_city_dressing` 恰好投影一个 slot，且位置与候选一致。
