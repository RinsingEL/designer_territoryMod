# City 模板内容包配置数据契约

## 定位

City 模板目录与实际固定 NBT 必须作为同一个整合包内容单元交付。当前世界不得依赖另一个存档遗留的 `generated`；世界启动时从当前托管规划配置目录安装内容包，D4 Context 创建前再由当前世界 `StructureTemplateManager` 校验全部目录模板。

## 文件布局

```text
config/structureTemplate/terrasense/<bundle>/
  template_catalog.json
  city_template_content_pack.json
  city_template_content_pack/
    <namespace>/structures/<path>.nbt

<world>/
  generated/<namespace>/structures/<path>.nbt
  geomantia_city_template_content_pack.json
```

`city_template_content_pack.json` 的 `schema` 固定为 `city_template_content_pack.v0.1`，必填 `packId`、`catalogSha256` 和非空 `templates[]`。每个模板必填：

- `templateRef`：目标 Minecraft resource location。
- `sourceFile`：相对 `city_template_content_pack/` 的固定 NBT 文件。
- `sourceSha256`：源文件字节 SHA-256。

可选 `sourceModId`、`sourceIdentity`、`converterId` 只记录来源和转换器身份，不能替代实际 NBT、运行时 hash 或目录元数据。

## 安装门禁

- manifest 的唯一 `templateRef` 集合必须与当前 `template_catalog.json` 完全一致；缺项和多项都拒绝。
- `catalogSha256`、每个 `sourceSha256`、schema、路径和重复引用必须严格校验。
- 只安装显式目录选择的模板，不扫描或全量导入外部模组资源。
- 目标缺失时安装；目标字节漂移时按内容包修复；一致时不重写；不得删除当前世界其他 generated 文件。
- 单文件使用同目录临时文件原子替换；全部源文件先通过校验后才开始写入。
- 安装状态只用于观测，不能跳过下一次完整性检查。

## 规划前校验

D4 Context 创建前必须对目录中每个唯一 `templateRef` 从当前世界运行时实读，并校验 `contentHash` 与 `rawSize`。任一模板缺失、hash 漂移或尺寸漂移时返回 `CITY_TEMPLATE_CONTENT_PREFLIGHT_FAILED`，不得创建 Context、消耗 Agent 调用或把失败延迟到 D6。

离线清洗和外部模组转换仍遵循《City模板建筑主路径数据契约》的独栋确认、Jigsaw 与 processor 规则。内容包安装器只分发已审核成品，不推断模板是否适合作为建筑。

## 聚落素材角色与公共绿化（2026-09-21）

`tools/city_templates/curate_planning_roles.py` 对已有 bundle 做保守角色整理，按现有名字与已确认功能初筛角色，实际尺寸独立分组，不宣称完成全素材视觉审查。报告在 `asset_catalogs/planning_roles/`；显式 override 绑定 `contentHash`，内容漂移即拒绝。源 NBT、模板目录及内容包哈希不改动。打包与增量合并脚本也保留角色并只将可重复结构入池，避免重建后恢复全量填充。

当前包471项：239项重复候选、97项功能主体、135项明确选用结构；其中1项花园经NBT与投影核对为完整组合。`pool:public_small_support`（占地不超过144格）与 `pool:public_medium_support`（不超过400格）提供高度不超过24格的既有小店铺/摊位等配套，每种结构每组最多2份；按原有风格分池（无后缀为中世纪，其余如 `_desert`、`_japanese`），避免跨风格随机混排。它们不是场景专用算法。实际大小搭配仍由AI负责。查询候选在同bundle可解析时附带 `displayName/rawSize/footprintAreaBlocks`。

自动公共绿化默认共享已经整理的道路树。可用 `config/geomantia/city_public_greenery_structures.json` 替换独立候选清单，例如：

```json
[{"templateRef":"geomantia:roadside/small_oak","usage":"SMALL_INDEPENDENT","groundMode":"SURFACE_ROOT","size":[10,11,8],"root":[5,0,4]}]
```

只接收小型独立结构的显式清单，`root.y=0`、根点在实际尺寸内；运行时检查模板可读性与尺寸一致。作者需核对连带装饰、地基和高差，完整花园/喷泉庭院不能加入此清单，而应作为D4结构。该清单不自动安装NBT，模板仍需由原内容包或资源包提供。


大型住宅/别墅可标记 planning_role.fill，尺寸不是核心身份或重复资格的判据。asset_names.json 保留 originalDisplayName，displayName 加入占地档、宽×深和高度；查询仍返回 rawSize 与 footprintAreaBlocks。按用途、风格、占地档、高度档生成 pool:scaled_*，避免大住宅或高耸房屋混入小型配套。占地档 small≤144且边长≤16、medium≤400且边长≤24、large≤900且边长≤36、其余extra_large；高度档low≤12、medium≤24、tall≤40、very_tall>40。尺寸是模板包围盒，含留白与装饰。

旧自动角色仅在审计报告匹配时迁移；报告外显式修改保留，哈希绑定override优先。人读分组清单与JSON报告同目录同名。
