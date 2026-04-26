# C阶段 AI 总规大重构验收

## 验收目标

验证 C 阶段 AI-first 总规路线是否能让 AI 直接产出城市边界、功能区和道路骨架，同时保证程序可以解析、校验、修复并衔接 C8/C9 落地。

## 必验项

| 编号 | 项目 | 验收方式 | 通过标准 |
| --- | --- | --- | --- |
| G1 | 底图可信 | 查看 `C1_design_base.png` 与 legend | 地形、海陆、高度、roughness、主权范围、已有城市和网格坐标清楚可辨 |
| G2 | AI 总规可读 | 查看 `C2_ai_masterplan_preview.png` | 边界、功能区、道路、保留区语义清楚，不依赖猜测 |
| G3 | 分层 mask | 读取 boundary / district / road mask | 固定颜色可解析，未知颜色不得静默通过 |
| G4 | 坐标一致 | 对比 mask 解析结果和 C1/C2 底图 | polygon / road 不应相对地形明显漂移 |
| G5 | 边界校验 | 构造越界边界 | validator 能裁剪、报错或要求 fallback |
| G6 | 地形校验 | 构造压水、压陡坡、断路样例 | 按城市设定输出 blocking error 或 risk warning |
| G7 | 道路连通 | 检查 `road_graph` | 主入口、核心区和主要 group 至少存在可解释连接 |
| G8 | group intent | 生成 `group_intent.json` | 每个可建 group 有 allowed polygon、入口、预算和主题 |
| G9 | C8 衔接 | 使用 group intent 进入 C8 | C8 能继续用 connector / jigsaw 求解，不依赖旧矩形槽位 |
| G10 | fallback | 禁用 AI 或导入坏图 | 能回退旧选簇/扩张路线，世界生成不中断 |

## 阻塞条件

出现以下任一情况不得进入 C8/C9 主链：

- AI 总规与底图坐标系明显不一致。
- `CityDesignPlan.json` 缺少可用 `boundary_polygon`。
- 核心区完全越界或完全不可建。
- 道路骨架无法连接任何入口与核心区。
- 功能区碎片过多，无法生成稳定 group intent。
- validator 未发现明显越界、压水或未知 mask 颜色。

## 人工审查点

- 城市轮廓是否比旧 chunk 扩张更自然。
- 功能区是否符合城市主题，而不是随机色块。
- 主道路是否顺应海岸、山脚、河流或平地。
- preserve / transition 是否真正承担留白和风险缓冲。
- 旧选簇 fallback 是否只在失败、小聚落或局部修复时出现。

## 第一批对照样例

使用 `city_3120_-3200` 作为第一批对照：

- 旧 C1 图：只有 chunk 草图，无地形底图。
- 旧 C2 图：有海陆、高度、网格和城市 chunk 叠加。
- 新目标：C1 底图包继承 C2/T4 地形语义；AI 总规图在同一坐标系下画边界、功能区和道路；程序解析后生成 `CityDesignPlan.json`。

## 产物要求

- `C1_design_base.png`
- `C1_design_base.legend.json`
- `C2_ai_masterplan_preview.png`
- `C2_boundary_mask.png`
- `C2_district_mask.png`
- `C2_road_mask.png`
- `CityDesignPlan.json`
- `CityDesignValidation.json`
- `group/<groupId>/group_intent.json`
