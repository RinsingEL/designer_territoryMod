# Repo Map

## Roles

- 实现仓库：`E:\Mod_Dev\StructureBinder`
  - 主要承载 Java / MCP / 运行时代码
- 文档仓库 / 策划案仓库：`E:\Mod_Dev\designer_territoryMod`
  - 主要承载当前有效方案、契约、代码导览与测试入口

## Rules

- 新建或重建系统的当前真值优先放在本仓库 `docs/systems/<系统>/`
- 新建或重建工具的当前真值优先放在本仓库 `docs/tools/<工具>/`
- 根级旧四层目录 `docs/10_product`、`docs/20_contracts`、`docs/30_code_guide`、`docs/40_tests` 不再作为当前真值入口
- 当前导航只登记已开发系统和工具；未开发系统不预建文档四层目录或实现仓库空 package
- 实现仓库 Java 代码优先按系统 / 能力边界内聚，Minecraft / Forge / HTTP / MCP 放在适配边界；详见 `00_nav/实现仓库结构规范.md`
- 实现仓库当前 `dev_docs/` 继续作为过程记录和提交归档依据
- 新建过程记录按 `dev_docs/systems/<系统>/`、`dev_docs/tools/<工具>/`、`dev_docs/workflows/<主题>/` 组织
- 系统和工具级故障经验优先沉淀到对应 `故障索引.md`
- 本仓库 `docs/90_archive` 只保留旧资料归档
- 不再维护双轨文档体系

## Cross-Repo Usage

### 从文档找实现

1. 先进入 `systems/<系统>/README.md` 或 `tools/<工具>/README.md`
2. 再看 `10_product/` 确认功能边界
3. 再看 `20_contracts/` 确认输入输出
4. 再看 `30_code_guide/` 跳到实现类、流程实现指南和 review 清单

### 从实现找文档

1. 先按 `00_nav/function_map.md` 和 `00_nav/AI语义检索规则.md` 判断系统 / 工具归属
2. 代码入口问题进入 `systems/<系统>/30_code_guide/` 或 `tools/<工具>/30_code_guide/`
3. 方案和边界问题回跳到同系统或同工具下的 `10_product/`
4. 数据结构和接口问题回跳到 `20_contracts/`
5. 测试、验收和失败问题回跳到 `40_tests/`
6. 如需当前过程记录或故障复盘，去实现仓库对应 `dev_docs/systems/<系统>/` 或 `dev_docs/tools/<工具>/`
7. 如需历史背景，再去 `90_archive/`
