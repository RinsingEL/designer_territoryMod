# Designer Territory Mod Docs

本仓库从现在开始只维护这一套新文档结构。

旧仓库 `StructureBinder` 的 `workFlow`、`dev_docs` 和相关历史文档，已经统一归入：

- `docs/90_archive/StructureBinder/`

并只作为只读归档保留，不再继续维护。

当前主阅读入口分为四层：

- `00_nav/`
  - 导航、仓库映射、功能地图
- `10_product/`
  - 当前仍然有效的功能方案
- `20_contracts/`
  - 当前数据契约与输入输出边界
- `30_code_guide/`
  - 面向 AI 和人类的代码导览
- `40_tests/`
  - 当前有效的测试、验收、联调入口

维护规则：

1. 新方案只写进 `10_product/`
2. 当前有效的数据边界只写进 `20_contracts/`
3. 类职责和代码入口只写进 `30_code_guide/`
4. 测试和验收记录只写进 `40_tests/`
5. `90_archive/` 不再继续更新，只保留历史追溯价值
