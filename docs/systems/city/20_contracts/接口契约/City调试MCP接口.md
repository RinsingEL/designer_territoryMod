# City 调试 MCP 接口契约

## 版本

v0.1 — City D2/D3 首版 MCP 接口

## 边界

Java 侧 HTTP 接口监听 `127.0.0.1:5000`，Node 侧 `country_designer_mcp` 通过 MCP 工具调用 HTTP。

环境变量：`GEOMANTIA_MC_API_URL`（默认 `http://127.0.0.1:5000`）

## 工具总览

| MCP 工具 | HTTP 端点 | 说明 |
|---|---|---|
| `city_plan_d2` | `POST /realm/city/plan_d2` | 构建 CitySiteContext |
| `city_plan_d3` | `POST /realm/city/plan_d3` | 构建 CityLandformReviewPackage（含局部 GIS 刷新） |

## city_plan_d2

**描述**：基于已有 W/T run 的 CitySeed 构建 CitySiteContext。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `runId` | string | 是 | 已有 W/T run ID |
| `citySeedId` | string | 是 | 目标城市种子的 citySeedId |
| `cellStepBlocks` | number | 否 | 可选覆盖；未传时从 `world_survey_manifest.json` 恢复 W/T 采样步长 |

**返回**：

```json
{
  "ok": true,
  "citySiteContext": { ... }
}
```

**最低验收**：返回 citySiteContext 含 schemaVersion、cityId、realmId、grid、bounds、anchorBlock、entryCandidates、territoryCheckResult。

**真实 run 规则**：入口必须优先使用 `city_seed_registry.json` 的 `anchorBlock`，并读取 `realm_territory_map.json` 计算领地归属。不得因为 MCP 默认参数导致真实坐标错位。

## city_plan_d3

**描述**：构建 CityLandformReviewPackage，会触发局部 GIS 刷新获取 patch 数据。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `runId` | string | 是 | 已有 W/T run ID |
| `citySeedId` | string | 是 | 目标城市种子的 citySeedId |
| `cellStepBlocks` | number | 否 | 可选覆盖；未传时从 `world_survey_manifest.json` 恢复 W/T 采样步长 |
| `dimensionId` | string | 否 | 维度 ID，省略时从 run manifest 恢复，再回退到玩家/overworld |
| `playerName` | string | 否 | 玩家名，用于定位维度 |

**返回**：

```json
{
  "ok": true,
  "patchCount": 18,
  "citySiteContext": { ... },
  "landformReviewPackage": { ... }
}
```

**最低验收**：
- landformReviewPackage 含 landformPatches、legend、planningContext、aiPromptContext
- 每个 patch 有 mapLabel（如 `平原01`）、landformType、areaClass、metricsSummary、summaryFacts
- 图例覆盖所有出现的地貌类型
- `reviewMapImage` 指向 `run/realm_debug/<runId>/city_d3_<citySeedId>/landform_review_map.png`
- `debugRefs` 至少包含 review PNG 与 D3 输出目录

## 使用流程

```
# 1. 查看已有 run
realm_status

# 2. 运行验收生成 T4 产物
realm_run_acceptance { runId: "city_test", planningRadiusBlocks: 4096, cellStepBlocks: 128 }

# 3. City D2 上下文
city_plan_d2 { runId: "city_test", citySeedId: "city_realm_0_capital" }

# 4. City D3 地貌审查
city_plan_d3 { runId: "city_test", citySeedId: "city_realm_0_capital" }
```

## 真实游玩验收状态

截至 2026-06-16，本接口已有自动测试和 sealed run 产物测试，但尚未在运行中的 Minecraft 中完成 MCP 真实游玩验收。
