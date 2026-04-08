# 主模块验收入口

当前主模块测试真值已迁移到目录化结构，旧文件保留为兼容入口。

## 当前主入口

- `C7 -> C8 -> C9` 是否打通
- MCP 是否能读取 `C8` 会话并提交节点决策
- `start` 节点直接放置是否稳定
- child 节点是否通过 connector / jigsaw 求解器完成落点，而不是长期依赖人工 `x / z`
- 已校验节点是否能进入 `C9` 队列
- `C9` 是否能按队列执行落地
- `city_jigsaw_solve` 是否返回中文 `debug_trace`，并且每步都能说明“做了什么 / 用什么实现的 / 结果是什么”
- solver 逐步预览图中是否能直接看见拼图方块位置与结构矩形
- `04_vanilla_piece_result` 是否能直接解释 child 失败卡在：
  - `target/name`
  - `attach`
  - `bounds/area`
  - `terrain`
  - `vanilla_empty_stub`
- `city_jigsaw_solve` 在请求 `jigsaw_up_*` / `jigsaw_down_*` 时，是否直接返回 `vertical_jigsaw_solver_pending` 与中文说明，而不再混入当前水平 solver
- `C8` 的 start 节点是否带出 runtime 选点字段：
  - `start_solver_kind`
  - `start_runtime_candidates`
  - `chosen_start_connector_id`
  - `chosen_start_connector_front`
  - `chosen_start_rotation`
  - `chosen_start_reason_zh`
  - `runtime_fallback_used`
  - `runtime_fallback_reason`

- 测试入口：`./测试入口.md`
- 影响面：`./影响面.md`

## 历史证据

- `../../../../90_archive/StructureBinder/dev_docs/current_20260402_030950/`
- `../../../../90_archive/StructureBinder/root_docs/TEST_C_FLOW_CHECKLIST.md`

## 当前建议继续验证

- 主链连续多节点施工
- `g_market_06` 这类 child collision 样例是否已前移到 `C8` 拦截
- `start` 直接放置与 child 求解放置是否能同时成立
- 失败后的 retry / blocked 可读性
- 若 solver 无合法解，是否能在 `C8` 明确回包，而不是拖到 `C9` runtime 才爆炸
- `g_market_02` 这类 catalog 漂移样例中，是否能从单次 solver 调试产物直接看懂：
  - 扫到了哪些 runtime jigsaw
  - 旧 connector 为什么对不上
  - runtime-derived connector 为什么能命中
  - 最终为什么停在 `no_valid_jigsaw_solution`
- 针对 `no_valid_jigsaw_solution`，是否能在单次产物中直接看到：
  - `manual_child_connector_candidates`
  - `manual_attach_summary`
  - `first_blocker_stage`
  - `vanilla_stub_generated`
  - 第 04 步预览图中的候选矩形颜色分层
- `g_market_03` 在重新生成 `C8` 后，start 是否不再长期固定在多边形北侧边缘，且首个水平扩展失败原因不再停留在已知的“朝外越界”
- 当当前环境拿不到 runtime 模板管理器时，`C8` 是否显式落出 fallback 证据，而不是静默继续沿用旧 seed / anchor
