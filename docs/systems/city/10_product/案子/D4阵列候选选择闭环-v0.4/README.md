# D4阵列候选选择闭环-v0.4

> 状态：v0.4 的“先选 `targetPatchRef` 再在 patch 内排簇”仍作为已实现兼容路径保留。常规 outward 的当前开发真值已转入 `D4连续外扩候选-v0.5`：未预选 patch 时从父结构 D2 bbox 连续向外生成候选；本文件不再定义该新路径。

## 修改目的

1、恢复单轮决策：AI 每次只规划一个阵列主题，程序生成候选并等待 AI 选择；选定后再进入下一轮，避免一次提交多个阵列并全部自动执行。

2、统一外扩语义：以已经 Plan 并形成 collision occupied 的建筑群为基础，把外扩定义为一个方向约束层。v0.4 不得删除或压平 v0.3 的 `composite_array` 父子阵列能力。

## 修改方案

1、查询附近空间：AI 选择一个已 Plan 的建筑群，程序返回其附近可用 patch、方向、距离、剩余容量和外扩预选点。预选点表示建筑群外缘的生长入口，不表示阵列中心；AI 明确要建立新功能区时，才改用全局 patch 搜索。

2、建立方向约束：程序根据建筑群 collision occupied 外缘、AI 选择的方向和目标 patch，生成只向外延伸的可用区域。阵列不得回填到旧 occupied 一侧；空间不足时应换候选或失败，不得靠删点形成残缺阵列。

3、复用现有阵列：外扩层只负责方向和可用区域，内部继续使用簇群、沿线两侧、grid、courtyard、L/U 形等现有算法。`plaza_ring` 在外扩时改为朝外的圆弧或半圆；`composite_array` 继续负责父区域、子区域和多个子阵列。例如以庄园为基础向东生成半环，半环上的点作为多个居住建筑簇的中心。

4、候选选择提交：AI 选定建筑群、方向、patch 和内部阵列方式后，程序生成 3-5 个完整候选并输出预览，暂不修改城市状态。AI 选择一整组后才提交到 loop state，更新 occupied、array zones 和剩余空间，再进入下一轮。快速测试可以显式自动选择最高分候选，但必须记录自动决策来源。

## 实施状态与调用边界

v0.4 已作为显式开发路径接入，使用 `city_create_d4_array_layout_loop`、`city_query_d4_array_expansion_space`、`city_plan_d4_array_expansion_candidates`、`city_select_d4_array_expansion_candidate`、`city_finalize_d4_array_layout_loop` 五段接口。不切换默认 `key_then_array` workflow，也不改变 v0.2/v0.3 的直接 execute 兼容入口。

- 常规外扩：query / plan 必须给 `focusRef`、`direction`、`targetPatchRef`；可用区严格在 focus collision occupied 的外侧，候选 collision 不得回填或重叠旧 occupied。
- 显式新功能区：只在 `newFunctionalArea=true` 时启用。query 不接收预选 patch，也不需要 `focusRef` / `direction` / `targetPatchRef`；它返回按可用性和剩余容量排序的 `globalPatchCandidates[]` 与入口。后续 plan 必须给 `selectedGlobalPatchRef`，否则返回 `D4_ARRAY_LAYOUT_GLOBAL_PATCH_SELECTION_REQUIRED`。
- plan 只生成 3-5 组完整候选，必须满足计数和 collision 约束；空间不足返回 hard fail，不得删点凑残缺阵列。select 默认要求 `candidateId`；仅 `autoSelectHighestScore=true` 才可自动选择，trace 写 `decisionSource=auto_highest_score_explicit`。
- `composite_array` 仍在一次候选内输出 parent zone、subZones 和 child arrays；`plaza_ring` 外扩时保留朝外半圆；`guide_line_dual_side` 在外侧可用区内生成不同的完整双侧候选变体。
