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
| `apply_now` | 只表示把求解结果继续交给执行层，不替代执行层系统真值 |

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
