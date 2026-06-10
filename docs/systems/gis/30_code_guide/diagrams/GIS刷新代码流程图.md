# GIS 刷新代码流程图

本文用代码视角展示 GIS 半径刷新主链。图中的主链、调试旁路、数据对象和未来消费者边界使用不同形状与连线区分；详细步骤见 `../flows/半径刷新实现指南.md`。

```mermaid
flowchart TD
  subgraph Entry["入口层"]
    Cmd(["Forge 命令<br/>/geomantia gis refresh"])
    Http(["HTTP 接口<br/>POST /gis/refresh"])
    Mcp(["MCP 工具<br/>gis_refresh"])
    Test(["合成测试<br/>GisTestRunner"])
  end

  Mcp -.->|HTTP JSON| Http
  Cmd --> Ctx["解析上下文<br/>维度 / 中心 / 半径 / sampleMode"]
  Http --> Ctx
  Test --> Synthetic["SyntheticAtlasSampler<br/>固定样例 profile"]

  subgraph Runtime["刷新主链"]
    Ctx --> Service["GisRefreshService.refresh"]
    Synthetic --> Service
    Service --> Job[(RefreshJob<br/>状态 / 预算 / 进度)]
    Service --> Region[(AtlasRegion<br/>128x128 Cell 网格)]
    Job --> Plan["RadiusRefreshPlanner.plan"]
    Region --> Plan
    Plan --> Planned[(PlannedCell 列表<br/>ring + stable)]

    Planned --> Sample{"采样器类型"}
    Sample --> Prior["MinecraftPriorAtlasSampler<br/>ChunkGenerator prior"]
    Sample --> Synth["SyntheticAtlasSampler<br/>测试地形"]
    Prior --> Cells1[(AtlasCell<br/>sample 字段 + SAMPLED)]
    Synth --> Cells1

    Cells1 --> Metrics["AtlasMetricsComputer.compute"]
    Metrics --> Cells2[(AtlasCell<br/>metrics + EDGE_DIRTY)]
    Cells2 --> Classify["LandformClassifier.classify"]
    Classify --> Cells3[(AtlasCell<br/>landformType)]
    Cells3 --> Patch["PatchMerger.merge"]
    Patch --> Patches[(LandformPatch 列表<br/>摘要 + flags)]
    Patch --> Result["RefreshResult<br/>job / region / counts / runDirectory"]
  end

  subgraph Debug["调试与复现旁路"]
    Job -.-> Progress["ProgressExporter<br/>progress.png / manifest"]
    Region -.-> Progress
    Result -.-> Preview["PreviewExporter<br/>elevation / water / slope / tpi / landform / patch"]
    Result -.-> Snapshot["AtlasRegionSnapshotIo<br/>region_snapshot.json"]
    Result -.-> Report["GisTestReport<br/>test_report.json"]
  end

  subgraph Response["返回层"]
    Result --> HttpJson["HTTP JSON<br/>runId / status / counts / artifacts"]
    HttpJson --> McpText["MCP text result"]
    Result --> CmdText["命令成功/失败消息"]
  end

  subgraph Future["未来消费者边界（G8 不在当前目标）"]
    Query(["GIS Query API"])
    City["City"]
    Roads["Roads"]
    Realm["Realm"]
    Structure["Structure"]
  end

  Patches -.->|未来正式查询| Query
  Query -.-> City
  Query -.-> Roads
  Query -.-> Realm
  Query -.-> Structure
```

## 读图说明

- 粗主链从入口层进入 `GisRefreshService`，再依次经过 planning、sampling、metrics、classify、patch。
- 圆柱节点表示数据对象或契约对象，例如 `RefreshJob`、`AtlasRegion`、`AtlasCell`、`LandformPatch`。
- 虚线表示调试或复现旁路；这些产物用于验收，不是生产主缓存。
- `MCP -> HTTP` 是本地调试桥，不是 G8 消费者查询接口。
- 未来消费者边界只表达方向，不表示当前 GIS v1 已提供正式 query API。

## 当前实现限制

- `MinecraftPriorAtlasSampler` 当前实现 prior 采样；`observedIfLoaded` 和 `verifySurface` 后验分支尚未落地。
- `PatchMerger` 当前只做同类型四邻接合并。
- `LandformPatch` 当前保存摘要和 bbox，不保存成员 Cell 集合。
- `PreviewExporter` 的 `patch.png` 当前是 bbox overlay，不代表最终 Patch 轮廓。
