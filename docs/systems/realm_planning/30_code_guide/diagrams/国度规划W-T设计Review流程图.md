# 国度规划 W-T 设计 Review 流程图

本文用来人工 review 国度规划 W / T 主链的阶段责任。它回答“过程设计有没有越界”，不替代 `../flows/W-T主链实现指南.md` 的代码调用说明。

```mermaid
flowchart TD
  A(["真实世界 / 合成样例"]) --> B["W 分片粗扫"]

  subgraph W["W 世界粗扫"]
    B --> C{所有 tile sealed?}
    C -- 否 --> C1["失败：不得进入正式 T"]
    C -- 是 --> D[("WorldSurveyResult")]
    D --> E["汇总 WorldPatchMap / continent / patch"]
    E --> F[("WorldSurveyContext + WorldPatchMap")]
    E -. 调试旁路 .-> F1["world_patch_preview.png / grid_overlay_preview.png"]
  end

  subgraph T1["T1 国度设定与候选图"]
    F --> G["生成或读取 RealmProfile"]
    G --> H["按目标大陆生成候选图包"]
    H --> I[("RealmCandidateMapPackage")]
    H -. 调试旁路 .-> I1["每国 candidate_map.png"]
  end

  subgraph T2["T2 坐标选择与种子"]
    I --> J["AI / 自动流程选择 grid 坐标"]
    J --> K{坐标 accepted?}
    K -- 否 --> K1["rejected selection + errors"]
    K -- 是 --> L[("RealmSeed + CapitalCityIntent")]
  end

  subgraph T3["T3 国度扩张"]
    L --> M["多国度统一 frontier 扩张"]
    M --> N["拓扑修复 / 面积过渡 rebalance"]
    N --> O[("RealmTerritoryMap")]
    N -. 调试旁路 .-> O1["territory_preview.png / repair log"]
  end

  subgraph T4["T4 城市种子名册"]
    O --> P["AI 先从单国候选选定唯一首都，再添加其他 CitySeed"]
    P --> Q{城市种子约束通过?}
    Q -- 否 --> Q1["T4 warning / hard block"]
    Q -- 是 --> R[("CitySeedRegistry")]
    P -. 调试旁路 .-> R1["city_seed_preview.png / city candidate packages"]
  end

  subgraph Score["验收评分"]
    R --> S["ScoreManifest"]
    S --> T{strict passed?}
    T -- 否 --> T1["acceptance_report.passed=false"]
    T -- 是 --> T2["acceptance_report.passed=true"]
  end

  M -. 已知过渡模型 .-> U["当前面积来自 quota；最终应改行动力 / 地形消耗 / wild land"]

  classDef data fill:#eef6ff,stroke:#4976a8,color:#1f2f3f;
  classDef debug fill:#fff7dc,stroke:#b58b00,color:#3d3000,stroke-dasharray: 4 3;
  classDef warn fill:#ffecec,stroke:#bb4b4b,color:#3d1111;
  class D,F,I,L,O,R,S data;
  class F1,I1,O1,R1 debug;
  class C1,K1,Q1,T1,U warn;
```

## 读图口径

- 实线是正式阶段数据流；虚线是调试 / 人工 review 旁路。
- `WorldSurveyResult.sealed=true` 是 T 阶段正式规划前置条件。
- 当前 T3 的 frontier 扩张已经修复连通性问题，但面积仍由 quota 过渡模型驱动；这不是最终行动力模型。
- T4 只生成 `CitySeedRegistry`，不创建城市实例，不进入 C 阶段内部规划。
