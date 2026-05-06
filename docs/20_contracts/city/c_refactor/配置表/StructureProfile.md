# StructureProfile 草案

## 定位

`StructureProfile` 是结构标记辅助 Mod 的目标结构画像。它在游戏或世界开始前离线生成，扩展当前结构池的 `function_candidates / style_score / weight_profile / tag_source` 思路，让结构搜索能从单标签过滤升级为权重召回。

## 顶层字段

| 字段 | 类型 | 来源 | 说明 |
| --- | --- | --- | --- |
| `structure_id` | string | 扫描 | 结构唯一编号 |
| `hard_facts` | object | 扫描/运行时 | 尺寸、footprint、connector、rotation 等事实 |
| `hard_constraints` | object | 扫描/规则 | 放置硬约束 |
| `function_affinity` | object | AI/人工 | 功能权重 |
| `style_affinity` | object | AI/人工 | 风格权重 |
| `placement_affinity` | object | AI/人工/程序 | 位置倾向 |
| `usage_affinity` | object | AI/人工 | 主建筑、次级建筑、装饰等用途倾向 |
| `tag_source` | object | 程序 | 来源、置信度、复核状态 |
| `evidence` | array | AI/人工 | 标注依据 |

## `hard_facts`

| 字段 | 说明 |
| --- | --- |
| `size` | length、width、height |
| `footprint` | min/max x/z |
| `connectors` | connector 列表 |
| `allowed_rotations` | 可旋转角度 |
| `piece_role` | START、SINGLE、MIDDLE、END 等 |
| `preset_pool` | 所属 pool |

这些字段不得由 AI 直接写为真值。

## `function_affinity`

示例：

```json
{
  "market": { "score": 0.85, "confidence": 0.8 },
  "residential": { "score": 0.35, "confidence": 0.6 },
  "civic_center": { "score": 0.2, "confidence": 0.5 }
}
```

搜索时建议使用：

```text
effective_score = score * confidence * source_weight
```

## `placement_affinity`

| 字段 | 说明 |
| --- | --- |
| `road_frontage` | 面向道路适配度 |
| `plaza_edge` | 广场边缘适配度 |
| `waterfront` | 临水适配度 |
| `corner` | 街角适配度 |
| `quiet_backstreet` | 背街或安静区域适配度 |
| `landmark_axis` | 城市轴线或地标视线适配度 |

这些字段是软倾向，不得覆盖硬约束。

## `tag_source`

| 字段 | 说明 |
| --- | --- |
| `scanner` | 是否来自扫描 |
| `ai_tagging` | 是否来自 AI 标注 |
| `manual_override` | 是否人工覆盖 |
| `heuristic` | 是否启发式猜测 |
| `review_state` | `pending`、`approved`、`rejected` |
| `confidence` | 总体置信度 |

## 搜索摘要字段

`structure_pool_search` 返回给 AI 的摘要建议包含：

| 字段 | 说明 |
| --- | --- |
| `template_id` | 结构编号 |
| `score` | 程序粗排分 |
| `why` | 命中原因 |
| `size` | 简化尺寸 |
| `role` | START、SINGLE 等 |
| `risks` | 主要风险 |
| `detail_ref` | 需要展开详情时使用 |

AI 默认只看摘要，只有少量候选进入 `structure_template_detail`。

## 生命周期

| 阶段 | 说明 |
| --- | --- |
| 开局前 | 扫描结构、AI 标注、人工复核、生成画像库 |
| C1-C2 | 不修改结构画像，只可读取结构池支持情况作为规划参考 |
| C7 | 查询画像库生成工头计划和候选结构池 |
| C8 | 按需读取结构详情进行放置和 jigsaw 求解 |
| C9 | 执行和复核，不参与结构标注 |
