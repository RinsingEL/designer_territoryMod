# AGENTS

## 仓库定位

本仓库是 `designer_territoryMod` 文档仓库，不承载运行时代码真值，主要承载以下内容：

- 当前有效的产品方案
- 当前有效的数据契约
- 面向 AI 和人类的代码导览
- 当前测试、验收、联调入口
- 与实现仓库的映射关系

实现代码真值仍在：

- `E:\mc_dev\StructureBinder-rebuild\StructureBinder`

## 文档主目录规则

本仓库当前有效文档只认以下目录：

- `docs/00_nav`
- `docs/10_product`
- `docs/20_contracts`
- `docs/30_code_guide`
- `docs/40_tests`

这些目录分别承担：

1. `00_nav`
   - 仓库映射、功能地图、总导航入口
2. `10_product`
   - 功能方案、范围、边界、阶段目标
3. `20_contracts`
   - 数据契约、输入输出边界、结构化协议
4. `30_code_guide`
   - 代码入口、类职责、主链说明、从文档跳实现
5. `40_tests`
   - 测试计划、验收口径、联调入口、问题清单

agent `MUST NOT` 将当前有效结论继续写回旧的 `workFlow` 风格文档中。

## 历史归档规则

`docs/90_archive/` 是历史资料区，只承担追溯价值。

其中：

- `docs/90_archive/StructureBinder/dev_docs`
- `docs/90_archive/StructureBinder/workFlow`
- `docs/90_archive/StructureBinder/whitepaper`
- `docs/90_archive/StructureBinder/root_docs`

都视为只读归档。

agent `MUST` 遵守：

1. 不在 `90_archive/` 中持续维护新方案。
2. 不把 `90_archive/` 当作当前真值来源。
3. 如需引用历史资料，必须将当前有效结论重写进 `10_product`、`20_contracts`、`30_code_guide` 或 `40_tests`。

## 双仓库协作规则

当前双仓库协作约定如下：

- 实现仓库负责：
  - Java / MCP / 运行时实现
  - 调试、联调、`dev_docs` 过程记录
- 文档仓库负责：
  - 功能方案真值
  - 契约真值
  - 代码导览真值
  - 测试与验收入口真值

当实现仓库发生以下变化时，agent `MUST` 判断是否同步更新本仓库：

- 阶段职责变化
- 接口或数据结构变化
- 测试入口或验收方式变化
- 代码入口、主链路径或类职责变化

## Git 提交规则

本仓库中的 agent 在执行 git 提交时，必须遵守以下规则：

1. `MUST` 使用全中文提交信息。
2. `MUST` 在提交标题中明确概括本次文档变更主题，不得使用“更新”“修改”“fix”这类模糊标题。
3. `MUST` 在提交正文中说明：
   - 更新了哪些功能文档
   - 更新了哪些契约或导览
   - 是否涉及历史归档调整
   - 与实现仓库的对应关系
4. `NEVER` 提交未经确认的实现仓库文件镜像或无关资料。

## 写作规则

agent 在本仓库写文档时，`MUST` 优先遵守以下原则：

1. 当前真值优先写“现在怎么做”，不要把历史讨论原样搬成主文档。
2. 产品方案、契约、代码导览、测试入口必须分层，不混写成一份大杂烩。
3. 从历史资料抽取内容时，要重写成当前口径，而不是简单复制旧文档。
4. 每份文档尽量能让读者快速回答三个问题：
   - 这块现在的目标是什么
   - 它和实现仓库的哪个部分对应
   - 如果要继续开发，下一步应该看哪里
