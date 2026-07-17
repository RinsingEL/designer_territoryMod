# City Decoration 分层内容契约 v0.4

## 范围

本契约扩展 `city_decoration_content_index` 与 DecorationProgram 的 palette slot，使一个几何 slot 可以按顺序放置多个内容层。它不改变 v0.3 的 Shape、Pattern、target、terrain policy 或 conflict policy。

## Catalog

`city_decoration_content_index.v0.4` 支持：

| `contentKind` | 必填字段 | 规则 |
| --- | --- | --- |
| `prefab` | v0.3 的 `nbtFile`、姿态与替换字段 | 继续由 NBT `StructureTemplate` 放置。 |
| `plant` | `blockState`、`support` | `blockState` 必须解析为 `CropBlock`；固定 `size=1x1x1`，不接受 `nbtFile`、实体、foundation 或 terrain fallback。 |

`plant.blockState` 为 block-state JSON，例如：

```json
{"Name":"minecraft:wheat","Properties":{"age":"0"}}
```

`plant.support` 声明放置位置下方必须满足的支撑方块或 tag。v0.4 首期农业基底使用 `minecraft:farmland`。plant 目标仅可写入空气或可替换方块，且必须在所属 slot 的 owner chunk 内。

## Palette Slot

v0.4 slot 使用 `layers[]`，禁止与 v0.3 的 `phase`、`entries`、`required` 同时出现：

```json
{
  "slotId": "crop",
  "layers": [
    {
      "layerId": "base",
      "phase": "surface",
      "required": true,
      "entries": [{"contentRef": "geomantia:decoration/farmland_tile", "weight": 1.0}]
    },
    {
      "layerId": "plant",
      "phase": "minor",
      "dependsOnLayerId": "base",
      "required": true,
      "entries": [{"contentRef": "geomantia:decoration/wheat_seed", "weight": 1.0}]
    }
  ]
}
```

规则：

- `layerId` 在 slot 内唯一；依赖必须指向前序 layer，禁止循环。
- 首期 `base` 必须为 `prefab`，所有 `plant` layer 必须直接或间接依赖 `base`。
- slot 的 footprint、rotation、datum、terrain eligibility、fallback、owner 和 suppression 均由 base layer 派生；plant 不得扩大 footprint。
- style resolver 对每个 layer 独立解析语义项，但不允许请求内联 block state 或覆盖 catalog 约束。

## Worldgen 与 Ledger

一个 slot 保留一个 `fragmentId` 与一个 owner ledger key。`layers[]` 状态作为该 fragment 的嵌套诊断字段：

```json
{
  "layerId": "plant",
  "contentRef": "geomantia:decoration/wheat_seed",
  "contentHash": "sha256:...",
  "status": "applied|already_satisfied|skipped|failed",
  "reasonCode": "..."
}
```

只有全部 required layer 为 `applied` 或 `already_satisfied` 时，外层 fragment 进入 `appliedFragments[]`。否则只写 `fragmentOutcomes[]`，不得把 partial base 写入误报为已完成。重试时先检查每层精确目标状态，已满足 layer 不重写。

## 版本边界

v0.4 是当前开发主线的唯一可加载 schema。loader、codec 和 active registry 必须拒绝 v0.2/v0.3，而不是把旧 slot 规范化、迁移或兜底执行。旧 catalog、program 和 active plan 需要通过 Git 回退到相应代码提交才可使用；当前测试存档必须清除旧 active plan 后重新规划，并仅在未生成 chunk 激活 v0.4。
