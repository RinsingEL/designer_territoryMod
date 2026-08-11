# City 当前故障修复案

本目录只保留尚未完成最终验收的当前问题。已完成或被实现替代的案件不留在 `40_tests/`，可复用结论写入实现仓库 `dev_docs/systems/city/故障索引.md`，历史过程从 Git 查询。

| 案件 | 状态 | 当前结论 |
| --- | --- | --- |
| [20260811 D6 续跑误重跑](./20260811_D6续跑误重跑.md) | 代码与聚焦回归已修复，待实机续跑复验 | Blueprint D4 以 accepted context 与 Blueprint hash 判断当前产物并遵守 `skipExisting`；D5/D6 保持完整来源校验，D6 具体失败原因提升至 workflow。 |
| [20260809 景观 Parcel 外轮廓近似固定](./20260809_景观Parcel外轮廓近似固定.md) | 代码与自动回归已修复，待新区块视觉验收 | 正式 Landscape 改用专用 frontier 外壳扩张；preferred 为正常目标、max 仅为硬上限，稳定 seed、地形、局部聚合和方向关系共同形成轮廓。 |
| [20260807 区域接力实际 Area 小于阶段数](./20260807_区域接力实际Area小于阶段数.md) | 代码已修复，待新区块复验 | Parcel 数已改为 Landscape/Group 总预算；core 先满足最小面积，fill 不足时零占地跳过。 |
