# C8 子节点 Jigsaw 求解实现

## 入口方法

| 位置 | 作用 |
| --- | --- |
| `CityController.handleCityJigsawSolve(...)` | 解析请求、恢复 parent 上下文、组织 debug trace 与 apply_now 逻辑 |

## 主要实现点

| 位置 | 说明 |
| --- | --- |
| `CityVanillaJigsawAdapterService.solve(...)` | 执行单步 child `jigsaw` 求解 |
| `CityJigsawSolverDebugTrace.create(...)` | 创建 `group/jigsaw_solver_debug/<runId>` 目录 |
| `CityJigsawSolverPreviewExporter.export(...)` | 生成步骤预览图与 legend |
| `SolvedPlacementExecutionService` | 在 `apply_now` 模式下把求解结果接到执行层 |

## 当前实现细节

- `handleCityJigsawSolve(...)` 先通过 `loadC9GenerationPlan(...)` 读取最新 group 级 `C8`，再定位 `parentPlacement` 与现有 placements。
- `CityVanillaJigsawAdapterService.solve(...)` 当前固定单步 child 扩展：
  - 深度固定为 `1`
  - 垂直 `jigsaw` 直接返回 pending 占位
  - `selected_rotation` 当前只保留为请求信息，结果里会给出忽略警告
- 当前 parent pool 解析不再构造脱离式单模板 pool，而是优先从 parent runtime jigsaw 原始 `pool` 中筛选 AI 指定模板。

## 当前调试产物

| 产物 | 说明 |
| --- | --- |
| `trace.json` | 记录请求、connector 解析、pool 选择、校验与 apply 结果 |
| `debug_preview_steps` | 回包中的预览步骤列表 |
| 步骤图片与 `*.legend.json` | 供人工与工具回放证据 |

## 继续追代码建议

1. 先看 `handleCityJigsawSolve(...)` 前半段如何恢复 `geometry / parentPlacement / existingPlacements`。
2. 再看 `CityVanillaJigsawAdapterService.solve(...)` 中 `findRuntimeParentConnector(...)`、`buildSelectedTemplatePool(...)` 与校验逻辑。
3. 若需要继续看立即落地，再跳到 `../c9_execution.md` 与执行层系统文档。
