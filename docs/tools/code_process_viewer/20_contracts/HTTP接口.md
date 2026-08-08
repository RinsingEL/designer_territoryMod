# Code Process Viewer HTTP 接口

当前服务默认监听 `:6657`，没有鉴权。只应在可信本机或受控局域网使用。

| 方法与路径 | 职责 |
| --- | --- |
| `GET /api/sessions` | 会话列表。 |
| `GET /api/sessions/{id}` | 会话、检查点和导入摘要。 |
| `GET /api/sessions/{id}/graph` | 节点与边。 |
| `GET /api/sessions/{id}/report` | Markdown 审查报告。 |
| `GET /api/sessions/{id}/assets/{name}` | 缓存预览图。 |
| `GET /api/nodes/{id}` | 节点详情与当前 review。 |
| `GET /api/nodes/{id}/tables` | 节点结构化表格。 |
| `POST /api/nodes/{id}/review` | 保存 `review_state` 与 comment。 |
| `POST /api/import/jigsaw-debug` | 导入已有 `jigsaw_solver_debug/<runId>`。 |

`review_state` 只允许 `pass|concern|reject|need_evidence|unchecked`。导入请求字段为 `artifact_path` 和 `replace_existing`；工具只读源调试目录，写入自身 SQLite 与 cache，不触发 Jigsaw 求解。
