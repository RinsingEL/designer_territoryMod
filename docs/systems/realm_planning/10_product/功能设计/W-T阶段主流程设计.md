# W / T 阶段主流程设计

## 定位

本文记录国度规划系统 v1.1 的 W / T 主流程。它把 legacy W / T 中仍有价值的思路迁移到当前地貌驱动主线，但不兼容旧 T1 / T2 的选簇、选方向和 pending selection 流程。

主链：

```text
WorldSurveyContext
  -> WorldPatchMap
  -> RealmProfile
  -> RealmCandidateMapPackage
  -> RealmCoordinateSelection
  -> RealmSeed + CapitalCityIntent
  -> RealmTerritoryMap
  -> T4 AI 首都候选选址
  -> CitySeedRegistry
```

v1.1 已验证该主链可以在真实世界中端到端跑通。v1.2 在不改变阶段边界的前提下，补 W 粗扫质量、T3 连通国境、T4 城市种子分布和 `ScoreManifest` 质量阻断。

## 阶段总览

| 阶段 | 新方案职责 | 参考的 legacy | 处理方式 | 主要产物 |
| --- | --- | --- | --- | --- |
| W | 世界粗扫、大陆 / 海洋摘要、粗 Patch、候选图。 | `W3Stage`、`W4Stage`、`ClusterAnalyzer`。 | 复用聚类、摘要、预览图思路；重写数据来源和产物结构。 | `WorldSurveyContext`、`WorldPatchMap`。 |
| T1 | 生成国度设定，准备带网格坐标的候选图包。 | `T1Stage`、`TerritoryStageOrchestrator.runT1`。 | 不复用旧选簇；保留阶段产物和状态追踪思想。 | `RealmProfile`、`RealmCandidateMapPackage`。 |
| T2 | AI 从候选图直接选国度扩张核心，程序校验并落盘。 | `T2Stage`、`selectT2Direction`。 | 旧选方向废弃，改成直接坐标选择。 | `RealmCoordinateSelection`、`RealmSeed`、`CapitalCityIntent`。 |
| T3 | 多国度统一扩张。 | `T3Stage`、`TerritoryManager`。 | 复用算法思想；重写全局状态、snap、坐标换算和 artifact 边界。 | `RealmTerritoryMap`。 |
| T4 | 先由 AI 在单国 owned territory 候选中选定唯一首都，再生成城市名册和条件。 | `RealmT4PatchPlanningService`。 | 旧 T4 语义不匹配，不作为主线复用。 | `CitySeedRegistry`。 |

## Legacy 取舍表

| legacy 内容 | 当前拿什么 | 当前不要什么 |
| --- | --- | --- |
| W3 大陆 / 海洋聚类 | 大陆、海洋、区域摘要的思路。 | 旧 `ScanResultHolder` 作为全局真值。 |
| W4 地貌图集 | 地貌摘要、预览图、调试图思路。 | 旧 `regionCacheMap` 数据耦合。 |
| T1 / T2 | 分阶段产物、状态落盘、程序校验。 | AI 选簇、AI 选方向、Q1 / Q2 pending selection。 |
| T3 | 多源扩张、地形 cost、冲突解决。 | 静态全局状态、静默远距离 snap、负坐标整数截断风险。 |
| T4 | 全境地貌窗口可作为调试参考。 | 旧首都 bootstrap 语义，不能当作 CitySeedRegistry。 |

## T1 / T2 新分界

| 决策点 | 当前方案 | 理由 |
| --- | --- | --- |
| T1 结束条件 | 产出 `RealmProfile` 和 `RealmCandidateMapPackage`。 | T1 负责准备候选图和约束，不负责最终落点。 |
| T2 开始条件 | 候选图包可读，AI 可看到 grid 坐标。 | 让选点、校验、重试集中在同一阶段。 |
| AI 返回内容 | `gridX/gridZ`、备选坐标、选择理由。 | 图上更容易读，程序统一转换 block 坐标。 |
| 程序校验内容 | 维度、大陆、patch、禁用区、冲突距离、有限 snap。 | 旧流程容易把候选簇和方向选择拆碎，当前改成一个明确校验点。 |
| 失败处理 | 返回结构化失败原因，允许重试。 | 不再把无效点静默改写成另一个语义不同的点。 |

## 国度规模与扩张配置

MC 的理论世界边界不能作为国度比例分母。W / T 的面积比例只按本次 `WorldSurveyContext` 中目标大陆 / 目标大区的可分配 land cell 计算。

| 配置块 | 解决的问题 | 配置来源 | 程序处理 |
| --- | --- | --- | --- |
| `scalePlan` | 这个国度占多少。 | AI 可按叙事量级给初始比例。 | 按 `normalizationGroup` 归一化，clamp 到 min / max。 |
| `expansionStyle` | 这个国度往哪里长、形状像什么。 | AI 给语义化数值和枚举。 | 翻译为 T3 内部 cost profile。 |

`scalePlan.targetAreaRatio` 的分母建议为：

```text
targetContinentId 对应大陆内可分配 land cell 总数
```

如果同一大陆多个国度的 `targetAreaRatio` 总和不等于 `1.0`，程序必须归一化，并在 T3 摘要中记录归一化前后的值。

AI 可以配置 `scalePlan` 和 `expansionStyle`，但不直接配置 T3 的水体 cost、坡度 penalty、距离衰减、冲突规则等算法裸参数。

## 坐标体系

| 坐标 | 使用方 | 说明 |
| --- | --- | --- |
| `gridX/gridZ` | AI、人类 review、W / T 粗流程。 | 候选图上的粗格坐标，是 T 阶段主要交互坐标。 |
| `blockX/blockZ` | 程序、后续 C 阶段。 | Minecraft 世界方块坐标，由程序从 grid 坐标换算。 |
| `cellStepBlocks` | 程序和 manifest。 | 每个粗 grid cell 覆盖多少 block。来自 GIS step 参数化能力或 W 粗扫配置。 |
| `gridOriginBlock` | 程序和 manifest。 | grid 坐标原点对应的世界方块坐标。 |

转换必须由程序执行。AI 不直接返回大数字 block 坐标作为主输入。

## Snap 策略

| 情况 | 处理 |
| --- | --- |
| 坐标落在允许 patch 内 | 接受。 |
| 坐标距离合法 cell 不超过配置阈值 | 可有限 snap，并记录原坐标、目标坐标、距离和原因。 |
| 坐标跨大陆、跨海或跨禁用 patch | 拒绝，不自动修正。 |
| 坐标与已有国度种子冲突 | 拒绝或要求 AI 使用备选坐标。 |
| 候选图或 manifest 缺少坐标转换信息 | 阶段失败，不进入 T3。 |

默认建议：snap 半径不超过 1 到 2 个粗 cell。具体阈值需要在实现前与用户确认。

## T3 扩张原则

| 原则 | 说明 |
| --- | --- |
| 粗 cell 级扩张 | T3 先在 W 粗 cell 上分配国度范围，不生成 block 级边界。 |
| frontier 扩张 | 国度只能从已有边界向邻接 cell 扩张，不再用全图静态 cost 排序抢格子。 |
| edge cost | 山脉、水体、海岸、坡度和通行性优先表达为 cell 边穿越成本。 |
| 动态配额 | `scalePlan` 控制目标面积，quota urgency 只影响扩张轮次，不破坏连通约束。 |
| per-job 状态 | 不保留 legacy `TerritoryManager` 式全局静态运行状态。 |
| floor 坐标语义 | 负坐标下 grid / block 换算必须使用 floor 语义，不能依赖整数截断。 |
| 显式异常 | 飞地、空洞、跨海扩张、面积过小等异常必须记录到结果摘要。 |
| 拓扑修复 | 默认修复非海权国小飞地和小孔洞；边界平滑不能跨强自然屏障。 |
| 策略待定 | 是否允许 wild land、海权 bridgehead 数量、山脉和水体 cost 默认值需要实现前再讨论。 |

## T4 CitySeedRegistry 原则

| 原则 | 说明 |
| --- | --- |
| 只登记城市 | T4 不创建城市实例，不生成边界、道路、功能区或结构落点。 |
| 城市存在性前置 | T4 决定有限城市是否存在，不能把有限城市名额留给 C 阶段按 chunk 加载顺序抢占。 |
| 首都必定存在 | `CapitalCityIntent` 必须在 T4 经 AI 候选选址转成恰好一座带追溯的 capital CitySeed。 |
| 单国度候选图 | T4 给 AI / 人类看的图应裁剪到单个国度及少量邻接上下文，避免整张世界图噪声干扰。 |
| 二级区域 | 城市候选应来自 macro patch、basin / corridor、边境带等二级区域，而不是全境取最高分。 |
| 空间约束 | 城市间使用规模半径、角色关系和国度内图距离约束，避免撞点和过度集中。 |
| 非首都可延迟触发 | 港口城、边境城、矿业城等可以由玩家接近、国度发展或剧情阶段触发。 |
| 稳定 ID | 每个 `CitySeed` 必须有稳定 ID，避免重复生成同一城市。 |
| 可追溯来源 | 每座城市要能追溯到国度、T3 范围、patch / 地理条件或叙事原因。 |

## 主流程验收

| 验收点 | 标准 |
| --- | --- |
| W 产物可追溯 | `WorldSurveyContext` 记录维度、seed、step、grid 原点和数据来源。 |
| W 分类质量 | `cliff` 不应作为大片主地貌；patch / continent 需经过清洗和跨 tile merge。 |
| 候选图可读 | `RealmCandidateMapPackage` 能说明 grid 坐标和 block 坐标换算。 |
| T2 可重试 | 非法坐标返回结构化原因，不直接进入 T3。 |
| T3 不串状态 | 不同 run、维度、大陆之间的扩张结果互不污染。 |
| T3 连通性 | 非海权国最大连通块比例、飞地面积、孔洞面积必须进入结果评分和阻断判断。 |
| T4 不越界 | `CitySeedRegistry` 不包含城市内部规划字段。 |
| T4 分布合理 | 城市锚点不得同格重叠，需满足规模半径、角色关系和图距离约束。 |

## W 大世界扫描口径

W 阶段的“整个世界”指配置指定的可规划世界范围，不等同于 Minecraft 理论最大世界边界。初始世界设定必须等待该配置范围完整扫描、tile 缓存写出、全局 patch 汇总完成，并把 `WorldSurveyContext` 标记为 sealed 后，才允许进入 T1 / T2 / T3 正式规划。

| 配置 / 状态 | 口径 |
| --- | --- |
| `planningRadiusBlocks` | 以扫描中心为原点的初始最大规划半径，默认建议 `8192`，可按存档目标调大。 |
| `cellStepBlocks` | W 粗 cell 步长，默认 `128`。该值与当前 GIS Region 的 `512 block` 尺寸整除，便于分片、缓存和预览。 |
| `microSampleStrideBlocks` | v1.2 feature 提取步长，建议 `16` 或 `32`，用于在 128 block planning cell 内生成稳健统计。 |
| `resumePolicy` | `use_cache` 复用已完成 tile，`rescan` 强制重扫，`use_cache_strict` 遇到损坏缓存直接失败。 |
| `WorldSurveyJob` | 按 GIS Region / W tile 枚举扫描任务，逐 tile 采样、分类、patch，并写入 tile cache。 |
| `world_survey_manifest.json` | 记录扫描范围、step、tile 状态、用时、缓存命中、数据量和 sealed 状态。 |
| `score_manifest.json` | 记录 W / T3 / T4 质量评分、硬阻断和人工 review 清单。 |

W 扫描过程中可以输出临时 preview 供人工观察，但 T 阶段只消费 sealed survey。这样可以保证国度比例分母、大陆 / patch id、AI 候选图和 T3 扩张范围都基于同一张完整世界底图。

v1.2 中，W 的 planning cell 尺度和 feature 提取尺度分离：`cellStepBlocks=128` 面向 T 阶段规划，micro-sampling 面向地貌统计、屏障边和 patch 清洗。
