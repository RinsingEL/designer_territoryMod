# 主模块建造范围

当前主模块系统真值已迁移到目录化结构，旧文件保留为兼容入口。

## 当前主入口

- 系统概述：`./系统概述.md`
- 功能设计：`./功能设计/C7工头计划.md`
- 功能设计：`./功能设计/C8节点会话与提交.md`
- 功能设计：`./功能设计/C8子节点Jigsaw求解.md`

当前主模块建造主链继续保持：

- `C7` 工头计划
- `C8` 节点决策、connector / jigsaw 求解与程序校验
- `C9` 队列生成与建造执行

## 当前边界说明

- 主模块系统当前重点维护 `C7` 工头计划、`C8` 节点会话与 `C8` 子节点 `jigsaw` 求解。
- `C9` 执行层真值已独立到 `../c9_execution/`，本目录只保留主链衔接关系。

## 当前有效结论

- 图像只在总规阶段使用一次
- 后续逐节点阶段只使用结构化数据
- AI / 工头负责当前节点决策
- 程序负责校验、状态维护、错误回包和队列推进
- `start` 节点保留直接 `place` 能力，作为每个主模块会话的标准起点能力
- child 节点不再长期依赖人工 `x / z`，后续统一通过 connector / jigsaw 求解器计算 `origin`、`rotation` 与真实 bounds
- `C9` 负责消费已校验节点，并进入运行时建造链路，不接管“下一步选哪个结构”的随机决策

## 当前新增方向

- 引入 connector / jigsaw 求解层，作为 `C8` 的标准 child 节点落点能力
- 优先复用原版 jigsaw / pool / socket 语义，但不复用原版随机扩张决策
- 落地前必须完成以下预判：
  - 是否超出 polygon / area block
  - 真实 bounds 是否与已成立结构冲突
  - 地形是否合法
  - 是否需要切换到收尾结构
- `start` 继续允许直接 `place`，child 节点逐步切到求解器路径

## 当前不做

- 不再扩展 `arrangement_type` 作为主参数
- 不再继续加厚 `core / wing / terminal / junction` 之类中间语义层
- 不把道路与次级建筑重新并入主模块主链
- 不让 `C9` 在运行时随机从模板池决定下一个结构
- 不删除 `start` 节点的直接 `place` 路径

## 当前依赖

- `C7` 工头计划
- `C8` 节点会话、求解与 MCP 提交
- `C9` BuildQueue、执行器与运行时执行层
- 结构模板中的 jigsaw connector / preset pool 元数据

## 相关方案

- `./02_jigsaw_solver.md`

## 历史背景

如需查看旧工作流或收口讨论：

- `../../../../90_archive/StructureBinder/dev_docs/current_20260402_001024/`
- `../../../../90_archive/StructureBinder/dev_docs/current_20260330_181530/`
- `../../../../90_archive/StructureBinder/workFlow/`
