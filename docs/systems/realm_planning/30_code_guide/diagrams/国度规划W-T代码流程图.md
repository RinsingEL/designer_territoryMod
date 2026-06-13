# 国度规划 W-T 代码流程图

本文用来定位当前实现调用链。它可以帮助 agent 或开发者从入口跳到类、方法和产物，不重新定义产品边界。

```mermaid
flowchart TD
  A1(["MCP realm_run_acceptance"]) --> A2["realm/handlers.ts"]
  A2 --> A3["POST /realm/acceptance/run"]
  A4(["Forge /geomantia realm acceptance"]) --> A5["GisPlatformEvents.realmAcceptance"]
  A6(["GameTest"]) --> A7["RealmPlanningGameTests.realmPlanningPriorAcceptance"]

  A3 --> B["RealmPlanningHttpController.handleAcceptance"]
  B --> C["callOnServerThread"]
  C --> D["runWorldSurvey"]
  A5 --> D2["WorldSurveyRunner.run"]
  A7 --> D2
  D --> D2

  subgraph WSurvey["systems.realm_planning.WorldSurveyRunner"]
    D2 --> E["Config.normalized"]
    E --> F["SurveyBounds.from"]
    F --> G["planTiles"]
    G --> H{tile cache exists?}
    H -- 是 --> I["AtlasRegionSnapshotIo.read"]
    H -- 否 --> J["scanTile"]
    J --> K["GisRefreshService.run"]
    K --> L["AtlasRegionSnapshotIo.write"]
    I --> M[("WorldSurveyResult")]
    L --> M
    M --> N[("world_survey_manifest.json")]
  end

  M --> O["RealmPlanningService.runAcceptance"]

  subgraph Service["systems.realm_planning.RealmPlanningService"]
    O --> P["runW"]
    P --> P1["buildWorld / assignContinents / buildPatchSummaries"]
    P1 --> P2[("world_survey_context.json / world_patch_map.json")]

    P2 --> Q["prepareT1"]
    Q --> Q1["RealmProfile.fromJson 或 defaultProfiles"]
    Q1 --> Q2["buildCandidatePackage / exportCandidateMap"]
    Q2 --> Q3[("realm_profiles.json / candidate_map_packages.json")]

    Q3 --> R["selectT2"]
    R --> R1["validateSelection / trySnap"]
    R1 --> R2["RealmSeed.from / CapitalCitySeed.from"]
    R2 --> R3[("realm_seeds.json / capital_city_seeds.json")]

    R3 --> S["expandT3"]
    S --> S1["buildTerritory"]
    S1 --> S2["buildFrontierTerritory"]
    S2 --> S3["repairDetachedComponents / rebalanceAreaQuotas"]
    S3 --> S4[("realm_territory_map.json / t3_report.json")]

    S4 --> T["buildT4"]
    T --> T1["buildRegistry"]
    T1 --> T2["bestCityCandidate / citySpacingOk"]
    T2 --> T3[("city_seed_registry.json / realm_city_candidate_packages.json")]

    T3 --> U["exportScoreManifest"]
    U --> U1["scoreManifest / wQualityScore / t3QualityScore / t4QualityScore"]
    U1 --> U2[("score_manifest.json")]
    U2 --> V["acceptanceReport"]
    V --> V1[("acceptance_report.json")]
  end

  V1 --> Z["HTTP / MCP response"]

  classDef entry fill:#eefcef,stroke:#4f8f4f,color:#183818;
  classDef process fill:#ffffff,stroke:#666,color:#222;
  classDef data fill:#eef6ff,stroke:#4976a8,color:#1f2f3f;
  classDef boundary fill:#f7f0ff,stroke:#7a55aa,color:#2a163f;
  class A1,A4,A6 entry;
  class WSurvey,Service boundary;
  class M,N,P2,Q3,R3,S4,T3,U2,V1 data;
```

## 读图口径

- 左上是入口层，紫色分组是主要实现类边界。
- `WorldSurveyRunner` 复用 GIS 刷新服务逐 tile 生成 sealed W 结果。
- `RealmPlanningService` 是 T 阶段主服务，负责 W 汇总、T1、T2、T3、T4 和评分产物。
- 图中 JSON / PNG 产物默认写入 `run/realm_debug/<runId>/`。
