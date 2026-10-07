# W / T 阶段 MCP 接口契约

## 定位

本文定义国度规划系统 v1.1 为真实游玩验收提供的 MCP 调试接口。它不是 legacy T1 / T2 工具的兼容层；旧 `t1_select_cluster`、`t2_select_direction` 等接口不进入当前主线。

接口目标：

- agent 可以通过 MCP 从真实 MC 世界触发 W / T 主链。
- 每个阶段都能返回结构化状态、产物路径和下一步建议。
- T2 推荐由 AI 先探索感兴趣的 patch 类型，再提交稳定 `patchSelectionRef`；直接提交候选图 grid 坐标保留为兼容入口。
- MCP 能支撑端到端验收，而不是只跑单元测试。

## 工具总览

### T1 核心建筑视觉上下文（2026-09-25）

共享任务准备层 `PreparedPlanningTurn` 在 T1 世界预览后附加当前托管素材包的核心建筑图册，内置 Harness 与外部 MCP 共用。用户确认只需核心建筑外观，重点认识风格与功能；住宅变体及配套详细选材留在 City。

- 素材包可携带 `realm_core_atlas.json`（schema=`realm_core_atlas.v1`）与 `core_atlas/page-*.png`。Studio 导出脚本按当前目录中作者 `planning_role.key/anchor` 选择核心，每页最多四项；不是固定风格或固定14项名单。
- `sources` 绑定 `template_catalog.json`、`asset_names.json`、`StructureProfile.jsonl` 的 SHA-256；`cores` 包含 templateRef、displayName、functionTerms、styleTerms、rawSize、siteConditions、page、slot；`pages` 包含顺序页号、相对文件路径、SHA-256、按阅读顺序的 templateRefs。`supportSummary` 给出素材总量及功能/风格计数。
- Studio 截图记录必须与测试包导出来源 NBT 哈希一致；不将截图重新标为审美验收。运行时校验目录版本、核心覆盖、页图哈希、图片格式和路径边界后，复制至当前 run 的哈希目录，作为实际图片传输。图册没有统一缩尺，体量看 rawSize。
- 有图册时 T1 的 `authoringBrief` 使用核心图文资料与配套能力摘要，替代全量单体标签。旧包没有图册仍保留作者文字资料并显式返回 `visualEvidenceAvailable=false`；已声明但损坏/过期的图册拒绝加载。
- 可编辑提示 `config/geomantia/prompts/realm/t1.md` 在 T1 注入为 `creativeGuidance`。要求结合地形、外观、真实功能主动构思，不按风格数量分国，不强制使用所有核心，不从外观推断传送等机制。
- 构想写入既有 RealmProfile.theme，无新增提交字段或阶段。City 与附属任务读取自己国度的已保存 profile 为 `realmDesignIntent`，继承主题并落实本城差异。已完成 T1 的存档不自动重写既有国度。

| 工具 | 阶段 | 作用 |
| --- | --- | --- |
| `realm_status` | 通用 | 读取国度规划系统状态、最近 run 和产物目录。 |
| `realm_w_refresh` | W | 在真实世界或固定测试世界中生成 `WorldSurveyContext`、`WorldPatchMap` 和候选底图。 |
| `realm_t1_prepare` | T1 | 基于 W 产物和国度配置生成 `RealmProfile` 与 `RealmCandidateMapPackage`。 |
| `realm_t2_select_coordinate` | T2 | 提交 AI / 人类选择的国度核心 grid 坐标，校验并生成 `RealmSeed`、无坐标 `CapitalCityIntent`。 |
| `realm_t3_expand` | T3 | 对指定大陆 / 分组运行国度扩张，输出 `RealmTerritoryMap`。 |
| `realm_t4_build_registry` | T4 兼容验收 | 以 `rule_fixture` 模式生成 `CitySeedRegistry`，不是正式 AI 选址主链。 |
| `patch_explorer_open` | T2 / T4 / City D4 | 打开指定尺度的探索会话，返回类型目录、原始地形总览和所有 Patch 总览。 |
| `patch_explorer_show_candidates` | T2 / T4 / City D4 | 按 AI 选择的兴趣类型分页返回每类候选、同框 Top Patch 总览和候选间稀疏几何关系。 |
| `patch_explorer_select_candidate` | T2 / T4 / City D4 | 选中已展示候选，返回确认染色图与稳定 `patchSelectionRef`。 |
| `realm_t4_patch_planning_create` | T4 | 为单个国度创建空城市规划会话，只载入无坐标首都意图。 |
| `realm_t4_patch_planning_select_capital` | T4 | 消费 `realm_t4` 选择凭证，建立该国唯一首都。支持独立指定 theoreticalScale、serviceHierarchy、定位与风格。 |
| `realm_t4_patch_planning_add_city` | T4 | 消费 `realm_t4` 选择凭证并添加一座城市种子。支持全量保存名称、层级、定位、功能与分项风格。 |
| `realm_t4_patch_planning_remove_city` | T4 | 移除已选入的城市种子，释放候选凭证回可用池，支持全国方案复核与调整。 |
| `realm_t4_patch_planning_preview` | T4 | 返回当前全国城市草案分布图、完整设计/保护范围、城市图例与 `proposalHash`。 |
| `realm_t4_patch_planning_review` | T4 | 看图后按当前 `proposalHash` 提交全国分工、规模和位置的复核意见；成立后才可封存。 |
| `realm_t4_patch_planning_finalize` | T4 | 完成单国规划并按国度合并写回全局城市名册。 |
| `realm_run_acceptance` | 验收 | 用固定配置跑完整 W -> T4 调试链，并输出验收报告。 |
| `realm_tag_audit` | W 调试 | 对已有 sealed W run 单独执行 Tag Audit 抽样局部精扫，不重跑 W/T 主链。 |
| `realm_debug_command` | 开发调试 | 对已启动的 MC 集成服务端执行单条 Minecraft 命令，用于 TP、时间、天气、游戏模式等真实验收辅助操作。 |

## 通用返回字段

工具返回 JSON 文本；包含预览时，同时返回真正的 MCP `image` 内容，不把本地 PNG 路径当作已看过图片。

MCP 与内置 Provider 均使用 `X-Geomantia-Agent-View: true` 请求共享的 `planning_decision_view.v0.1`。它保留身份、目录语义、指标与产物引用，把密集 cell 集合替换为数量摘要；完整几何仍保存在正式 artifact 中，局部证据通过 Patch Explorer 获取。普通 HTTP 不带此头时仍返回完整原始响应。预览仅允许读取当前世界 debug root 内的 PNG（最多 4 张、单张 8 MiB），不可读取时返回 `previewWarnings`，不伪装成视觉证据。

内置 Provider 的 6 MiB 文本预算不计图片 base64；传输总量另按上述图片上限约束。当前内置运行时为 DeepSeek Harness，图像随原生消息与工具结果传递，不沿用旧 Gateway 的首轮 HTTP 大小限制。宿主续接时保留近期文字与资料引用，历史图片退出活跃上下文，需要时重新请求；当前必要预览仍实际返回。图片安全上限不等于模型上下文预算，不能用静默丢图代替明确反馈。

`realm_w_refresh` 开始前校验宿主作者资料，成功时返回 `authoringBrief`。作者未确认结构功能/风格或来源不唯一时阻塞，不让模型寻找或补造配置。

### 运行时 checkpoint 恢复

- `realm_status` 只列当前 `MinecraftServer` 进程已经激活的 run，不在启动时扫描整个 `realm_debug` 目录。
- `realm_t1_prepare`、`realm_t2_select_coordinate`、`realm_t3_expand`、`realm_t4_build_registry` 和 `realm_tag_audit` 首次按 `runId` 访问内存中不存在的 run 时，必须从磁盘懒恢复。
- 恢复真值先是 sealed `world_survey_manifest.json`、tile snapshots 和 `world_feature_grid.json`；若完整 T1/T2/T3/T4 checkpoint 存在，再按阶段顺序恢复。T2 必须能继承 T1，T3 必须能继承 T1/T2，T4 必须能继承 T1/T2/T3。
- 恢复是只读操作：不得调用 W refresh、不得加载或扫描 Minecraft chunk、不得重写 W 或既有 T checkpoint。调用目标阶段自身正常产生的新产物不受此限制。
- 某阶段只有部分必需文件时，不把它当成完成的 checkpoint；下一阶段按原前置条件拒绝。完整 checkpoint JSON 损坏、来源不一致或引用 sealed W 外坐标时返回 `REALM_CHECKPOINT_INVALID`，不得静默重算或覆盖。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `ok` | boolean | 是否成功。 |
| `stage` | string | 当前阶段。 |
| `runId` | string | 本次 W / T run ID。 |
| `status` | string | `pending`、`running`、`completed`、`failed` 等。 |
| `artifacts` | object | 产物路径。 |
| `nextActions[]` | string[] | 建议下一步。 |
| `warnings[]` | string[] | 可继续但需要注意的问题。 |
| `errors[]` | string[] | 失败原因。 |

失败时必须返回 `ok=false` 和 `errors[]`，不得只返回自然语言错误。

## realm_status

读取当前国度规划系统状态。

请求：

```json
{}
```

返回重点：

| 字段 | 说明 |
| --- | --- |
| `serviceReady` | HTTP / Forge 侧国度规划服务是否在线。 |
| `latestRunId` | 最近一次 W / T run。 |
| `debugRoot` | 当前 Minecraft 存档 world root 下的 `realm_debug` 产物根目录；不得指向同一游戏实例内跨存档共享的目录。 |
| `availableStages[]` | 已实现阶段。 |
| `gisReady` | GIS 调试服务是否可用。 |

## realm_w_refresh

生成 W 粗扫产物。

请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `planningRadiusBlocks` | number | 否 | 配置的 W 最大扫描半径，单位 block。正式 W 优先使用该字段。 |
| `radiusChunks` | number | 否 | 兼容字段；未传 `planningRadiusBlocks` 时换算为 block 半径。 |
| `cellStepBlocks` | number | 否 | 粗 cell 步长，默认 `128`，可选 64 / 128 / 256。 |
| `sampleMode` | string | 否 | 默认 `prior`。 |
| `preferGeneratorNativeTerrain` | boolean | 否 | 默认 `true`；检测到兼容生成器时优先使用原生二维粗地形快路径。`false` 强制使用 Minecraft prior sampler。仅控制本次 W 请求。 |
| `resumePolicy` | string | 否 | `use_cache`、`rescan`、`use_cache_strict`，默认 `use_cache`。 |
| `microSampleStrideBlocks` | number | 否 | v1.3 cell 内 micro-sampling 步长，默认 `32`。 |
| `localSlopeRadiusBlocks` | number | 否 | v1.3 micro sample 局部坡度半径，默认 `8`。 |
| `runTagAudit` | boolean | 否 | v1.5 开发期调试开关；为 `true` 时，W 完成后抽样局部精扫并输出 tag audit 产物。 |
| `tagAuditSampleCount` | number | 否 | v1.5 Tag Audit 抽样点数量，默认 `120`。 |
| `tagAuditSampleSeed` | string | 否 | v1.5 Tag Audit 抽样 seed；同一 run 可换 seed 抽另一批点，便于分批人工传送复核。 |
| `tagAuditRadiusBlocks` | number | 否 | v1.5 Tag Audit 局部精扫半径，默认 `32`。 |
| `tagAuditStrideBlocks` | number | 否 | v1.5 Tag Audit 局部精扫步长，默认 `4`。 |
| `tagAuditSlopeRadiusBlocks` | number | 否 | v1.5 Tag Audit 局部坡度半径，默认 `4`。 |
| `centerBlockX` / `centerBlockZ` | number | 否 | 本次完整粗扫的配置中心。城市距 0,0 的调度顺序不由该字段决定。 |
| `dimensionId` | string | 否 | 维度 ID，默认玩家维度或 `minecraft:overworld`。 |
| `playerName` | string | 否 | W 扫描进度聊天消息的接收玩家；省略时使用当前在线玩家。 |
| `worldTheme` | object/string | 否 | 世界主题摘要。 |
| `runId` | string | 否 | 指定 run ID；省略则自动生成。 |

W 对请求配置的规划范围执行一次完整扫描。tile 结果写入既有缓存，`resumePolicy=use_cache` 可恢复中断前已完成部分，但缓存恢复不把 W 变成随城市逐圈扩张的长期队列。扫描主循环在 API worker 执行，不阻塞服务器主线程。

扫描运行期间，服务端每秒更新 `world_survey_progress.json`；有目标玩家时，聊天框每 5 秒显示一次当前阶段、进度百分比和 ETA，阶段切换、完成或失败立即显示。聊天通知转交服务器线程执行。无人在线时不发送聊天消息，不影响扫描和进度文件写出。

返回产物：

| 产物 | 说明 |
| --- | --- |
| `WorldSurveyContext` | W 粗扫上下文。 |
| `WorldPatchMap` | 粗地貌地图。 |
| `worldPatchPreview` | 粗 patch 调试图。 |
| `gridOverlayPreview` | 带 grid 坐标的候选底图。 |
| `wManifest` | 坐标转换、step、patch、continent 摘要。 |
| `worldSurveyManifest` | 分片扫描、缓存命中、失败 tile、耗时和数据量审计。 |
| `worldFeatureGrid` | v1.3 micro-sampling 聚合特征，分片 W survey 下输出 `world_feature_grid.json`。 |
| `tagAuditSamples` / `tagAuditReport` | v1.5 开发期抽样局部精扫产物，仅 `runTagAudit=true` 时输出。 |
| `scoreManifest` | v1.2 若执行评分，返回评分与阻断摘要。 |

最低验收：

- `cellStepBlocks`、`gridOriginBlock`、`gridSize` 可追溯。
- `WorldSurveyContext.sealed = true` 后才能进入 T1。
- `world_survey_manifest.json` 中 `failedTileCount = 0`。
- 至少存在一个可分配 land continent。
- preview 能显示 grid 坐标或可由 manifest 映射 grid 坐标。

## realm_t1_prepare

生成国度设定和候选图包。

请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `runId` | string | 是 | 来源 W run。 |
| `realmProfiles[]` | array | 是 | 1～12 份完整显式设计；正式入口不生成默认国家。 |
| `realmCount` | integer | 否 | 若提供，必须与 `realmProfiles` 实际数量相等。 |

每份 profile 必须显式填写 `realmId/name/targetContinentId/theme`、`cultureTags/industryTags/materialTags/landformPreferences/avoidLandforms`、`scalePlan` 和 `expansionStyle`。标签数组允许显式为空；目标大陆不可省略后自动选择最大大陆。

`scalePlan` 必须包含 `priority=minor|normal|major|empire`、`normalizationGroup` 和 `targetAreaRatio/minAreaRatio/maxAreaRatio`，比例属于 `[0,1]` 且满足 `min <= target <= max`。`expansionStyle` 必须包含全部七项数值性格以及 `seaCrossingPolicy=none|limited|allowed`；`mountainAffinity/forestAffinity` 属于 `[-1,1]`，其余属于 `[0,1]`。嵌套字段 schema 由 Java/Node 工具定义同步发布。

缺字段、未知字段（包括 `civilizationTheme/preferredLandforms/avoidedLandforms`）、重复 ID、非整数数量或越界值均返回带精确字段路径的 `REALM_PROFILE_INPUT_INVALID`，且不得覆盖已有设计。底层 `rule_fixture` 验收仍可使用固定配置，但不属于正式 AI 工具输入。

返回产物：

| 产物 | 说明 |
| --- | --- |
| `RealmProfile[]` | 国度设定，含 `scalePlan` 和 `expansionStyle`。 |
| `RealmCandidateMapPackage[]` | 每个国度的目标大陆合法 scope 参考图包；同一大陆上的国度可以得到相同图片。 |
| `t1Manifest` | 国度数量、目标大陆、比例归一化前摘要。 |

成功响应必须同时声明：

| 字段 | 值 / 说明 |
| --- | --- |
| `selectionMode` | `patch_explorer_primary`。 |
| `candidateMapRole` | `continent_scope_reference`，不得把整大陆参考图解释为按文明差异生成的正式候选图。 |
| `nextActions[]` | 只把 `patch_explorer_open` 作为推荐主动作。 |
| `compatibilityActions[]` | 可列 `realm_t2_select_coordinate`，但它只表示直接 grid 兼容入口。 |

约束：

- `RealmProfile.scalePlan.normalizationGroup` 必须可归到目标大陆 / 大区。
- T1 不选择最终坐标。
- 参考图包必须包含 grid 坐标说明、允许 patch、`mapRole`、`scopeBasis`、`profileDifferentiated=false` 和主选择流；AI 不得因为图包名称仍含 candidate 就跳过 Patch Explorer。
- 即使 W 由上一次客户端 / 服务进程生成，只要磁盘 survey 已 sealed，T1 也必须按 `runId` 懒恢复后继续，不要求重新调用 W。

- T1 默认选洲与候选生成共用 T2 的出生探索区、生成缓冲及附属预留排除；显式指定的大陆没有合法核心候选时，在修改已有方案前拒绝。候选图包的 `blockedCells` 同时约束 Patch Explorer。

## realm_t2_retarget

将当前未完成核心选址的国度改派到可用大陆。请求包含 `runId`、`realmId`，可选 `targetContinentId`；省略目标时选择有合法核心候选的最大大陆。保留国度设计、其他国度和已完成核心，已有核心的国度拒绝改派；随旧大陆归一化的组名同步更新。

旧 T1 checkpoint 即使指向出生大陆也允许恢复，以便调用本入口修复。内外 AI 的 T2 当前任务均提供此工具，宿主锁定当前国度；成功后结束本轮并准备新大陆的 Patch Explorer 候选，不复用旧会话。

## realm_t2_select_coordinate

提交坐标选择并生成种子。

正常 AI 主链必须先完成 `patch_explorer_open -> patch_explorer_show_candidates -> patch_explorer_select_candidate` 并提交 `patchSelectionRef`。直接 `gridX/gridZ` 只用于旧调用方或明确的人工调试。

请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `runId` | string | 是 | 当前 run。 |
| `realmId` | string | 是 | 国度 ID。 |
| `patchSelectionRef` | string | 条件必填 | 推荐入口；来自同一 run、同一 realm 的 `realm_t2` Patch Explorer。传入后由服务端解析建议粗锚点。 |
| `gridX` | number | 条件必填 | 兼容入口；未传 `patchSelectionRef` 时必填。 |
| `gridZ` | number | 条件必填 | 兼容入口；未传 `patchSelectionRef` 时必填。 |
| `alternates[]` | array | 否 | 备选 grid 坐标。 |
| `reason` | string | 否 | AI / 人类选择理由。 |
| `selectedBy` | string | 否 | `ai`、`human`、`debug`，默认 `ai`。 |
| `allowSnap` | boolean | 否 | 是否允许有限 snap，默认 true。 |

返回产物：

| 产物 | 说明 |
| --- | --- |
| `RealmCoordinateSelection` | 原始坐标、block 坐标、校验结果。 |
| `RealmSeed` | T3 扩张种子。 |
| `CapitalCityIntent` | 无坐标首都意图；最终点位由 T4 选定。 |

失败情况：

| 情况 | 行为 |
| --- | --- |
| 坐标缺少候选图映射 | `ok=false`，提示重新运行 T1。 |
| 坐标跨大陆 / 跨海 / 禁用 patch | `ok=false`，返回 `errors[]` 和可用备选提示。 |
| 坐标冲突 | `ok=false` 或使用 `alternates[]` 尝试校验。 |
| snap 超过阈值 | `ok=false`，不得静默改点。 |

## Patch Explorer

三个工具共用同一交互协议，但候选真值按尺度隔离：`realm_t2` 以 sealed W 的允许 Patch 作为搜索范围，`realm_t4` 以该国 T3 owned territory 作为搜索范围，两者都在 T 的不大于 32 格尺度重新采样、分类并跨 GIS region 生成 Patch；`city_d4` 读取 D3 自身尺度、跨 region 合并后的局部地貌 Patch 并扣除 hard occupied。群系只作为候选附加事实，不参与候选生成和类型目录。

`patch_explorer_open` 请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `runId` | string | 是 | 当前 run。 |
| `scopeType` | enum | 是 | `realm_t2`、`realm_t4`、`city_d4`。 |
| `scopeId` | string | 条件必填 | 对应 realm / continent / citySeed；也可使用下列显式字段。 |
| `realmId` / `continentId` / `citySeedId` | string | 条件必填 | 按 scope 提供。 |
| `sessionId` | string | 否 | 自定义稳定会话 ID；省略时由服务端生成。 |
| `preferGeneratorNativeTerrain` | boolean | 否 | 默认 `true`；`false` 强制 T Patch 重算和候选高程预览使用 Minecraft prior sampler。仅控制本次 session。 |

当 `scopeType=realm_t2` 或 `realm_t4` 时，HTTP 层从运行中的 `ServerLevel` 选择 T Patch 重算使用的 provider；默认优先 RTF 二维 Heightmap 快速路径，RTF 未安装、运行时契约不可用或开关关闭时整次 refinement 回退 Minecraft prior sampler，禁止逐点混用。RTF random state 尚未初始化 generator context 时，provider 可使用当前世界 RegistryAccess 完成初始化后重试。`realm_t4` 还会在打开会话前按需 ensure 当前 realm 的 `RealmT4CoarseTerrainEvidence`。调用方不需要传 RTF 专用字段，可选 `dimensionId` / `playerName` 仅用于现有世界上下文解析。

T Patch refinement 按规范化搜索 cell 集、实际 provider 身份、维度、尺度和算法版本形成共享缓存 identity。同一 run 内搜索范围和 provider identity 完全相同的 `realm_t2` / `realm_t4` open 必须复用一次重采样与分类结果；响应中的 `tScaleRefinementCacheHit` 表示本次是否命中，`tScaleRefinementArtifact` / `tScaleRefinementIdentity` 给出共享产物及其内容身份。provider、来源 fingerprint、sampling semantics 或搜索范围变化时不得命中旧缓存。

返回类型目录只给出当前 scope 的类型数量、面积与容量事实，不自动选择“最佳文明类型”。T和D共用 `patchTypePalette` 固定色表，`typeCatalog[].color` 返回对应色号。`artifacts.terrainOverview` 是当前 scope 的原始高程/水体总览，`artifacts.allPatchesOverview` 在完全相同的边界和比例上标出全部 Patch，`artifacts.biomeOverview` 是 T 尺度最终 Minecraft biome id 的独立群系总览。`realm_t4` 额外返回：

| 字段 | 说明 |
| --- | --- |
| `terrainPreviewCacheHit` | 本次是否复用有效的单国粗览缓存。 |
| `terrainPreviewProvider` | 实际 provider、fast path、fallback reason、source fingerprint 和 sampling semantics。 |
| `typeCatalog[].coarseTerrainEvidence` | 当前类型覆盖样本的高度、水体、坡度与 terrain/source biome 摘要。 |
| `artifacts.coarseTerrainEvidence` | 单国粗证据 JSON。 |
| `artifacts.heightWaterPreview` | 单国高度/水体预览 PNG。 |

`patch_explorer_show_candidates` 请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `runId` / `sessionId` | string | 是 | 打开的探索会话。 |
| `interestTypes[]` | string[] | 是 | AI 当前主动感兴趣的 `landform` 类型，例如 `plain`、`valley`、`ridge`、`shore`。 |
| `page` | int | 否 | 从 0 开始的页号。 |
| `pageToken` | string | 否 | 上一页返回的稳定续页凭证。 |
| `pageSize` | int | 否 | 每种类型每页数量，默认 3，最大 12。 |

返回 `candidatePage` 和关系表。`artifacts.topPatchesOverview` 在 `open` 返回的原始地形总览同一边界、同一比例上，一次叠加本页所有兴趣类型的 Top Patch，并标注候选 ID；准确边界替代包围盒。候选同时返回 `terrainComposition`、`baseLandformComposition` 和最大连续面积；`realm_t4` 在有粗览时还返回 `coarseTerrainEvidence`，建议锚点按非水、低起伏、低坡度、边界深度排序。关系只覆盖本次 `interestTypes` 中当页已展示候选，内容限于相邻、距离、方位、共享边界等结构化几何事实；首都、国境、已有城市和 occupied 只参与硬校验，不进入关系表。

批量比较不再为每个候选生成自适应取景的 `terrainPreview`，也不返回 `artifacts.candidateTerrainPreviews`；候选之间的位置关系以同框 `topPatchesOverview` 为准。

`patch_explorer_select_candidate` 请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `runId` / `sessionId` | string | 是 | 当前探索会话。 |
| `candidateId` | string | 是 | 必须是当前会话中已经展示的候选。 |
| `selectionReason` | string | 否 | AI 选择理由。 |

返回 `patchSelectionRef` 与选中确认。三个 scope 都在建议锚点周围按 `sampleStepBlocks=16`、`windowDiameterBlocks=1024` 生成 `evaluationLevel=city_scale_confirmation` 的单张高程高亮确认图，并冻结 `terrainPreview` 与图片引用；`artifacts.cityScaleTerrainPreview` 指向该图。来源 W、territory、粗地形证据、scope、候选事实、采样 provider 或选中确认 JSON 变化时，旧选择凭证必须拒绝消费。

T4 粗览、候选比较精扫和选中确认必须使用同一 provider 身份、source fingerprint 与 sampling semantics；运行时来源变化时必须重开 Patch Explorer 会话。两级精扫均固定 `advisoryOnly=true`、`requiredNextGate=city_d3_site_review`，不得绕过 D3 最终局部审查。

HTTP 路径分别为 `/realm/patch_explorer/open`、`/realm/patch_explorer/show_candidates`、`/realm/patch_explorer/select_candidate`。

## realm_t3_expand

运行国度扩张。

请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `runId` | string | 是 | 当前 run。 |
| `normalizationGroup` | string | 否 | 扩张分组；默认所有已完成 T2 的目标大陆。 |
| `allowUnclaimedLand` | boolean | 否 | 是否允许保留 wild land。 |
| `seaCrossingPolicyOverride` | string | 否 | 调试用总开关，通常不填。 |
| `qualityMode` | string | 否 | v1.2 调试字段，`smoke` 或 `strict`；正式验收使用 `strict`。 |
| `expansionModel` | string | 否 | `quota_frontier` 或 `action_budget`；`strict` 默认 `action_budget`，`smoke` 默认 `quota_frontier`。 |

分组标签不是地理 ID：地格归属以各 `RealmProfile.targetContinentId` 为准。省略分组时一次计算所有目标大陆；显式逻辑分组选中其成员所在大陆，也兼容显式大陆 ID。同一大陆上的其他国度必须一同参与竞争，不能通过改分组标签重复分配土地。不同大陆分别以各自可分配土地为分母，合并为本次 T3 产物。计算失败不得先清除此前已接受的内存状态和产物。

返回产物：

| 产物 | 说明 |
| --- | --- |
| `RealmTerritoryMap` | cell 级国度范围。 |
| `territoryPreview` | 国境预览图。 |
| `t3Report` | 面积比例、邻接、异常和归一化结果。 |
| `territoryRepairLog` | v1.2 飞地、孔洞、边界修复日志。 |
| `scoreManifest` | v1.4 T3 质量评分和硬阻断，包含 budget / terrain identity / wildland / contested 指标。 |

最低验收：

- 所有参与扩张的国度必须已有 accepted `RealmSeed`。
- 同一输入重复运行结果稳定。
- 输出记录归一化前后的 `targetAreaRatio`，并在 `action_budget` 下记录行动力预算、地形成本、wild / contested / blocked / unreachable 比例。
- v1.2 strict 模式下，非海权国 `largestComponentRatio < 0.90` 或 `detachedAreaRatio > 0.05` 必须失败。

## realm_t4_build_registry

生成城市种子名册。

请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `runId` | string | 是 | 当前 run。 |
| `territoryMapId` | string | 否 | 指定 T3 结果；省略使用最新结果。 |
| `allowAiCityNaming` | boolean | 否 | 是否允许 AI 给城市命名。 |
| `cityPlanningMode` | string | 否 | v1.2 建议：`rule_fixture`、`ai_candidate_selection`。 |

返回产物：

| 产物 | 说明 |
| --- | --- |
| `CitySeedRegistry` | 城市种子名册。 |
| `RealmCityCandidateMapPackage[]` | v1.2 单国度城市候选图包。 |
| `citySeedPreview` | 城市锚点预览图。 |
| `t4Report` | 城市数量、规模分布、触发条件摘要。 |
| `scoreManifest` | v1.2 城市分布评分和硬阻断。 |

约束：

- 正式 AI 主链的首都必须来自 `CapitalCityIntent` + `realm_t4` Patch Explorer 选择凭证。
- `realm_t4_build_registry` 仅为兼容验收入口，其首都必须标记 `source.selectionMode=rule_fixture`。
- T4 不创建城市实例，不生成城市边界、功能区、道路或结构落点。
- v1.2 中，有限城市必须有稳定粗锚点或候选编号；不得只输出无坐标条件模板。
- 除显式复合城市或卫星节点外，城市种子不得同格重叠。

## T4 Patch 规划会话

该路径替代“T2 自动定首都 + 程序按预设角色一次性挑完其他城市”的正式交互方式，但不删除 `realm_t4_build_registry` 兼容验收入口。

1. `realm_t4_patch_planning_create`：传 `runId`、`realmId`，可选 `planningSessionId`。新会话载入 `CapitalCityIntent`，`citySeeds=[]`、`capitalSelectionStatus=awaiting_selection`。
2. AI 对该国调用 Patch Explorer，查看兴趣类型、候选染色图和候选之间的几何关系。
3. `realm_t4_patch_planning_select_capital`：传 `runId`、`planningSessionId`、`patchSelectionRef`；可选最小连续面积和选择理由。服务端以 intent 固定首都 ID / 规模，校验 owned territory 和承载量。
4. `realm_t4_patch_planning_add_city`：只能在首都已选后添加非首都城市；`role=capital` 直接拒绝。
5. `realm_t4_patch_planning_finalize`：只有会话内恰好一座带 `patchSelectionRef` 的首都时才合并写回全局 `CitySeedRegistry`，并同步重建 T4 派生产物。

对应 HTTP 路径为 `/realm/t4/patch_planning/create`、`/realm/t4/patch_planning/select_capital`、`/realm/t4/patch_planning/add_city`、`/realm/t4/patch_planning/finalize`。

### 宿主自动推进边界

- W 扫描、T3 统一扩张和城市队列刷新由程序执行，不额外请求模型决定是否调用这些确定性步骤。
- 全部国度完成 T1/T2 后才统一 T3。此后按 `RealmSeed.seedBlock` 距世界原点排序国度；当前国 T4 finalize 立即建立/合并城市队列，先完成已登记城市，再进入下一国 T4，不等待全世界 T4。
- 每轮成功提交 T1、T2、T4 finalize 或 D4 Blueprint 后，由宿主结束该模型轮并核对真实阶段推进。内置 Harness 经宿主工具执行器、外部接续经 planning_action 调用同一作用域与停止规则；共享的停止策略不依赖模型口头宣布完成。
- 作者资料/宿主故障立即阻塞；连续三次相同拒绝结束本轮并显式报告停滞，不消耗 D4 真实编译的五次失败预算。程序/环境重试不暴露给自动城市设计轮，需先修复故障再由人发起。
- 内置 Harness 的业务插件依据宿主完成状态停止后续模型步骤；外部 Agent 通过任务完成状态继续领取或停止。运行中操作与连接断开后的占用恢复见本页公共接续协议；不能据此承诺上游请求一定立即取消或固定城市耗时。

## realm_run_acceptance

端到端验收工具，用于真实游玩前的快速闭环。

请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `caseId` | string | 否 | 固定验收用例，例如 `realm_v1_1_smoke`。 |
| `planningRadiusBlocks` | number | 否 | 配置的 W 最大扫描半径，默认由 case 决定。 |
| `radiusChunks` | number | 否 | 兼容字段；未传 block 半径时使用。 |
| `cellStepBlocks` | number | 否 | 默认 `128`。 |
| `microSampleStrideBlocks` | number | 否 | v1.3 cell 内 micro-sampling 步长，默认 `32`。 |
| `localSlopeRadiusBlocks` | number | 否 | v1.3 micro sample 局部坡度半径，默认 `8`。 |
| `preferGeneratorNativeTerrain` | boolean | 否 | 默认 `true`；控制验收内 W 是否优先使用生成器原生快路径。 |
| `runTagAudit` | boolean | 否 | v1.5 开发期调试开关；验收完成后对 W tag 抽样局部精扫。 |
| `tagAuditSampleCount` | number | 否 | v1.5 Tag Audit 抽样点数量，默认 `120`。 |
| `tagAuditSampleSeed` | string | 否 | v1.5 Tag Audit 抽样 seed；同一 run 可换 seed 抽另一批点，便于分批人工传送复核。 |
| `tagAuditRadiusBlocks` | number | 否 | v1.5 Tag Audit 局部精扫半径，默认 `32`。 |
| `tagAuditStrideBlocks` | number | 否 | v1.5 Tag Audit 局部精扫步长，默认 `4`。 |
| `tagAuditSlopeRadiusBlocks` | number | 否 | v1.5 Tag Audit 局部坡度半径，默认 `4`。 |
| `resumePolicy` | string | 否 | 默认 `use_cache`。 |
| `playerName` | string | 否 | W 阶段进度聊天消息的接收玩家；省略时使用当前在线玩家。 |
| `realmProfiles[]` | array | 否 | 可覆盖默认国度配置。 |
| `autoSelectCoordinates` | boolean | 否 | 是否使用 fixture 坐标自动走 T2；真实 AI 选点验收时应为 false。 |
| `qualityMode` | string | 否 | v1.2 验收质量模式，`smoke` 可只看链路，`strict` 必须执行评分阻断。 |
| `expansionModel` | string | 否 | `quota_frontier` 或 `action_budget`；省略时按 `qualityMode` 默认。 |

返回产物：

| 产物 | 说明 |
| --- | --- |
| `acceptanceReport` | 端到端验收报告。 |
| `artifacts` | W / T1 / T2 / T3 / T4 全部产物路径。 |
| `previewSet` | 可人工查看的关键预览图集合。 |
| `scoreManifest` | v1.2 质量评分、硬阻断和人工 review 清单。 |
| `tagAuditSamples` / `tagAuditReport` | v1.5 开发期抽样局部精扫产物，仅 `runTagAudit=true` 时输出。 |

## realm_tag_audit

对已有 sealed W run 单独执行 v1.5 Tag Audit。该工具用于“已经跑过大世界 W / acceptance 后，再抽更多点复核 tag 正确率”的开发验收场景。

请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `runId` | string | 是 | 已有 sealed W / W-T run ID。 |
| `tagAuditSampleCount` | number | 否 | 抽样点数量，默认 `120`。 |
| `tagAuditSampleSeed` | string | 否 | 抽样 seed；默认使用 `runId`，传不同 seed 可在同一 run 上换一批抽样点。 |
| `tagAuditRadiusBlocks` | number | 否 | 局部精扫半径，默认 `32`。 |
| `tagAuditStrideBlocks` | number | 否 | 局部精扫步长，默认 `4`。 |
| `tagAuditSlopeRadiusBlocks` | number | 否 | 局部坡度半径，默认 `4`。 |
| `dimensionId` | string | 否 | 采样维度；省略时从该 run 的 `world_survey_manifest.json` 恢复。 |
| `playerName` | string | 否 | 维度回退辅助；通常不需要。 |

行为：

- 如果 run 仍在内存中，直接复用当前 `RealmRun`。
- 如果 run 不在内存中，必须从 `world_survey_manifest.json`、tile snapshots 和 `world_feature_grid.json` 恢复 sealed W 结果；缺少 sealed manifest 或 tile cache 时返回失败，不静默重扫 W。
- 输出 `tag_audit_samples.json` 与 `tag_audit_report.json`，并更新返回的 `artifacts`。

## realm_debug_command

开发调试命令入口。该工具不属于 W/T 或 City 主链阶段，只用于真实游玩验收时从 MCP / HTTP 执行一条 Minecraft 命令，避免通过键盘聊天框输入。

请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `command` | string | 是 | 单条 Minecraft 命令，可带或不带开头 `/`。 |
| `confirmCommandExecution` | boolean | 是 | 必须为 `true`，确认这是有副作用的调试命令。 |
| `sourceMode` | string | 否 | `auto` / `player` / `server`，默认 `auto`；`player` 使用玩家上下文，`server` 使用服务端上下文。 |
| `playerName` | string | 否 | 玩家名；用于 `sourceMode=player` 或 `auto` 下选择玩家上下文。 |
| `dimensionId` | string | 否 | 维度 ID；省略时使用玩家维度或 overworld。 |
| `saveAfter` | boolean | 否 | 执行后是否请求保存世界，默认 false；TP 通常不需要。 |
| `allowUnsafeCommand` | boolean | 否 | 默认 false。执行 `stop`、`reload`、`op`、`ban` 等高风险管理命令时必须显式为 true。 |

行为：

- command 会规范化为单行命令并去掉开头 `/`，执行时再补回 `/`。
- 未传 `confirmCommandExecution=true` 时必须拒绝执行。
- 多行命令必须拒绝，避免一次请求执行多条命令。
- 默认拦截服务端管理类高风险命令；如确需执行，必须传 `allowUnsafeCommand=true`。
- 返回 `result` 为 Minecraft command dispatcher 的执行结果，`ok=true` 表示 `result > 0`。

示例：

```json
{
  "command": "/tp Rinsing 775 200 -6552",
  "confirmCommandExecution": true,
  "sourceMode": "player",
  "playerName": "Rinsing"
}
```

## realm_t4_patch_planning_remove_city

移除当前 T4 城市规划会话中已选入的某座城市种子，用于 AI / 人类复核全国方案时进行调整和重组。

请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `runId` | string | 是 | run ID。 |
| `planningSessionId` | string | 是 | 当前 T4 规划会话 ID。 |
| `citySeedId` | string | 是 | 要移除的城市种子 ID。 |

行为：
- 从当前会话的 `citySeeds` 列表中移除对应城市。
- 若被移除城市来源带有 `patchSelectionRef`，自动将其从 `usedPatchSelectionRefs` 中移除并释放回可用地块池，允许后续重新选择该地块。
- 若移除的是首都，会话的 `capitalSelectionStatus` 自动回退为 `awaiting_selection`，必须重新选择首都才能 finalize。
- 会话持久化落盘，返回操作结果及被移除的城市种子镜像。

## T4 草案图与复核

`select_capital` / `add_city` 的 `serviceHierarchy` 接受自由字符串，用于说明全国服务范围与分工，不限制四种层级标签。原标签继续兼容，缺省值沿用原行为。规模字段 `theoreticalScale` 仍使用既有档位并参与面积与半径计算。全国图对过长说明作省略显示，`cityLegend`、种子名册与下游交接保留完整说明。

`realm_t4_patch_planning_preview` 请求 `runId`、`planningSessionId`，返回 `cityDistributionPreview.imagePath`、`proposalHash` 和 `cityLegend`。创建、选首都、增删城市的响应也包含当前图；图展示完整设计范围与保护范围，使用实际城市名册，不发布正式名册。

`realm_t4_patch_planning_review` 请求 `runId`、`planningSessionId`、`proposalHash`、`decision`（`accept` / `revise`）和非空 `assessment`。复核保存到会话 `proposalReview`。草案变更后复核失效；旧 hash 返回 `T4_CITY_PROPOSAL_REVIEW_STALE`。finalize 除既有数量、首都、领土与保护范围检查外，还要求当前草案已 `accept`，否则返回 `T4_CITY_PROPOSAL_REVIEW_REQUIRED`。已有未封存会话可通过 preview 补图和新复核；已封存会话不重新打开。

## 建议 HTTP 对应路径

| MCP 工具 | HTTP 路径 |
| --- | --- |
| `realm_status` | `GET /realm/status` |
| `realm_w_refresh` | `POST /realm/w/refresh` |
| `realm_t1_prepare` | `POST /realm/t1/prepare` |
| `realm_t2_select_coordinate` | `POST /realm/t2/select_coordinate` |
| `realm_t3_expand` | `POST /realm/t3/expand` |
| `realm_t4_patch_planning_create` | `POST /realm/t4/patch_planning/create` |
| `realm_t4_patch_planning_select_capital` | `POST /realm/t4/patch_planning/select_capital` |
| `realm_t4_patch_planning_add_city` | `POST /realm/t4/patch_planning/add_city` |
| `realm_t4_patch_planning_remove_city` | `POST /realm/t4/patch_planning/remove_city` |
| `realm_t4_patch_planning_preview` | `POST /realm/t4/patch_planning/preview` |
| `realm_t4_patch_planning_review` | `POST /realm/t4/patch_planning/review` |
| `realm_t4_patch_planning_finalize` | `POST /realm/t4/patch_planning/finalize` |
| `realm_t4_build_registry` | `POST /realm/t4/build_registry` |
| `realm_run_acceptance` | `POST /realm/acceptance/run` |
| `realm_tag_audit` | `POST /realm/tag_audit` |
| `realm_debug_command` | `POST /realm/debug/command` |

## 实现优先级

| 优先级 | 接口 |
| --- | --- |
| P0 | `realm_status`、`realm_w_refresh`、`realm_run_acceptance` 的 skeleton。 |
| P1 | `realm_t1_prepare`、`realm_t2_select_coordinate`。 |
| P2 | `realm_t3_expand`。 |
| P3 | `realm_t4_build_registry`。 |

只有 P0-P3 全部落地后，才算具备 W / T 真实游玩验收闭环。


## T4 地理开放与选址隔离补充（2026-09-09）

`realm_t4_patch_planning_select_capital/add_city` 无新增 AI 坐标或圈选参数。程序返回的 `designBounds` 是唯一设计边界，`protectionBounds` 为外围安全圈，不能用于设计。工具描述已同步此约束。

新增可纠正错误：

| 错误 | 下一步 |
| --- | --- |
| `T4_CITY_PROTECTION_OVERLAP` | 返回冲突城市、请求矩形和已占矩形；在 Patch Explorer 另选更远地块，不能靠卫星身份或缩小安全比例绕过。 |
| `T4_CITY_PROTECTION_INSIDE_INITIAL_AREA` | 整个保护矩形移出初始活动区及 1024 格加载缓冲，不能只移动中心。 |
| `T4_CITY_PROTECTION_ALREADY_LOADED` | 返回首个冲突区块及状态；改选未加载地形，不要继续修改 D4 或尝试补建。 |
| `CITY_D3_RESERVATION_BOUNDS_CHANGED` | 恢复 T4 冻结中心、规模和原预览范围，保护圈不是 D3 设计边界。 |
| `CITY_BLUEPRINT_OUTSIDE_DESIGN_BOUNDS` / `CITY_BLUEPRINT_ROAD_OUTSIDE_DESIGN_BOUNDS` | 将指定边缘阵列/道路接口向内调整，或减少边缘填充；不得扩到安全圈。 |

finalize 封存该国名册，不直接解锁大陆。地图和服务端会等相关国度名册全部封存、大陆城市全部准备好首次生成后整体开放。

## 冒险者地图客户端视口协议

Forge `adventurer_map` 通道协议版本为 `6`。快照请求依次发送 `zoom`、`centerX`、`centerZ` 三个 double，中心为客户端当前浏览的世界 X/Z 坐标。缩放限制为 0.5–4；中心非有限时回退玩家坐标，有限值限制到 ±30000000 格，再按既有 256 格中心量化。服务端继续按 `4096 / zoom`（1024–8192 格半径）裁剪 W 底图和节点并应用实际开放蒙版，不因浏览远处生成区块或揭示未开放区域。响应结构不变；客户端同时最多一个在途快照，拖动期间合并刷新，最短间隔 4 tick，松手刷新最终视口。客户端绘制中心独立于响应底图范围，旧响应不得重置浏览位置。

## 外部 Agent 存档大厅与任务接续

外部 MCP（游戏托管 Streamable HTTP 或开发 stdio）在 initialize 响应的 instructions 中要求首次接入先调用 `geomantia_lobby`，呈现存档大厅并等待玩家选择。玩家已明确要求开始/继续时不重复确认。初始化只传指引，不自动扫描世界；是否主动显示由 Agent 客户端决定。`GEOMANTIA_PROVIDER_TOOL_URL` 内置桥接模式不发布大厅 instructions 或大厅/接续工具，继续使用宿主限定的工具表。

| 工具 | 行为 |
| --- | --- |
| `geomantia_lobby` | 只读当前世界名称、阶段、任务、占用及阻塞，返回开始/继续、查看成果、查看状态菜单。 |
| `planning_resume` | 玩家要求推进后获取世界级占用，从正式存档恢复 W/T/City 阶段。后台最多连续处理 8 个程序步骤，备齐与内置执行端共用的任务状态、工具 schema、指引和实际预览图。`retry=true` 仅用于问题已处理后的明确重试。 |
| `planning_action` | 使用本轮 `taskId`、`actionId`、`tool`、`arguments` 执行允许的决策工具。旧 taskId 拒绝；最近一次相同 actionId/输入的网络重试返回已完成结果，不重复修改。不同输入不可复用 actionId。 |
| `planning_wait` | 使用 cursor 等待状态变化，最长 20 秒；只返回进度，避免重复发送图片。任务准备好后 resume 取得任务包。程序阻塞返回 blocked 与原因。 |
| `planning_release` | 暂停/完成时释放执行权，不删除进度；执行中的程序调用不能被强行释放。 |
| `planning_artifact` | 当前 run 内只读 list/search/text/image；相对路径、真实路径校验、文本分页，图片作为 MCP image 返回。可在大厅查看成果时使用，不需先启动规划。 |

HTTP 对应 `/planning/lobby|resume|action|wait|heartbeat|release|artifact`（POST）。外部桥接保存 ownerId 与 leaseToken，并通过 `X-Geomantia-Planning-Token` 请求头携带占用凭证；不把凭证传给模型。世界重开后从正式产物恢复，内存占用和旧任务凭证作废。

公共 `PlanningSessionService`、`PlanningStepPolicy`、`PreparedPlanningTurn` 被内置和外部执行端共用。它不要求启用 Provider 或配置 API Key；W/T3/队列刷新/D3 等确定步骤由程序处理。原 D4 自动编译队列继续推进至 waiting_for_generation。

占用覆盖当前世界规划。原 HTTP 修改入口在占用期间拒绝其他执行端，状态查询不受阻。操作执行中不会因租约到期转交；外部桥接活动时自动续租，空闲 2 分钟后停止心跳，剩余租约最长 2 分钟，避免已取消聊天永久占用。正常暂停立即 release；MCP 断开尽力释放。MCP 连接本身不触发模型回合，不依赖通知强行唤醒外部 Agent。

## 游戏托管 MCP URL 服务

MCP 在 Mod common setup 后异步启动，主菜单即可连接；进入世界后才调用具体规划服务。默认连接地址 `http://127.0.0.1:5001/mcp`，传输为标准 MCP Streamable HTTP（POST/GET/DELETE 会话），现有 stdio 开发入口保留。HTTP 会话各自创建 MCP Server 与 planning 客户端，不能共享不同 Agent 的占用凭证。只监听本机回环地址，校验 Host/Origin；非法会话返回 404，客户端需重新 initialize。

实例配置 `config/geomantia/mcp_server.json` 包含 `enabled`（默认 true）与 `port`（默认 5001，允许 1024–65535，不得与内部游戏 API 端口重复）。在 Mods → Geomantia → Config，或游戏内 Provider 设置中的 MCP 设置，查看状态、复制 URL、修改端口、保存并重启。保存会重启 MCP 监听，外部客户端需使用新地址重新连接。配置损坏或端口占用明确显示失败，不默默切换端口或要求配置 Provider Key。

服务使用 Mod 打包的 Node 运行环境和 MCP bundle，无需系统安装 Node；与内置 Harness 共用运行环境安装锁，但不会因启动 MCP 而请求模型或启用内置自动规划。MCP 随游戏进程退出，退出/切换存档时保持监听。Java 托管子进程，stdin 关闭与父进程监测用于避免游戏退出后残留服务。启动健康检查仅说明 MCP 监听已就绪，不代表存档、模型或城市设计已经可用。

实现入口：`McpServerService`、`McpServerConfig`、`McpSettingsScreen`、`country_designer_mcp/src/server.ts` 和 `http-server.ts`。验证入口：`McpServerServiceTest`（实际内置运行环境启动、MCP initialize、端口变更与停用）、`country_designer_mcp/test/mcp-http.test.mjs`（标准客户端、独立会话、大厅、图片、拒绝跨来源和端口冲突）。


## 固定领土输入补充（2026-10-07）

`realm_t1_prepare.realmProfiles[]` 可带 `territoryPolicy: {mode: "fixed", nearshoreRadiusCells: 2}`；使用既有 `targetContinentId` 选择完整目标陆块。缺失 policy 保持扩张模式。Java 正式任务 schema 与外置 MCP schema 同步支持该对象，未知字段、非整数宽度及模式不符的宽度拒绝。

固定国度仍通过 T2/T3 交接；T3 为固定范围核验与保存，不是面积竞争。`FIXED_TERRITORY_CONFLICT`、`FIXED_TERRITORY_RESERVED`、`FIXED_TERRITORY_OUTSIDE_SURVEY`、`FIXED_TERRITORY_EMPTY` 分别说明重叠、保护区、未完整扫描与无可归属陆地。调用方须调整声明，不能将错误当作部分领土成功。
