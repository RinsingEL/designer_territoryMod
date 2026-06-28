# City 案子：Road Weaver 结构连接 v0.1

## 定位

本案用于把结构之间的道路连接交给成熟道路生成能力处理。City 不重新发明完整道路生成算法，只输出结构 anchor、入口、连接意图和约束。

## 核心目标

- 结构落地后，结构之间能形成自然连接。
- D5 / D7 当前道路后处理保留为调试路径。
- 后续接入 Road Weaver 或同类辅助 mod，处理真实道路曲线、坡度、桥、岸线等问题。

## City 输出给 Road Weaver 的信息

- structure anchor。
- actual bbox / maskEnvelope。
- entrance candidates。
- roadAccessIntent。
- D3 地形 patch、坡度、水岸、禁行区域。
- noVegetationMask / noVanillaStructureMask。
- 已有道路或桥梁片段。

## 初版流程

```text
D6/D7 worldgen ledger
  -> actual bbox / pieces
  -> infer entrance candidates
  -> build road connection graph
  -> call Road Weaver
  -> road ledger / preview
```

## 接入边界

City 负责：

- 确定哪些结构需要连。
- 给出入口、优先级、不可穿越区域。
- 记录 road trace 和验收结果。

Road Weaver 负责：

- 路径规划。
- 地表铺装。
- 坡度 / 水体 / 桥梁适配。
- 道路装饰。

## 验收

- Road Weaver 不会穿过结构 actual bbox。
- Road Weaver 不会破坏 D5 mask 或 planned structure registry。
- 道路连接能解释来源：行政到港口主轴、居住支路、农业支路等。
- 失败时返回明确 reason，而不是回退到直线 gravel 路。

## 暂不处理

- 不在本案实现 Road Weaver 本体。
- 不定义最终道路美术。
- 不做玩家导航 AI。

## 待定

- 选用哪个具体道路辅助 mod。
- Road Weaver 调用方式：API、数据包、命令、MCP 还是文件协议。
- 是否需要 Road Weaver 的 non-mutating preview。
