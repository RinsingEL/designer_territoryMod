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
6. `10_product/案子/W一次完整扫描-v0.1/README.md`（**实现当前案**：W 执行方式）
7. `10_product/案子/AI场景策划与程序执行分工-v0.1/README.md`（**实现当前案**：世界自动规划总调度链，含 AI/程序分工、作者标注真值与运行方式）
8. `10_product/案子/冒险者地图-v0.1/README.md`（**实现当前案**：规划地图与进度展示链）
9. 区域开放职责链见下方“区域开放当前案”。
10. `20_contracts/数据契约/W-T阶段数据契约.md`
11. `20_contracts/接口契约/W-T阶段MCP接口.md`
12. `30_code_guide/代码导览.md`
13. `40_tests/测试入口.md`
14. `40_tests/真实游玩验收计划.md`

## 区域开放当前案

- [大陆大洋分区开放与城市郊区隔离](10_product/案子/大陆大洋分区开放与城市郊区隔离-v0.1/README.md)：**实现当前案**：按完整地理区域解锁，城市原预览范围内设计，1.5 倍保护圈不重叠。

## 当前实现能力

- 公共规划服务执行 W、统一 T3、队列刷新、D3 扫描和城市首批候选准备；T2/T4 会话与初始候选在模型启动前备齐。AI 仍选择国度/城市起点、决定城市角色、明确复核 D3 并设计蓝图；候选冻结后的引用提交由宿主代办。必要图片作为实际图像返回，其他当前任务资料由 Agent 按需浏览、搜索和请求图片；不把全部图片反复注入上下文。外部 MCP 以存档大厅进入，内置 Harness 无大厅；两者共用任务准备和占用保护，进度从存档恢复。

- W 对配置的规划范围执行一次完整扫描，支持 sealed artifact、checkpoint 恢复、provider 隔离、micro-sampling 和轻量批量预览；城市排序不属于 W。
- T1/T2 通过 Patch Explorer 浏览与选择国度核心。
- T3 按行动力、地形成本、竞争压力和状态分类扩张国度。
- T4 在 owned territory 生成城市候选、生成器粗览证据和最终城市名册。
- RTF provider 可用时使用生成器原生二维高度；不可用时整阶段回退并记录 provenance。
- HTTP、MCP、JVM 测试和 Forge GameTest 均已有入口。

已完成的 v1.1-v1.6 开发计划和旧实机快照不再作为当前文档保存；其现行结论已收敛到产品、契约、代码导览和测试入口。

## 附属扩展接口

[附属区域预留 Java 接口](20_contracts/接口契约/附属区域预留Java接口.md)：在首次 T1 前通过 Forge 事件登记区域，统一接入国度/城市/城际道路避让和地理区域生成就绪；Boss 与战役进度由附属独立管理。

## 数量配置

[国度与城市数量配置](20_contracts/数据契约/国度与城市数量配置.md)：国度总数、每国城市最少/最多数（含首都），以及新旧会话生效规则。
