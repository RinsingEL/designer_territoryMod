# 主模块 Jigsaw 求解器接入方案

## 背景

当前主模块会话已经切到：

- `C7` 工头计划
- `C8` 节点会话
- `C9` 执行层

但 child 节点的落点仍可能依赖人工给定 `x / z`，这会导致以下问题：

- `C8` 可以先放行
- `C9` 才在真实模板 bounds 上发现 `runtime_footprint_collision`
- connector / jigsaw 语义没有真正进入主链

这会让主模块工头系统只能决定“选哪个结构”，却不能稳定控制“这个结构怎么接上去”。

## 目标

- 保留 `start` 节点直接 `place` 的标准能力
- 为 child 节点引入 connector / jigsaw 求解器
- 在正式入队前完成可落地性预判
- 继续由工头系统决定“下一步选哪个结构”，而不是回退到原版随机扩张逻辑

## 核心原则

### 保持开闭分层

- 工头系统继续负责：
  - 节点顺序
  - 阶段推进
  - 结构选择
  - 收尾与 fallback 策略意图
- 求解器负责：
  - 父 / 子 connector 匹配
  - `origin` / `rotation` 求解
  - 真实 bounds 计算
  - 落地前合法性预判
- `C9` 继续负责：
  - runtime 最终校验
  - 清空与真实执行
  - retry / blocked

### 保留 start 直接放置

- 每个主模块会话都必须保留 `start` 节点直接 `place` 的能力
- 这条路径不应因为求解器接入而被删除
- `start` 节点仍保留直接 `place` 能力，但 `C7` 给出的 `start_x / start_z / start_rotation` 只再视为 hint
- `C8` 在有 runtime 模板时会重新扫描 `start` 模板的水平 jigsaw，并围绕 anchor 做局部挪位与 rotation 评分，最终决定真正的起点与朝向
- 若当前主链拿不到 `ServerLevel / StructureTemplateManager`，必须显式回退到旧 seed / anchor heuristics，并写入 warning 与调试证据

### child 节点默认走求解器

- child 节点后续默认不再要求人工提供最终 `x / z`
- 工头主要提供：
  - `selected_template_id`
  - `selected_connector_dir`
  - 必要时的 `selected_rotation` 偏好
- 程序根据父节点和子模板的 connector 信息解出最终落点

## 与原版 jigsaw 的关系

- 优先复用原版 jigsaw / pool / socket / connector 的语义与求解能力
- 不把原版“随机扩张决定下一块是谁”直接引入主模块主链
- 仍由工头系统明确决定本步使用哪个结构；求解器只负责回答“这个结构能否这样接上去”

## 责任边界

### C7 工头计划

- 决定当前节点与阶段顺序
- 决定本步候选结构
- 决定当前节点是否应进入收尾语义
- 不负责精确几何落点

### C8 节点会话

- 接收工头决策
- 调用求解器完成：
  - parent / child connector 匹配
  - `origin` / `rotation` 求解
  - 真实 bounds 计算
- 在 `C8` 先做以下拒绝：
  - `out_of_area`
  - 真实 bounds 冲突
  - 地形不合法
  - 收尾条件不满足
- 只有通过后，才把节点写入 `validated_nodes`

### C9 执行层

- 消费已经求解完成的节点
- 继续做 runtime 最终校验
- 当世界状态在 `C8` 之后发生变化时，仍可拒绝落地
- 不重新决定 child 结构，也不再做手工 origin 猜测

## 兼容路径

### Path A：start 直接放置

适用范围：

- 每个主模块 foundation 的起点节点
- 必要的显式 debug / 回归场景

特征：

- 允许继续直接使用给定 `x / z`
- 允许继续直接 `place`
- 仍需经过 polygon / 地形 / 执行层门控校验

### Path B：child 求解放置

适用范围：

- 所有通过 connector 继续扩张的 child 节点

特征：

- 由程序按 parent / child connector 反解 origin
- 使用真实模板 bounds 做预校验
- 不能再长期依赖手填 `x / z`

### Path C：手工覆盖

适用范围：

- 极少量调试或人工修正场景

特征：

- 手工坐标仅作为显式 override / debug 手段
- 不是 child 主路径
- 若 override 与求解结果冲突，应优先记录为调试路径，而不是主契约默认口径

## 最小输入输出

### 工头最小输入

- `node_id`
- `selected_template_id`
- `selected_connector_dir`
- 可选的 `selected_rotation`
- 可选的调试级 `placement_override`

### 求解器最小输出

- `resolved_origin_x`
- `resolved_origin_z`
- `resolved_rotation`
- `incoming_parent_connector_id`
- `incoming_child_connector_id`
- `resolved_bounds`
- `placement_mode`
  - `direct_start`
  - `jigsaw_solved`
  - `manual_override`

## 当前不做

- 不删除直接 `place` 路径
- 不把道路和次级建筑一起并入本轮求解器案子
- 不把完整原版随机村庄扩张逻辑直接搬进主模块主链
- 不让 `C9` 再承担“帮 `C8` 猜 child 落点”的职责

## 首批验收样例

- `g_market_06`
  - 首节点直接放置成功
  - `child_1` 不应再因手工 origin 造成 runtime collision
- `g_market_05`
  - 已经跑通多节点 direct / apply_now 链路
  - 后续作为对比样本，验证求解器接入后不会破坏既有 `start` 能力

## 当前决定

- 该能力层被视为主模块工头系统的正式配套能力，而不是临时调试脚本
- 本轮允许做大重构，但要求拆得干净：
  - `start` 直接放置继续保留
  - child 求解器单独成层
  - `C8` 和 `C9` 边界不回退到旧式混写逻辑

## 当前阶段落地范围

- 当前阶段先交付一个独立的 AI 可调用 jigsaw 求解器工具
- 该工具不再采用手工 `origin / rotation` 解算，而是改为：
  - 使用真实 `parent_connector_id`
  - 为已选 child 模板构造临时单模板 pool
  - 调用 vanilla jigsaw 深度 1 拼接逻辑生成单个 child piece
- 工具支持两种模式：
  - 仅返回 vanilla jigsaw 求解出的 child placement 结果
  - 求解成功后继续复用现有 `place` / 执行链完成清理与落地
- `solve_and_place` 会复用现有 chunk gate、runtime validator、terrain preparation，但最终 placement 改为放置 vanilla jigsaw piece，并保留 child 里的 jigsaw 方块
- 当前阶段只接受真实 jigsaw connector id，不再兼容 `next_start_*` 这类旧 synthetic connector
- 当前阶段会在 `solve_result.runtime_parent_connectors` 中结构化返回 runtime 模板实际扫到的 parent jigsaw 候选
- 当旧 catalog connector 与 runtime 模板发生漂移时，可以直接把这些 runtime 派生的 `jigsaw_<front>_<x>_<y>_<z>` id 重新作为 `parent_connector_id` 提交给工具
- 当前阶段每次 `city_jigsaw_solve` 都会额外输出一组 solver 调试产物：
  - `debug_run_id`
  - `debug_artifact_dir`
  - `debug_trace`
  - `debug_preview_steps`
- `debug_trace` 中的每个关键步骤都必须同时说明：
  - 这一段主要做了什么
  - 这一段是用什么实现机制做的
  - 这一段产出了什么关键结果或证据
- 当前阶段 `debug_trace[step_key=04_vanilla_piece_result]` 还必须补充 runtime 真值驱动的 child 失败机制拆解，至少包括：
  - `parent_target`
  - `start_pos`
  - `pool_template_id`
  - `manual_child_connector_candidates`
  - `manual_attach_summary`
  - `first_blocker_stage`
  - `vanilla_stub_generated`
  - `piece_generated`
- 当第 04 步进一步卡在 `vanilla_empty_stub` 时，还应继续输出 vanilla builder 诊断字段，用于解释“stub 为什么没提取出 child piece”，至少包括：
  - `vanilla_piece_count`
  - `vanilla_pool_element_piece_count`
  - `selected_vanilla_piece_index`
  - `vanilla_piece_extraction_stage`
  - `vanilla_piece_debug_summary_zh`
  - `vanilla_piece_types`
  - `vanilla_piece_items`
- 其中 child 兼容诊断必须以运行时已加载模板为真值：
  - parent jigsaw 由 `StructureTemplate.filterBlocks(..., Blocks.JIGSAW)` 扫描
  - child jigsaw 也必须由 runtime 模板枚举
  - catalog 仅作为参考，不再作为 child attach 成败的主判断来源
- 当前中文关键步骤至少覆盖：
  - 请求上下文装载
  - runtime parent jigsaw 扫描
  - parent connector 解析
  - 临时模板池与 vanilla child 生成
  - child / bounds 校验
  - `apply_now` 时的执行层落地结果
- 当前阶段默认导出逐步预览图序列，并落盘到：
  - `cities/<city>/groups/<group>/jigsaw_solver_debug/<debug_run_id>/`
- 逐步预览图至少展示：
  - parent 与已有结构矩形
  - runtime 扫到的拼图方块位置与标签
  - 当前选中的 connector
  - 生成出的 child 结构矩形
  - 失败时的关键几何状态
- 第 04 步预览图还必须额外展示：
  - parent connector 与 startPos
  - 每个 child runtime 候选的结构矩形
  - `name 不命中 / attach 失败 / bounds 或碰撞失败 / terrain 失败 / 理论可行` 的颜色区分
  - 与 `manual_attach_summary` 对齐的中文结论标题
- 当前独立 `city_jigsaw_solve` 求解器正式收口为“水平专用”：
  - `north / south / east / west` 继续走现有 `CityVanillaJigsawAdapterService`
  - `up / down` 在 parent connector runtime 解析完成后立刻分流到独立 vertical solver 占位路由
  - 当前占位返回 `vertical_jigsaw_solver_pending`，并附中文说明“当前 solver 仅支持水平 jigsaw，垂直 jigsaw 将由独立求解器处理”
- `C8` 主链的 `start` 评分当前也只把水平 jigsaw 作为首扩展候选：
  - 先扫描 runtime 模板中的水平 connector
  - 再判断 connector 是否朝向多边形内部
  - 再复用当前水平 solver 做第一跳 child dry-run
  - 若 runtime 不可用，则显式回退，不允许静默沿用旧 heuristics
- 当前阶段对 `terrain_probe_points` 的运行口径已临时调整：
  - `terrain_probe_points` 仍来自 TerraSense C3.5 预处理产物，不从运行时现算
  - TerraSense 默认会按 `placement.footprint` 自动补出“矩形四角 + 中心点”5 个 probe 点
  - 但当前主模块已经引入 foundation / terrain adaptation 语义，因此 `StructureBinder` 里的 solver 与 arrangement engine 暂时不再把这些 probe 点用于硬地形拒绝
  - 当前代码里统一以 `TEMP-C35-TERRAIN-PROBE-HARD-CHECK-DISABLED` 作为临时关闭标记，后续若要恢复，可按该标记整体检索回滚
- 当前阶段地形职责的临时划分为：
  - solver 继续负责 connector、rotation、bounds、碰撞、可解释调试
  - foundation / terrain adaptation / 执行层负责真实的地形适配、嵌入地面、基台与地表修正
  - 因此当前若模板只靠 `terrain_probe_points` 才会被拒绝，不应在 solver 阶段直接判死
- 当前阶段 `selected_rotation` 仅保留兼容字段，第一版不作为实际求解约束，应以 vanilla jigsaw 返回的实际 rotation 为准
- 当前阶段暂不把 child 默认切进 `C8 submit` 主链
- 当前阶段也不改 `C9` 的默认消费方式
- 后续主模块正式接入时，应直接复用本轮工具层与其真实 connector 口径、vanilla piece placement 输出

## 当前真机状态

- 以 `g_market_03` 为当前主回归样例时：
  - `C8` 的 start 已由 runtime 水平 connector 评分决定，不再因为旧的北侧朝外越界问题直接失败
  - 在临时关闭 `terrain_probe_points` 硬限制后，start 第一跳 dry-run 的首阻塞已从 `terrain` 前移为 `vanilla_empty_stub`
  - 当前水平口 `jigsaw_east_7_1_0` 的手工兼容分析已经可以得到：
    - `attachable_count = 1`
    - `area_pass_count = 1`
    - `collision_free_count = 1`
    - `terrain_pass_count = 1`
    - `viable_count = 1`
  - 这表示当前“理论可行候选”已经存在，下一阶段的主问题是 `JigsawPlacement.addPieces(...)` 返回了 stub，但没有提取出可用 child piece
- 垂直口当前仍按计划分流：
  - `jigsaw_up_*` / `jigsaw_down_*` 直接返回 `vertical_jigsaw_solver_pending`
  - 不再混入当前水平求解器的 start / child 评分链
