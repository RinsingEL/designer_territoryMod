# City 故障修复案

## 定位

本目录记录已经复现、正在定位或等待排期的 City 缺陷。它用于沉淀现象、证据、排查过程和待确认的修复方向；实现仓库的 `dev_docs/systems/city/故障索引.md` 仍记录可复用的故障摘要。

已完成修复后，应同步更新对应的契约、代码导览、测试入口和故障索引；本目录中的方案不能单独覆盖这些真值文档。

## 案件

| 案件 | 状态 | 结论 |
| --- | --- | --- |
| [20260722 LandUse Owner 事务失败粒度过大](./20260722_LandUseOwner事务失败粒度过大.md) | 已修复，待新区块实机复验 | placement 内容不适配改为跨 owner 共享 fallback，系统错误仍保持 owner 硬失败；水槽 prefab 是本次复现场景。 |
| [20260717 模板 worldgen 高度 datum 暂不可用](./20260717_模板worldgen高度datum暂不可用.md) | 已定位，未修复 | 跨 chunk 的固定模板在部分 owner 的 `FEATURES` 回调中无法读取可靠高度 datum，执行层因保护逻辑跳过写入；手动模板验证地形和 NBT 均可用。 |
| [20260717 旋转模板 pivot 与规划几何错位导致分片裁剪](./20260717_旋转模板pivot与规划几何错位导致分片裁剪.md) | 已定位，未修复 | D4/D6 的归一化旋转坐标与 worldgen 写入器额外设置的 Minecraft rotation pivot 不一致；实际模板向旋转前轴负方向平移后落在 planned owner fragment 外，因而被裁成局部。道路穿楼是独立风险，不是本案主因。 |
| [20260720 LandUse 栅栏 WorldGenRegion 半连接](./20260720_LandUse栅栏WorldGenRegion半连接.md) | 已修复，待新区块实机复验 | 第一次修复依赖 `UPDATE_ALL` 反向通知，但 `WorldGenRegion#setBlock` 忽略 flags；现改为显式水平连接回刷和失败快照恢复。 |
