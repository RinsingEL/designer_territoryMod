# TerraSense 结构扫描与策展

## 定位

TerraSense 是独立 Forge/Studio 工具：在 Minecraft 中扫描结构与截图，在 Studio 中进行 AI 初标和人工审核，再导出冻结语义画像。它不参与 StructureBinder 的 runtime 规划或 worldgen。

## 当前流程

```text
Forge 发现并放置样本
-> 写 ScanWorkspace 硬事实与截图
-> Studio AI suggestion
-> 人工 review / vocabulary
-> export-city-profiles.mjs
-> official / debug / binder 静态产物
```

AI 只提供初标建议。`review_state=approved` 才能进入 official 或 binder 导出；硬事实、截图和放置结果不得由 AI 改写。

## 样本类型

| 类型 | 入口与用途 |
| --- | --- |
| `single/template/single_template` | 固定 NBT 模板扫描；`single_template` 是当前 binder mode 唯一准入样本。 |
| `structure_assembly` | 通过 MC `place structure` 扫描 configured structure 的整体结果，供 TerraSense official/debug 研究，不是 City active 建筑输入。 |
| `jigsaw_assembly` | 通过 MC `place jigsaw` 扫描 pool 展开结果，只用于底层组合调试。 |

样本类型不能互相替代。一个包含 Jigsaw connector、但经人工确认可独立使用的 NBT，仍需在 StructureBinder 离线清洗流程中冻结源 hash、connector 数量和收尾结果；TerraSense 截图不能自动批准它进入 City catalog。

## ScanWorkspace

每次 run 由 manifest 索引结构目录。单结构至少保留 `data.json`、`scan_config.json`、截图、`ai_suggestion.json`（若执行）和 `review.json`（若审核）。完整字段见 `../20_contracts/ScanWorkspace.md`。

Studio 文件 API 必须限制在 workspace/imports 根目录。导入 zip 不得覆盖共享 vocabulary/tag index；中断扫描可通过索引继续。

## 策展边界

人工审核负责功能、规划角色、地形/拓扑语义、风格和推荐场景。以下内容始终是扫描或 Minecraft 事实：NBT 大小、palette、connector、pool、放置命令、实际 footprint 和截图来源。

debug 导出可以保留未审核信息，但必须显式 `catalogMode=debug`。official/binder 不得自动把 proposed term 当 approved，也不得根据结构 ID 或文件名猜缺失标签。

## 与 StructureBinder 的边界

当前 City active path 只使用固定 NBT。模板几何由当前世界 `StructureTemplateManager` 与 City template catalog 冻结；TerraSense 最多提供 AI 可读、可审核的结构语义，不提供 configured/Jigsaw 几何、统计 envelope 或运行时放置计划。

当前 binder 集成尚未闭环：TerraSense exporter 输出 `terrainTerms`，StructureBinder importer 要求 `terrainModes` 并拒绝前者。在字段统一和跨仓库 fixture 通过前，binder 产物只能作为待接入输出，不能宣称已经进入 D4/D6。

## 验收

- 扫描入口按样本类型写出可重放 workspace，截图和硬事实身份一致。
- Studio 可脱离 MC 浏览、初标、审核和保存，AI 不覆盖人工真值。
- exporter 的四种 mode、准入、skip reason 和 v0.2 schema 与代码一致。
- debug/unapproved 不混入正式输出。
- StructureBinder 集成只有在真实 exporter 输出被 importer 直接读取后才算完成。
