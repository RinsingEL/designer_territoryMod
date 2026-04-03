# 主模块代码导览

## 主要仓库

- `StructureBinder`

## 主要类

- `src/main/java/com/user/terra_script/world/city/stage/c7/CityC7Stages.java`
- `src/main/java/com/user/terra_script/world/city/stage/c8/CityC8Stages.java`
- `src/main/java/com/user/terra_script/world/city/stage/c9/CityC9Stages.java`
- `src/main/java/com/user/terra_script/server/mcp/CityController.java`

## 阅读顺序

1. `CityController`
2. `CityC7Stages`
3. `CityC8Stages`
4. `CityC9Stages`

## 当前职责摘要

- `CityC7Stages`
  - 产出工头计划
- `CityC8Stages`
  - 管理节点会话、提交、失败、重试
- `CityC9Stages`
  - 生成可执行计划与队列
- `CityController`
  - 暴露 MCP / HTTP 入口
