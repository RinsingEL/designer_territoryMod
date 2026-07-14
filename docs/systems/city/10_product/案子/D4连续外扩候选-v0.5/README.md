# D4连续外扩候选-v0.5

## 一、目的

1、连续外扩问题修复：

   - 常规外扩不再由人工预选 `patch`；避免父结构与首个住宅簇之间因 patch 边界留下大空档。
   - 阵列从父结构的真实 D2 范围开始向指定方向生长，而不是跳到某个远处地块后再排布。

2、地形约束优化：

   - D3 patch 从“选址前提”改为候选点的地形筛选和评分事实；候选可跨 patch，不因边界中断。
   - 近圈被水体、陡坡或已占用否决时才向外扩张，必须解释跳过原因。

3、预览可读性优化：

   - 设计验收图能分辨 D2 实体、collision 和 mask，不再只给重叠长标签的调试总图。
   - 每轮外扩输出局部放大图，便于判断父结构与首户、簇内建筑之间的真实距离。

## 二、方案

1、连续候选生成：

   - 默认输入锁定为父结构引用、方向、目标实体间距和阵列方式；常规外扩不要求 `targetPatchRef`，显式传入时仅作为兼容约束。
   - 以父结构的 D2 `body` / `collision` bbox 外缘为原点，沿方向生成近、中、远三档连续候选；近圈优先满足目标实体间距，后两档只在近圈不可用时作为回退。
   - `actualBodyGapBlocks` 取整组结构相对父 body 的最近方向间距。连续 `guide_line_dual_side` 的内侧首排锁定该间距，另一侧只能继续向外展开，不得因双侧横移把整组推远。
   - 混合尺寸阵列以全部成员的 D2 body 并集计算连续前沿；最大外伸成员决定首排退距，不能只按数组第一个结构计算后让其他成员回压父簇。
   - 阵列内部仍按 D2 collision 尺寸排布；`mask` 不参与 D4 防撞或自动间距。

2、后置地形筛选：

   - 每个几何候选再与 D3 `memberCells`、水体、坡度、可用容量和既有 occupied 相交并评分。
   - 一个候选可覆盖多个 patch；返回命中的 patch 只作为解释、风险和后续装饰语境，不作为边界。
   - 近圈无可用候选时，trace 逐项记录碰撞、水体、陡坡、member-cell 不足或容量不足，再开启中圈；中圈失败才开启远圈。

3、候选选择与预览：

   - 保留 `create -> query -> plan -> select -> finalize`：生成候选不写 state，整组选定才写 occupied、zones 和剩余空间。
   - 默认至少返回 3 组完整合法候选；调用方显式传 `minCandidateCount=2` 时，允许返回 2 组完整合法候选供人工选择，不得以删点或不完整簇凑数。
   - 总览图用于比较近、中、远组；局部图以父结构和当前候选簇为中心，短标签只标候选编号。
   - 调试图可显示 D2 body、collision、mask 三层；设计主图默认不叠 bbox，避免将保留边距误看成建筑体积。

4、接口口径：

   - 沿用 `city_d4_array_layout_plan.v0.4`；常规 outward 未传 `targetPatchRef` 时进入 `expansionPolicy` 连续前沿模式。`expansionPolicy` 使用 `actualBodyGapMin`、`actualBodyGapMax`，可选 `frontierExpansionStepBlocks`、`frontierMaxExpansionRounds`。
   - 查询返回 `focusBodyEnvelope`、`frontierRings[]`；候选返回 `expansionMode=continuous_focus_frontier`、`parentBodyEnvelope`、`frontierRing`、`actualBodyGapBlocks`、`terrainPatchRefs` 和 `frontierTrace.reasonCode`。候选集另写逐圈 `frontierSearchTrace[]`。
   - 总览沿用 `d4_array_expansion_candidates.png`，候选局部图为 `d4_array_expansion_candidate_detail.png`；最终锚点最密簇局部图为 `structure_anchor_cluster_preview.png`。
   - 本案先锁定行为：常规外扩不得要求或暗含 `targetPatchRef`；`newFunctionalArea=true` 的全局 patch 搜索语义保持独立。
