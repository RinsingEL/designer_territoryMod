# 次级建筑代码导览

## 当前实现状态

次级建筑当前尚未形成独立完整实现链，但已有明显入口可复用：

- `C6.secondary_fill`
- 主体建筑最终结果
- `C9` 队列与执行器

## 主要类入口

- `src/main/java/com/user/terra_script/world/city/stage/c6/CityC6Stages.java`
- `src/main/java/com/user/terra_script/world/city/stage/c6/PlazaRingArranger.java`
- `src/main/java/com/user/terra_script/world/city/stage/c9/CityC9Stages.java`
- `src/main/java/com/user/terra_script/world/city/CityBuildQueueExecutor.java`

## 当前建议阅读顺序

1. `CityC6Stages.LayoutPlan.secondary_fill`
2. `PlazaRingArranger`
3. `CityC9Stages`
4. `CityBuildQueueExecutor`
