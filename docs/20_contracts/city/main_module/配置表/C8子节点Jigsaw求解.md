# C8 子节点 Jigsaw 求解配置表

## 入口契约

### `city_jigsaw_solve`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `city_id` | string | 是 | 城市编号 |
| `group_id` | string | 否 | 目标 group |
| `build_area_id` | string | 否 | 目标建造区 |
| `parent_node_id` | string | 是 | 当前 parent placement 节点 |
| `parent_connector_id` | string | 是 | 本次使用的 parent jigsaw |
| `selected_template_id` | string | 是 | 本次 child 模板 |
| `selected_connector_dir` | string | 否 | AI 期望方向 |
| `selected_rotation` | int | 否 | 当前请求保留字段 |
| `apply_now` | boolean | 否 | 是否立即交给执行层落地 |

## 当前回包重点

| 字段 | 说明 |
| --- | --- |
| `solve_result` | 当前求解结果对象 |
| `reject_reason` | 结构化拒绝原因 |
| `runtime_parent_connectors` | runtime 模板中扫描出的 parent jigsaw 候选 |
| `debug_preview_steps` | 调试预览步骤列表 |
| `apply_now` | 当前是否走立即落地 |
| `queue_summary / active_node / validated_nodes / failed_attempts` | 求解成功后最新的 C8 会话树快照 |
| `solve_result.placement.incoming_pool_refs` | 当前 solved child 实际接入的 runtime parent pool |
| `solve_result.placement.outgoing_connectors` | child 当前真实 runtime outgoing connector、`pool_refs` 与 pool 真值诊断 |
| `placement_execution.terrain_preparation.post_cleanup` | `apply_now=true` 时的落地后 jigsaw 收口统计 |

## 当前稳定调试产物

| 产物 | 位置 | 说明 |
| --- | --- | --- |
| `trace.json` | `group/<groupId>/jigsaw_solver_debug/<runId>/` | 保存完整 debug trace |
| 预览图 | 同目录 | 保存步骤预览图 |
| `*.legend.json` | 同目录 | 保存预览图图例与 evidence |

## 当前行为约束

| 约束 | 说明 |
| --- | --- |
| 求解深度 | 当前固定单步 child 扩展，深度为 `1` |
| 垂直 jigsaw | 当前不进入真实求解，只返回 pending 占位结果 |
| runtime parent pool | 当前优先读取 parent runtime jigsaw 原始 `pool`，再在该 pool 中筛 AI 指定模板 |
| 求解成功后的 child | 会立即写回 `validated_nodes / placements`，即使 `apply_now=false` 也入树 |
| placeholder child | 同一 parent 下旧的合成 placeholder 会被真实 `vjigsaw_*` child 替换 |
| 下一层 ready 节点 | 当前优先按真实 child runtime connector 的 `pool_refs` 展开；对 namespaced runtime pool 先按 pool 路径收束成员，catalog 仅做兜底 |
| runtime/catalog pool 冲突 | 当前不阻断求解，但会把 `pool_truth_source / pool_mismatch / mismatch_detail` 写进 `solve_result.placement.outgoing_connectors` 与 `node_debug` |
| `apply_now` | 只表示把已成功入树的求解结果继续交给执行层，不控制是否入树 |
| 落地后 jigsaw | 所有已落地 jigsaw 统一按 `final_state -> air fallback` 收口，不保留世界中的残留 jigsaw 方块 |
| 调试预览图 | 当前 `jigsaw_solver_debug` 预览标签改为外置错位、半透明底、带引线；`*.legend.json` 会额外写入 `label_layout / label_opacity / label_scope` |

## 常见拒绝类型

| `reject_reason` | 说明 |
| --- | --- |
| `missing_parent_connector_id` | 缺少 parent connector |
| `missing_selected_template_meta` | catalog 中缺少 child 模板元数据 |
| `parent_connector_not_found_in_catalog` | catalog 中找不到请求的 connector |
| `selected_template_not_in_runtime_parent_pool` | 指定模板不在当前 runtime parent pool 中 |
| `runtime_parent_pool_missing` | runtime parent jigsaw 没有可用 pool |

## 关联系统

- `apply_now` 后续执行真值：`../../../../10_product/city/c9_execution/01_scope.md`
- 调试回放工具：`../../../../10_product/devtools/code_process_viewer/功能设计/Jigsaw求解器回放.md`
