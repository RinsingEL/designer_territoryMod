# GIS G1-G7 设计 Review 流程图

本文给人工 review 整体流程设计使用。G 编号沿用 `../../10_product/开发计划.md` 的阶段名；箭头表达运行时数据流和验收流，不要求 G 编号本身等同于严格调用顺序。

节点以中文过程为主，保留 `AtlasCell`、`AtlasRegion`、`RefreshJob`、`LandformPatch`、`PreviewManifest` 等数据结构英文名。若要看具体代码调用链，读 `GIS刷新代码流程图.md`。

```mermaid
flowchart TD
  Start(["接收 GIS 刷新请求<br/>玩家位置 / 调试中心 / 规划中心"])

  subgraph G4["G4 半径刷新与缓存"]
    G4A[(创建 RefreshJob)]
    G4B["解析中心点、维度和半径"]
    G4C["规划稳定区与依赖边界"]
    G4D["按 ring 推进刷新进度"]
    G4E[(更新 AtlasRegion 状态)]
    G4F[(写入 region_snapshot.json<br/>测试复现 / 现场还原)]
  end

  subgraph G1["G1 基础采样"]
    G1A[(创建或读取 AtlasRegion)]
    G1B[(生成 AtlasCell 网格)]
    G1C["读取生成器高度"]
    G1D["判断水体、水深和表面类型"]
    G1E["读取生物群系"]
    G1F[(写入 AtlasCell 基础事实)]
  end

  subgraph G2["G2 指标层"]
    G2A["计算坡度"]
    G2B["计算局部起伏与粗糙度"]
    G2C["计算小尺度 / 大尺度 TPI"]
    G2D["传播水距"]
    G2E["标记边界不稳定 Cell<br/>edgeDirty"]
  end

  subgraph G3["G3 地貌分类"]
    G3A["水体与岸线优先"]
    G3B["识别悬崖、山脊、谷地、盆地"]
    G3C["识别平原、台地、坡地"]
    G3D[(写入 landformType)]
    G3E["合并相邻同类 Cell"]
    G3F[(生成 LandformPatch 列表)]
    G3G["标记 fragment / edgeDirty / crossRegionCandidate"]
  end

  subgraph G5["G5 运行中进度预览"]
    G5A["按阶段输出进度"]
    G5B[(progress_manifest.json)]
    G5C["progress.png"]
  end

  subgraph G6["G6 调试预览"]
    G6A[(生成 PreviewManifest)]
    G6B["导出高度图"]
    G6C["导出水体 / 坡度 / TPI 图"]
    G6D["导出地貌图"]
    G6E["导出 Patch 调试图"]
  end

  subgraph G7["G7 自动测试与验收报告"]
    G7A["通过命令、HTTP 或 MCP 触发"]
    G7B["运行固定样例或真实世界 refresh"]
    G7C[(生成 test_report.json)]
    G7D["检查 preview、progress 和统计"]
  end

  subgraph G8["G8 消费者接入（不在当前目标）"]
    G8A["City 读取地貌事实"]
    G8B["Roads 读取代价与走廊"]
    G8C["Realm 读取天然边界"]
    G8D["Structure 读取结构偏好地貌"]
  end

  Start --> G4A --> G4B --> G4C
  G4C --> G1A --> G1B --> G1C --> G1D --> G1E --> G1F
  G1F --> G2A --> G2B --> G2C --> G2D --> G2E
  G2E --> G3A --> G3B --> G3C --> G3D --> G3E --> G3F --> G3G
  G3F --> G4E
  G4C --> G4D

  G4D -.-> G5A
  G4E -.-> G5A
  G5A --> G5B --> G5C

  G3F -.-> G6A
  G6A --> G6B
  G6A --> G6C
  G6A --> G6D
  G6A --> G6E

  G7A --> G7B --> Start
  G7B -.-> G7C
  G7B -.-> G7D
  G4E -.-> G4F
  G6A -.-> G7D
  G5B -.-> G7D

  G3F -.->|未来正式查询| G8A
  G3F -.->|未来正式查询| G8B
  G3F -.->|未来正式查询| G8C
  G3F -.->|未来正式查询| G8D

  classDef future fill:#eeeeee,stroke:#999999,color:#777777,stroke-dasharray: 5 5;
  class G8A,G8B,G8C,G8D future;
  style G8 fill:#eeeeee,stroke:#999999,color:#777777,stroke-dasharray: 5 5
```

## Review 读图口径

- G 编号来自开发计划，方便按阶段验收；箭头表达数据和验收如何流动。
- 看设计阶段是否漏了 G1-G7 中任一必要产物。
- 看某个改动是否跨阶段写错责任，例如在 G1 采样阶段做 G3 分类。
- 看调试旁路是否只用于验收和复现，不能回写成生产主数据。
- 看 G8 是否仍保持未来边界；当前 GIS v1 不要求消费者正式接入。
- 数据结构节点保留英文名，用来和契约文件、报告字段、代码对象对应。

## 当前特别注意

- G4 的 `region_snapshot.json` 是轻量快照，只服务测试复现和现场还原，不是完整生产级 SavedData 或二进制长期持久层。
- G3 当前已包含 `LandformPatch` 合并；实现中 `PatchMerger` 仍只做同类型四邻接合并。
- G6 的 patch 图当前是调试证据，不是 Patch 几何真值。
