# PreviewManifest 数据契约

PreviewManifest 是 GIS 调试预览输出的清单。它用于把预览图、配置版本、刷新范围和验收信息绑定在一起。

## 字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| manifestId | string | 本次预览输出标识。 |
| worldId | string | 世界或 seed 标识。 |
| dimensionId | string | Minecraft 维度。 |
| centerBlockX | int | 输出中心方块 X。 |
| centerBlockZ | int | 输出中心方块 Z。 |
| radiusChunks | int | 输出半径。 |
| cellStepBlocks | int | Cell 采样步长。 |
| atlasVersion | int | Atlas 数据格式版本。 |
| configVersion | string | 指标和分类配置版本。 |
| generatedAt | long | 生成时间。 |
| layers | PreviewLayer[] | 输出图层列表。 |
| hasEdgeDirty | boolean | 是否存在边缘脏区。 |
| unknownCellCount | int | 未分类 Cell 数量。 |
| notes | string | 人工备注。 |

## PreviewLayer

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| name | string | 图层名，例如 elevation、slope、landform。 |
| file | string | 图层文件路径。 |
| minValue | float | 数值图层最小值，可选。 |
| maxValue | float | 数值图层最大值，可选。 |
| palette | string | 使用的色带或分类调色板。 |

## 约束

- PreviewManifest 是调试和验收契约，不是主数据契约。
- 图层文件可以重建，Manifest 需要足够描述生成条件。
- 每次阈值调整后，Manifest 的 `configVersion` 必须变化或能追溯到配置变更。

