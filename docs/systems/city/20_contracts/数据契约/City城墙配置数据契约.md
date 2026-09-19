# City 城墙独立配置

用户 2026-09-19 确认：“城墙就该自己走自己的配置……不能从普通建筑走”。

## 配置入口与职责

游戏实例 `config/geomantia/city_walls/modules.json` 是城墙专用入口。启动时安装缺失的默认配置和模块文件，已有文件不覆盖；规划和执行时重新读取。普通建筑的 template catalog、语义 profile、入口审核与内容包 manifest 均不包含这些城墙模块，AI 普通建筑候选池也不包含它们。

```json
{
  "schema": "city_wall_modules",
  "moduleSet": "guard_tower",
  "connections": {"walkwayFloorY": 9, "passageHeadroom": 2},
  "foundationBlock": "minecraft:stone_bricks",
  "modules": {
    "guardTower": "modules/guard_tower.nbt",
    "straightWall": "modules/wall_straight.nbt"
  }
}
```

模块路径相对专用配置目录，不允许越出目录。格式为压缩的 Minecraft structure NBT，不直接接受 `.litematic`。默认守卫塔来自用户指定的 `ac3 城墙守卫塔.litematic`，已做四向步道连接；长墙段为配套制作的 NBT。

当前只支持这套连接几何：塔楼 X/Y/Z 为 7/15/10，长墙段为 16/12/5，步道局部 Y9、净空 2 格。连接字段用于校验兼容性，不意味着支持任意尺寸。替换模块可修改外观和方块，须保留步道、开口、楼梯及对应连接位置；目前不自动证明通行拓扑。NBT 必须完整覆盖体素网格，不能包含实体或方块实体数据。执行前检查实际方块注册与方块实体类型。

基础材质使用 `foundationBlock` 的默认方块状态，拒绝未知方块、空气、流体与方块实体。墙段实际施工读取 `straightWall` 的方块数据；Z 向段旋转方块状态，门洞保留步道以上结构。塔楼读取 `guardTower`，不转入普通建筑施工链。

## 冻结与执行

真实世界规划将配置和两个模块文件的 SHA-256 写入 `wallModuleSnapshot`，并在 `templateLibrary.configuration` 中记录配置。执行前重新加载，配置或任一模块变化时拒绝旧计划，返回 `WALL_MODULE_CONFIGURATION_CHANGED_REPLAN_REQUIRED`（执行接口包装于 `WALL_MODULE_LOAD_FAILED`），必须重新规划。无快照的旧计划也要重新规划。

artifact 的 `city_wall_templates/` 保存配置、模块、快照和库描述；模块路径与配置相符。离线几何测试未绑定真实世界时仍可导出内置模块，但其计划不能直接用于真实施工。

配置不负责开启施工，也不改变城区边界算法。仍须经过 D5 墙线预留、D7 实际建筑账本、真实出城道路与地形校验，再调用 `city_plan_city_walls`、`city_execute_city_walls`。工作流启用 `planWalls` / `executeWalls`；施工沿用显式世界修改确认。

## 当前验收边界

独立配置加载、文件保留、素材更新与快照失效执行自动化验证；世界内墙塔衔接仍需实测。大高差自动节点和绕河重规划尚未实现，不因配置开放而改变。
