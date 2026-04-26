# T3 单大陆扩张入口代码导览

## 实现位置

- HTTP 路由：`StructureBinder/src/main/java/com/user/terra_script/server/ModHttpServer.java`
- Controller：`StructureBinder/src/main/java/com/user/terra_script/server/mcp/TerritoryController.java`
- 阶段编排：`StructureBinder/src/main/java/com/user/terra_script/domain/territory/stage/TerritoryStageOrchestrator.java`
- 完整阶段入口：`StructureBinder/src/main/java/com/user/terra_script/domain/territory/stage/T3Stage.java`

## 当前职责边界

- `/t3_run_continent` 只负责单大陆 T3 扩张入口、结果导出后的 HTTP 响应汇总和零面积门禁。
- T3 扩张算法仍由 `TerritoryManager.runExpansionForContinent(...)` 承载。
- 完整阶段 `T3Stage.execute(...)` 的全局零面积检查保持不变。

## 响应构造

`TerritoryController.buildT3RunContinentResponse(...)` 负责：

- 统计 `claimed_total`
- 统计 `wild_total`
- 输出 per-territory `claimed_chunks / wild_chunks`
- 当 `claimed_total + wild_total == 0` 时返回 `409` 响应体

这个 helper 可用纯单元测试覆盖，不需要启动 HTTP server 或 Minecraft server。
