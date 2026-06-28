# City 案子：城市边界与城墙 v0.1

## 定位

本案处理结构落地后的城市边界表达。当前阶段边界可以继续使用道路 / mask / preview 范围；后续逐步替换为更有城市感的城墙、栅栏、挡墙、码头线或自然边界。

## 核心目标

- 不回到旧式“先画功能区硬边界再塞结构”。
- 边界由已规划结构、reservation mask、道路连接和地形共同反推。
- 初期保留当前道路边界作为调试表达。
- 后续可将部分边界升级为城墙或其他主题边界。

## 边界来源

- 结构 `maskEnvelope` 的并集。
- 道路 corridor。
- 水岸 / 山脊 / 崖壁等 D3 地形 patch 边缘。
- 结构群之间的功能归类结果。
- noVegetation / noVanillaStructure mask。

## 初版策略

```text
placed structures
  -> union(maskEnvelope + road corridor)
  -> simplify boundary
  -> classify boundary segment
  -> debug road / gravel / marker
```

边界类型先只分：

- 调试道路边界
- 水岸边界
- 山体 / 崖壁边界
- 开放农田边界
- 预留城墙边界

## 城墙升级方向

当结构密度、Road Weaver 和地形适配稳定后，再把部分边界替换为：

- 城墙
- 木栅栏
- 农田篱笆
- 码头岸线
- 山体挡墙
- 城门 / 门楼

## 验收

- 边界不会先于结构决定城市形状。
- preview 能显示边界来源：结构、道路、水岸、地形。
- 边界不会穿过结构 actual bbox。
- 调试道路边界可被后续城墙系统替换，不写死为最终城市形态。

## 暂不处理

- 不生成完整城墙。
- 不处理复杂城门寻路。
- 不做军事防御逻辑。
- 不把边界当作功能区硬边界。

## 待定

- 城墙结构来源：自建模板、Trek、其他结构包或专用 mod。
- 边界简化算法。
- 水岸边界和港口码头的优先级。
