# CitySiteContext 数据契约

## 版本

| 字段 | 值 | 说明 |
|---|---|---|
| `schemaVersion` | `city_site_context.v0.1` | City C0 局部上下文初版 |
| `coordinateUnit` | `block` | 坐标统一为 block |
| `gridUnit` | `cell` | 网格使用 City 本地 cell |

## 定位

`CitySiteContext` 是 City 系统 D2 (C0) 的主输出。从 T4 `CitySeed` 和 `CitySiteCandidate` 锁定城市局部范围，确定规划网格、入口候选和领地归属。

## 字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `schemaVersion` | string | 是 | 固定 `city_site_context.v0.1` |
| `cityId` | string | 是 | 城市唯一 ID，来自 CitySeed |
| `realmId` | string | 是 | 所属国度 ID |
| `dimensionId` | string | 是 | Minecraft 维度 ID |
| `seedId` | string | 是 | 对应 CitySeed ID |
| `siteCandidateId` | string | 是 | 对应 CitySiteCandidate ID |
| `bounds` | object | 是 | `{ minX, minZ, maxX, maxZ }` block 包围盒 |
| `grid` | object | 是 | 局部规划网格，见子结构 |
| `anchorBlock` | object | 是 | `{ x, z }` 锚点 block 坐标 |
| `cityRole` | string | 是 | 城市功能类型，如 capital、port、mining_town |
| `scaleClass` | string | 是 | 规模等级，hamlet/village/town/city |
| `planningRadiusBlocks` | int | 是 | 规划半径，单位 block |
| `entryCandidates` | array | 是 | 入口候选点列表 |
| `territoryCheckResult` | string | 是 | inside/border/outside/unknown |

### entryCandidates[] 子结构

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 是 | 入口 ID，如 main_gate、gate_n |
| `block` | object | 是 | `{ x, z }` block 坐标 |
| `direction` | string | 是 | 方向标识，N/S/E/W/NE/NW/SE/SW/center |
| `description` | string | 是 | 可读描述，如 "北门入口" |

## 实现位置

- 实现类：`com.rinsing.geomantia.systems.city.domain.model.CitySiteContext`
- Builder：`com.rinsing.geomantia.systems.city.application.CitySiteContextBuilder`
- 配置：`com.rinsing.geomantia.systems.city.domain.config.CityPlanningConfig`
- HTTP 端点：`POST /realm/city/plan_d2`
- MCP 工具：`city_plan_d2`

## 规模映射

| 规模 | 规划半径 | Cell Step | 说明 |
|---|---|---|---|
| hamlet | 160-240 blocks | 8-16 | 小聚落 |
| village | 256-384 blocks | 16 | 村镇 |
| town | 512-640 blocks | 16 | 城镇；保持 GIS region 可整除 |
| city | 768+ blocks | 32 | 城市；保持 GIS region 可整除 |

T4 兼容映射：`capital`/`large_city` → `city`，`outpost` → `hamlet`；`hamlet`、`village`、`town`、`city` 保持原值。前哨站使用最小规模的规划半径，城市角色 `cityRole` 与 T4 种子中的原始规模不改写。D3 网格固定为 16 格，不受上表 D2 Cell Step 影响。

## Run 元数据恢复规则

- D2/D3 HTTP/MCP 入口未显式传 `cellStepBlocks` 时，必须从 `run/realm_debug/<runId>/world_survey_manifest.json` 的 `config.cellStepBlocks` 恢复 W/T 采样步长。
- `dimensionId` 优先使用请求参数；未传时从 `world_survey_manifest.json` 的 `config.dimensionId` 恢复；仍缺失时才使用 `minecraft:overworld`。
- D2 可以离线读取 artifact；D3 及后续任何读取或修改实时世界的入口必须额外读取 `world_survey_context.json`，要求其 `worldSeed` 与 `dimensionId` 同当前 `ServerLevel` 完全一致。该校验是产生实时阶段副作用前的硬前置，不允许用 run 内部 artifact hash 或 selection ref 代替。
- `anchorBlock` 优先使用 T4 `city_seed_registry.json` 中 seed 的 `anchorBlock`，不得用 MCP 默认步长重算真实锚点。
- `siteCandidateId` 优先使用 seed 的 `candidateId`，缺失时才回退到 `citySeedId`。
- `territoryCheckResult` 优先使用 `realm_territory_map.json` 中同 `realmId` 且 `status=owned` 的 territory cells 计算；文件缺失或无匹配 cells 时返回 `unknown`。

## 验证规则

- `cityId`、`realmId`、`grid`、`bounds` 必填
- anchor block 必须在 bounds 内
- territoryCheck: anchor 不在领地内 → `outside`
- territoryCheck: 边界超过 10% 不在领地内 → `border`
- territoryCheck: 无领地数据 → `unknown`
