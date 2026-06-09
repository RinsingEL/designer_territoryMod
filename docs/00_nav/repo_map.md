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
- 实现仓库当前 `dev_docs/` 继续作为过程记录和提交归档依据
- 本仓库 `docs/90_archive` 只保留旧资料归档
- 不再维护双轨文档体系

## Cross-Repo Usage

### 从文档找实现

1. 先进入 `systems/<系统>/README.md` 或 `tools/<工具>/README.md`
2. 再看 `10_product/` 确认功能边界
3. 再看 `20_contracts/` 确认输入输出
4. 再看 `30_code_guide/` 跳到实现类

### 从实现找文档

1. 先按功能进入 `systems/<系统>/30_code_guide/` 或 `tools/<工具>/30_code_guide/`
2. 再回跳到同系统或同工具下的 `10_product/` 和 `20_contracts/`
3. 如需当前过程记录，去实现仓库 `dev_docs/`
4. 如需历史背景，再去 `90_archive/`
