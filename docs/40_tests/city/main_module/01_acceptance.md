# 主模块验收入口

## 当前主线验证重点

- `C7 -> C8 -> C9` 是否打通
- MCP 是否能读取 C8 会话并提交节点决策
- 已校验节点是否能进入 `C9` 队列
- `C9` 是否能按队列执行落地

## 当前证据来源

- `../../../../90_archive/StructureBinder/dev_docs/current_20260402_030950/`
- `../../../../90_archive/StructureBinder/root_docs/TEST_C_FLOW_CHECKLIST.md`

## 当前建议继续验证

- 主链连续多节点施工
- 主模块落地后的 runtime collision
- 失败后的 retry / blocked 可读性
