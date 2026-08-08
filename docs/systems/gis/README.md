# GIS 地貌基础设施

GIS 把 Minecraft 世界转换成可查询、可缓存、可验证的地理空间事实，供 W/T 与 City D3 消费。当前实现包含采样、Atlas、指标、地貌分类、Patch、预览和调试接口。

## 阅读入口

1. `10_product/系统概述.md`
2. `10_product/功能设计/GIS主流程图.md`
3. `10_product/功能设计/半径刷新与Atlas构建.md`
4. `10_product/功能设计/GIS指标层.md`
5. `10_product/功能设计/地貌分类与地貌区.md`
6. `10_product/功能设计/预览图与调试图.md`
7. `20_contracts/`
8. `30_code_guide/代码导览.md`
9. `40_tests/测试入口.md`

## 当前边界

- GIS 提供地貌事实，不决定国度、城市功能或结构落点。
- 普通 refresh 保留完整 preview；W 批量粗扫使用自己的轻量产物策略。
- W/T 的生成器原生粗览和多尺度聚合由国度规划系统编排，GIS 只提供可复用采样与指标能力。
- City D3 使用当前 GIS/terrain 实现形成局部审查包；未来设想不写入当前 GIS 真值。

代码入口、类职责和测试锚点分别以 `30_code_guide/代码导览.md` 和 `40_tests/测试入口.md` 为准。已完成开发计划和一次性结果报告不再保留，历史从 Git 查询。
