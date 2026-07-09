# 03 D4 多轮设计 Loop

## 修改目的

D4 从一次性结构落点阶段，调整为 AI 多轮城市设计 loop。D4 只负责城市设计状态的增量构建，不在每轮设计中执行 D5、D6、dressing、worldgen 或 D7。

## 方案

### 1. 主流程

1. AI 拿到一个城市中心点或设计起点。
2. 程序按照半径扫描城市范围，生成可供后续循环使用的地形基础数据；这一步允许耗时较长。
3. 程序生成本轮地形 patch 图，并把 patch 图、上一轮已放结构、occupied field 和功能区上下文交给 AI。
4. AI 根据 patch 图和城市意图，决定本轮要使用什么结构或结构组。
5. 程序根据功能、风格、placement、usage、quality 等 tags 搜索候选结构，并返回可选结构池。
6. AI 调用预选点工具，指定想落地的 patch、结构或结构组；程序根据地形、结构 profile、`collisionEnvelope` 和已有 occupied field 返回一批预选点，AI 从中选择。
7. AI 选择预选点后，决定本轮是直接落一个单一关键结构，还是规划一个阵列方法。
8. 程序执行结构或阵列 plan，生成新的结构 plan，并把本轮结果转成下一轮可用的 occupied field、功能 zone、阵列 zone、已放结构摘要和预览图，避免各个 plan 彼此独立碰撞。
9. AI 重复第 3 到第 8 步，直到决定城市结构设计完成；完成后再进入道路连接、装饰和真实落地阶段。

### 2. 每轮状态

D4 每轮执行后，需要把新生成的结构 plan 转成下一轮可用的占用上下文，包括 `collisionEnvelope` occupied field、功能 zone、阵列 zone、已放结构摘要和预览图。后续 AI 再基于这些上下文继续规划，而不是让每个 plan 彼此独立碰撞。

首个可验收切片先只实现 state / artifact 基础设施，不要求 AI 自动选结构、不要求完整候选点工具、不执行阵列形态扩展、不进入 D5 / D6 / dressing / roads / worldgen。该切片输出 `city_d4_design_loop_<citySeedId>/d4_design_loop_state.json`，并拆分写出 occupied field、function zones、array zones、patch availability、下一轮 AI 摘要和 execution trace。

`d4_design_loop_state.json` 至少包含：

- `cityId`
- `planningMode`
- `roundIndex`
- `placedStructures`
- `anchors`
- `occupiedField`
- `functionZones`
- `arrayZones`
- `patchAvailability`
- `nextAiContextSummary`
- `executionTrace`

`occupiedField` 只能由本轮或历史结构的 `collisionEnvelope` / `bodyEnvelope` 派生，不得读取或恢复 `safetyEnvelope`、`estimatedSafetyEnvelope`、`groupSafetyEnvelope`。

首个切片的最小操作流：

1. `create`：基于 D3 patch 初始化 design loop state，可选从既有 `structure_anchor_map.json` 读取 base anchors。
2. `read`：读取当前 state 和拆分 artifact。
3. `append-one-round`：追加一轮 `anchors[]` / `placedStructures[]` / zones / summary，并把新增结构的 `collisionEnvelope` / `bodyEnvelope` 写入 occupied field。
4. `write-back`：校验并重写 state 与拆分 artifact，不触发提交阶段。

### 3. 设计 loop 与提交阶段分离

D4 不在每轮设计中执行 D5、D6、dressing、worldgen 或 D7。它只负责城市设计状态的增量构建；当 AI 决定完成设计后，再进入提交阶段。

## 可验收提交点

1. 新增 D4 design loop state，提交状态 artifact、读取 / 写入和测试。
2. 新增结构检索上下文和候选点返回能力，提交候选点工具、失败原因和测试。
3. 新增阵列执行结果回写 occupied field / function zones / array zones 的能力，提交增量上下文和测试。
4. 新增 D4 loop 预览和 AI 下一轮输入摘要，提交 preview / summary artifact 和测试。

## 验收需求

1. D4 design loop 必须能保存和读取 loop state，包含已放结构、occupied field、功能 zone、阵列 zone、当前轮次和下一轮 AI 输入摘要。
2. 每轮执行结构或阵列 plan 后，下一轮候选点必须避让上一轮产生的 `collisionEnvelope` occupied field。
3. 候选点工具必须返回候选点列表和不可用原因，至少区分 patch 不存在、容量不足、地形不适配和 envelope 冲突。
4. D4 loop 不得隐式执行 D5、D6、dressing、worldgen 或 D7。
5. 预览图必须能看出本轮新增结构、历史 occupied、功能 zone 或阵列 zone 的关系。
6. 验证用例必须覆盖至少两轮连续设计：第一轮放置结构，第二轮读取第一轮 occupied 并成功避让。
