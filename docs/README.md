# Designer Territory Mod 文档

本仓库维护 Geomantia 当前有效的产品方案、数据契约、代码导览、测试入口、验收口径和全局工作流。

实现代码位于 `E:\Mod_Dev\StructureBinder`；当前文档仓库不保留旧 `workFlow`、旧 whitepaper 或历史方案，追溯统一使用 Git 历史。

## 开始阅读

非简单查询只需先读：

1. `00_nav/README.md`
2. `00_nav/task_router.md`

随后由任务路由进入目标 system / tool README 和一份对应工作流，不默认读取所有全局文档。

## 目录职责

| 目录 | 职责 |
| --- | --- |
| `00_nav/` | 薄导航：任务、领域和仓库路由。 |
| `01_workflows/` | 从 0 到 1、开发、验收、诊断、修复和发布流程。 |
| `02_standards/` | 角色权限、仓库结构、文档与提交规范。 |
| `03_shared_contracts/` | 跨系统共享契约。 |
| `systems/` | 按系统维护方案、契约、导览和测试。 |
| `tools/` | 按工具维护方案、契约、导览和测试。 |

## 当前领域入口

| 领域 | 入口 |
| --- | --- |
| GIS 地貌基础设施 | `systems/gis/README.md` |
| 国度规划 | `systems/realm_planning/README.md` |
| City | `systems/city/README.md` |
| 开发与调试工具 | `tools/README.md` |

领域的活动案、计划、契约和测试明细只在对应 README 维护，不再复制到全局导航。

## 维护原则

- 当前结论按 `10_product/`、`20_contracts/`、`30_code_guide/`、`40_tests/` 分层。
- 导航只链接，不承载流程正文、系统状态和历史列表。
- 每条规则只有一个真值位置，其他文档只引用。
- 未开发领域不预建完整目录或实现空 package。
- 过程记录和故障复盘写入实现仓库 `dev_docs/`，不替代当前文档真值。

当前共享契约包括 `03_shared_contracts/MCP调用日志契约.md` 与 `03_shared_contracts/测试运行包契约.md`。前者记录调用边界，后者规定多阶段测试的保存和恢复单位；两者不能互相替代。
