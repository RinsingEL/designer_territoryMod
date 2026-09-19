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

配置不改变城区边界算法。D5 墙线、墙带 mask、塔位和预留城门是墙体的施工权来源；建筑、道路、绿化与铺地必须遵守预留。城墙不依赖 D7 实际建筑账本、全城地表完成状态或实际道路扫描，开门只依据 D5 gateSlots。自动流程在 D5 激活后独立规划并执行墙体，再继续 D7。施工只采样自身墙段/塔位地形，校验模块不得越出墙带与塔位；地形、模块、方块实体等自身安全检查保留。成功施工保存世界并记录计划 hash，续跑不重复砌墙。手动施工接口仍要求显式世界修改确认。

## 当前验收边界

独立配置加载、文件保留、素材更新与快照失效执行自动化验证；世界内墙塔衔接仍需实测。局部地形高程、挡土基础和阶梯连接已有实现；不改变 D5 墙线，不自动绕河。

城墙访问区块前检查墙段、塔位及其生成依赖区域的地理开放状态；未开放返回 waiting_for_worldgen，不伪装为已施工。已激活城市的后半段运行、重试、程序失败和局部完成状态不撤销生成开放资格；仍要求国度定稿和实际结构/地表激活证据，不开放待设计城市。

## 分段地形施工（2026-09-20）

`terrainFitPolicy.heightStrategy` 和 `wallPlacementProfile.policy` 为 `terrain_following_sections`。不再使用整圈共用 baseY，也不因整圈最高/最低差值返回 WALL_TERRAIN_REQUIRES_REDESIGN。墙段按局部采样中位数取目标基准，每个五格横断面保持水平；相邻断面最多差一格并落台阶。塔楼和同一个 gateSlotId 的门洞各自保持平台，连接高程在附近墙段逐级过渡。门洞顶板相对门区最高现状地面至少四格净空；不等待 D7 道路。

冻结 profile 记录 minBaseY/maxBaseY/minSurfaceY/maxSurfaceY、transitionCount、foundationColumnCount、embeddedColumnCount；surfaceColumns 中每列保存 surfaceY/baseY/walkwayFloorY/terrainMode。墙段和塔楼保存自己的 minBaseY/maxBaseY/baseY 与 terrainMode。旧的高差调节选项只保留请求兼容，不再决定整圈拒绝阈值。

低地只在墙/塔预留内补基础，向下寻找实体支撑，水面不作为地基。山地允许墙体嵌入，保留步道以下的模板空气位置原有山体；步道处清出净空。洞口封闭范围限定为墙带内、全墙最低地表下两格至该列基准/地表之间的空气和流体，不进行无限地下封堵，门洞除外。

天然屏障必须经过实际方块检查：五格完整横断面在冻结勘测下界到该列 baseY+12 全部是无流体的完整自然实体，且山顶高于这一范围，才能标为 natural_barrier；门洞和塔位不省略。只看 surfaceY 不构成天然屏障证据，砂/砾石等重力材料也不作为此类证据。执行时重查，若屏障变化，回退为同一墙带内的实体墙和封洞，不跳过空洞。执行报告区分阶梯块数、封洞块数和天然屏障断面数。

重试时旧的未施工等高计划自动重算；已有与计划 hash 匹配的成功施工报告仍复用，避免因升级重砌已经成功的墙。未做真实世界体素校验的离线回放不证明山体屏障或最终通行效果。
