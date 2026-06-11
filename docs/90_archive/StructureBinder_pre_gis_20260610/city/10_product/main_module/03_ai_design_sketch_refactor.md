# AI 总体设计草图重构方案

## 定位

本方案用于重构城市生成主链的上游设计方式：

- 保留总体设计图能力
- 降低 `C3` 数学随机多边形、`C6` 矩形槽位、`C7` 厚排列语义对城市想象力的限制
- 引入 AI 图像模型基于地形底图生成城市总体设计草图
- 程序负责矢量化、查错、约束校验和运行时落地

本方案是产品级重构方向，不直接改变当前代码契约。

## 背景问题

当前城市主链中，早期阶段已经承担过多硬决策：

- `C1 / createCity` 在城市创建时直接从中心点按 chunk 泛洪扩张，形成 `claimedChunks` 与层级边界
- 当前扩张口径强依赖网格与 4 方向邻接，城市外轮廓容易出现方正、折线感强的问题
- `C3` 将城市区域继续切成大量数学多边形，但这些多边形不理解城市构图、海岸、山脊、入口、视线或留白
- `C5` 合组只能在随机/数学碎片上做补救
- `C6` 继续生成矩形 placement / rect guidance，容易把自然地形压扁成施工槽位
- `C7` 仍保留 `arrangement_type`、`linear / courtyard / spine_branch / cluster` 等厚语义，提前替城市决定局部组织方式
- 下游 `C8 / Jigsaw` 已经具备更真实的 connector、bounds、碰撞、地形和执行证据链，上游硬布局反而变成负担

因此，重构目标不是取消总体设计，而是把总体设计从“数学切块 + 矩形排布”改成“AI 草图 + 程序查错 + Jigsaw 生长”。

## OpenAI 图像模型使用口径

OpenAI 官方 API 文档中，`gpt-image-2` 是最新图像生成模型，支持基于文本与图像输入进行高质量图像生成与编辑，并提供尺寸、质量、背景、压缩等控制参数。

在本项目中，图像模型只承担以下职责：

- 根据 `C2` 地形底图、坐标网格、图例和约束，生成城市总体设计草图
- 保持地形底图与坐标系的一致性，输出适合程序后处理的色块/线稿/标注图
- 表达宏观城市构图，例如核心、主城区、过渡区、港口、道路骨架、广场、留白、禁建区

图像模型不承担以下职责：

- 不直接产出未经校验的最终城市真值
- 不直接决定 Minecraft 结构模板的精确坐标
- 不绕过 polygon、bounds、collision、terrain、sovereignty 等程序校验
- 不代替 `C8 / Jigsaw` 的真实拼接与执行层验证

## 新阶段职责

### C1：选址与城市参数

`C1` 从“直接配置 + 程序扩张”调整为“AI 看图选址 + 程序查错”的入口阶段。

保留：

- `territory_id`
- `center_x / center_z`
- `targetChunkCount`
- `bias`
- `ecology`
- `density`
- `layers[]`

调整：

- 程序先输出选址预览图、坐标网格和已有城市/国境/水域/坡地信息
- AI 基于图像一次性选择城市中心与大致规模
- 程序校验中心点是否越界、重水域、离其他城市过近或与已有城市重叠
- 原 `expandCity` 结果不再视为不可挑战的城市构图真值，而是候选占地或 fallback

### C2：地形底图与可视化输入

`C2` 继续保留，并成为 AI 设计草图的主要输入。

必须输出：

- 卫星地形图
- 水体 / 海岸信息
- 高度或 hillshade
- roughness / 坡度提示
- 坐标网格与比例尺
- 当前城市候选边界或可用范围

`C2` 不负责决定城市分区，只负责生成足够清晰的视觉底图。

### C3：AI 总体设计草图

`C3` 从“数学随机 polygon segmentation”改为“AI city composition sketch”。

输入：

- `C2_satellite_preview.png`
- `C2_satellite_hillshade.png`
- `C2_satellite_roughness.png`
- 城市中心、目标规模、国境/可用范围
- 设计规则 prompt

输出：

- `C3_design_sketch.png`
- `C3_semantic_mask.png`
- `C3_design_regions.json`
- `C3_validation_report.json`

建议颜色语义：

| 图层 | 含义 |
| --- | --- |
| core | 核心区、中心广场、主公共空间 |
| urban | 主城区、主要建筑生长区 |
| transition | 过渡区、低密度外缘、农田/林地/边缘街区 |
| road_spine | 主道路骨架或路径意图 |
| plaza | 广场、留白、视觉节点 |
| waterfront | 滨水利用区、码头、港湾 |
| preserve | 保留地形、树林、水岸、禁建或低干预区 |

C3 的真值不是“图像像素本身”，而是程序从图像中矢量化并通过校验后的 `design_regions.json`。

### C4：功能意图轻量化

`C4` 不再给大量数学多边形逐个分配功能，而是对 `C3_design_regions` 做轻量注释：

- 主功能倾向
- 风格关键词
- 人流/物流/防御/市场/住宅等宏观关系
- 不超过必要数量的区域标签

C4 不应制造新的碎片区域。

### C5：组团整理与矢量修正

`C5` 从“合并随机 polygon”改为“清理 AI 草图矢量化结果”。

职责：

- 合并过小碎片
- 消除过细长区域
- 修正越界、水上、陡坡和不可建区域
- 保留必要留白
- 生成供 C8 使用的 `group_intent`

C5 应输出“可用组团”，不是最终建筑槽位。

### C6：可建约束图

`C6` 降级为约束层，不再主导矩形 placement。

保留输出：

- 可建 area block
- 禁建区
- 地形风险区
- 推荐入口带
- 推荐扩展方向
- 面积预算与密度预算

降级输出：

- `rect_sizes`
- `rect_guidance`
- 多矩形 placement 主方案

这些字段可在迁移期保留兼容，但不再作为 C8/Jigsaw 的主输入。

### C7：导演意图与工头计划

`C7` 从“排列方式枚举器”改为“导演意图卡”。

应保留：

- group 目标
- 风格倾向
- 节奏和密度
- 最大节点数 / 分支预算
- 起点意图
- 是否靠水、靠路、留白、压缩或扩张
- 推荐结构族或模板池

应降级：

- `arrangement_type`
- `linear / courtyard / spine_branch / cluster`
- 预先生成的多节点坐标链
- 对 child 节点的长期手工 `x / z`

### C8：AI 决策 + 程序求解

`C8` 成为局部生长主阶段。

职责：

- AI 决定当前节点下一步意图
- 程序通过 connector / jigsaw / bounds / collision / terrain 校验找到合法落点
- 失败时回包可解释拒绝原因
- 成功时写入 validated node，并可进入 C9

C8 可以读取 C3/C5/C6/C7 的意图和约束，但不被它们的旧矩形槽位锁死。

### C9：执行层

`C9` 保持当前边界：

- 只消费已校验节点
- 负责地形准备、结构放置、jigsaw final_state 收口、执行证据
- 不重新随机选择下一个结构
- 不接管城市设计决策

## 新数据产物

### C3_design_regions.json

建议结构：

```json
{
  "step": "C3_AI_DESIGN_SKETCH",
  "city_id": "city_3120_-3200",
  "source_images": [
    "C2_satellite_preview.png",
    "C2_satellite_hillshade.png",
    "C2_satellite_roughness.png"
  ],
  "model": "gpt-image-2",
  "regions": [
    {
      "region_id": "core_01",
      "semantic_type": "core",
      "polygon": [[3120, -3230], [3140, -3230]],
      "confidence": 0.82,
      "design_notes": "靠近南侧海湾上方的中心公共空间",
      "validation": {
        "inside_allowed_area": true,
        "water_overlap_ratio": 0.0,
        "roughness_risk": "low",
        "too_small": false,
        "too_thin": false
      }
    }
  ],
  "roads": [],
  "preserve_areas": [],
  "validation_summary": {
    "status": "needs_review",
    "blocking_errors": [],
    "warnings": []
  }
}
```

### group_intent.json

建议结构：

```json
{
  "group_id": "g_market_03",
  "source_region_ids": ["urban_02", "waterfront_01"],
  "intent": {
    "theme": "滨水市场",
    "density": "medium",
    "growth_style": "organic_jigsaw_growth",
    "entry_band": "south_waterfront",
    "max_nodes": 8,
    "branch_budget": 2,
    "preserve_notes": ["保留海湾边缘留白"]
  },
  "constraints": {
    "allowed_polygon": [],
    "avoid_polygons": [],
    "preferred_directions": ["north", "east"],
    "waterfront_sensitive": true
  }
}
```

## 校验规则

程序必须校验：

- AI 草图是否超出城市允许范围
- 区域是否压水、压陡坡或压禁建区
- 区域是否太碎、太小、太细长
- 核心/主城/过渡区比例是否异常
- 过渡区是否完全被挤压
- 道路骨架是否跨越不可通行地形
- 是否保留足够留白
- 是否能给 C8 提供入口带和扩展方向

建议阈值：

- core：目标占比 15% 到 30%
- urban：目标占比 35% 到 55%
- transition / preserve：目标占比 20% 到 40%
- 单区域最小面积：不低于可配置阈值
- 细长比：超过阈值则要求合并或简化

这些阈值只作为 validator 的默认建议，不应再次变成硬编码城市风格答案。

## 人工审核点

AI 草图生成后，应暂停并要求人工查看：

- 总体轮廓是否自然
- 核心区是否有城市中心感
- 主城区是否有足够展开空间
- 过渡区是否真的承担外缘和低密度缓冲
- 是否误占水体、陡坡或狭窄碎地
- 是否符合当前城市主题

审核通过后再进入 C4/C5/C6 的结构化处理。

## 迁移策略

### 第一阶段：文档和双轨产物

- 保留当前 C1-C9 代码主链
- 新增 C3 AI 草图方案文档与样例产物格式
- 允许同一个城市同时保存旧 `C3_polygon_preview` 和新 `C3_design_sketch`
- 不改变 C8/C9 运行时契约

### 第二阶段：C3 新入口

- 新增 C3 AI 草图生成/导入入口
- 程序读取 AI 草图并矢量化为 `design_regions.json`
- Validator 给出 blocking errors / warnings
- 旧数学 polygon segmentation 作为 fallback

### 第三阶段：C6/C7 减负

- C6 输出可建约束图，不再默认生成矩形槽位主方案
- C7 输出导演意图卡，不再默认依赖 `arrangement_type`
- C8 从 `group_intent` 和 constraints 中读取边界与预算

### 第四阶段：主链切换

- 默认流程切到 AI 草图路线
- 旧 C3/C6/C7 厚语义保留为 debug/fallback
- 对外文档更新契约与测试入口

## 不做的事情

- 不让图像模型直接生成最终 Java 结构队列
- 不把 AI 草图像素直接当作不可质疑的真值
- 不绕过运行时 jigsaw 真值
- 不取消 C8/C9 的程序校验
- 不在第一阶段删除旧 C3/C6/C7 产物

## 验收标准

- 给定 `C2_satellite_preview.png`，能产出一张可人工审阅的城市总体设计草图
- 草图能保持坐标网格、地形底图和图例基本一致
- 程序能从草图中提取区域、道路、保留区并生成 JSON
- Validator 能拒绝明显越界、压水、过碎、过窄、比例异常的草图
- C6/C7 不再强迫城市进入固定矩形/排列语义
- C8/Jigsaw 能在 group 约束内继续自由生长并输出可解释失败原因

## 当前建议结论

城市系统需要总体设计图，但总体设计图不应由随机 polygon 和矩形槽位主导。更合适的方向是：

```text
C1 AI 看图选址
-> C2 地形底图
-> C3 AI 总体设计草图
-> C5/C6 程序矢量化与查错
-> C7 导演意图卡
-> C8/Jigsaw 局部生长
-> C9 执行落地
```

这条路线能保留城市构图能力，同时把程序从“提前替城市决定形态”改回“校验、约束、解释和执行”。
