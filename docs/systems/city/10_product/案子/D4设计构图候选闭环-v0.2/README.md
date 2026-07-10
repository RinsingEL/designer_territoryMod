# City 案子：D4 设计构图候选闭环 v0.2

## Summary

v0.2 将 D4 候选闭环从 v0.1 的“一次性为全部 slot 生成候选，再批量选择”改为“逐 slot 生成候选、选中后冻结占用、再生成下一个 slot 候选”。

核心目的不是让程序自动全局最优，而是让 AI / 人每次只面对当前结构槽位的少量安全候选；每选定一个 anchor，后续候选都基于新的 occupied set、关系距离和当前城市构图重新生成，减少 D6 才发现碰撞后回头重选的情况。

本案不恢复功能区边界主链，不把 `slotId` 做成 City 枚举，不要求 AI 手算坐标。D6 probe-and-lock 仍是最终硬真值；D4 v0.2 负责把候选生成变成真正的交互式逐步规划。

同时，本案要求 D4 明确记录设计耗时。后续真实验收不只看最终城市是否漂亮，还要回答“从创建 D4 session 到完成 6 个结构 slot 的设计，一共花了多久，每一步慢在哪里”。

## Current Implementation Status

本案已完成并入当前 City 主线：

- 已有 `city_create_d4_candidate_session` / `city_plan_d4_next_candidates` / `city_select_d4_candidate` / `city_finalize_d4_candidate_session` 四段接口。
- `city_run_workflow` 默认 `key_then_array` 的关键结构阶段会复用该 sequential session，逐 slot 生成、选择并冻结 occupied。
- D4 结构群整组候选也复用该 session 的 `planNext/select/finalize` 口径做 beam search。
- v0.1 批量候选仍保留为 debug / 兼容入口，不再是推荐主路径。

因此本案不是废案；它已经变成 D4 关键结构逐个定锚的基础能力。后续新增能力应优先围绕 array_fill、嵌套阵列、RoadWeaver corridor 和装饰填充层继续推进。

## Problem In v0.1

v0.1 已经证明“设计 slot + D3 patch + envelope facts + 少量候选”是正确方向，但本轮真实测试暴露出一个结构性问题：

```text
all_slots_tentative_order
  -> 一次性生成 6 个 slot 的候选
  -> 人 / AI 一次性选择 6 个
  -> D4 select 做一轮 estimated envelope 校验
  -> D6 probe 才发现 actual footprint / locked collision overlap
```

这会带来几个问题：

- 后续 slot 的候选点是基于 tentative order 估算出来的，不一定反映最终真实已选 anchor。
- 如果人 / AI 不总是选候选集中最高分项，后续候选的 occupied 预估会失真。
- 固定 / 近固定结构的实际 bbox group 仍可能和 D4 dominant group 不同，导致 D6 才发现 overlap。
- 失败后需要人工回到上一轮 selection 重新挑，loop 变长。

本轮真实测试中，第一次住宅候选看起来可选，但 D6 probe 后报 `LEDGER_OCCUPIED_OVERLAP`，说明 D4 批量候选无法充分承担“每一步选完后再防撞”的职责。

## Target Flow

v0.2 的主流程改为：

```text
D3 city_landform_review_package
  + StructureProfile / envelope facts
  + DesignSlotPlan
  -> create D4 candidate session
  -> generate candidates for next unresolved slot only
  -> AI / human selects one candidate
  -> freeze selected anchor into session occupied set
  -> optionally run non-mutating preflight for selected anchor
  -> regenerate candidates for next slot
  -> repeat until all required slots are selected
  -> finalize StructureAnchorPlan / StructureAnchorMap
  -> existing D5 / D6 / execute_d5 / worldgen / D7 flow
```

关键变化：

- 候选生成的单位从“整座城市所有 slot”变成“当前 next slot”。
- 每次选择后，session 都会持久化 `selectedAnchors[]` 和 `occupiedEnvelopes[]`。
- 下一个 slot 的候选只基于已冻结 anchors 生成，不基于未来 slot 猜测。
- 如果某个 slot 选完后 D6 quick preflight 发现 actual overlap，可立即要求重选当前 slot，而不是等 6 个都选完。

## Core Principles

### 1. Pick One, Then Regenerate

D4 candidate endpoint 每次只返回一个 slot 的候选：

```json
{
  "sessionId": "city_example_d4_session",
  "currentSlotId": "residential_01",
  "selectedAnchors": ["admin_castle", "harbor_ship", "agriculture_farm"],
  "candidates": []
}
```

选择成功后，系统立刻更新 occupied set，再进入下一个 slot。后续候选永远不复用旧的“未考虑当前选择”的候选结果。

### 2. Occupied Set Is Frozen By Selection

每个已选 anchor 至少写入：

- `anchorId`
- `slotId`
- `candidateId`
- `structureId`
- `anchorBlock`
- `estimatedCollisionEnvelope`
- `estimatedMaskEnvelope`
- `selectedEnvelopeGroupKey`
- `selectionReason`

后续候选必须避开这些 frozen envelopes。若启用 quick preflight，还应优先使用 `lockedActualFootprint + collisionClearanceBlocks` 替代 estimated collision envelope。

### 3. D4 Still Estimates, D6 Still Decides

D4 v0.2 不篡改 D6 的职责：

- D4：根据 D3 patch / envelope facts / 已选 anchors 生成低风险候选。
- D6：对最终 anchors 做 non-mutating probe-and-lock，得到真实 `actualFootprint`、`lockedBBoxGroupKey`、`expectedStartSignature`。
- worldgen hook：按 D6 signature gate 做最终落地验证。

也就是说，D4 负责让选择过程更聪明；D6 仍是硬防撞真值。

### 4. Quick Preflight Is Optional But Recommended

为了缩短真实测试 loop，v0.2 建议在每次选择候选后支持一个轻量 quick preflight：

```text
select current candidate
  -> non-mutating probe selected anchor
  -> if actual bbox overlaps frozen occupied:
       reject this candidate immediately
     else:
       freeze actual footprint into occupied set
```

首版可以先用 estimated envelope 冻结；如果实现成本可接受，再把 quick preflight 接进 selection 阶段。无论是否启用 quick preflight，最终 D6 full plan 仍必须再跑一遍。

## Proposed Interfaces

### city_create_d4_candidate_session

输入：

```json
{
  "runId": "city_run",
  "citySeedId": "city_id",
  "terrasenseProfileSource": {},
  "structureEnvelopeFactsSource": {},
  "designSlotPlan": {}
}
```

输出：

```json
{
  "ok": true,
  "sessionId": "city_id_d4_session",
  "placementOrder": ["admin_core", "harbor_trade"],
  "currentSlotId": "admin_core",
  "selectedAnchorCount": 0,
  "remainingSlotCount": 6,
  "timingMs": {
    "total": 12,
    "loadD3": 2,
    "loadProfiles": 3,
    "loadEnvelopeFacts": 4,
    "initSession": 3
  }
}
```

### city_plan_d4_next_candidates

输入：

```json
{
  "runId": "city_run",
  "citySeedId": "city_id",
  "sessionId": "city_id_d4_session",
  "candidateCount": 5
}
```

输出当前 slot 的候选：

```json
{
  "ok": true,
  "sessionId": "city_id_d4_session",
  "currentSlotId": "residential_01",
  "selectedAnchors": [],
  "slotCandidateSet": {
    "slotId": "residential_01",
    "candidates": []
  },
  "artifacts": {
    "candidatePreview": "anchor_candidate_preview_residential_01.png",
    "candidateSet": "anchor_candidate_set_residential_01.json",
    "sessionState": "d4_candidate_session.json"
  },
  "timingMs": {
    "total": 25,
    "loadSession": 1,
    "resolvePatches": 3,
    "generateRawCandidates": 8,
    "filterOccupied": 4,
    "scoreCandidates": 3,
    "renderPreview": 6
  }
}
```

预览图读法：

- `anchor_candidate_preview.png` 必须叠加 D3 patch member-cell 底图，让候选点能直接对照水岸、平地、山脊、崖壁等 patch。
- 已冻结的前序 anchor 用 `S1/S2...` 和蓝色 occupied envelope 表示。
- 当前 slot 的多个候选用 `C1/C2...` 编号表示；这些候选之间允许互相重叠，因为最终只会选择一个。
- 候选完整 id、score、role 和风险放在右侧 legend，不在地图上绘制长文本，避免把候选备胎误读为最终结构重叠。

### city_select_d4_candidate

输入：

```json
{
  "runId": "city_run",
  "citySeedId": "city_id",
  "sessionId": "city_id_d4_session",
  "slotId": "residential_01",
  "candidateId": "residential_01_practical_04",
  "anchorId": "residential_spruce",
  "selectionReason": "避开城堡真实 footprint，改选东侧山脊候选。",
  "quickPreflight": true
}
```

输出：

```json
{
  "ok": true,
  "selectedAnchorCount": 4,
  "nextSlotId": "residential_02",
  "selectedAnchor": {},
  "quickPreflightReport": {
    "status": "accepted",
    "actualFootprint": {},
    "reasonCode": "D4_QUICK_PREFLIGHT_ACCEPTED"
  },
  "timingMs": {
    "total": 37,
    "loadSession": 1,
    "validateSelection": 2,
    "quickPreflight": 30,
    "updateOccupiedSet": 1,
    "writeSession": 3
  }
}
```

若失败：

```json
{
  "ok": false,
  "reasonCode": "D4_SELECTED_CANDIDATE_OCCUPIED_OVERLAP",
  "overlapWithAnchorId": "admin_castle",
  "message": "Selected candidate actual footprint overlaps frozen occupied envelope."
}
```

### city_finalize_d4_candidate_session

当所有 required slot 都选完后，生成当前 active path 需要的 `StructureAnchorPlan` / `StructureAnchorMap`：

```json
{
  "ok": true,
  "status": "finalized",
  "selectedAnchorCount": 6,
  "designTimingMs": {
    "totalWallClock": 420000,
    "agentThinkTime": 360000,
    "toolRuntime": 60000,
    "sessionCreate": 12,
    "candidateGenerationTotal": 140,
    "selectionTotal": 180,
    "quickPreflightTotal": 58000,
    "previewRenderTotal": 2200
  },
  "artifacts": {
    "structureAnchorPlan": "structure_anchor_plan.json",
    "structureAnchorMap": "structure_anchor_map.json",
    "structureAnchorPreview": "structure_anchor_preview.png"
  }
}
```

## Data Artifacts

### d4_candidate_session.json

```json
{
  "schemaVersion": "city_d4_candidate_session.v0.2",
  "sessionId": "city_id_d4_session",
  "cityId": "city_id",
  "placementOrder": [],
  "currentSlotIndex": 3,
  "selectedAnchors": [],
  "occupiedEnvelopes": [],
  "rejectedSelections": [],
  "candidateHistory": [],
  "timing": {
    "createdAt": "2026-07-01T00:00:00+08:00",
    "updatedAt": "2026-07-01T00:05:00+08:00",
    "stepTimings": [],
    "toolRuntimeMs": 0,
    "agentThinkTimeMs": 0,
    "totalWallClockMs": 0
  }
}
```

### slot_candidate_set.json

每次只保存当前 slot 的候选，也可在 `candidateHistory[]` 中保留历史快照。

### d4_candidate_session_trace.json

用于回答：

- 每个 slot 是在什么 occupied set 下生成候选的。
- 哪些候选因为已选 anchor 被过滤。
- 哪个候选被选中，选择理由是什么。
- 是否做了 quick preflight。
- quick preflight 与最终 D6 full preflight 是否一致。
- 每个 slot 的候选生成、选择、quick preflight、预览渲染分别耗时多少。
- 总耗时里有多少是程序运行时间，有多少是等待 AI / 人选择的思考时间。

## Timing And Performance

D4 v0.2 必须把“设计一座城市要多久”作为一等验收指标。

### Timing Scope

至少记录三类时间：

- `toolRuntimeMs`：程序实际运行时间，包括读取 D3、解析 profile、候选生成、过滤、评分、quick preflight、预览渲染、写 artifact。
- `agentThinkTimeMs`：从候选返回到下一次 selection 提交之间的等待时间，用于衡量 AI / 人做设计取舍的时间。
- `totalWallClockMs`：从 `city_create_d4_candidate_session` 到 `city_finalize_d4_candidate_session` 的真实墙钟时间。

### Step Timing

每个 slot 记录一条 step timing：

```json
{
  "slotId": "residential_01",
  "candidateGenerationMs": 25,
  "selectionValidationMs": 7,
  "quickPreflightMs": 30,
  "previewRenderMs": 6,
  "agentThinkTimeMs": 90000,
  "selectedCandidateId": "residential_01_practical_04",
  "rejectedSelectionCount": 1
}
```

### Design Time Report

`city_finalize_d4_candidate_session` 输出 `d4_design_time_report.json`：

```json
{
  "schemaVersion": "city_d4_design_time_report.v0.2",
  "cityId": "city_id",
  "slotCount": 6,
  "selectedAnchorCount": 6,
  "rejectedSelectionCount": 2,
  "totalWallClockMs": 2400000,
  "toolRuntimeMs": 180000,
  "agentThinkTimeMs": 2220000,
  "slowestSteps": [
    {
      "slotId": "defense_edge",
      "phase": "agentThinkTime",
      "durationMs": 600000
    }
  ],
  "failureReasons": {
    "D4_SELECTED_CANDIDATE_OCCUPIED_OVERLAP": 1,
    "D4_QUICK_PREFLIGHT_ACTUAL_OVERLAP": 1
  }
}
```

真实游玩测试需要把该报告和最终城市截图一起保存，用来判断设计流程是否已经足够快。

## Parallel / Multi-Agent Design

D4 v0.2 支持“多个城市并行设计”，但不建议把同一座城市的 slot 选择粗暴并行化。

### Safe Parallelism

安全并行边界：

- 不同 `runId + citySeedId` 的 D4 session 可以并行。
- 不同 agent 可以各自设计不同城市，写入独立 artifact 目录。
- D3 package、TerraSense profile、structure envelope facts 是只读输入，可以被多个 session 共享读取。
- 每个 session 的 `d4_candidate_session.json`、candidate preview 和 selection trace 必须独立写入，不能共享 mutable state。

推荐调度方式：

```text
city_seed_A -> agent/job A -> D4 session A
city_seed_B -> agent/job B -> D4 session B
city_seed_C -> agent/job C -> D4 session C
```

最后由人 / 总控 agent 对多个候选城市的 D4 preview、D6 preview 和 design time report 做横向比较，选择最值得进入真实 worldgen 验收的城市。

### Unsafe Or Deferred Parallelism

同一城市内部不建议并行选择多个 slot：

- slot 之间存在 occupied set 依赖。
- 住宅、农场、防御塔等后续候选依赖前面结构的真实选择结果。
- 并行预选多个 slot 容易回到 v0.1 的 batch 问题，D6 才发现碰撞。

可以作为后续优化探索“speculative candidates”：程序提前为未来 slot 生成草稿候选，但这些候选只能标记为 stale / speculative。只要前一个 anchor 被选中，后续 slot 的正式候选必须重新生成。

### Acceptance Target

后续批量设计测试应统计：

- 单城市 sequential D4 平均耗时。
- 多城市并行时每个 agent 的 wall-clock 耗时。
- 进入 D6 后的失败率。
- 因 D4 选择导致的回退次数。
- 最终被人工选中进入真实游玩测试的城市比例。

## Candidate Generation Rules

### Input Context

生成当前 slot 候选时，输入必须包含：

- D3 patch package。
- 当前 slot 的 `candidatePatchRefs`。
- TerraSense structure profile。
- structure envelope facts。
- session 中已冻结的 `selectedAnchors`。
- session 中已冻结的 `occupiedEnvelopes`。
- relation hints 中已经可解析的 target anchor。

尚未选择的 `targetSlotId` 只作为软提示，不得成为硬约束。

### Filtering Order

建议过滤顺序：

1. patch ref 能解析。
2. structure profile / envelope facts 可用且 hash 匹配。
3. anchor 在 city grid 内。
4. estimated collision envelope 不撞 frozen occupied envelopes。
5. estimated mask envelope 不越过 hard city safety bounds。
6. relation hint 评分。
7. candidate kind 去重与数量截断。

### Candidate Count

- 默认每个 slot 只返回 3-5 个候选。
- 如果所有候选都被过滤，返回 blocking report，不扩大成海量候选。
- 可以支持 `relaxationLevel`，但必须写 trace，例如放宽距离关系或换 patch，不得悄悄放宽防撞。

## Preview Requirements

每次 `city_plan_d4_next_candidates` 生成当前 slot 专用预览：

- D3 patch 底图。
- 已选 anchors 和 occupied envelopes。
- 当前 slot 候选点和 estimated envelopes。
- 当前 slot 的 relation hints。
- 被过滤候选数量摘要。

预览图必须表达“这是第几步”，例如：

```text
D4 sequential candidates: step 4/6 residential_01
selected: admin_core, harbor_trade, agriculture
current candidates: 5
filtered by occupied: 4
filtered by city bounds: 0
```

## Failure / Reason Codes

新增或稳定 reason code：

- `D4_CANDIDATE_SESSION_NOT_FOUND`
- `D4_SLOT_ORDER_VIOLATION`
- `D4_SLOT_ALREADY_SELECTED`
- `D4_NO_AVAILABLE_CANDIDATES`
- `D4_SELECTED_CANDIDATE_NOT_FOUND`
- `D4_SELECTED_CANDIDATE_OCCUPIED_OVERLAP`
- `D4_QUICK_PREFLIGHT_SIGNATURE_UNAVAILABLE`
- `D4_QUICK_PREFLIGHT_ACTUAL_OVERLAP`
- `D4_SESSION_NOT_FINALIZABLE`

## Migration From v0.1

v0.1 的批量接口可保留为 debug / batch preview：

- `city_plan_d4_candidates`：保留，但标记 `planningMode=all_slots_tentative_order_debug`。
- `city_select_d4_candidates`：保留，但推荐路径改为 sequential session finalize 后自动产出 `StructureAnchorPlan`。

active 推荐路径应改为：

```text
city_create_d4_candidate_session
city_plan_d4_next_candidates
city_select_d4_candidate
... repeat ...
city_finalize_d4_candidate_session
city_plan_d5
city_plan_d6
city_execute_d5
worldgen
city_execute_d7
```

## Test Plan

### Unit Tests

- 创建 session 后 current slot 为 placementOrder 第一项。
- 选择第一个 anchor 后，第二个 slot 候选会避开第一个 anchor 的 occupied envelope。
- 选择非 current slot 返回 `D4_SLOT_ORDER_VIOLATION`。
- 重复选择同一 slot 返回 `D4_SLOT_ALREADY_SELECTED`。
- 候选全部被 occupied 过滤时返回 `D4_NO_AVAILABLE_CANDIDATES`。
- quick preflight actual overlap 会拒绝当前选择，并保留 session 可继续重选。
- finalize 前 slot 未全部选择时返回 `D4_SESSION_NOT_FINALIZABLE`。
- session / step / finalize 均输出 timing 字段，且 `totalWallClockMs >= toolRuntimeMs`。
- rejected selection 会进入 design time report 的 failure reason 统计。

### Integration Tests

- 6 个 Trek 测试 slot 逐步选择后可生成与当前 active path 兼容的 `StructureAnchorPlan`。
- D5 读取 finalized D4 anchor map 不需要改主契约。
- D6 full preflight 能复核 sequential session 选择结果。
- v0.1 batch endpoint 仍可用于 preview，但 trace 明确标记 debug。

### Real Playtest Acceptance

- 人 / AI 每次只选择当前 slot 的候选。
- 每选一个结构后，下一个结构候选预览会显示新的 occupied envelope。
- 不再出现“批量选完 6 个后，D6 才发现早期住宅撞城堡”的常见回退。
- 真实测试总 loop 时间明显下降，失败定位可以落到具体 slot / candidate。
- `d4_design_time_report.json` 能回答单城市 D4 设计总耗时、程序耗时、AI / 人思考耗时和最慢 slot。
- 可同时开多个不同城市的 D4 session 做并行设计评估，artifact 互不覆盖。

## Non-Goals

- 不做全局自动最优布局。
- 不引入功能区边界主链。
- 不把 `slotId`、`displayRole` 做成 City 全局枚举。
- 不把 D4 quick preflight 作为最终 materialization 真值。
- 不在本案处理城墙、美术换皮、RoadWeaver 样式、地形融合。
- 不在同一城市内并行最终选择多个 slot；同城 slot 选择保持顺序依赖。

## Open Questions

- quick preflight 是否应该在 v0.2 首轮实现，还是作为 v0.2.1。
- session 是否允许人工撤销上一步选择。
- relation hints 是否需要在 targetSlotId 被选择后自动转成 targetAnchorId。
- 是否给 AI 暴露“重新生成当前 slot 候选”的参数，例如新增 patch refs、调整 distanceBand 或提高 compactness 权重。
- 多 agent 并行设计不同城市时，是否需要一个上层 city design tournament / ranking report。
