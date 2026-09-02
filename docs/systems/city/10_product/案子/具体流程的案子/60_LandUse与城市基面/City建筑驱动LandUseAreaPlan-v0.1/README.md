# City 建筑驱动 LandUse 与景观接力

## 状态

当前正式户外执行层。LandUse 在 D6 锁定建筑 footprint 后由 CityBlueprint `outdoorPlan` 编译，不恢复“先画功能区再塞建筑”的旧流程。

## 当前顺序

```text
D3 LandUseTerrainField
-> D4 CityBlueprint v0.12
-> D5 轻量 reservation
-> D6 lockedActualFootprint
-> 单一 Foundation
-> Landscape Parcels
-> SurfacePrintPlan v0.7
-> execute_d5 激活
-> FEATURES owner-chunk 执行
```

## Foundation 与 Landscape

程序先生成覆盖城市户外空间的连续 Foundation，再为每个 Landscape/Group 分配独立 Parcel。Landscape 使用 Group 总预算，不让核心建筑和每个子建筑分别取得一整份同等扩张额度。

核心 Parcel 先竞争空间，并必须达到配置的最小可执行面积；不足时规划明确失败。填充 Parcel 后进入，空间不足时允许零占地跳过，不得挤掉核心主题。景观 Parcel 保持独立，不因类型相同自动合并。

## 区域接力

景观填充只允许 `SINGLE_SOURCE_REGION_RELAY`：

1. 第一个区域从该 Parcel 内的稳定单源逐格扩张。
2. 后续区域从父区域的局部边界选择新起点，继续占用尚未分配的连通空间。
3. 每个阶段使用 Blueprint 选定 fill profile 中冻结的类型、权重、目标占比、层序列和内容白名单。
4. 相同输入、catalog、seed 和 D6 几何必须得到相同 source、region spans 与 parent trace。

禁止使用圆、菱形、矩形、全局距离环、固定宽同心带或几何 fallback。区域形状必须来自逐格生长、真实可用域和接力关系；owner chunk 只裁切已经冻结的全局 spans，不得各自重新起算。

## AI 与程序边界

AI 在 Blueprint 中选择 Foundation Profile、Landscape Profile、ParcelStyle 和 Landscape Fill Profile，并为允许的方案填写类型权重或目标占比。目录给出合法范围与示例，程序负责严格校验、稳定抽样、预算换算和实际扩张。AI 不提交逐格 mask、世界绝对坐标、固定图形或未登记算法。

农田应以耕地为主题，水、岸/半砖等作为间隔角色；花田可以组合多种花、树叶或其他登记内容；林场可以以树木随机散布为主，并穿插石子路、灌木等区域。具体材料和比例由本次冻结 profile 决定，不能硬编码成所有城市同一模板。

## SurfacePrint 与执行

`CityLandUseSurfacePrintPlan v0.7` 冻结 fill profile、稳定 seed、有序 region、角色 spans、接力 trace 与道路/建筑绿化/住宅外溢 `featureCells[]`。执行期按 owner chunk 建索引，先预检和快照，再写基础、overlay、道路与绿化地面、crop/plant/外溢边界、Area boundary；任一步失败按 owner 事务回滚，成功后才写 ledger。

建筑可以带可选的矩形绿化地块，但喷泉、广场等开放结构可以不带。绿化不得种满：必须从真实建筑入口留出连接实际街巷的连续引路；可使用自由式或田字式花纹，植物只能来自本城冻结 palette。AI 选中的填充住宅还可以向外阵列形成有明确边界、入口和内部道路的住宅子区；其边界由实际建筑与街巷形成，不得先画空壳区域。

正式 Blueprint 路径不生成自动连接 corridor、近邻桥线或 residual 补洞。LandUse 只执行 D4 已冻结、具有真实目的地的 City 自有 roads，不猜路线，也不得从距离或功能区关系自行生成连接。旧 chunk 不回填，停用 active plan 也不回滚已写世界。

## 硬边界

- D3 terrain field 只提供已有扫描事实，不为规划主动加载新区块。
- D6 `lockedActualFootprint` / collision / gate / reservation 是硬排除。
- Landscape 实际成员必须是连通逐格结果，不能用 bbox 填满或按 chunk 造型。
- 旧 SurfacePrint schema、active registry、ledger 或 completion 不迁移，必须清理后完整重规划。

## 验收重点

自动测试覆盖核心先行、填充可跳过、Group 总预算、区域连通、父子接力、稳定 seed、输入顺序扰动、跨 chunk 裁切、角色占比和 owner 回滚。人工预览重点检查是否仍出现固定圆/菱形、大片单色、重复等宽环、过窄通道，以及农田、花田、林场的主题和间隔是否可读。
