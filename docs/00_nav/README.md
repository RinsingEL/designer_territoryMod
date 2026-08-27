# 项目入口

本页是双仓库唯一的项目规则入口。最新一次经用户确认的原话、图片和示意图高于索引、工作流及既有文档；发生冲突时先指出冲突，再按最新确认结果工作。

## Session 启动

只运行：

`powershell -NoProfile -ExecutionPolicy Bypass -File E:\Mod_Dev\StructureBinder\scripts\check_requirement_cleanup_due.ps1`

- 输出 `OK`：结束启动检查，不读取清理工作流、案子索引或需求案。
- 输出 `DUE`：先询问用户是否启动清理；用户同意后才通过 `task_router.md` 进入清理工作流，并暂停原任务直至清理完成。
- **只有本次 Session 现场运行上述脚本得到的 `DUE` 才能触发询问。**上下文摘要、`dev_docs/**/active/` 任务记录、未提交工作区、上轮故障或文档中的 `DUE` 字样均不是触发信号；`active/` 只表示任务尚未提交，不表示本轮应继续执行。

## 收到项目任务后

1. 先读取轻量索引 `task_router.md`。
2. 只读取当前任务命中的工作流正文；不得预加载未触发的工作流。
3. 无法判断领域时再读取 `domain_map.md`，然后进入目标 system / tool README。
4. 只继续读取当前任务直接需要的需求案、契约、代码入口或测试入口，不默认加载全部文档层。

## 导航文件

| 文件 | 用途 |
| --- | --- |
| `task_router.md` | 工作流标题、准确路径和触发条件的唯一索引。 |
| `domain_map.md` | 定位目标系统、工具和跨系统产品主线。 |
| `repo_map.md` | 判断内容属于实现仓库还是文档仓库。 |
