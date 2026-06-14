# Designer Territory Mod Docs

本仓库从现在开始只维护这一套新文档结构。

当前双仓库路径：

- 实现仓库：`E:\Mod_Dev\StructureBinder`
- 文档仓库 / 策划案仓库：`E:\Mod_Dev\designer_territoryMod`

旧仓库 `StructureBinder` 的 `workFlow`、旧 whitepaper、旧总览型方案文档，不再作为当前真值来源。历史资料如需保留，只放入 `docs/90_archive/`，并作为只读归档，不再继续维护。

当前主阅读入口：

- `00_nav/`
  - 导航、仓库映射、功能地图、地貌驱动主线 Workflow、AI 协作开发规范、语义检索规则、实现仓库结构规范、代码导览编写规范、从 0 到 1 开发流程、Bug 修复流程、dev_docs 组织规则、Git 提交规则
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
  - v1 开发计划：`systems/gis/10_product/开发计划.md`
  - v1.1 开发计划：`systems/gis/10_product/开发计划-v1.1-Step参数化最小闭环.md`
  - 契约：`systems/gis/20_contracts/`
  - 代码导览：`systems/gis/30_code_guide/代码导览.md`
  - 测试与验收：`systems/gis/40_tests/`
- 国度规划系统
  - 总入口：`systems/realm_planning/README.md`
  - T 阶段方案：`systems/realm_planning/10_product/T阶段国度与城市种子方案.md`
  - W / T 主流程设计：`systems/realm_planning/10_product/功能设计/W-T阶段主流程设计.md`
  - v1.1 开发计划：`systems/realm_planning/10_product/开发计划-v1.1-W粗Patch与T阶段重建.md`
  - v1.2 质量重构计划：`systems/realm_planning/10_product/开发计划-v1.2-W粗扫T3T4质量重构.md`
  - v1.3 Dregora 标准 W 粗扫计划：`systems/realm_planning/10_product/开发计划-v1.3-Dregora标准W粗扫与GIS指标聚合.md`
  - v1.4 T3 行动力国度扩张计划：`systems/realm_planning/10_product/开发计划-v1.4-T3行动力国度扩张模型.md`
  - v1.5 高步长局部指标计划：`systems/realm_planning/10_product/开发计划-v1.5-高步长局部指标封装与地貌判定修正.md`
  - v1.6 多尺度 GIS 地貌特征栈计划：`systems/realm_planning/10_product/开发计划-v1.6-多尺度GIS地貌特征栈与面域验收.md`
  - 数据契约：`systems/realm_planning/20_contracts/数据契约/W-T阶段数据契约.md`
  - MCP 接口契约：`systems/realm_planning/20_contracts/接口契约/W-T阶段MCP接口.md`
  - 代码导览：`systems/realm_planning/30_code_guide/代码导览.md`
  - 测试入口：`systems/realm_planning/40_tests/测试入口.md`
  - 真实游玩验收计划：`systems/realm_planning/40_tests/真实游玩验收计划.md`
- City 系统
  - 总入口：`systems/city/README.md`
  - 方案：`systems/city/10_product/系统概述.md`
  - C1-C4 城市规划过程：`systems/city/10_product/过程设计/C1-C4城市规划过程.md`
  - C5-C8 结构落地交接过程：`systems/city/10_product/过程设计/C5-C8结构落地交接过程.md`
  - 数据契约：`systems/city/20_contracts/数据契约/`
  - 代码导览：`systems/city/30_code_guide/代码导览.md`
  - 测试入口：`systems/city/40_tests/测试入口.md`

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
7. 涉及 W / T / C 主链职责、AI 介入边界、城市功能区生成和 jigsaw 物化链路时，先读 `00_nav/地貌驱动主线Workflow.md`
8. 涉及国度配置、国度扩张、城市名册、城市生长种子或 T 到 C 交接时，先读 `systems/realm_planning/README.md`
9. 涉及城市局部规划、功能区、道路、边界或结构落地交接时，先读 `systems/city/README.md`
10. 新系统、新工具、大重构或从 0 到 1 开发，先读 `00_nav/从0到1设计开发流程.md`
11. bug、异常、测试失败或多轮不收敛，先读 `00_nav/Bug修复流程.md`
12. 编写或重构 `30_code_guide/` 时，先读 `00_nav/代码导览编写规范.md`
13. 调整实现仓库 package、系统边界或 workflow 组织时，先读 `00_nav/实现仓库结构规范.md`
14. 不清楚文档归属时，按 `00_nav/AI语义检索规则.md` 从领域和文档类型两步定位
15. 准备提交时，先读 `00_nav/Git提交规则.md`，提交标题和正文都必须中文且沿用近期日志风格
