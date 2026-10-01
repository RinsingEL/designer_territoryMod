"""Offline W-scale proposals, NOT Patch Explorer selections or submitted T2 seeds."""
import json, math, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(r'D:\PCL2-2.8.12\.minecraft\versions\1.20.1-Forge_47.4.23\saves\geometia_beta2_08 (1)\realm_debug\provider_ffffffff825a07bd_r19200')
OUT = ROOT/'archive/旧结果'/'T1扩张起点建议'
OUT.mkdir(parents=True, exist_ok=True)
def read(p): return json.loads(p.read_text(encoding='utf-8'))
world = read(SRC/'world_patch_map.json')
features = {(c['gridX'], c['gridZ']): c for c in read(SRC/'world_feature_grid.json')['cells']}
climate = {(r[0],r[1]): r for r in read(SRC/'world_climate_grid.json')['cells']}
# Manually interpreted regional targets from T1 and maps. Climate ranges are
# selection preferences for this proposal, not new country definitions.
# name, continent, target X/Z, temperature interval, moisture interval, rationale
specs = [
 ('萨维拉',6,6500,-15400,(.65,1),(.55,1),'北岸暖湿带后方，沿岸与谷地联系；为内陆奥伦保留向南发展的空间。'),
 ('奥伦',6,4200,-12200,(.4,.6),(.15,.55),'中北部温和内陆，选择低地或谷地作为扩张支点，周边丘岭留给分台地工场。'),
 ('斯凯恩',6,5200,-6200,(0,.25),(.1,.65),'中南部冷带腹地，承接长厅、室内生活与远行补给设定。'),
 ('哈尔维',20,-11600,-7600,(0,.4),(.4,1),'大陆中北部冷带，兼顾谷地联系与向岸地扩展；南部过渡区留作后续延伸。'),
 ('纳希尔',82,-8500,6200,(.8,1),(0,.4),'北部偏热且偏干的内陆，符合围院、遮棚、织物与畜群照护需求。'),
 ('榆岑',82,-6000,12300,(.4,.65),(.4,.85),'中南部温和过渡地，连接南伸陆地，适合庭园村落与生活组团分布。'),
 ('贝莱萨',56,6800,-900,(.4,.65),(.6,1),'北半部偏西湿润地带，向西岸展开接待与船具服务，向内陆连接庭园和学习空间。'),
 ('塔希兰',56,6500,5000,(.8,1),(.15,.55),'南半部热区内陆，向较干一侧发展围院聚落，同时保留与北部往来的陆地联系。'),
 ('维伦',9,17000,-11500,(.3,.6),(.2,.7),'已扫描西侧腹地的温和至冷带过渡，避开最东侧截断边界，作为工匠组团的起点。'),
 ('青岚',76,17100,2900,(.4,.65),(.2,.65),'北部温和内陆，后续可向西侧湿润岸地展开，避开南部热区成为唯一中心。'),
 ('梅里萨',129,7200,16900,(.25,.6),(.3,.8),'可见北部陆地，保留向两侧岸地扩展的余地，不依赖扫描外南部土地。'),
]
selected=[]
for name, cid, tx,tz,tr,mr,reason in specs:
    options=[]
    for c in world['cells']:
        if c.get('continentId') != f'continent_{cid}' or c['landWater']!='land': continue
        key=(c['gridX'],c['gridZ']); f=features[key]; r=climate[key]
        x,z=r[2:4]
        if math.hypot(x-tx,z-tz)>2200 or abs(x)>18432 or abs(z)>18432: continue
        if not tr[0]<=r[4]<=tr[1] or not mr[0]<=r[5]<=mr[1]: continue
        if f['waterFrac']>.125 or f['robustRelief']>24 or c['landform']=='cliff': continue
        if c['baseLandform'] not in ('lowland','valley'): continue
        score=math.hypot(x-tx,z-tz)/128 + f['robustRelief']*.6 + f['waterFrac']*30
        options.append((score,c,f,r))
    if not options: raise ValueError(f'No candidate: {name}')
    _,c,f,r=min(options,key=lambda a:a[0])
    selected.append(dict(name=name,continentId=f'continent_{cid}',gridX=c['gridX'],gridZ=c['gridZ'],blockX=r[2],blockZ=r[3],baseLandform=c['baseLandform'],landform=c['landform'],temperature=r[4],moisture=r[5],heightP50=f['heightP50'],robustRelief=f['robustRelief'],waterFrac=f['waterFrac'],patchId=c['patchId'],reason=reason))
assert len({(s['gridX'],s['gridZ']) for s in selected})==11
minimum=min(math.hypot(a['blockX']-b['blockX'],a['blockZ']-b['blockZ']) for i,a in enumerate(selected) for b in selected[i+1:])
doc={'status':'offline_W_proposal_not_submitted','sourceWorld':'geometia_beta2_08 (1)','sourceRun':str(SRC),'cellStepBlocks':128,'coordinateMeaning':'W cell center; not capital coordinates, not a 32-block T Patch anchor','minimumPairDistanceBlocks':minimum,'pending':['32-block Patch Explorer candidate selection','runtime initial activity area, reservations and seed legality validation','T3 expansion parameters and execution'],'sourceHashes':{n:hashlib.sha256((SRC/n).read_bytes()).hexdigest() for n in ['world_patch_map.json','world_feature_grid.json','world_climate_grid.json']},'seeds':selected}
(OUT/'扩张起点建议.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# T1 收尾：11 国扩张起点建议','', '沿用本次 T1 的文化、国度和大致分布，仅补扩张起点建议。坐标为 W 的 128 格单元中心，不是首都或城市位置。','', '**状态：离线选点，尚未提交 T2、执行 T3。** 使用真实 W 地貌、格内高差和原生温湿度核对；还不是正式 32 格 Patch Explorer 的选择结果。','', '| 国度 | 陆块 | 建议 X / Z | W 格坐标 | 温度 / 湿度 | 高度P50 / 格内高差 | 选择理由 |','|---|---|---|---|---|---|---|']
for s in selected:
    lines.append(f"| {s['name']} | {s['continentId'].replace('continent_','C')} | {s['blockX']} / {s['blockZ']} | {s['gridX']}, {s['gridZ']} | {s['temperature']:.2f} / {s['moisture']:.2f} | {s['heightP50']:g} / {s['robustRelief']:g} | {s['reason']} |")
lines += ['', '## 选点依据与下一步','', '- 根据 T1 与图面人工指定各国的目标区域，再在附近 2200 方块内筛选同大陆陆地；偏好低地或谷地，排除崖壁分类、高水占比和过大的格内高差。筛选脚本中的温湿度区间是本次辅助选点偏好，不改写 T1。','- 数值为 W 粗尺度证据；温湿度是无量纲生成器参数。选点不证明港口、淡水、道路或可施工面积。',f'- 11 个起点互不重复，最近两点相距约 {minimum:.0f} 方块。C9、C76、C129 只使用扫描内土地，不补画边界外地形。','- 同大陆的南北位置与气候差异已保留，但仅有种子不能保证扩张后的国界符合设定；扩张面积与偏好仍需按 T1 配置并检查结果。','- 接入程序时，以这些位置意图为依据打开对应大陆的 Patch Explorer，在附近适合的地貌候选中确认起点；接受程序合法性检查后再运行 T3。若候选不能落实原位置意图，应记录调整理由。','- 第二题改为扩张完成后的 T4 城市选址；原 A/B 局部采样保留，不能作为本次 11 国扩张种子的替代。','', '来源：result/T1_文化圈与国度_20260928_本次/T1_文化圈与国度设计.md；当前存档 sealed W 地貌、特征格和原生气候数据。']
(OUT/'扩张起点说明.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
im=Image.open(ROOT/'data/第一题_国度设定/01_世界GIS/W01_世界地貌.png').convert('RGB'); d=ImageDraw.Draw(im)
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
d.rectangle((0,0,1400,100),fill='#f4f3ee');d.text((35,20),'T1 收尾｜11 国扩张起点建议',font=font(30),fill='#233042');d.text((35,65),'W 粗格中心 · 尚未提交 T2 / 执行扩张 · 点位不是首都，未划国界',font=font(18),fill='#526277')
for s in selected:
    x=90+(s['blockX']+19456)/38912*960;y=140+(s['blockZ']+19456)/38912*960
    d.ellipse((x-6,y-6,x+6,y+6),fill='#ef6844',outline='white',width=2)
    label=s['name']; bx=x+10;by=y-23
    box=d.textbbox((bx,by),label,font=font(19));d.rectangle((box[0]-3,box[1]-3,box[2]+3,box[3]+3),fill='#17263b');d.text((bx,by),label,font=font(19),fill='white')
im.save(OUT/'扩张起点总览.png')
print(json.dumps(selected,ensure_ascii=False,indent=2))
