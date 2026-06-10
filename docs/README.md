# Designer Territory Mod Docs

本仓库从现在开始只维护这一套新文档结构。

当前双仓库路径：

- 实现仓库：`E:\Mod_Dev\StructureBinder`
- 文档仓库 / 策划案仓库：`E:\Mod_Dev\designer_territoryMod`

旧仓库 `StructureBinder` 的 `workFlow`、旧 whitepaper、旧总览型方案文档，不再作为当前真值来源。历史资料如需保留，只放入 `docs/90_archive/`，并作为只读归档，不再继续维护。

当前主阅读入口：

- `00_nav/`
  - 导航、仓库映射、功能地图、AI 协作开发规范、语义检索规则、实现仓库结构规范、代码导览编写规范、从 0 到 1 开发流程、Bug 修复流程、dev_docs 组织规则、Git 提交规则
- `systems/`
  - 按系统内聚维护当前方案、契约、代码导览、测试与验收
- `tools/`
  - 按工具内聚维护开发工具、辅助 Mod、扫描和调试工具文档
- `90_archive/`
  - 历史资料，只读归档

当前核心系统入口：

- GIS 地貌基础设施层
  - 总入口：`systems/gis/README.md`
  - 方案：`systems/gis/10_product/系统概述.md`
  - 开发计划：`systems/gis/10_product/开发计划.md`
  - 契约：`systems/gis/20_contracts/`
  - 代码导览：`systems/gis/30_code_guide/代码导览.md`
  - 测试与验收：`systems/gis/40_tests/`

当前工具入口：

- 工具总览：`tools/README.md`
- Code Process Viewer：`tools/code_process_viewer/README.md`
- TerraSense：`tools/TerraSense/README.md`

维护规则：

1. 新建或重建系统优先写进 `systems/<系统>/`
2. 新建或重建工具优先写进 `tools/<工具>/`
3. 系统和工具内部继续分 `10_product`、`20_contracts`、`30_code_guide`、`40_tests`
4. 根级旧四层目录不再作为当前真值入口，四层结构只作为系统或工具内部子目录
5. `90_archive/` 不再继续更新，只保留历史追溯价值
6. 进入实现开发前，先遵守 `00_nav/AI协作开发规范.md` 的设计检查单和人工介入规则
7. 新系统、新工具、大重构或从 0 到 1 开发，先读 `00_nav/从0到1设计开发流程.md`
8. bug、异常、测试失败或多轮不收敛，先读 `00_nav/Bug修复流程.md`
9. 编写或重构 `30_code_guide/` 时，先读 `00_nav/代码导览编写规范.md`
10. 调整实现仓库 package、系统边界或 workflow 组织时，先读 `00_nav/实现仓库结构规范.md`
11. 不清楚文档归属时，按 `00_nav/AI语义检索规则.md` 从领域和文档类型两步定位
12. 准备提交时，先读 `00_nav/Git提交规则.md`，提交标题和正文都必须中文且沿用近期日志风格
