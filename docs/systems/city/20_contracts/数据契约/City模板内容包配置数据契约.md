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
