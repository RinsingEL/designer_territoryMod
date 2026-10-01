"""Prepare inherited Yucen context using the same question and reference scope."""
from pathlib import Path
import json,re,shutil,hashlib
ROOT=Path(__file__).resolve().parents[1]
TASK=ROOT/'data/第二题_榆岑城市设计'
SOURCE=ROOT/'data/第一题_国度设定'
REF=ROOT/'data/第二题_领土内城市选址'
SRC=Path(r'D:\PCL2-2.8.12\.minecraft\versions\1.20.1-Forge_47.4.23\saves\geometia_beta2_08 (1)\realm_debug\provider_ffffffff825a07bd_r19200')
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
def write(name,s):(TASK/name).write_text(s,encoding='utf-8')
data=read(TASK/'榆岑领土数据.json')['cells']
stat=next(c for c in read(SRC/'t3_report.json')['realmStats'] if c['realmId']=='realm_yucen')
assert stat['neighbors']==['realm_nashir']
stats={}
for k in ['temperature','moisture']:
    v=sorted(c[k] for c in data);stats[k]={'min':v[0],'median':v[(len(v)-1)//2],'max':v[-1]}
t,m=stats['temperature'],stats['moisture']
shutil.copy2(SOURCE/'03_功能与空间标签.md',TASK/'03_功能与空间标签.md')
s=(REF/'04_共有生活与城市职能.md').read_text(encoding='utf-8').replace('奥伦','榆岑').replace('维伦工匠文化、Create、Immersive Engineering、Chipped',"岑岚庭园文化、Botania、Ars Nouveau、Farmer's Delight").replace('机械制造不只是制作更多机器，也可以支持共有生活和地方生产','魔法与庭园活动可以支持共有生活和地方生产')
write('04_共有生活与城市职能.md',s)
mods=(SOURCE/'05_真实模组玩法与文化素材.md').read_text(encoding='utf-8')
parts=[re.search(r'### '+code+r'\b.*?(?=\n### |\Z)',mods,re.S).group(0).strip() for code in ['P07','P05','P09']]
write('05_榆岑相关模组玩法.md',"# 榆岑相关模组玩法\n\nBotania、Ars Nouveau、Farmer's Delight 是已确认的主要方向，原版生活和通用职能见04；不是全国所有活动的穷尽清单。城市按需求选择侧重，不必每城全部采用。摘录第一题2026-09-28核实的资料，保留来源，本次不新增模组事实。设计目标不等于已安装或已接通NPC系统，两套魔法系统不默认互通。\n\n"+'\n\n'.join(parts)+'\n')
write('06_榆岑相关风格.md','''# 榆岑相关风格

继承岑岚庭园文化：中式院落与植被穿插，木梁、浅灰墙、瓦檐和花架，庭园兼具生活与生产意义。本轮选择城市的地方风格及环境依据，不展开单城内部布局。

| 风格 | 作者资料中的方向 |
|---|---|
| 精灵 | 木构、树体与自然形态，生活空间与植被交织；为风格参考，不指定居民种族或证明当地林木储量。 |
| 中式 | 院落、街巷、门廊、院墙与园林；第一题素材中属于尚未建模的候选方向，不保证现成资产。 |

可按实际地形与温湿度形成地方差异，不要求每城成为同一种花园展示地。家宅、生产、交易与公共生活均可承载这套风格。

来源：第一题06风格素材与已采用T1答卷。背景中的院落和植被关系是后续设计参考，本题不要求展开相邻关系或街区。
''')
write('榆岑_最新国度设定.md',f'''# 榆岑：第二题继承的国度设定

沿用已采用的T1设计，国土采用本存档真实T3扩张结果。国度的文化与模组倾向仍是主要方向；通用职能和原版生活自然参与。以下空间习惯是后续单城设计背景，本轮不要求展开。

| 项目 | 已确认内容 |
|---|---|
| 文化与命名 | 岑岚庭园文化；两字旧地名，以树木、地貌或天气意象组合，避免把职业和模组写进城市名。 |
| 风格 | 中式院落与精灵式植被穿插，木梁灰墙、瓦檐和花架；庭园兼作生产空间，不只是观景绿地。 |
| 生计与生活 | 农事、园艺、料理、木作与家庭魔法，经营菜园、花木及魔法材料加工；村落与城镇交换种苗、食材、手艺和庭园作品。 |
| 共同习惯 | 邻里共餐与学徒展示，生产庭园兼顾日常使用与维护，前院接待、后院劳作，生产花园保留检修通路。 |
| 主要模组倾向 | Botania＋Ars Nouveau＋Farmer's Delight；玩家经营工作花园、自编法术、种植与做饭。功能花、活木、活石、魔源宝石与食材构成需求；两套魔法各自运行，不默认Mana与魔源互通。 |
| 当前国土 | C82中南部及南伸陆地，实际国界见五图和领土JSON，共{len(data)}个128方块owned粗格。国家起点不预定首都，城市数量没有预设。 |

## 实际环境与关系

温度参数范围{t['min']:.3f}–{t['max']:.3f}，中位数{t['median']:.3f}；湿度范围{m['min']:.3f}–{m['max']:.3f}，中位数{m['median']:.3f}。统计取国土粗格中心，不是气象单位或作物适生证明。原T1的温湿与森林/平原描述是粗读背景，选址以当前图面和数据为准；本题未提供实测群系图，不把背景推断当作已证实群系。

实际接壤国家为纳希尔，偏围院、织物、陶作、畜群照护与小片农作。原设计允许交换织物、器皿、食材和庭园作品；位置关系已由T3确定，道路、贸易机制和供给数量尚未验证，不预设门户或交通线。

03/04/05/06是落实设计的参考，可按地方条件选择和组合；既定文化与模组是主要方向，不排除原版生产生活。可以设计计划种植、加工与消费的具体内容，已有资源与产量需另行验证。城市可以重复职能、共享物产，不能因资料缺少实测资源就回避具体生活设计。

来源：采用的T1文化圈与国度答卷、realm_yucen的正式T3领土和报告、同源W特征与气候数据。本题只做多城定位与粗尺度选址。
''')
guide=(REF/'设计任务与读图说明.md').read_text(encoding='utf-8').replace('奥伦','榆岑').replace('C6为初始大陆，旧C6的A/B采样已停用。','C6为初始大陆，不参与本题；当前资料仅包含榆岑国土。')
write('设计任务与读图说明.md',guide)
task=(ROOT/'data/题目/02_奥伦选址判断.md').read_text(encoding='utf-8').replace('奥伦','榆岑').replace('不把全国产业缩成机器制作与维修','不把全国产业缩成魔法材料制作或庭园展示').replace('第二题_城市设计_YYYYMMDD_HHMMSS.md','第二题_榆岑城市设计_YYYYMMDD_HHMMSS.md')
write('题目.md',task)
source={'sourceWorld':'geometia_beta2_08 (1)','sourceRun':str(SRC),'realmId':'realm_yucen','formalT3':True,'sampling':'sealed W, 128-block cells; not new T4 fine scan','climateStats':stats,'neighbors':stat['neighbors'],'hashes':{n:hashlib.sha256((SRC/n).read_bytes()).hexdigest() for n in ['realm_territory_map.json','world_feature_grid.json','world_climate_grid.json']}}
write('来源.json',json.dumps(source,ensure_ascii=False,indent=2))
print(json.dumps({'realm':'榆岑','ownedCells':len(data),'climate':stats,'output':str(TASK)},ensure_ascii=False))

# Shared code-scale reference for future independent tasks.
from pathlib import Path as _Path
_preview_root = _Path(__file__).resolve().parents[1]
(_preview_root / 'data/第二题_榆岑城市设计/07_城市尺度与预览.md').write_text((_preview_root / 'data/题目/07_城市尺度与预览.md').read_text(encoding='utf-8'), encoding='utf-8')
