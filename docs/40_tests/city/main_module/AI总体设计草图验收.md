# AI 总体设计草图验收

## 验收目标

验证 AI 总体设计草图路线是否能替代旧 C3 数学随机多边形与 C6 矩形槽位主导的设计方式，同时保留程序查错和 C8/Jigsaw 生长能力。

## 输入样例

- `C2_satellite_preview.png`
- `C2_satellite_hillshade.png`
- `C2_satellite_roughness.png`
- 城市中心与目标规模
- 坐标网格、比例尺、图例和允许范围

## 必验项

| 编号 | 项目 | 验收方式 | 通过标准 |
| --- | --- | --- | --- |
| A1 | 地形一致性 | 对比 C2 底图与 AI 草图 | 海岸、水体、主要地形边界不应明显漂移 |
| A2 | 城市轮廓 | 人工查看草图 | 外轮廓不再呈强 chunk 方格扩张感 |
| A3 | 层级比例 | 检查 validator 报告 | core / urban / transition 不应出现明显挤压或失衡 |
| A4 | 留白 | 人工查看与 JSON 检查 | 水岸、陡坡、狭窄地应允许保留，不强行填满 |
| A5 | 查错 | 构造压水/越界草图 | validator 必须返回 blocking error 或 warning |
| A6 | 矢量化 | 读取 `C3_design_regions.json` | 区域、道路、保留区能被结构化表达 |
| A7 | C8 衔接 | 使用 group intent 进入 C8 | C8 能读取约束和意图，但不被矩形槽位锁死 |

## 人工审核问题

- 城市是否有清晰中心感？
- 主城区是否有自然展开空间？
- 过渡区是否真正包裹/缓冲主城区？
- 海岸线是否被合理利用或保留？
- 是否出现“漂亮但不可建”的区域？
- 是否还有 C3/C6 那种数学碎片和矩形槽位感？

## 阻塞条件

出现以下任一情况，不得进入后续 C8/Jigsaw 主链：

- 草图坐标系与 C2 明显不一致
- 核心区域大面积压水或越界
- 主城区被切成大量不可用碎片
- 过渡区占比极低且 validator 无提示
- 道路骨架跨越明显不可通行区域且无替代路线
- `design_regions.json` 缺少可用 group intent

## 产物要求

- `C3_design_sketch.png`
- `C3_semantic_mask.png`
- `C3_design_regions.json`
- `C3_validation_report.json`
- 人工审核记录
