# 附属规划流程 Java 接口 v1

对应产品当前案：[附属模组规划流程扩展](../../10_product/案子/附属模组规划流程扩展-v0.1/README.md)。本接口负责追加设计任务，与[附属区域预留接口](附属区域预留Java接口.md)分别使用。

## 生命周期与挂接点

主模组启动当前服务器的规划服务时，在服务端线程向 `MinecraftForge.EVENT_BUS` 发布 `RegisterPlanningExtensionsEvent`。附属模组在事件内调用 `event.register(extension)`；事件返回后禁止继续注册。登记结果属于当前服务器实例，关闭世界后不会保留旧 Java 实例，下次启动重新登记。

v1 提供 `PlanningHook.AFTER_CITY_PLANNING`：当前城市蓝图已完成编译、城市队列条目为 `waiting_for_generation`，在统一规划会话开始下一座城市或下一国度之前执行附属任务。无需等待玩家加载城市区块。尚未完成或编译失败的城市不会触发此挂接点。

城市队列中的 `waiting_for_generation` 继续表示地形/结构规划已准备好；统一规划会话在附属设计未完成时显示 `EXTENSION`，不会把整个设计流程报告为完成。本接口不改变区块放行规则，涉及生成地形或大型结构的附属仍应使用区域预留接口。

未安装任何扩展时维持原有流程。给已有世界安装扩展后，已到达挂接点、缺少该扩展有效回执的城市也会获得任务；不需要回填的城市可由扩展的 `applies` 明确跳过。

## 公开 API

包：`com.rinsing.geomantia.api.planning`。

- `PlanningExtension.API_VERSION = 1`。
- `RegisterPlanningExtensionsEvent`：`server()`、`register(PlanningExtension)`。
- `PlanningExtension`：标识、版本、标题、挂接点、前置依赖、工具，以及适用性、任务准备、执行、完成判定回调。
- `PlanningTool`：工具名、说明、参数 JSON Schema。
- `PlanningExtensionContext`：当前世界规划 run、国度、城市、资料目录、输入与任务版本，以及国度设定、城市种子和已保存蓝图。

注册形式：

```java
@Mod.EventBusSubscriber(modid = "exampleaddon", bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class PlanningRegistration {
    @SubscribeEvent
    public static void register(RegisterPlanningExtensionsEvent event) {
        event.register(new CityResidentsPlanning(event.server()));
    }
}
```

`CityResidentsPlanning` 由附属实现 `PlanningExtension`，在自身业务服务中准备资料、校验及发布配置。可运行的最小示例与断点恢复用例见实现仓 `src/test/java/com/rinsing/geomantia/systems/provider/application/PlanningExtensionsTest.java` 中的 `Addon`。测试实现使用文件保存结果；实际模组可采用自身持久化事务。

## 注册元数据

| 方法 | 含义 |
| --- | --- |
| `id()` | 稳定命名空间 ID，例如 `realmfolk:city_residents`，不重复 |
| `version()` | 扩展业务契约版本字符串；改变结果语义、工具定义或发布规则时升级 |
| `title()` | 当前任务的人类可读名称 |
| `hook()` | 默认 `AFTER_CITY_PLANNING` |
| `after()` | 同挂接点必须先完成的扩展 ID；默认空 |
| `tools()` | 当前扩展允许的工具定义 |

元数据在注册时冻结。依赖按拓扑顺序运行；同等条件按 ID 稳定排序。重复 ID、重复工具名（含主模组工具）、不存在的依赖、循环依赖及不支持的 schema 均拒绝登记。工具名采用模型兼容的英文字母、数字、下划线或连字符，建议以附属名为前缀。

v1 保护上限：每服务器最多 128 项扩展，每扩展 1–32 个工具。注册是可信 Java 模组接口，不能由 AI 提交脚本、类名或远程执行代码。

## 上下文与回调

`PlanningExtensionContext` 的国度、城市、run 和版本由主模组提供，不能从模型参数重新选择执行范围。JSON 访问器返回副本。

- `inputRevision`：国度设定、城市种子、蓝图的规范化 JSON 摘要；键顺序改变不会产生新任务。
- `taskRevision`：包含输入摘要、当前扩展 ID/版本及递归依赖版本的任务摘要。附属应以 **run + city + taskRevision** 作为幂等和结果有效性依据。
- `runDirectory`：当前存档规划资料目录。工具返回简明材料，其他资料可以由主 MCP 的 `planning_artifact` 按需读取；不必把整份蓝图传给模型。

所有业务回调均由主模组调度到服务器线程，不能在回调中等待模型、执行网络长请求或阻塞式轮询：

1. `applies(context)`：判断该城市是否需要此任务。false 保存跳过回执，不消耗模型调用。
2. `isComplete(context)`：检查附属已经持久化的结果是否对应此 `taskRevision`。准备任务前检查，成功工具执行后再次检查。
3. `prepare(context)`：返回当前任务的说明、作者配置目录或其他必要事实。作为 `state.extensionTask` 交给 AI，不覆盖主模组身份字段。
4. `execute(context, tool, arguments)`：执行当前任务声明的工具。主模组先验证工具范围与参数形状；附属继续校验物品、配置引用、版本等业务规则。

输入可纠正时返回 `{ "ok": false, "error": "具体问题" }`。程序故障抛出异常，主流程报告 `PLANNING_EXTENSION_FAILED` 并保留当前任务。成功输出被包在 `extensionOutput` 内；附属返回的 `hostDecisionCommitted` 等字段不能单独结束任务。只有主模组检查完成后才写完成回执。

执行必须能够容忍崩溃后的重试：先持久化发布结果，再令 `isComplete` 返回 true。主模组在调用前再次检查完成状态，可恢复“附属已发布、宿主尚未记回执”的中断；不承诺为任意附属副作用提供跨模组原子事务。

## 工具 Schema 与模型入口

v1 支持有明确 `type` 的 object、array、string、integer、number、boolean、null，以及 `properties`、`required`、`additionalProperties`、`items`、`enum`、数值上下界、字符串/数组长度界限、description/title/default。数组必须提供 items。暂不接受 `$ref`、oneOf 等其他关键字，避免声明与实际校验不一致。

工具定义由同一个任务提供给外部 `planning_resume → planning_action`、内置 Harness，以及直接 Provider 的 Responses/Chat Completions 两种协议。扩展工具走当前任务的 Java 回调，无需由主模组 HTTP 调用附属 MCP。

原有任务占用、taskId、actionId、重复请求回执、失败预算继续适用。不同扩展或其他城市的工具不在当前作用域内。

## 存档与恢复

宿主回执：当前 run 的 `automation/planning_extensions/<citySeedId>.json`，schema 为 `planning_extension_receipts.v1`。文件记录当前输入版本、已开始批次需要的扩展及各任务的完成/跳过版本，使用临时文件替换方式写入。

- 相同输入及扩展版本的有效回执不会再次调用业务执行。
- 输入、扩展版本或依赖版本改变时，对应任务重新进入调度；旧回执不能代表新任务完成。
- 准备好的任务执行前重新检查城市输入；变更后拒绝旧任务。
- 已经登记进当前城市批次的未完成扩展缺失时明确报告 `PLANNING_EXTENSION_MISSING`，不静默跳过。
- 不适用的扩展保存跳过回执，后续依赖可继续；依赖若要求实际业务内容，应在自身校验中检查。
- 无法读取必要蓝图、上下文或回执时报告错误，不用默认数据伪造完成。

当前仅提供上述城市挂接点。Realmfolk 的居民与经济实现仍需在附属侧实现并注册任务，本接口本身不会自动生成 NPC 或修改商品。
