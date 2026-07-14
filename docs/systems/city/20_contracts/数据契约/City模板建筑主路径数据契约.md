# City 模板建筑主路径数据契约

## 定位与强制口径

本文是 City 固定模板建筑主路径的当前数据真值，覆盖 D2 模板目录、D4 placement plan、D5 active registry、worldgen 交接和 D7 ledger。

City active 主建筑只读取 `StructureTemplate` NBT 和本契约的模板目录，不查询 `Minecraft Registries.STRUCTURE`，不生成 `StructureStart`，不使用 Jigsaw pool。City 自己的 active template placement registry 可以作为 D5 -> worldgen 的交接，但它不是 Minecraft StructureStart，也不允许携带 Jigsaw 展开结果。

D2、D4、D6、D7 对同一建筑必须保持以下 identity 完全一致：

```text
templateRef + templateHash + variant + rawSize + rotation + mirror + anchor
```

identity 或由它派生的 world footprint 漂移必须 hard fail。旧 `structureId`、configured structure、Jigsaw、StructureStart、旧 profile bbox 和 bbox 外侧伪入口不得被静默转换。

## 版本与产物

| 产物 | schemaVersion | 作用 | 主要阶段 |
| --- | --- | --- | --- |
| 模板目录 | `city_template_catalog.v0.1` | 登记模板 NBT、hash、变体、变换限制、道路入口和地形策略 | D2 |
| placement plan | `city_template_placement_plan.v0.1` | 冻结每个建筑的模板 identity、anchor、NBT size、派生 world footprint、碰撞范围和道路入口 | D4 / D6 |
| active template placement registry | `city_active_template_placement_registry.v0.1` | D5 -> worldgen 的 City 内部 active 交接 | D5 |
| placement ledger | `city_template_placement_ledger.v0.1` | 记录 worldgen NBT 放置、跳过、失败和实际 closed footprint，保证幂等 | worldgen / D7 |

`schemaVersion` 必须精确匹配。未知版本、未知字段、缺失必填字段和跨版本自动降级均 hard fail；`v0.1` 不承诺旧 Jigsaw 或 StructureStart artifact 兼容。

## 共同几何约定

### Anchor

`anchor` 是 transformed 模板 footprint 的最小角世界方块坐标，不是中心点，也不是道路外侧的辅助点：

```json
{"x": 1200, "y": 72, "z": -340}
```

- `anchor.x / anchor.z` 是 transformed footprint 的 `minX / minZ`。
- `anchor.y` 是模板放置 datum；模板高度从该 y 开始计算。
- D4 选择 anchor 后，D6、active registry、worldgen 和 D7 必须沿用同一 anchor。

### Half-open 与 closed bbox

- 模板 NBT 原始局部范围是 half-open：`[0,width) × [0,height) × [0,depth)`。
- `roadEntrances[].position` 的局部 `x / z` 必须落在 `[0,width) × [0,depth)`，越界即拒绝。
- transformed actual footprint、collision bbox、mask bbox、ledger actual footprint 对外统一表示为 closed block bounds，包含两端：`[minX..maxX] × [minY..maxY] × [minZ..maxZ]`。
- 对 transformed size `width × height × depth`，实际 world bbox 为：`min=anchor`、`maxX=anchor.x+width-1`、`maxY=anchor.y+height-1`、`maxZ=anchor.z+depth-1`。
- collision / mask 只能从 actual closed bbox 按声明的 clearance / mask margin 扩展；任何文档或 artifact 都不得把 half-open `maxExclusive` 当作 closed `max`。

通用 `BlockBounds` 字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `minX` / `minY` / `minZ` | int | 是 | 包含的最小方块坐标 |
| `maxX` / `maxY` / `maxZ` | int | 是 | 包含的最大方块坐标，必须不小于对应 min |
| `convention` | string | 是 | 固定为 `closed_inclusive_blocks` |

## 模板目录 `city_template_catalog.v0.1`

顶层必填字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schemaVersion` | string | 是 | 固定为 `city_template_catalog.v0.1` |
| `templates[]` | object[] | 是 | 不得为空；`templateRef + variant` 唯一 |

每个 `templates[]` 条目必填：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `buildingSemantic` | string | AI-facing 建筑语义；不是 City 自建功能枚举 |
| `style` | string | 风格键 |
| `templateRef` | string | Minecraft resource location，指向可由 `StructureTemplateManager` 读取的 NBT |
| `templateHash` | string | 模板内容的稳定 hash；推荐 lowercase SHA-256，禁止空值 |
| `variant` | string | 模板变体；与 `templateRef` 共同唯一 |
| `rawSize` | object | `{width,height,depth}`，三者均为正整数，来自 NBT |
| `allowedRotations[]` | string[] | `NONE`、`CLOCKWISE_90`、`CLOCKWISE_180`、`COUNTERCLOCKWISE_90` 中的非空子集 |
| `allowedMirrors[]` | string[] | `NONE`、`LEFT_RIGHT`、`FRONT_BACK` 中的非空子集 |
| `roadEntrances[]` | object[] | 模板局部道路入口；每项含 `entranceId`、`position{x,z}`、`direction` |
| `terrainPosePolicy` | string | 模板地形姿态策略 |
| `supportPolicy` | string | 支撑 / 基础策略 |
| `clearanceBlocks` | int | 非负；只用于从 actual footprint 派生 collision bbox |

目录 loader 必须从 NBT 重新确认 `rawSize` 和 `templateHash`。配置不能覆盖 NBT 尺寸，不能把 `nbtFile`、`structureId` 或 TerraSense 静态 footprint 当作 `templateRef` 的兼容别名。

目录条目示例：

```json
{
  "schemaVersion": "city_template_catalog.v0.1",
  "templates": [
    {
      "buildingSemantic": "market",
      "style": "coastal_medieval",
      "templateRef": "geomantia:city/market_a",
      "templateHash": "sha256:0123456789abcdef...",
      "variant": "a",
      "rawSize": {"width": 10, "height": 8, "depth": 12},
      "allowedRotations": ["NONE", "CLOCKWISE_90"],
      "allowedMirrors": ["NONE"],
      "roadEntrances": [
        {"entranceId": "front", "position": {"x": 4, "z": 11}, "direction": "SOUTH"}
      ],
      "terrainPosePolicy": "flat_or_small_step",
      "supportPolicy": "full_footprint_support",
      "clearanceBlocks": 2
    }
  ]
}
```

## Placement plan `city_template_placement_plan.v0.1`

顶层必填字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schemaVersion` | string | 固定为 `city_template_placement_plan.v0.1` |
| `runId` | string | 当前 City run |
| `cityId` | string | 城市 ID |
| `planId` | string | 本次 immutable placement plan ID |
| `placements[]` | object[] | 必填，可按设计顺序排列 |

每个 `placements[]` 必填字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `anchorId` | string | 本 plan 内唯一的建筑 anchor ID |
| `slotId` | string | D4 设计 slot 引用 |
| `templateRef` | string | 必须命中 catalog |
| `templateHash` | string | 必须与 catalog 和加载 NBT 一致 |
| `variant` | string | 必须命中 catalog |
| `rotation` | string | 必须在该变体 `allowedRotations[]` 内 |
| `mirror` | string | 必须在该变体 `allowedMirrors[]` 内 |
| `anchor` | object | `{x,y,z}`，transformed footprint 最小角 |
| `templateSize` | object | `{width,height,depth}`；从已校验 NBT `rawSize` 原样带入，是 placement 的唯一局部矩形几何 |
| `actualFootprint` | object | D4/D6 的派生输出快照；由 `templateSize + rotation + mirror + anchor` 计算，closed bounds |
| `collisionEnvelope` / `maskEnvelope` | object | 从 `actualFootprint` 按 clearance / mask margin 派生，closed bounds |
| `roadEntrances[]` | object[] | transformed 入口；含 `entranceId`、`relativePosition{x,z}`、`worldPosition{x,y,z}`、`direction` |

`roadEntrances[]` 必须由目录局部入口按同一 rotation / mirror 变换并加 anchor 得到。RoadWeaver 使用 worldPosition / direction 注册，禁止使用 `bbox + 外扩距离` 推导入口。`templateFootprint`、`bbox`、`footprint` 不是模板目录或阵列 item 的合法输入；它们不会作为另一套本地尺寸真值保存。

## Active registry `city_active_template_placement_registry.v0.1`

D5 可以写入 City 自己的 server-root active registry，作为 worldgen 交接。顶层必填：`schemaVersion`、`dimensionId`、`cityId`、`planId`、`activatedAt`、`placements[]`。每个 placement 必须原样保留 placement plan 的 identity、anchor、`templateSize` 和 transformed `roadEntrances[]`，并携带 D6 派生并锁定的 world footprint 快照，另外增加：

- `registryStatus=active`
- `worldgenSource=city_template_nbt`
- `roadProvider=auto|roadweaver|worldedit_debug|none`

`roadProvider=auto` 缺 RoadWeaver 时只写 skip state 和 `ROADWEAVER_UNAVAILABLE`；`roadProvider=roadweaver` 缺 mod 或注册失败时 hard fail；`worldedit_debug` 只授权旧 debug road，不授权旧建筑物化路径。

模板 D6 item 的 lock 必须包含 `locked=true`、`actualFootprint`、`lockedActualFootprint`、`lockedCollisionEnvelope`、`lockedBBoxGroupKey` 和 `pieceBoxes[]`。因为模板路径明确不生成 `StructureStart`，`expectedStartSignature` 可以为空；D5 只能对非模板 configured-structure item 保持非空 signature 的约束，不能为模板伪造或要求 StructureStart signature。

## Placement ledger `city_template_placement_ledger.v0.1`

顶层必填：`schemaVersion`、`dimensionId`、`cityId`、`planId`、`entries[]`。每个 entry 必填：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `anchorId` | string | 对应 placement plan |
| `templateRef` | string | identity 原样回写 |
| `templateHash` | string | identity 原样回写 |
| `variant` / `rotation` / `mirror` | string | identity 原样回写 |
| `templateSize` | object | identity 原样回写；本地尺寸只能来自 D2 已校验 NBT |
| `chunk` | object | worldgen owner chunk，含 `x`、`z` |
| `status` | string | `pending`、`placed`、`skipped`、`failed` |
| `placementSource` | string | 固定为 `city_template_nbt_worldgen` |
| `actualFootprint` | object | `placed` 时必填；closed bounds，必须等于或落在计划允许范围内 |
| `reasonCode` | string | `skipped` / `failed` 必填；成功可为 `TEMPLATE_PLACED` |
| `appliedAt` | string | `placed` / `skipped` / `failed` 的完成时间 |

ledger 幂等键为 `dimensionId + cityId + planId + anchorId + chunk`。重复 worldgen hook 不得重复放置或追加重复 entry；写 ledger 失败不得提前把 entry 标成 `placed`。D7 只汇总该 ledger，不反查 StructureStart，不调用 Jigsaw，不做 late paste。

## 错误码

### 模板目录与几何

- `CITY_TEMPLATE_CATALOG_SCHEMA_UNSUPPORTED`：schemaVersion 不支持。
- `CITY_TEMPLATE_CATALOG_FIELD_MISSING` / `CITY_TEMPLATE_CATALOG_FIELD_UNKNOWN`：必填字段缺失或出现未声明字段。
- `CITY_TEMPLATE_CATALOG_JSON_INVALID` / `CITY_TEMPLATE_CATALOG_ROOT_INVALID`：目录 JSON 根或语法非法。
- `CITY_TEMPLATE_CATALOG_DUPLICATE_VARIANT`：`templateRef + variant` 重复。
- `CITY_TEMPLATE_CATALOG_TEMPLATE_UNKNOWN` / `CITY_TEMPLATE_CATALOG_VARIANT_NOT_FOUND`：引用不存在。
- `CITY_TEMPLATE_NBT_NOT_FOUND` / `CITY_TEMPLATE_NBT_READ_FAILED`：模板 NBT 无法读取。
- `CITY_TEMPLATE_HASH_MISMATCH`：目录、plan 或加载内容 hash 不一致。
- `CITY_TEMPLATE_CATALOG_SIZE_INVALID` / `CITY_TEMPLATE_CATALOG_TEMPLATE_INVALID`：NBT 尺寸或模板条目非法。
- `CITY_TEMPLATE_CATALOG_ENTRANCE_INVALID` / `CITY_TEMPLATE_CATALOG_ENTRANCE_OUT_OF_BOUNDS`：入口字段或局部坐标非法。
- `CITY_TEMPLATE_CATALOG_ROTATION_INVALID` / `CITY_TEMPLATE_CATALOG_ROTATION_NOT_ALLOWED`：旋转非法或不在允许集合。
- `CITY_TEMPLATE_CATALOG_MIRROR_INVALID` / `CITY_TEMPLATE_CATALOG_MIRROR_NOT_ALLOWED`：镜像非法或不在允许集合。
- `CITY_TEMPLATE_BBOX_INVALID`：half-open / closed 转换或 bbox min/max 非法。
- `CITY_TEMPLATE_PLACEMENT_IDENTITY_DRIFT`：D2、D4、D6、active registry、worldgen 或 D7 identity 不一致。
- `CITY_TEMPLATE_ACTIVE_REGISTRY_MISSING`：worldgen 前未找到对应 active template placement registry。
- `CITY_TEMPLATE_CHUNK_ALREADY_GENERATED`：目标 chunk 已过 worldgen 交接窗口且没有可用 ledger。

### RoadWeaver 与 legacy

- `ROADWEAVER_UNAVAILABLE`：`roadProvider=roadweaver` 缺少 mod；`auto` 下为 skip，不得回退旧 debug road。
- `ROADWEAVER_REGISTRATION_FAILED`：mod 存在但 endpoint / connection 注册失败。
- `CITY_TEMPLATE_TRANSFORMED_ENTRANCE_INVALID`：transformed entrance 越界、方向或 anchor 不一致。
- `CITY_TEMPLATE_LEGACY_INPUT_REJECTED`：旧建筑输入被拒绝；响应必须带具体 legacy reason。
- `CITY_TEMPLATE_LEGACY_STRUCTURE_REGISTRY_INPUT`：试图用 `Registries.STRUCTURE` 作为 active 模板来源。
- `CITY_TEMPLATE_LEGACY_STRUCTURE_START_INPUT`：试图提交或消费 StructureStart。
- `CITY_TEMPLATE_LEGACY_JIGSAW_POOL_INPUT`：试图提交或消费 Jigsaw pool / 展开结果。
- `CITY_TEMPLATE_LEGACY_BBOX_ENTRANCE_INPUT`：试图用 bbox 外侧伪入口替代模板 `roadEntrances[]`。

既有旧 City 功能区链路仍按 `LEGACY_CITY_FUNCTION_ZONE_FLOW_REMOVED` 处理；该错误不能被解释为模板路径兼容成功。

## 兼容策略与硬规则

- `v0.1` 只兼容本契约四种 schema 的精确版本；只要涉及模板建筑 active path，就不兼容旧 `structureId`、`nbtFile`、configured structure、Jigsaw pool、StructureStart、profile safety envelope 或 bbox 外侧 `roadPoint`。
- 目录更新必须重新计算 `templateHash`，并使旧 plan / active registry 失效；不能只改文件名、variant 或尺寸字段绕过 hash 校验。
- active registry、worldgen ledger、D7 汇总均必须保留相同 identity；每次使用 `templateSize + rotation + mirror + anchor` 复算并校验 closed `actualFootprint`。缺字段、hash 漂移、变换漂移、派生 footprint 漂移和入口漂移均 hard fail。
- RoadWeaver 缺失时，`auto` 的唯一兼容行为是跳过道路并写 `ROADWEAVER_UNAVAILABLE`；只有显式 `worldedit_debug` 可产生旧 debug road，且不能改变模板建筑落地路径。
- StructureStart / Jigsaw 自动生成的旧测试和旧 artifact 只用于历史保护，不能作为模板专项验收通过依据。
