# Repo Map

## Roles

- 实现仓库：`E:\mc_dev\StructureBinder-rebuild\StructureBinder`
  - 主要承载 Java / MCP / 运行时代码
- 文档仓库：`E:\mc_dev\StructureBinder-rebuild\designer_territoryMod`
  - 主要承载当前有效方案、契约、代码导览与测试入口

## Rules

- 当前真值只认本仓库 `docs/10_product`、`docs/20_contracts`、`docs/30_code_guide`、`docs/40_tests`
- 旧 `workFlow`、`dev_docs` 只保留在 `docs/90_archive/StructureBinder`
- 不再维护双轨文档体系

## Cross-Repo Usage

### 从文档找实现

1. 先看 `10_product/` 确认功能边界
2. 再看 `20_contracts/` 确认输入输出
3. 再看 `30_code_guide/` 跳到实现类

### 从实现找文档

1. 先按功能进入 `30_code_guide/`
2. 再回跳到对应 `10_product/` 和 `20_contracts/`
3. 如需历史背景，再去 `90_archive/StructureBinder/`
