# GIS 主流程图

本文只描述 GIS 的主链路：它如何从一次范围刷新请求，生成可缓存、可预览、可被规划系统消费的地貌事实。

```mermaid
flowchart TD
  A["刷新入口<br/>玩家位置 / 调试中心 / 规划中心"] --> B["创建 RefreshJob<br/>中心点 + 区块半径 + 预算"]
  B --> C["计算刷新范围<br/>稳定区 + 依赖边界"]
  C --> D["划分 AtlasRegion<br/>按固定区块范围组织缓存"]
  D --> E["生成 AtlasCell 网格<br/>默认 4x4 blocks 一个 Cell"]

  E --> F["基础采样层"]
  F --> F1["高度<br/>WORLD_SURFACE_WG"]
  F --> F2["水体 / 水深<br/>WORLD_SURFACE_WG + OCEAN_FLOOR_WG"]
  F --> F3["生物群系 / 表面类型"]

  F1 --> G["指标计算层"]
  F2 --> G
  F3 --> G
  G --> G1["小邻域指标<br/>坡度 / 局部起伏 / 粗糙度"]
  G --> G2["TPI 指标<br/>小尺度 TPI / 大尺度 TPI"]
  G --> G3["水距与可建性<br/>waterDistance / buildability"]

  G1 --> H["Cell 级地貌分类"]
  G2 --> H
  G3 --> H
  H --> H1["water / shore"]
  H --> H2["plain / terrace / slope / cliff"]
  H --> H3["ridge / valley / basin / unknown"]

  H1 --> I["合并 LandformPatch"]
  H2 --> I
  H3 --> I
  I --> J["写入 Atlas 缓存<br/>Cell + Region + Patch + 状态标记"]

  J --> K["调试输出"]
  K --> K1["PreviewManifest"]
  K --> K2["高度 / 坡度 / TPI / 地貌 / 可建性图"]

  J --> L["GIS 查询接口"]
  L --> M1["City<br/>选址 / 可建区 / 临水评价"]
  L --> M2["Roads<br/>代价 / 避障 / 谷地与岸线走廊"]
  L --> M3["Realm<br/>天然边界 / 势力范围"]
  L --> M4["Structure<br/>结构偏好地貌 / 落点筛选"]
```

## 读图说明

GIS 的输入不是“生成城市”，而是一次地貌事实刷新请求。刷新请求会先拆成 `RefreshJob`，再按半径计算稳定区和依赖边界。稳定区给消费者使用，依赖边界主要用于 TPI、水距等邻域指标，避免边缘 Cell 误判。

`AtlasCell` 是整条链路的最小数据单元。它把 Minecraft 方块世界压缩成固定步长的栅格，首版建议 `4x4 blocks = 1 Cell`。后续坡度、TPI、可建性和地貌分类都基于 Cell 计算，而不是让每个消费者重复逐方块扫描。

指标层分两类：小邻域指标适合快速判断坡度和破碎程度，大邻域指标适合判断山脊、谷地、盆地、台地等区域地貌。依赖数据不足的 Cell 必须保留状态标记，例如 `edgeDirty`，不能假装已经稳定。

地貌分类先在 Cell 级完成，再合并成 `LandformPatch`。消费者优先查询 Patch，因为城市、道路、国度边界和结构分布更关心连续区域，而不是单个离散 Cell。

调试输出和查询接口是同一份 Atlas 的两个出口：调试图用于人工验收和阈值校准，查询接口用于后续系统消费。两者都不应该绕过 Atlas 重新扫描世界。

