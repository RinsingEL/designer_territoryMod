"""Package accepted game T3 artifacts and an independent coarse T4 exercise."""
import json, shutil, hashlib, zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'result/T3实机扩张_迁址_20260929'
SRC=Path(json.loads((OUT/'13_t3_response.json').read_text(encoding='utf-8'))['artifacts']['runDirectory'])
TASK=ROOT/'data/第二题_领土内城市选址';TASK.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
def write(p,s):p.write_text(s,encoding='utf-8')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2))
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
territory=read(SRC/'realm_territory_map.json');report=read(SRC/'t3_report.json')
profiles=read(OUT/'01_t1_request.json')['body']['realmProfiles'];names={p['realmId']:p['name'] for p in profiles}
world=read(SRC/'world_patch_map.json');cells={(c['gridX'],c['gridZ']):c for c in world['cells']}
feat={(c['gridX'],c['gridZ']):c for c in read(SRC/'world_feature_grid.json')['cells']}
climate={(r[0],r[1]):r for r in read(SRC/'world_climate_grid.json')['cells']}
starter={(c['gridX'],c['gridZ']) for c in read(SRC/'starter_realm.json')['cells']}
owned={ (c['gridX'],c['gridZ']):c['realmId'] for c in territory['territoryCells'] if c['status']=='owned'}
assert len(report['realmStats'])==11 and not set(owned)&starter
assert all(cells[k].get('continentId')!='continent_6' for k in owned)
assert all(r['largestComponentRatio']==1 and r['detachedAreaRatio']==0 for r in report['realmStats'])
formal=OUT/'正式产物';formal.mkdir(exist_ok=True)
for n in ['realm_profiles.json','realm_seeds.json','realm_coordinate_selections.json','capital_city_intents.json','realm_territory_map.json','t3_report.json','territory_repair_log.json','territory_preview.png']:
    shutil.copy2(SRC/n,formal/n)
# Re-render accepted ownership on full W extent; do not infer boundaries from seed positions.
palette=['#e86851','#4d91cb','#72ae68','#caa347','#a275be','#de8bb1','#63bdc0','#c77643','#bac75b','#7e87cf','#ab9b85']
colors={p['realmId']:palette[i] for i,p in enumerate(profiles)}
raw=Image.new('RGB',(304,304),'#295c88')
for key,c in cells.items():
    if c['landWater']=='water':continue
    raw.putpixel((key[0]+152,key[1]+152),tuple(bytes.fromhex((colors.get(owned.get(key),'#66745b') if key not in starter else '#93979c')[1:])))
im=Image.new('RGB',(1400,1160),'#f4f3ee');d=ImageDraw.Draw(im)
d.text((35,20),'11 国实际扩张结果｜C6 初始大陆保留',font=font(30),fill='#233042')
d.text((35,65),'游戏 T3 action_budget / strict 完成；按正式 territoryCells 绘制，尚未生成城市。',font=font(18),fill='#526277')
im.paste(raw.resize((960,960),Image.Resampling.NEAREST),(50,130));d=ImageDraw.Draw(im)
for i,p in enumerate(profiles):
    y=145+i*51;d.rectangle((1040,y,1063,y+23),fill=colors[p['realmId']]);d.text((1075,y),p['name']+' / '+p['targetContinentId'].replace('continent_','C'),font=font(20),fill='#233042')
for j,(c,t) in enumerate([('#93979c','初始大陆 / 保护区'),('#66745b','未分配陆地'),('#295c88','水域')]):
    y=750+j*40;d.rectangle((1040,y,1063,y+23),fill=c);d.text((1075,y),t,font=font(18),fill='#233042')
d.text((60,1110),'上北 / 下南 · X、Z ∈ [-19456,19456) · 128 方块/格 · 每国一块连续领土，无飞地',font=font(20),fill='#526277')
im.save(OUT/'实际扩张总览.png')
# Explicit T1 exclusion overlay, derived from actual protected coordinates.
p=ROOT/'data/第一题_国度设定/01_世界GIS/W06_大陆编号.png';base=Image.open(p).convert('RGBA');overlay=Image.new('RGBA',base.size);od=ImageDraw.Draw(overlay)
for gx,gz in starter:
    x=90+(gx+152)*960/304;y=140+(gz+152)*960/304
    od.rectangle((x,y,x+960/304,y+960/304),fill=(70,70,80,90))
base=Image.alpha_composite(base,overlay).convert('RGB');d=ImageDraw.Draw(base)
d.rectangle((500,410,869,444),fill='#17263b');d.text((510,413),'C6 初始大陆：不分配新国度',font=font(22),fill='white')
base.save(ROOT/'data/第一题_国度设定/01_世界GIS/W11_初始大陆排除.png')
# Standalone second exercise: authoritative border + same-frame W evidence.
aoren=next(p for p in profiles if p['realmId']=='realm_aoren')
land={k for k,v in owned.items() if v=='realm_aoren'}
minx,maxx=min(k[0] for k in land)-4,max(k[0] for k in land)+4
minz,maxz=min(k[1] for k in land)-4,max(k[1] for k in land)+4
width,height=maxx-minx+1,maxz-minz+1
layers=[('01_地貌与国界.png','W 粗地貌',None),('02_高度与国界.png','高度中位数 Y','heightP50'),('03_高差与国界.png','格内高差 P90-P10','robustRelief'),('04_温度与国界.png','原生温度参数',4),('05_湿度与国界.png','原生湿度参数',5)]
terrainColors={'water':'#2a60a4','shore':'#d6c580','lowland':'#68a856','upland':'#ac9c5c','ridge':'#929a9c','valley':'#529476'}
for fn,title,field in layers:
    pix=Image.new('RGB',(width,height),'#d4d4d4')
    for z in range(minz,maxz+1):
      for x in range(minx,maxx+1):
        k=(x,z);c=cells.get(k)
        if not c:continue
        if c['landWater']=='water':color='#2a60a4'
        elif field is None:color=terrainColors.get(c['baseLandform'],'#444444')
        elif field=='heightP50':
            v=feat[k][field];color=next(co for limit,co in [(64,'#bddaa4'),(80,'#86b777'),(100,'#c8c071'),(128,'#be965e'),(160,'#987564'),(9999,'#efebe4')] if v<limit)
        elif field=='robustRelief':
            v=feat[k][field];color=next(co for limit,co in [(4.001,'#c4debd'),(8.001,'#8fbd8c'),(16.001,'#d7d075'),(32.001,'#dba765'),(64.001,'#c67869'),(9999,'#844968')] if v<limit)
        else:
            cs=['#a6bce7','#76b7cf','#8cbd8a','#e3c579','#cc6555'] if field==4 else ['#d6b786','#c4c88f','#9abd8b','#63a687','#287f79'];color=cs[min(4,max(0,int(climate[k][field]*5)))]
        rgb=tuple(bytes.fromhex(color[1:]));rgb=rgb if k in land else tuple(int(v*.25+215*.75) for v in rgb);pix.putpixel((x-minx,z-minz),rgb)
    scale=min(1000/width,800/height);sx,sy=round(width*scale),round(height*scale)
    pic=Image.new('RGB',(1160,1020),'#f4f3ee');dr=ImageDraw.Draw(pic);dr.text((25,15),'奥伦｜'+title,font=font(28),fill='#233042');dr.text((25,60),'白线内为实际国土；外部淡化，仅作参照。上北，X 向右增加，Z 向下增加。',font=font(17),fill='#526277');pic.paste(pix.resize((sx,sy),Image.Resampling.NEAREST),(80,120));dr=ImageDraw.Draw(pic)
    for x,z in land:
      for dx,dz in [(0,-1),(0,1),(-1,0),(1,0)]:
        if (x+dx,z+dz) in land:continue
        xx=80+(x-minx)*sx/width;yy=120+(z-minz)*sy/height;cw=sx/width;ch=sy/height
        line=(xx,yy,xx+cw,yy) if dz==-1 else (xx,yy+ch,xx+cw,yy+ch) if dz==1 else (xx,yy,xx,yy+ch) if dx==-1 else (xx+cw,yy,xx+cw,yy+ch)
        dr.line(line,fill='white',width=2)
    dr.text((80,94),f'X: {minx*128} → {(maxx+1)*128}；Z: {minz*128} → {(maxz+1)*128}；128 方块/像素格',font=font(16),fill='#233042')
    for x in range((minx//8+1)*8,maxx,8):
        q=80+(x-minx)*sx/width;dr.line((q,120,q,120+sy),fill='#747474',width=1);dr.text((q,125+sy),str(x*128),font=font(13),anchor='mt',fill='#233042')
    for z in range((minz//8+1)*8,maxz,8):
        q=120+(z-minz)*sy/height;dr.line((80,q,80+sx,q),fill='#747474',width=1);dr.text((75,q),str(z*128),font=font(13),anchor='rm',fill='#233042')
    legends=['水域蓝 / 海岸米黄 / 低地绿 / 高地褐 / 山脊灰 / 谷地青绿','高度配色由低到高：<64 / 64–80 / 80–100 / 100–128 / 128–160 / ≥160','高差配色由低到高：≤4 / 4–8 / 8–16 / 16–32 / 32–64 / >64','温度由冷到热：蓝紫 / 蓝绿 / 绿 / 黄 / 红，各档 0.2','湿度由干到湿：土黄 / 黄绿 / 浅绿 / 绿 / 深绿，各档 0.2']
    dr.text((25,957),legends[[v[0] for v in layers].index(fn)],font=font(17),fill='#233042');dr.text((25,988),'W 粗尺度证据；局部城市用地仍需精扫确认，颜色不代表已验证的可施工面积。',font=font(16),fill='#526277');pic.save(TASK/fn)
data=[{'gridX':x,'gridZ':z,'blockX':x*128+64,'blockZ':z*128+64,'landform':cells[(x,z)]['baseLandform'],'heightP50':feat[(x,z)]['heightP50'],'robustRelief':feat[(x,z)]['robustRelief'],'temperature':climate[(x,z)][4],'moisture':climate[(x,z)][5]} for x,z in sorted(land)]
dump(TASK/'奥伦领土数据.json',{'realmId':'realm_aoren','territoryMapId':territory['territoryMapId'],'cellStepBlocks':128,'cells':data})
task=(ROOT/'data/题目/02_奥伦选址判断.md').read_text(encoding='utf-8')
write(TASK/'题目.md',task)
dump(TASK/'来源.json',{'sourceWorld':'geometia_beta2_08 (1)','sourceRun':str(SRC),'realmId':'realm_aoren','formalT3':True,'sampling':'sealed W, 128-block cells; not T4 fine scan','hashes':{n:hashlib.sha256((SRC/n).read_bytes()).hexdigest() for n in ['realm_territory_map.json','world_feature_grid.json','world_climate_grid.json']}})
summary=['# 迁址后的真实扩张结果','','T1 与全部11次 T2 均成功；T3 action_budget / strict 返回 completed，无 warnings/errors。初始大陆保护保持不变，正式 owned 地格与保护格交集为0。11国均只有一块连续领土，无飞地。尚未进入T4选城或生成建筑。','','| 国家 | 大陆 | 实际面积粗格 | 大陆面积比例 |','|---|---|---:|---:|']
for p in profiles:
    r=next(v for v in report['realmStats'] if v['realmId']==p['realmId']);summary.append(f"| {p['name']} | {p['targetContinentId']} | {r['areaCells']} | {r['actualAreaRatio']:.1%} |")
summary+=['','面积参数为本次实验补充，完整请求保留在01_t1_request.json。实际范围由游戏扩张生成，不是离线手绘。各国可能增长到允许最大面积附近，并非严格停在目标比例。','迁址：萨维拉→C56；奥伦→C82；斯凯恩→C20。哈尔维起点调整到C20中南部，为斯凯恩保留北部冷带。原始T1答卷作为历史保留，当前迁址说明及实际profile优先。','第二题独立资料在 data/第二题_领土内城市选址，使用迁址后的奥伦正式领土；旧A/B资料仅保留为历史。']
write(OUT/'结果说明.md','\n'.join(summary)+'\n')
print(json.dumps({'realms':len(profiles),'ownedCells':len(owned),'starterOverlap':len(set(owned)&starter),'aorenCells':len(land),'t3Status':'completed'},ensure_ascii=False))

from build_t2_context import build as build_t2_context
build_t2_context()
