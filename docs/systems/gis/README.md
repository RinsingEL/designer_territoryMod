# GIS 文档入口

GIS 是 Geomantia 的地貌基础设施层。它负责把 Minecraft 世界转换成可查询、可缓存、可验证的地理空间事实，再交给城市、道路、国度边界、结构分布等系统消费。

## 阅读顺序

1. `10_product/系统概述.md`
2. `10_product/开发计划.md`
3. `10_product/功能设计/GIS主流程图.md`
4. `10_product/功能设计/半径刷新与Atlas构建.md`
5. `10_product/功能设计/GIS指标层.md`
6. `10_product/功能设计/地貌分类与地貌区.md`
7. `20_contracts/数据契约/`、`20_contracts/接口契约/`
8. `30_code_guide/代码导览.md`
9. `40_tests/自动测试方案.md`
10. `40_tests/验收计划.md`

## 目录说明

| 目录 | 内容 |
| --- | --- |
| `10_product/` | GIS 的系统定位、开发计划和功能设计。 |
| `20_contracts/` | AtlasCell、AtlasRegion、LandformPatch、RefreshJob、PreviewManifest、GIS 调试 MCP 接口和配置表。 |
| `30_code_guide/` | 后续实现仓库的目标代码分层与文档映射。 |
| `40_tests/` | 测试入口、验收计划、影响面和结果报告模板。 |
