"""Read existing real T3/W artifacts; build Yucen comparison inputs without game mutations."""
import json, hashlib, re, shutil, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
TASK=ROOT/'data/第二题_榆岑城市设计'
TASK.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
def write(p,s):p.write_text(s,encoding='utf-8')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2))
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
with urllib.request.urlopen('http://localhost:5000/realm/status',timeout=15) as response:status=json.load(response)
assert status['ok'] and status['debugRoot'].endswith('geometia_beta2_08 (1)\\realm_debug')
SRC=Path(status['debugRoot'])/'provider_ffffffff825a07bd_r19200'
territory=read(SRC/'realm_territory_map.json');report=read(SRC/'t3_report.json')
world=read(SRC/'world_patch_map.json');cells={(c['gridX'],c['gridZ']):c for c in world['cells']}
feat={(c['gridX'],c['gridZ']):c for c in read(SRC/'world_feature_grid.json')['cells']}
climate={(r[0],r[1]):r for r in read(SRC/'world_climate_grid.json')['cells']}
owned={(c['gridX'],c['gridZ']):c['realmId'] for c in territory['territoryCells'] if c['status']=='owned'}
stat=next(c for c in report['realmStats'] if c['realmId']=='realm_yucen')
assert stat['largestComponentRatio']==1
land={k for k,v in owned.items() if v=='realm_yucen'}
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
    pic=Image.new('RGB',(1160,1020),'#f4f3ee');dr=ImageDraw.Draw(pic);dr.text((25,15),'榆岑｜'+title,font=font(28),fill='#233042');dr.text((25,60),'白线内为实际国土；外部淡化，仅作参照。上北，X 向右增加，Z 向下增加。',font=font(17),fill='#526277');pic.paste(pix.resize((sx,sy),Image.Resampling.NEAREST),(80,120));dr=ImageDraw.Draw(pic)
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
dump(TASK/'榆岑领土数据.json',{'realmId':'realm_yucen','territoryMapId':territory['territoryMapId'],'cellStepBlocks':128,'cells':data})
