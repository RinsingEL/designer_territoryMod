# MCP 调用日志契约

## 定位

`geomantia_mcp_call_log.v0.2` 是 `country_designer_mcp` 全部工具共用的调用边界日志。它用于自动回答一次 MCP 调用何时开始、是否结束、耗时多久，以及结束状态是成功、错误还是超时；不得再要求 AI 用文档手工计时。

日志不替代业务 artifact、workflow step report、worldgen ledger 或 Minecraft 方块观测。`status=success` 只表示 handler 正常返回，不表示世界内结果已经真实落地。

## 存储与事件

Node MCP 进程在当前工作目录追加 `country_designer_mcp_log.jsonl`，每行一个紧凑 JSON object。每次工具调用写两类事件：

- 收到请求后、调用 handler 前立即写 `eventType=mcp_call_started`。
- handler 返回或抛错后写 `eventType=mcp_call_completed`。

两条事件共享随机 `callId`。日志写入失败不得影响 MCP stdio 响应。

### started

必含：`schemaVersion`、`eventType`、`callId`、`toolName`、`recordedAt`、`recordedAtEpochMs`、`startedAt`、`startedAtEpochMs`、`args`。

### completed

必含：started 身份与时间、`endedAt`、`endedAtEpochMs`、`durationMs`、`status`、`isError`、`errorMessage`、`resultSummary`。

- `durationMs` 使用进程单调时钟计算，墙钟字段只用于跨记录定位。
- `status=success|error|timeout` 描述 MCP 调用边界，不替代响应中的业务 `status/reasonCode`。
- Axios `ECONNABORTED`、`ETIMEDOUT`、HTTP 408/504 或明确 timeout message 归类为 `timeout`。
- completed 不重复请求参数或完整结果；`resultSummary` 只保留 `contentItemCount`、`textLength` 和最多 512 字符的 `textPreview`。

进程或外层 Agent 在完成前中断时，JSONL 会保留没有 completed 配对的 started 事件。它只表示“MCP 已观测到开始，但未观测到结束”，不得伪造结束时间，也不得自动解释为业务失败。

## 边界

- 本契约覆盖 MCP 工具调用，不覆盖 AI 隐式思考时间，也不记录或要求原始 chain-of-thought。
- D4 等设计理由若后续需要强制审计，应另建结构化 decision record，并引用输入、候选和 artifact；不得混入本调用计时日志。
- started 当前记录调用参数，因此调用方不得通过工具参数传入密钥、账号凭据或其他不应落盘的敏感值。

## 验收

- 任意已完成调用必须存在同 `callId` 的 started/completed 对。
- completed 必须满足 `endedAtEpochMs >= startedAtEpochMs` 且 `durationMs >= 0`。
- 超时、普通异常和成功必须分别落入 `timeout`、`error`、`success`。
- 大响应不得被完整复制到 completed 事件。
