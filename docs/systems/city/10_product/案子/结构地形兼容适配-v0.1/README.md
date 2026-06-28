# City 案子：结构地形兼容适配 v0.1

## 定位

本案处理结构落地后的地形融合问题。植被穿结构的问题已经通过生成期 mask 解决；下一类问题是结构悬空、硬切、浮空岛、底部不贴地等地形兼容问题。

本案倾向优先评估依赖成熟结构地形兼容 mod，不急着在 City 内部自研完整 terraforming。

## 核心目标

- 结构仍然走 worldgen-time placement，不回退到 late paste。
- D6 preflight 后知道 actual bbox / piece boxes。
- 结构落地前后能生成台基、削坡、填土或过渡地形。
- 对 Trek 这类落地适配较弱的结构包，提供可验收的地形融合方案。

## 问题类型

- 建筑部分悬空。
- 结构底部切出浮空岛。
- 道路悬空或断崖。
- 结构跨水岸时没有码头 / 支撑。
- 大型结构压在陡坡上导致视觉割裂。

## 初版策略

优先顺序：

1. 调研并接入成熟结构地形兼容 mod。
2. 如果外部能力可用，City 输出 bbox、height sample、desired foundation policy。
3. 如果外部能力不足，再补最小自研适配：
   - bbox 下方填土 / 石基。
   - 入口到地面的短坡道。
   - 边缘过渡带。
   - 水岸结构的桩基 / 码头基础。

## 数据输入

- D3 高度、坡度、水体、地形 patch。
- D4 anchor、maskEnvelope、roadAccessIntent。
- D6 actual bbox、piece boxes、expected signature。
- worldgen ledger。
- Road Weaver 道路结果。

## 验收

- 不再出现明显树上房子；该问题由 D5 mask 继续兜住。
- 悬空结构数量明显下降。
- 地形适配不会让结构 bbox 越界或撞上其他结构。
- 适配 trace 能说明每个结构使用了哪种 policy。
- 如果依赖 mod 不可用，必须 hard fail 或退回明确调试状态，不静默伪装成功。

## 暂不处理

- 不做完整世界地形重写。
- 不让地形适配改变结构选择逻辑。
- 不恢复 late structure paste 作为正式路径。

## 待定

- 选择哪个结构地形兼容 mod。
- 地形适配发生在 worldgen 哪个阶段。
- 是否按结构 profile 标注 foundation policy。
- 对水岸 / 城墙 / 桥梁是否需要独立适配策略。
