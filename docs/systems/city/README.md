# City 系统

City 承接 T4 `CitySeedRegistry` 和候选选址，在 D3-D7 生成可审查、可冻结、由 worldgen 落地的城市。当前唯一正式建筑路径是固定 NBT；configured structure、外部 Jigsaw、FunctionZone 先行和 late materialization 均不属于 active path。

## 当前主链

2026-09-11 已清理规模与景观的旧混合案。最新需求分别由[意图驱动规模与嵌套设计](10_product/案子/具体流程的案子/00_跨阶段主线/City意图驱动规模与嵌套设计-v0.1/README.md)和[景观独立空间与代价生长](10_product/案子/具体流程的案子/00_跨阶段主线/City景观独立空间与代价生长-v0.1/README.md)保存，其中规模与嵌套案已于 2026-09-13 接管实现，景观案于 2026-09-14 接管实现：AI 组织城市主体、取消面积补量外扩，景观独立需求并按代价生长。

下方说明主链入口；具体变更以对应当前案与数据契约为准，不能据此恢复已废弃的产品要求。提交恢复与基础域的独立能力参考见产品索引。

```text
T4 CitySeed
-> D3 局部地貌扫描与选址复核
-> D4 prepare / submit / compile CityBlueprint v0.12，阵列先预留街巷净空并落 required 建筑，再按实际入口冻结必要街巷与景观容量
-> D5 reservation 与 wall mask 预案
-> D6 当前世界 NBT identity / geometry lock
-> D6 后按邻域主高程编译城区分级平台、真实目的地道路、Landscape Parcel、建筑绿化、住宅外溢边界与 LandUse
-> execute_d5 激活结构与 LandUse
-> worldgen createStructures / FEATURES 分片落地
-> D7 ledger、现场观测、道路和城墙后处理
```

正式 D4 冻结完整 CityBlueprint revision，输入允许完整设计或带 baseBlueprintHash 的局部替换补丁；宿主补齐省略的身份字段，并在显式相对权重模式下换算占比，再执行原有完整校验。同一 Context 的设计编译失败最多 5 次；提交校验拒绝、明确的程序搜索/安全上限及锚点终审故障不消耗设计预算。程序故障进入 blocked_by_program，保留方案，不要求 AI 重写。具体输入和恢复规则以 CityBlueprint 数据契约为准。

`groups[]`、`arrayCompositions[]` 与显式 `Landscape` 共同进入 D4：父阵列按完整 Group 范围编排子阵列，Group 可按 Patch 边界或其他 Group 关系定位；required 建筑以所选 Patch 起步，后续连续阵列可跨 Patch 边界。景观以 owner 为种子按地形生长，preferred Patch 仅为软偏好；数量或面积可被地形减少，零格写警告，不让整城失败。景观在 required owner 确立后、阵列 fill 前规划；后续建筑与道路可占用并裁去景观 spans，D6 后非零 Parcel 按冻结父子来源逐格生成。

## 当前实现边界

- D4 采用“落地底线 / 布局质量”分层：最终同 Group 同 ref 指定内容、资源/边界/碰撞、功能区与必需关系必须通过；入口局部断路、阵列视觉缺口告警，允许继续 D5/D6。保留原阶段缺口与全部质量明细，不将可落地标成质量完善。详见 CityBlueprint 数据契约。
- D3 地貌事实由 `CityLandformReviewBuilder` 和 `LandUseTerrainFieldCompiler` 生成，不在 D4 重扫世界。
- D4 Context `v0.10`、Reference Catalog `v0.9`、snapshot `v0.10`、Blueprint `v0.12` 必须严格匹配。
- D2/D4/D6 只读取 `city_template_catalog.v0.1` 和当前世界 NBT，所有 City 模板冻结为 `structure_start_beard_thin`。
- 托管规划配置中的版本化模板内容包在世界启动时自动安装到该世界 `generated`；manifest 必须完整覆盖当前 template catalog，D4 Context 前对全部模板执行当前世界 hash/尺寸预检。
- D6 后生成一个 Foundation owner：城区建设面按邻域主高程形成分级平台，台基只处理剩余局部高差；Landscape Parcel 保留自然地形。普通 GRID 在建筑落位时预留街巷净空，全部建筑落位后冻结服务真实入口的最小路网；功能景观含 `GROUND_PATH + CORRIDOR` 的农业/林场组改由大小不一的景观 Parcel 与一格间隔承担内部流线，不生成城市式 GRID 街网。COURTYARD/LINEAR/COMPACT 与可选 CENTER 轴街同样只冻结服务实际建筑入口的区内街巷。城市主路必须连接真实目的地且沿途具有实际交通用途；功能区关系、相向扩张和距离不得自动生成道路或桥梁。SurfacePrint 逐 block 执行 City 自有的分级材质道路、建筑绿化与住宅外溢边界。
- worldgen 只创建 City 自有单-piece template start；运行时 bbox 不回写规划几何。
- `key_then_array`、array loop、sequential session 和 cluster groups 只保留为实现层 legacy HTTP/测试代码，不再暴露为 Agent Loop MCP 工具，也不是正式 workflow 的失败保底。
- 城墙默认 D5 reservation 版本为 v2；workflow 可显式使用 v3/v4/v5，v1 只保留为 debug。

## 产品入口

| 能力 | 当前文档 |
| --- | --- |
| City 产品案职责索引 | `10_product/案子/README.md` |
| 提交反馈与恢复能力参考 | `10_product/案子/具体流程的案子/30_D4蓝图编译/City提交纠错与失败恢复-v0.1/README.md` |

各独立能力的实现当前案、设计中案和能力参考在产品案职责索引维护，不在本页复制清单。已完成计划、失败原型、未实现方向和单次城市实例不保留在当前文档仓库，历史只从 Git 查询。

## 契约入口

- [AI 材质与方块检索](20_contracts/数据契约/CityAI材质与方块检索数据契约.md)

- `20_contracts/数据契约/CitySiteContext数据契约.md`
- `20_contracts/数据契约/CityLandformReviewPackage数据契约.md`
- `20_contracts/数据契约/CityBlueprint数据契约.md`
- `20_contracts/数据契约/City模板建筑主路径数据契约.md`
- `20_contracts/数据契约/City模板内容包配置数据契约.md`
- `20_contracts/数据契约/CityLandUseAreaPlan数据契约.md`
- `20_contracts/数据契约/CityWorldgenBlockObservation数据契约.md`
- `20_contracts/接口契约/City调试MCP接口.md`

## 实现与验收

- 代码导览：`30_code_guide/代码导览.md`
- 测试入口：`40_tests/测试入口.md`
- 影响面：`40_tests/影响面.md`
- 当前待复验故障：`40_tests/故障修复案/README.md`

代码、契约和测试入口是当前实现依据；版本化产品案只解释仍在运行的能力，不得覆盖上述真值。
