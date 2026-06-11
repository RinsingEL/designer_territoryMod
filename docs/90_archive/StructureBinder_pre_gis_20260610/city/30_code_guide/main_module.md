# 主模块代码导览

当前主模块代码导览真值已迁移到目录化结构，旧文件保留为兼容入口。

## 当前主入口

- 代码导览：`./main_module/代码导览.md`
- 功能实现：`./main_module/功能实现/C7工头计划.md`
- 功能实现：`./main_module/功能实现/C8节点会话与提交.md`
- 功能实现：`./main_module/功能实现/C8子节点Jigsaw求解.md`

## 当前边界说明

- 主模块目录当前重点维护 `C7`、`C8` 与 `jigsaw` 求解实现。
- `C9` 执行层请继续查看 `./c9_execution.md`。

- `src/main/java/com/user/terra_script/server/mcp/CityController.java`
- `src/main/java/com/user/terra_script/world/city/stage/c7/CityC7Stages.java`
- `src/main/java/com/user/terra_script/world/city/stage/c8/CityC8Stages.java`
- `src/main/java/com/user/terra_script/world/city/stage/c8/CityC8ArrangementEngine.java`
- `src/main/java/com/user/terra_script/world/city/stage/c9/CityC9Stages.java`
- `src/main/java/com/user/terra_script/world/city/execution/BuildExecutionPipeline.java`
- `src/main/java/com/user/terra_script/world/StructureInjector.java`

## 阅读顺序

1. `CityController`
2. `CityC7Stages`
3. `CityC8Stages`
4. `CityC8ArrangementEngine`
5. `CityC9Stages`
6. `world/city/execution/*`
7. `StructureInjector`

## 当前职责摘要

- `CityC7Stages`
  - 产出工头计划
- `CityC8Stages`
  - 管理节点会话、提交、失败、重试
  - 承担 child 节点落地前程序校验
- `CityC8ArrangementEngine`
  - 负责 connector 匹配、世界坐标推导、child origin / rotation 求解能力
  - 应成为 child 节点的标准求解层，而不是继续作为旁路工具代码
- `CityC9Stages`
  - 生成可执行计划与队列
- `world/city/execution/*`
  - 运行时区块门控、清空、放置、校验与失败策略
- `StructureInjector`
  - 保留直接 `place` facade
  - 保留 `start` 节点可用的直接放置能力
  - 为执行层与后续求解器提供真实模板 bounds 与实际落地入口

## 当前关键边界

- 工头系统负责“选哪个节点、哪个结构、哪个阶段”
- 求解器负责“这个结构怎么接上去”
- `C9` 负责“这个已求解节点在当前世界里能不能执行”
- `start` 直接放置与 child 求解放置需要长期并存
