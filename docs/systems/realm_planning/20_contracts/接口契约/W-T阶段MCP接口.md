# W / T 阶段 MCP 接口契约

## 定位

本文定义国度规划系统 v1.1 为真实游玩验收提供的 MCP 调试接口。它不是 legacy T1 / T2 工具的兼容层；旧 `t1_select_cluster`、`t2_select_direction` 等接口不进入当前主线。

接口目标：

- agent 可以通过 MCP 从真实 MC 世界触发 W / T 主链。
- 每个阶段都能返回结构化状态、产物路径和下一步建议。
- T2 采用“AI / 人类从带网格坐标候选图直接提交坐标”的新流程。
- MCP 能支撑端到端验收，而不是只跑单元测试。

## 工具总览

| 工具 | 阶段 | 作用 |
| --- | --- | --- |
| `realm_status` | 通用 | 读取国度规划系统状态、最近 run 和产物目录。 |
| `realm_w_refresh` | W | 在真实世界或固定测试世界中生成 `WorldSurveyContext`、`WorldPatchMap` 和候选底图。 |
| `realm_t1_prepare` | T1 | 基于 W 产物和国度配置生成 `RealmProfile` 与 `RealmCandidateMapPackage`。 |
| `realm_t2_select_coordinate` | T2 | 提交 AI / 人类选择的 grid 坐标，校验并生成 `RealmSeed`、`CapitalCitySeed`。 |
| `realm_t3_expand` | T3 | 对指定大陆 / 分组运行国度扩张，输出 `RealmTerritoryMap`。 |
| `realm_t4_build_registry` | T4 | 生成 `CitySeedRegistry`。 |
| `realm_run_acceptance` | 验收 | 用固定配置跑完整 W -> T4 调试链，并输出验收报告。 |

## 通用返回字段

所有工具返回 JSON 文本。成功时建议包含：

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
| `debugRoot` | 调试产物根目录。 |
| `availableStages[]` | 已实现阶段。 |
| `gisReady` | GIS 调试服务是否可用。 |

## realm_w_refresh

生成 W 粗扫产物。

请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `radiusChunks` | number | 是 | 粗扫半径，单位 chunk。 |
| `cellStepBlocks` | number | 是 | 粗 cell 步长，建议 64 / 128 / 256。 |
| `sampleMode` | string | 否 | 默认 `prior`。 |
| `centerBlockX` / `centerBlockZ` | number | 否 | 粗扫中心；省略时使用玩家位置或测试默认点。 |
| `dimensionId` | string | 否 | 维度 ID，默认玩家维度或 `minecraft:overworld`。 |
| `worldTheme` | object/string | 否 | 世界主题摘要。 |
| `runId` | string | 否 | 指定 run ID；省略则自动生成。 |

返回产物：

| 产物 | 说明 |
| --- | --- |
| `WorldSurveyContext` | W 粗扫上下文。 |
| `WorldPatchMap` | 粗地貌地图。 |
| `worldPatchPreview` | 粗 patch 调试图。 |
| `gridOverlayPreview` | 带 grid 坐标的候选底图。 |
| `wManifest` | 坐标转换、step、patch、continent 摘要。 |

最低验收：

- `cellStepBlocks`、`gridOriginBlock`、`gridSize` 可追溯。
- 至少存在一个可分配 land continent。
- preview 能显示 grid 坐标或可由 manifest 映射 grid 坐标。

## realm_t1_prepare

生成国度设定和候选图包。

请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `runId` | string | 是 | 来源 W run。 |
| `realmProfiles[]` | array | 否 | 外部提供的 RealmProfile 草案。 |
| `realmCount` | number | 否 | 未提供 profiles 时由程序 / AI 生成草案数量。 |
| `targetContinentId` | string | 否 | 限定大陆。 |
| `allowAiDraftProfile` | boolean | 否 | 是否允许 AI 生成 RealmProfile 草案。 |

返回产物：

| 产物 | 说明 |
| --- | --- |
| `RealmProfile[]` | 国度设定，含 `scalePlan` 和 `expansionStyle`。 |
| `RealmCandidateMapPackage[]` | 每个国度的候选图包。 |
| `t1Manifest` | 国度数量、目标大陆、比例归一化前摘要。 |

约束：

- `RealmProfile.scalePlan.normalizationGroup` 必须可归到目标大陆 / 大区。
- T1 不选择最终坐标。
- 候选图包必须包含 grid 坐标说明和允许 patch。

## realm_t2_select_coordinate

提交坐标选择并生成种子。

请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `runId` | string | 是 | 当前 run。 |
| `realmId` | string | 是 | 国度 ID。 |
| `gridX` | number | 是 | 候选图上的 grid X。 |
| `gridZ` | number | 是 | 候选图上的 grid Z。 |
| `alternates[]` | array | 否 | 备选 grid 坐标。 |
| `reason` | string | 否 | AI / 人类选择理由。 |
| `selectedBy` | string | 否 | `ai`、`human`、`debug`，默认 `ai`。 |
| `allowSnap` | boolean | 否 | 是否允许有限 snap，默认 true。 |

返回产物：

| 产物 | 说明 |
| --- | --- |
| `RealmCoordinateSelection` | 原始坐标、block 坐标、校验结果。 |
| `RealmSeed` | T3 扩张种子。 |
| `CapitalCitySeed` | 首都城市种子。 |

失败情况：

| 情况 | 行为 |
| --- | --- |
| 坐标缺少候选图映射 | `ok=false`，提示重新运行 T1。 |
| 坐标跨大陆 / 跨海 / 禁用 patch | `ok=false`，返回 `errors[]` 和可用备选提示。 |
| 坐标冲突 | `ok=false` 或使用 `alternates[]` 尝试校验。 |
| snap 超过阈值 | `ok=false`，不得静默改点。 |

## realm_t3_expand

运行国度扩张。

请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `runId` | string | 是 | 当前 run。 |
| `normalizationGroup` | string | 否 | 扩张分组；默认所有已完成 T2 的目标大陆。 |
| `allowUnclaimedLand` | boolean | 否 | 是否允许保留 wild land。 |
| `seaCrossingPolicyOverride` | string | 否 | 调试用总开关，通常不填。 |

返回产物：

| 产物 | 说明 |
| --- | --- |
| `RealmTerritoryMap` | cell 级国度范围。 |
| `territoryPreview` | 国境预览图。 |
| `t3Report` | 面积比例、邻接、异常和归一化结果。 |

最低验收：

- 所有参与扩张的国度必须已有 accepted `RealmSeed`。
- 同一输入重复运行结果稳定。
- 输出记录归一化前后的 `targetAreaRatio`。

## realm_t4_build_registry

生成城市种子名册。

请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `runId` | string | 是 | 当前 run。 |
| `territoryMapId` | string | 否 | 指定 T3 结果；省略使用最新结果。 |
| `allowAiCityNaming` | boolean | 否 | 是否允许 AI 给城市命名。 |

返回产物：

| 产物 | 说明 |
| --- | --- |
| `CitySeedRegistry` | 城市种子名册。 |
| `citySeedPreview` | 城市锚点预览图。 |
| `t4Report` | 城市数量、规模分布、触发条件摘要。 |

约束：

- 首都必须来自 `CapitalCitySeed`。
- T4 不创建城市实例，不生成城市边界、功能区、道路或结构落点。

## realm_run_acceptance

端到端验收工具，用于真实游玩前的快速闭环。

请求：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `caseId` | string | 否 | 固定验收用例，例如 `realm_v1_1_smoke`。 |
| `radiusChunks` | number | 否 | 默认由 case 决定。 |
| `cellStepBlocks` | number | 否 | 默认由 case 决定。 |
| `realmProfiles[]` | array | 否 | 可覆盖默认国度配置。 |
| `autoSelectCoordinates` | boolean | 否 | 是否使用 fixture 坐标自动走 T2；真实 AI 选点验收时应为 false。 |

返回产物：

| 产物 | 说明 |
| --- | --- |
| `acceptanceReport` | 端到端验收报告。 |
| `artifacts` | W / T1 / T2 / T3 / T4 全部产物路径。 |
| `previewSet` | 可人工查看的关键预览图集合。 |

## 建议 HTTP 对应路径

| MCP 工具 | HTTP 路径 |
| --- | --- |
| `realm_status` | `GET /realm/status` |
| `realm_w_refresh` | `POST /realm/w/refresh` |
| `realm_t1_prepare` | `POST /realm/t1/prepare` |
| `realm_t2_select_coordinate` | `POST /realm/t2/select_coordinate` |
| `realm_t3_expand` | `POST /realm/t3/expand` |
| `realm_t4_build_registry` | `POST /realm/t4/build_registry` |
| `realm_run_acceptance` | `POST /realm/acceptance/run` |

## 实现优先级

| 优先级 | 接口 |
| --- | --- |
| P0 | `realm_status`、`realm_w_refresh`、`realm_run_acceptance` 的 skeleton。 |
| P1 | `realm_t1_prepare`、`realm_t2_select_coordinate`。 |
| P2 | `realm_t3_expand`。 |
| P3 | `realm_t4_build_registry`。 |

只有 P0-P3 全部落地后，才算具备 W / T 真实游玩验收闭环。
