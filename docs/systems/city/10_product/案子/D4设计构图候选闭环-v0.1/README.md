# City 案子：D4 设计构图候选闭环 v0.1

## Summary

本案目标是在当前 D3-D6 结构落地闭环之上，补齐 D4 的“城市设计感”能力：AI 不再直接手填每个结构的 `anchorBlock`，而是先提交一组城市设计 slot 和通用空间关系意图；程序根据 D3 地形 patch、结构 envelope facts、已选 anchor 和几何防撞规则，为每个 slot 生成少量代表性候选点；AI 再基于设计理由选择候选。

本案不恢复旧“先规划功能区边界，再把结构塞进功能区”的主链。`slotId` 是本次城市设计里的结构角色槽位，不是功能区枚举；`candidatePatchRefs` 只是候选搜索范围和地形依据，不是硬边界。真正硬约束仍来自 D6 locked actual footprint、collision envelope、ledger overlap 和 worldgen signature gate。功能区 / 城市边界继续在 D7 后根据真实落地结构和道路关系反推。

## Why

当前底层落地能力已经基本站住：

- D4 可以校验 anchor 在 D3 patch / city grid 内。
- envelope facts 可以缩紧固定 / 近固定结构 bbox。
- D6 可以 non-mutating probe-and-lock，锁定真实 bbox group、actual footprint 和 signature。
- D5 / worldgen hook 可以在生成期抑制植被和自然结构抢占。
- D7 可以基于 ledger actual footprint 做道路和边界后处理。

但现在 D4 仍依赖 AI / Codex 直接选择结构落脚点。AI 可以看 D3 patch 图做设计判断，却不擅长稳定处理几何细节，例如：

- 两个相邻结构是否会因为 envelope 互相重叠。
- 大结构是否还有足够 clearance。
- 某个水岸 / 高点 patch 中哪个点更适合当 anchor。
- 先放核心结构后，住宅 / 农业 / 防御节点应该围绕哪里找点。

因此下一步最有价值的不是继续堆底层落地能力，而是把 D4 改成“AI 提意图，程序给少量安全候选，AI 做设计取舍”的闭环。

## Core Principles

### 1. Slot 是设计意图，不是功能区边界

`slotId` 代表本次城市设计中需要一个结构节点，例如：

```json
{
  "slotId": "admin_core",
  "displayRole": "行政核心",
  "structureIds": ["trek:overworld/rare/villager_castle"]
}
```

程序只把 `slotId` 当作本次 plan 内对象 ID，不把 `admin_core` 当成全局 City 枚举，也不由它推导结构语义。结构语义仍来自 TerraSense profile。

### 2. Patch 是候选搜索依据，不是硬边界

```json
{
  "slotId": "admin_core",
  "candidatePatchRefs": ["山脊112", "崖壁22"]
}
```

含义是：优先在这些 D3 patch 内寻找 anchor 候选，并把它们作为地形解释依据。结构真实 bbox / soft yard 可以跨出 patch，只要不违反硬约束。

### 3. 关系只引用 slotId / anchorId

不引入 `too_close_to_farm`、`inside_dense_forest` 这类业务枚举。D4 只支持通用空间关系：

```json
{
  "relationHints": [
    {"targetSlotId": "harbor_trade", "distanceBand": "medium"},
    {"targetAnchorId": "agriculture_farm_01", "distanceBand": "far"}
  ]
}
```

- `targetSlotId`：引用尚未落地或正在规划的 slot，只参与软评分。
- `targetAnchorId`：引用已经选定的具体 anchor，可参与硬防撞和距离评分。
- `distanceBand`：通用距离档，首版只保留 `near`、`medium`、`far`。

### 4. 先后顺序显式化

D4 必须有 `placementOrder`：

```json
{
  "placementOrder": [
    "admin_core",
    "harbor_trade",
    "main_plaza",
    "residential_cluster",
    "agriculture_farm",
    "defense_tower"
  ]
}
```

首版建议顺序：

1. 大结构 / 核心结构：行政核心、港口、地标。
2. 骨架连接节点：广场、道路节点。
3. 依附结构：住宅、市场、仓库。
4. 外圈结构：农田、牧场、防御塔、边界节点。

已经选定的 anchors 进入本轮 occupied set；尚未选定的 slots 只作为软关系目标。

### 5. 少量代表候选，不做海量菜单

候选点不是让 AI 从 200 个点里选最高分。每个 slot 首版只返回 3-5 个代表性候选，并按设计取舍分组：

- `best_fit`：最符合 slot query。
- `dramatic`：视觉 / 叙事更强，但几何或道路风险更高。
- `practical`：最稳、最容易连路。
- `compact`：更利于城市紧凑。

AI 需要选择候选并写出理由，也可以要求程序按新的 patch / 距离关系重新生成候选。

## Proposed Flow

```text
D3 city_landform_review_package.json + landform_review_map.png
  + curated StructureProfile / envelope facts
  + D4 DesignSlotPlan
  -> D4 candidate generation
  -> D4 candidate preview / candidate report
  -> AI selects candidates with reason
  -> D4 StructureAnchorPlan / StructureAnchorMap
  -> D5 / D6 / execute_d5 / worldgen / D7 existing flow
```

## Data Sketch

### D4 DesignSlotPlan

```json
{
  "schemaVersion": "city_d4_design_slot_plan.v0.1",
  "cityId": "city_example",
  "placementOrder": [
    "admin_core",
    "harbor_trade",
    "main_plaza",
    "residential_cluster",
    "agriculture_farm",
    "defense_tower"
  ],
  "slots": [
    {
      "slotId": "admin_core",
      "displayRole": "行政核心",
      "candidatePatchRefs": ["山脊112", "崖壁22"],
      "structureIds": ["trek:overworld/rare/villager_castle"],
      "relationHints": [
        {"targetSlotId": "harbor_trade", "distanceBand": "medium"},
        {"targetSlotId": "main_plaza", "distanceBand": "near"}
      ],
      "layoutHints": {
        "density": "normal",
        "edgePreference": "high_edge",
        "roadAccess": "primary"
      }
    }
  ]
}
```

字段约束：

- `slotId`：本 plan 内唯一 ID。
- `displayRole`：给 AI / 人类 review 看，程序不作为硬枚举解释。
- `candidatePatchRefs`：D3 `landformPatchId` 或 `mapLabel`，至少一个。
- `structureId` / `structureIds`：来自 TerraSense profile catalog；单结构 slot 可写 `structureId`，多备选 slot 写 `structureIds`。
- `relationHints[].targetSlotId` 与 `targetAnchorId` 二选一。
- `distanceBand` 首版限定为 `near` / `medium` / `far`。
- `layoutHints` 首版只作为评分 hint，不作为 hard fail。

### D4 AnchorCandidateSet

```json
{
  "schemaVersion": "city_d4_anchor_candidate_set.v0.1",
  "cityId": "city_example",
  "slotCandidates": [
    {
      "slotId": "admin_core",
      "candidates": [
        {
          "candidateId": "admin_core_best_fit_01",
          "candidateKind": "best_fit",
          "structureId": "trek:overworld/rare/villager_castle",
          "anchorBlock": {"x": 1408, "z": -1728},
          "sourcePatchRefs": ["崖壁22"],
          "estimatedCollisionEnvelope": {"minX": 1328, "minZ": -1744, "maxX": 1424, "maxZ": -1638},
          "estimatedMaskEnvelope": {"minX": 1324, "minZ": -1748, "maxX": 1428, "maxZ": -1634},
          "geometryStatus": "available",
          "scoreBreakdown": {
            "terrainFit": 0.82,
            "relationFit": 0.64,
            "collisionSafety": 1.0,
            "roadAccessPotential": 0.7,
            "designDrama": 0.9
          },
          "placementReason": "位于高点 patch 边缘，适合作为行政核心并形成视觉中心。",
          "risks": ["slope_medium"]
        }
      ]
    }
  ]
}
```

`candidateId` 需要在同一个 slot 内稳定且唯一；首版建议由 `slotId + candidateKind + 两位序号` 组成，便于人/AI 在 `city_select_d4_candidates` 中精确选择。

### D4 AnchorSelectionPlan

```json
{
  "schemaVersion": "city_d4_anchor_selection_plan.v0.1",
  "cityId": "city_example",
  "selectedCandidates": [
    {
      "slotId": "admin_core",
      "candidateId": "admin_core_best_fit_01",
      "anchorId": "admin_core_01",
      "selectionReason": "选择高点候选，让城堡成为城市视觉核心。"
    }
  ]
}
```

程序可由 selection plan 转换为当前 active `StructureAnchorPlan`，再进入既有 D4 anchor 校验与 D5-D7 主链。

## Candidate Generation Rules

首版候选生成只做低复杂度规则，不引入全局优化器。

### Patch 代表点

每个引用 patch 默认取 1-2 个代表点：

- patch center。
- 靠近目标关系方向的 patch 内点。
- 水岸 patch 可取靠水边代表点。
- 高点 / 山脊 patch 可取高度更高或靠边缘点，前提是 D3 metrics 支持。

如果 D3 只有 cell 级 patch 信息，首版按 member cell 中心取点，不做逐 block 搜索。

### 几何过滤

候选点必须先通过程序几何过滤：

- anchor 在 city grid 内。
- anchor 在 `candidatePatchRefs` 中至少一个 patch 的 member cell 内。
- structure profile / envelope facts 可用。
- estimated collision envelope 不与已选 anchors 的 collision envelope 重叠。
- estimated envelope 不越过本阶段定义的 hard city safety bounds。

注意：estimated envelope 只是 D4 候选阶段预估；D6 仍会用 actual footprint 重新锁定，且 D6 结果才是最终防撞真值。

### 关系评分

`distanceBand` 不直接等于 hard fail。首版建议：

- `near`：优先在 32-96 blocks。
- `medium`：优先在 96-224 blocks。
- `far`：优先大于 224 blocks。

具体数值应可配置，并根据城市 scale / 结构 envelope 动态调整。

### 候选数量限制

- 每个 slot 默认最多 5 个候选。
- 每个 candidate kind 最多 1-2 个。
- 如果所有候选都不可用，输出 blocking reason，而不是扩大到海量候选。

## Preview / Review

新增或扩展 D4 预览：

- D3 patch 底图。
- 已选 anchors 和 collision / mask envelope。
- 当前 slot 的候选点，按 candidate kind 区分颜色。
- relation hints 线条，例如 near / medium / far。
- 每个候选的 `placementReason` 和主要风险。

预览必须避免文字重叠。候选图只展示少量候选；详细评分进入 JSON trace。

## Non-Goals

- 不恢复 `FunctionZoneMap` / `BuildableAreaMap` 主链。
- 不把 `slotId` 升级成 City 全局功能枚举。
- 不让 `candidatePatchRefs` 成为结构不可超出的功能区边界。
- 不实现 beam search、遗传算法或全局最优城市布局。
- 不要求 AI 一次性填完整城市全部 anchor。
- 不在本案处理 Road Weaver 接入、城墙、地形兼容、NPC / loot 替换。

## Success Criteria

- AI 可以只提交 slot 意图和通用关系，不需要手算 anchorBlock。
- 程序能为每个 slot 生成 3-5 个可 review 候选。
- 候选报告能说明每个候选的地形依据、关系依据、几何状态和风险。
- AI 选择候选后，可自动生成当前 active `StructureAnchorPlan` 并进入既有 D4-D7 主链。
- D4 候选阶段不会误把 patch 当功能区硬边界。
- D6 仍能在 actual group 与 D4 估计不一致时锁定真实结果；若防撞失败，明确回写候选/选择诊断。

## Open Questions

- `distanceBand` 默认数值是否按 city scale / 结构大小动态化。
- D3 是否需要额外输出高点候选、水岸边线、入口方向、可连路廊道等 design review 信息。
- slot selection 是否允许多轮交互：AI 选核心后，程序再为依附 slot 重新生成候选。
- 是否需要把 D4 candidate query 暴露为独立 MCP endpoint，还是先合入 `city_plan_d4` 的前置调试接口。
