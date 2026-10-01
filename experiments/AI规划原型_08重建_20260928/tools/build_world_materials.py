from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from collections import Counter
import json, hashlib, shutil, math

OUT = Path(__file__).resolve().parents[1] / 'data/第一题_国度设定'
SRC = Path(r'D:\PCL2-2.8.12\.minecraft\versions\1.20.1-Forge_47.4.23\saves\geometia_beta2_08 (1)\realm_debug\provider_ffffffff825a07bd_r19200')
FONT = 'C:/Windows/Fonts/msyh.ttc'
BG, INK, MUTED = '#f4f3ee', '#233042', '#526277'

def font(n): return ImageFont.truetype(FONT, n)
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def dump(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2), encoding='utf-8')
def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding='utf-8')
def copy(src, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)

def framed_map(raw, title, subtitle, name, legends, origin, span, sectors, note):
    im = Image.new('RGB', (1400, 1170), BG)
    d = ImageDraw.Draw(im)
    d.text((35, 20), title, font=font(30), fill=INK)
    d.text((35, 65), subtitle, font=font(18), fill=MUTED)
    ox, oy, side = 90, 140, 960
    im.paste(raw.convert('RGB').resize((side, side), Image.Resampling.NEAREST), (ox, oy))
    grid = Image.new('RGBA', im.size)
    gd = ImageDraw.Draw(grid)
    for i in range(sectors+1):
        q = round(i*side/sectors)
        gd.line((ox+q, oy, ox+q, oy+side), fill=(240,240,240,100), width=1)
        gd.line((ox, oy+q, ox+side, oy+q), fill=(240,240,240,100), width=1)
    im = Image.alpha_composite(im.convert('RGBA'), grid).convert('RGB')
    d = ImageDraw.Draw(im)
    for i in range(sectors):
        q = (i+.5)*side/sectors
        d.text((ox+q, oy-22), chr(65+i), anchor='mm', font=font(19), fill=INK)
        d.text((ox-27, oy+q), str(i+1).zfill(2), anchor='mm', font=font(19), fill=INK)
    d.text((ox, oy-50), f'西 / X={origin[0]}', font=font(16), fill=MUTED)
    d.text((ox+side, oy-50), f'东 / X={origin[0]+span}（边界）', anchor='ra', font=font(16), fill=MUTED)
    y = 145
    for color, label in legends:
        if color:
            d.rectangle((1090, y, 1112, y+22), fill=color)
        d.text((1124 if color else 1090, y), label, font=font(17), fill=INK)
        y += 34
    for line in [f'北：Z={origin[1]}', f'南：Z={origin[1]+span}（边界）', '', '上北 / 下南 / 左西 / 右东', f'每个字母数字格：{span//sectors} 方块', '格号示例：D04', '', *note]:
        d.text((1090, y+22), line, font=font(16), fill=MUTED)
        y += 29
    d.text((90, 1125), '真实存档扫描资料 · 颜色与分类是扫描输出，不等于已验证的游戏内可建造面', font=font(18), fill=MUTED)
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p)

survey = read(SRC/'world_survey_context.json')
manifest = read(SRC/'world_survey_manifest.json')
export = read(SRC/'w_manifest.json')
assert survey['sealed'] and export['sealed'] and manifest['status'] == 'sealed'
assert survey['configHash'] == manifest['configHash'] == export['configHash']
assert survey['surveyStats']['failedTileCount'] == 0
world = read(SRC/'world_patch_map.json')
feature_doc = read(SRC/'world_feature_grid.json')
assert feature_doc['configHash'] == survey['configHash']
features = {(c['gridX'],c['gridZ']):c for c in feature_doc['cells']}
bounds = survey['scanBounds']
origin = (bounds['minBlockX'],bounds['minBlockZ'])
span = bounds['diameterBlocksX']
width = survey['gridSize']['width']
step = survey['cellStepBlocks']
assert width == 304 and span == 38912 and step == 128
assert len(features) == len(world['cells']) == width*width
assert len({(c['gridX'],c['gridZ']) for c in world['cells']}) == len(features)
assert all(sum(c['biomeHist'].values()) == c['microSampleCount'] == 16 for c in features.values())
sectors = span//2048
world_colors = [('水域','#2a60a4'),('海岸','#d6c580'),('低地 / 平原','#68a856'),('高地 / 坡地','#ac9c5c'),('山脊','#929a9c'),('山谷','#529476'),('未知','#363a40'),('崖壁标签（覆盖色）','#b0484e')]
framed_map(Image.open(SRC/'world_patch_preview.png'),'W01｜08 重建世界 · 地貌','原有 W 地貌图加坐标网格；304×304 个粗格，每格 128 方块','01_世界GIS/W01_世界地貌.png',[(c,n) for n,c in world_colors],origin,span,sectors,['国度与边界尚未指定','未叠加已有规划结果'])
height_bins = [(64,'#bddaa4','<64'),(80,'#86b777','64–<80'),(100,'#c8c071','80–<100'),(128,'#be965e','100–<128'),(160,'#987564','128–<160'),(math.inf,'#efebe4','≥160')]
relief_bins = [(4.001,'#c4debd','≤4'),(8.001,'#8fbd8c','>4–8'),(16.001,'#d7d075','>8–16'),(32.001,'#dba765','>16–32'),(64.001,'#c67869','>32–64'),(math.inf,'#844968','>64')]
for field,bins,title,filename,subtitle in [
    ('heightP50',height_bins,'W02｜08 高度中位数','W02_高度中位数.png','每个 128 格单元内 16 个采样点的高度 P50；单位：方块 Y'),
    ('robustRelief',relief_bins,'W03｜08 格内高差','W03_格内高差.png','高度 P90−P10；单位：方块；不是坡度角，也不是施工结论')]:
    raw = Image.new('RGB',(width,width))
    for c in world['cells']:
        f = features[(c['gridX'],c['gridZ'])]
        color = '#2a60a4' if c['landWater']=='water' else next(color for limit,color,_ in bins if f[field]<limit)
        raw.putpixel((c['gridX']-origin[0]//step,c['gridZ']-origin[1]//step),tuple(bytes.fromhex(color[1:])))
    framed_map(raw,title,subtitle,'01_世界GIS/'+filename,[('#2a60a4','分类为水域'),*[(c,n) for _,c,n in bins]],origin,span,sectors,['底层数值来自本次扫描','水域以蓝色覆盖','陆上颜色按图例分档'])
copy(SRC/'world_biome_preview.png',OUT/'01_世界GIS/W04_推断生物群系_原图.png')
for n in ['world_patch_preview.png','world_biome_preview.png','grid_overlay_preview.png']:
    copy(SRC/n,OUT/'原始图'/n)
members = {}
for c in world['cells']:
    if c['landWater'] != 'water': members.setdefault(c.get('continentId'),[]).append(c)
continents=[]
for cont in world['continents']:
    if cont['areaCells']<300: continue
    cells=members[cont['continentId']]
    cx,cz=cont['centerBlock']['x'],cont['centerBlock']['z']
    anchor=min(cells,key=lambda c:(c['blockX']-cx)**2+(c['blockZ']-cz)**2)
    continents.append({**cont,'nonWaterCellsCounted':len(cells),
        'baseLandformCellCounts':dict(Counter(c['baseLandform'] for c in cells)),
        'touchesScanBoundary':any(c['blockX'] in [origin[0],origin[0]+span-step] or c['blockZ'] in [origin[1],origin[1]+span-step] for c in cells),
        'mapLabelAnchorBlock':{'x':anchor['blockX'],'z':anchor['blockZ']},
        'nonWaterBounds':{'minX':min(c['blockX'] for c in cells),'minZ':min(c['blockZ'] for c in cells),'maxXExclusive':max(c['blockX'] for c in cells)+step,'maxZExclusive':max(c['blockZ'] for c in cells)+step}})
dump(OUT/'01_世界GIS/W05_主要陆块事实.json',{'sourceWorld':'geometia_beta2_08 (1)','note':'标注面积至少 300 粗格的陆块；不是国家数量、国家边界或选择限制。面积仅为扫描窗口内。','continents':continents,'allContinentSummaries':world['continents']})
im=Image.open(OUT/'01_世界GIS/W01_世界地貌.png').convert('RGB');d=ImageDraw.Draw(im)
d.rectangle((0,0,1400,62),fill=BG)
d.text((35,20),'W06｜08 重建世界 · 陆块编号',font=font(30),fill=INK)
for c in continents:
    a=c['mapLabelAnchorBlock'];x=90+(a['x']-origin[0]+step/2)/span*960;y=140+(a['z']-origin[1]+step/2)/span*960
    label='C'+c['continentId'].split('_')[-1]
    box=d.textbbox((x,y),label,font=font(21),anchor='mm')
    d.rounded_rectangle((box[0]-6,box[1]-4,box[2]+6,box[3]+4),radius=4,fill='#17263b',outline='white')
    d.text((x,y),label,font=font(21),fill='white',anchor='mm')
d.rectangle((1080,780,1399,1100),fill=BG)
for i,line in enumerate([f'标注 {len(continents)} 个较大陆块','C9 = continent_9','编号不是国家或文化圈','小岛也可以参与设定','边缘陆块可能被截断','同大陆可有多个国度','文化联系可以跨越海洋']):
    d.text((1090,800+i*30),line,font=font(16),fill=MUTED)
im.save(OUT/'01_世界GIS/W06_大陆编号.png')
dump(OUT/'来源与校验.json',{'sourceWorld':'geometia_beta2_08 (1)','sourceRun':str(SRC),'configHash':survey['configHash'],'bounds':bounds,'cellCount':len(features),'microSampleCount':survey['microSampleCount'],'scanDurationMs':survey['surveyStats']['durationMs'],'failedTiles':0,'majorContinentCount':len(continents),'sources':[{'path':str(SRC/n),'sha256':hashlib.sha256((SRC/n).read_bytes()).hexdigest()} for n in ['world_survey_manifest.json','world_survey_context.json','world_feature_grid.json','world_patch_map.json','w_manifest.json','world_patch_preview.png','world_biome_preview.png']]})
print(json.dumps({'world':'geometia_beta2_08 (1)','cells':len(features),'majorContinents':len(continents),'bounds':bounds},ensure_ascii=False))

