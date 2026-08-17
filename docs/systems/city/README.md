# City 系统

City 承接 T4 `CitySeedRegistry` 和候选选址，在 D3-D7 生成可审查、可冻结、由 worldgen 落地的城市。当前唯一正式建筑路径是固定 NBT；configured structure、外部 Jigsaw、FunctionZone 先行和 late materialization 均不属于 active path。

## 当前主链

```text
T4 CitySeed
-> D3 局部地貌扫描与选址复核
-> D4 prepare / submit / compile CityBlueprint v0.11，并联合求解 required 建筑与景观容量
-> D5 reservation 与 wall mask 预案
-> D6 当前世界 NBT identity / geometry lock
-> D6 后在冻结容量内编译 Foundation、Landscape Parcel 与 LandUse
-> execute_d5 激活结构、LandUse、Decoration 和 RoadWeaver 交接
-> worldgen createStructures / FEATURES 分片落地
-> D7 ledger、现场观测、道路和城墙后处理
```

正式 D4 只允许一次 CityBlueprint 决策。`groups[]`、`arrayCompositions[]` 与显式 `Landscape` 主体共同进入 D4：父阵列按完整 Group 范围编排子阵列，Group 可按 Patch 边界或其他 Group 关系定位；required 建筑候选和其 required 景观容量必须联合求解、原子提交，fill/connectivity 不得进入冻结景观容量。AI 精确提交实例数和每实例 Parcel 数；required 不缩减、不按顺序抢地，全部有限组合无解就明确失败。D6 后每实例按冻结父子树逐格生成互斥但可接壤的独立 Parcel。

## 当前实现边界

- D3 地貌事实由 `CityLandformReviewBuilder` 和 `LandUseTerrainFieldCompiler` 生成，不在 D4 重扫世界。
- D4 Context `v0.10`、Reference Catalog `v0.8`、snapshot `v0.10`、Blueprint `v0.11` 必须严格匹配。
- D2/D4/D6 只读取 `city_template_catalog.v0.1` 和当前世界 NBT，所有 City 模板冻结为 `structure_start_beard_thin`。
- D6 后先生成一个连续 Foundation，再生成独立 Landscape Parcel；RoadWeaver 是道路唯一正式来源。
- worldgen 只创建 City 自有单-piece template start；运行时 bbox 不回写规划几何。
- `key_then_array`、array loop、sequential session 和 cluster groups 仍是显式 legacy/debug endpoint，不是默认 workflow。
- 城墙默认 D5 reservation 版本为 v2；workflow 可显式使用 v3/v4/v5，v1 只保留为 debug。

## 产品入口

| 能力 | 当前文档 |
| --- | --- |
| 嵌套阵列与关系位置 | `10_product/案子/City嵌套阵列与关系位置-v0.1/README.md` |
| 固定模板唯一落地 | `10_product/案子/City固定模板唯一落地主线-v0.1/README.md` |
| 单次 Blueprint、Foundation 与 Landscape | `10_product/案子/City单次蓝图户外空间编译-v0.1/README.md` |
| LandUse 执行层 | `10_product/案子/City建筑驱动LandUseAreaPlan-v0.1/README.md` |
| Decoration v0.4 | `10_product/案子/City通用装饰阵列系统-v0.4/README.md` |
| required 装饰候选 | `10_product/案子/City关键装饰锚点候选-v0.1/README.md` |
| RoadWeaver 交接 | `10_product/案子/RoadWeaver结构连接-v0.1/README.md` |
| 城市边界与城墙 | `10_product/案子/城市边界与城墙.md` |

产品案状态总表见 `10_product/案子/README.md`。已完成计划、失败原型、未实现方向和单次城市实例不再保留在当前文档仓库，历史只从 Git 查询。

## 契约入口

- `20_contracts/数据契约/CitySiteContext数据契约.md`
- `20_contracts/数据契约/CityLandformReviewPackage数据契约.md`
- `20_contracts/数据契约/CityBlueprint数据契约.md`
- `20_contracts/数据契约/City模板建筑主路径数据契约.md`
- `20_contracts/数据契约/CityLandUseAreaPlan数据契约.md`
- `20_contracts/数据契约/CityDecorationLayeredContent-v0.4.md`
- `20_contracts/数据契约/CityWorldgenBlockObservation数据契约.md`
- `20_contracts/接口契约/City调试MCP接口.md`

## 实现与验收

- 代码导览：`30_code_guide/代码导览.md`
- 测试入口：`40_tests/测试入口.md`
- 影响面：`40_tests/影响面.md`
- 当前待复验故障：`40_tests/故障修复案/README.md`

代码、契约和测试入口是当前实现依据；版本化产品案只解释仍在运行的能力，不得覆盖上述真值。
