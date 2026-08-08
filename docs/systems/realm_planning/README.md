# 国度规划系统

国度规划系统承接 W 世界粗扫和 GIS 粗尺度事实，生成国度配置、T2 核心选择、T3 势力范围、T4 城市候选与 `CitySeedRegistry`。它不负责城市内部布局、道路或结构落地。

## 当前主链

```text
W refresh / resume
-> T1 候选图包
-> T2 国度核心与 CapitalCityIntent
-> T3 action_budget 势力扩张
-> T4 owned territory 城市候选与 AI 首都选择
-> CitySeedRegistry
-> City D3 局部复核
```

strict T3 默认使用 `action_budget`；旧 quota frontier 只作为测试对照。T4 粗地形证据是候选辅助，City D3 才是局部选址最终真值。

## 阅读入口

1. `10_product/功能设计/W-T阶段主流程设计.md`
2. `10_product/T阶段国度与城市种子方案.md`
3. `10_product/案子/Patch探索式选址-v0.1/README.md`
4. `10_product/案子/首都AI候选选址-v0.1/README.md`
5. `10_product/案子/T4生成器原生粗地形预览-v0.1/README.md`
6. `20_contracts/数据契约/W-T阶段数据契约.md`
7. `20_contracts/接口契约/W-T阶段MCP接口.md`
8. `30_code_guide/代码导览.md`
9. `40_tests/测试入口.md`
10. `40_tests/真实游玩验收计划.md`

## 当前实现能力

- W 支持 sealed artifact、checkpoint 恢复、provider 隔离、micro-sampling 和轻量批量预览。
- T1/T2 通过 Patch Explorer 浏览与选择国度核心。
- T3 按行动力、地形成本、竞争压力和状态分类扩张国度。
- T4 在 owned territory 生成城市候选、生成器粗览证据和最终城市名册。
- RTF provider 可用时使用生成器原生二维高度；不可用时整阶段回退并记录 provenance。
- HTTP、MCP、JVM 测试和 Forge GameTest 均已有入口。

已完成的 v1.1-v1.6 开发计划和旧实机快照不再作为当前文档保存；其现行结论已收敛到产品、契约、代码导览和测试入口。
