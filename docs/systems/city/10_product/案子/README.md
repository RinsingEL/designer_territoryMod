# City 案子状态索引

## 定位

本索引用来回答“哪些 City 案子是当前真值、哪些已经完成并入主线、哪些只是后续方向、哪些已经被新主线替代”。

当前 City 真值以 `docs/systems/city/README.md`、`20_contracts/`、`30_code_guide/代码导览.md`、`40_tests/测试入口.md` 为准。案子目录保留阶段方案和历史背景，但不能脱离上述入口单独作为实现依据。

## 状态说明

| 状态 | 含义 |
| --- | --- |
| 当前真值 | 当前 active path 的主方案，改实现和接口前必须先读。 |
| 下一步开发计划 | 已确定为下一轮开发方向，但尚未替换当前 active path。 |
| 已完成并入主线 | 核心能力已进入当前主线，后续只按缺口继续迭代。 |
| 后续待做 | 方向仍有效，但尚未作为当前实现主线完成。 |
| 待退役 | 当前仍可能存在显式实现路径，但已确定将在下一步开发中删除。 |
| 已替代 | 方案被 D3-D6 结构落地驱动主线替代，不再作为实现依据。 |
| 历史参考 | 可用于理解问题来源或技术试验，不再承诺维护接口。 |

## 当前阅读顺序

1. `D3-D6结构落地驱动城市重构-v0.1/README.md`
2. 下一步开发先读 `D4城市生成职责重构-v0.1/` 下四个拆分案：单次城市决策、程序化城市编译器、通用装饰系统退役、景观系统。
3. `D4设计构图候选闭环-v0.1/README.md`
4. `D4设计构图候选闭环-v0.2/README.md`
5. `D4阵列布局AgentLoop-v0.2-v0.3/README.md`
6. `D4阵列候选选择闭环-v0.4/README.md`
7. `结构Envelope精修-v0.1/README.md`
8. 需要其他后续方向时，再读 Road Weaver、地形兼容、城墙、语义重标记、结构风格化换皮等待做案。

## 案子状态表

| 案子 | 状态 | 当前结论 |
| --- | --- | --- |
| `D3-D6结构落地驱动城市重构-v0.1` | 当前真值 | 当前 City 主线：D3 patch 真值 -> D4 structure anchor -> D5 mask / registry -> D6 probe-and-lock -> worldgen-time placement -> D7 ledger / actual-footprint road。旧功能区优先链路不再兼容。 |
| `D4城市生成职责重构-v0.1` | 下一步开发计划 | 下一步按四个独立案推进：D4 删除逐步 AI 决策并在开头一次输出 `CityBlueprint`；程序化城市编译器自动完成结构候选、扩张与锚点冻结；通用装饰系统整体退役；景观系统独立承接农田、树林、花田等连续面域。当前 active path 尚未切换，D5/D6/D7 契约暂时保持不变。 |
| `D4设计构图候选闭环-v0.1` | 已完成并入主线 | 已形成推荐路径：人 / AI 提交设计 slot 和 patch / 距离意图，程序生成少量安全候选，再选择候选转成 `StructureAnchorPlan`。后续重点是设计评分、结构套件和更好的候选解释。 |
| `D4设计构图候选闭环-v0.2` | 已完成并入主线 | 已实现逐 slot session：`create -> plan_next -> select -> finalize`。`key_then_array` 的关键结构阶段复用该 session 自动选择并冻结 occupied；v0.1 批量候选保留为 debug / 兼容入口。 |
| `D4阵列布局AgentLoop-v0.2-v0.3` | 显式开发路径 | 同一条 D4 阵列布局版本线：v0.2 已接入三段 endpoint 与显式 workflow 模式 `array_layout_loop_v0_2`；v0.3 已接入 `array_layout_loop_v0_3` 和 `composite_array`，一个 item 可生成 parent zone / subZones / child arrays。AI 每轮仍只提交一个阵列 item，程序执行后更新 state / occupied field / preview。当前不切默认。 |
| `D4阵列候选选择闭环-v0.4` | 显式开发路径 | 已接入 `create -> query -> plan -> select -> finalize`：常规外扩以已 Plan collision occupied 的 focus、direction、target patch 限定外侧空间；`newFunctionalArea=true` 专门开启全局 patch 搜索，query 不预选 patch，plan 必须显式传 `selectedGlobalPatchRef`。候选生成不提交，整组选定才原子写 state；保留簇群、沿线两侧、朝外半环和 `composite_array` 父 / 子区。当前不切默认。 |
| `City装饰填充层Plan-v0.1` | 待退役 | 当前仍有显式 `plan_city_dressing` 路径，但下一步不再深化该通用中尺度装饰层。按 `D4城市生成职责重构-v0.1/03_通用装饰系统退役.md` 删除 active path，并把固定构图迁到结构、连续面域迁到景观、道路内容迁到道路附属、极小细节收回所属生成器内部最终 pass。 |
| `结构Envelope精修-v0.1` | 已完成并入主线 | 已完成固定 / 近固定结构 bbox group、D6 锁 actual group、D7 基于真实 footprint 生成道路的口径。后续问题是确定性 group 选择、更多结构 profiling 和更紧的 road avoidance。 |
| `结构语义重标记-v0.1` | 后续待做 | 方向有效：整理 TerraSense 结构语义白名单和高质量测试 profile。注意不恢复 City 自建枚举。 |
| `RoadWeaver结构连接-v0.1` | 已完成并入主线 | 已完成 optional RoadWeaver adapter：`city_execute_d5` 生成 connection plan 并注册 endpoint / connection；缺 mod 时 `roadProvider=roadweaver` hard fail、`auto` 跳过道路并标记 `ROADWEAVER_UNAVAILABLE`，只有显式 `worldedit_debug` 进入旧 debug fallback。后续是入口候选、道路风格和水岸 / 桥梁策略。 |
| `结构地形兼容适配-v0.1` | 已完成并入主线 | 已完成 terrain adaptation / Beardifier 诊断 trace：D7 trace 能报告 hook unavailable、terrain adaptation none、beardifier seen / not seen。后续才做真正台基、削坡、填土或第三方地形兼容接入。 |
| `城市边界与城墙-v0.1` | 已完成并入主线 | 已完成 D7 ledger 后临时城墙闭环：按真实 actualFootprint union 外扩生成矩形墙、塔楼、7 格门洞、预览图和 NBT 模板，执行走 vanilla setBlock。后续是边界算法、门楼、转角和地形融合。 |
| `城市边界与城墙-v0.2` | 已完成并入主线 | 当前默认城墙口径：D5 生成 D3 patch 贴边 wall reservation mask，RoadWeaver 真实道路生成后扫描 actual road mask 并裁出城门，最后放墙 / 塔 / foundation，避免城墙砍断道路；v0.1 矩形墙仅为 `wallVersion=v1_debug`。 |
| `城市边界与城墙-v0.3` | 显式开发路径 | 已接入 `wallVersion=v3`：从结构 actualFootprint / sourcePatch 出发，在 D3 patch 邻接图上扩张城市占地区域，填掉小凹陷 / 小洞 / 内部道路口袋，再生成单一城市外环；同时增加 step=1 地形 debug 扫描、mask 冲突坐标和 gap debug report。`wallTerrainPolicy=v3.1` 负责阶梯墙、嵌坡和天然峭壁边界，仍需真实验收后再考虑切默认。 |
| `城市边界与城墙-v5` | 草案 | 由人工继续掌控的小流程案：D5 决定城墙平面和 mask，worldgen 保护 corridor 并记录地表 surface cache，D7 后城墙不再改线，只做高度适配和是否落地判断。 |
| `City结构风格化换皮-v0.1` | 后续待做 | 方向有效：D7 ledger 完整后按国度 / 城市 palette 对结构真实 footprint 内的方块做主题化替换，保护功能方块和 blockstate，优先摆脱 WorldEdit 依赖。 |
| `城市构造流程-v0.1` | 已替代 | 旧“功能区优先”总流程，涉及 `FunctionZoneMap`、`BuildableAreaMap` 等旧主线，只作历史背景。 |
| `C5锚点与保留区-v0.1` | 已替代 | 旧功能区边界 / 保留区案，已被 D4 anchor + D5 reservation mask + D6 locked footprint 替代。 |
| `D6结构池规划-v0.1` | 已替代 | 旧 `StructureChoicePlan` / `StructurePoolMap` / 固定落点规划案，已被 structure anchor 与 envelope facts 主线替代。 |
| `D7条件包装结构生成-v0.1` | 历史参考 | 旧条件包装 / late materialize / bounded jigsaw 探索，正式路径已改为 worldgen-time planned structure。 |
| `D7剩余结构起点候选-v0.1` | 历史参考 | 旧 single-start / bounded dry-run / 面积预算探索，可用于理解为什么不再走多 start 追面积。 |

## 案子目录之外的旧计划

`10_product/开发计划-v0.1-*` 到 `开发计划-v0.5-*` 属于旧 City 阶段计划。它们记录了从功能区、D6 结构池、D7 bounded jigsaw 到 late paste 的探索过程，但当前 active path 不再以这些计划为准。

`10_product/系统概述.md`、`10_product/过程设计/C1-C4城市规划过程.md`、`10_product/过程设计/C5-C8结构落地交接过程.md` 仍保留早期总体设想，阅读时必须先看文件开头状态提示。

## 当前已验收能力

- D3 patch 作为地形事实输入，不重复做功能区真值层。
- Trek 顶层 configured structure 可做 envelope profiling。
- D4 可通过候选闭环选择结构落脚点，不要求 AI 直接手算坐标和防撞。
- D4 v0.2 逐 slot session 已实现并被 `key_then_array` 关键结构阶段复用；当前 v0.1 批量候选只作为 debug / 兼容路径。
- D4 阵列布局 Agent Loop v0.2/v0.3 已作为显式开发路径接入；当前默认 `key_then_array` 的 array_fill 仍以 v0.1 阵列候选为准，显式 endpoint / workflow 可每轮执行一个 patch / sector 驱动的阵列 item，v0.3 `composite_array` 可在同轮展开 parent/subZones/child arrays。
- City 装饰填充层 v0.1 已作为显式路径接入；`plan_city_dressing` 输出 effective mask、surface operation、decoration placement、局部 occupied field、模板库和 per-item 局部预览，`execute_d5` 激活装饰 worldgen plan。
- D5 可激活 reservation mask 和 planned structure registry。
- 结构可在 worldgen structure 阶段落地，植被在 feature 阶段被 mask 抑制。
- D6 可 probe-and-lock actual footprint / bbox group / signature，并用 locked footprint 做最终防撞。
- D7 可基于 worldgen ledger 的真实 `actualFootprint` 生成道路和 inferred function area。

## 当前未完成方向

- Road Weaver 深度接入：入口候选、道路风格、水岸 / 桥梁策略和更好预览。
- D4 阵列布局 Agent Loop 后续：真实游玩验证 v0.4 外扩候选的构图、入口和 preview 可读性，以及 v0.3 `composite_array` 的紧凑度；默认 `key_then_array` 是否升级仍需单独决策。
- D4 城市生成职责重构：先完成单次 `CityBlueprint` 与程序化结构编译器，再退役 City 通用装饰填充层，最后建立独立景观系统；当前 D5/D6/D7 保持既有 worldgen 准入边界。
- Beardifier / terrain adaptation 深度接入：真正观察 hook、台基 / 削坡 / 填土和结构 profile foundation policy。
- 城墙 / 边界深化：v0.2 已实现墙带早期 mask、D3 patch 贴边非矩形边界、RoadWeaver 真实道路裁门、道路保护和基础地形贴合；v0.3 已进入显式开发路径；v5 草案把后续方向收紧为 D5 定平面、worldgen 保护、D7 后只做垂直适配。
- TerraSense 结构语义重标记，先用少量高质量结构套件验证“国度 / 城市设计感”。
- 结构风格化换皮 / 方块替换，基于真实落地结构做国度主题化。
