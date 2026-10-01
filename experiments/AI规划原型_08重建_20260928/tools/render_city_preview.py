"""Render a city answer JSON over its sealed territory cells. No game access."""
import argparse
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

COLORS = {'water':'#2a60a4', 'shore':'#d6c580', 'lowland':'#68a856',
          'upland':'#ac9c5c', 'ridge':'#929a9c', 'valley':'#529476'}
FONT = 'C:/Windows/Fonts/msyh.ttc'

def render(source):
    source = Path(source).resolve()
    answer = json.loads(source.read_text(encoding='utf-8-sig'))
    territory_path = (source.parent / answer['territoryFile']).resolve()
    territory = json.loads(territory_path.read_text(encoding='utf-8-sig'))
    if answer['realmId'] != territory['realmId']:
        raise ValueError('realmId does not match territory')
    cells = {(c['gridX'], c['gridZ']): c for c in territory['cells']}
    step = territory['cellStepBlocks']
    cities = answer['cities']
    if not cities or len({c['id'] for c in cities}) != len(cities):
        raise ValueError('cities must be nonempty with unique ids')
    if sum(bool(c['capital']) for c in cities) != 1:
        raise ValueError('exactly one capital required')
    checks = []
    limits = {'hamlet':(160,240), 'village':(256,384), 'town':(512,640),
              'city':(768,2147483647), 'large_city':(768,2147483647)}
    radii = {'capital':4, 'city':3, 'large_city':3, 'town':2}
    for city in cities:
        label = city['theoreticalScale']
        normalized = {'capital':'city', 'outpost':'hamlet'}.get(label,label)
        minimum, maximum = limits[normalized]
        radius_cells = 1 if city.get('seedRole') == 'border_fort' else radii.get(label,1)
        radius = max(minimum,min(maximum,radius_cells*step))
        cx,cz = city['anchorBlock']['x'],city['anchorBlock']['z']
        city['radiusBlocks'] = radius
        city['bounds'] = dict(minX=cx-radius,maxX=cx+radius,minZ=cz-radius,maxZ=cz+radius)
        # Inclusive endpoints, matching CityPlanningReservation.centered.
        safe = math.ceil(((2*radius+1)*1.5-1)/2)
        city['protectionBounds'] = dict(minX=cx-safe,maxX=cx+safe,minZ=cz-safe,maxZ=cz+safe)
        b=city['bounds']
        covered=[(x,z) for x in range(b['minX']//step,b['maxX']//step+1)
                 for z in range(b['minZ']//step,b['maxZ']//step+1)]
        missing=sum(k not in cells for k in covered)
        checks.append(dict(name=city['name'],radiusBlocks=radius,sideBlocks=2*radius+1,
                           outsideOwnedCoarseCells=missing,totalCoarseCells=len(covered)))
    overlaps=[]
    for i,c in enumerate(cities):
        a=c['protectionBounds']
        for other in cities[i+1:]:
            b=other['protectionBounds']
            if a['minX']<=b['maxX'] and a['maxX']>=b['minX'] and a['minZ']<=b['maxZ'] and a['maxZ']>=b['minZ']:
                overlaps.append([c['name'],other['name']])
    report={'cities':checks,'protectionOverlaps':overlaps,
            'note':'Owned coverage is a coarse diagnostic, not a terrain/buildability verdict.'}
    source.with_suffix('.validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    loX = (min(x for x,z in cells)-3)*step
    hiX = (max(x for x,z in cells)+4)*step
    loZ = (min(z for x,z in cells)-3)*step
    hiZ = (max(z for x,z in cells)+4)*step
    height = max(1100, 210 + len(cities)*140)
    scale = min(1000/(hiX-loX), (height-220)/(hiZ-loZ))
    left, top = 100, 125
    def xy(x,z): return left+(x-loX)*scale, top+(z-loZ)*scale
    pic = Image.new('RGB', (1660,height), '#f4f3ee')
    draw = ImageDraw.Draw(pic)
    def text(pos, msg, size=20, fill='#243747', **kwargs):
        draw.text(pos, msg, font=ImageFont.truetype(FONT,size), fill=fill, **kwargs)
    def wrap(msg, width=435, size=19):
        lines, line = [], ''
        font = ImageFont.truetype(FONT,size)
        for char in msg:
            if draw.textlength(line+char,font=font)>width:
                lines.append(line); line=''
            line += char
        if line: lines.append(line)
        return lines
    text((35,24), answer['realmName']+'｜城市分布预览',34)
    text((35,77),'上北下南 · X 向东增加，Z 向南增加 · 编号对应右侧城市表',20)
    draw.rectangle((*xy(loX,loZ),*xy(hiX,hiZ)),fill='#dfe4e7')
    for (x,z),cell in cells.items():
        draw.rectangle((*xy(x*step,z*step), *xy((x+1)*step,(z+1)*step)),
                       fill=COLORS.get(cell['landform'],'#a0a0a0'))
    for x,z in cells:
        for dx,dz in [(0,-1),(0,1),(-1,0),(1,0)]:
            if (x+dx,z+dz) in cells: continue
            a,b = ((x,z),(x+1,z)) if dz==-1 else (((x,z+1),(x+1,z+1)) if dz==1 else (((x,z),(x,z+1)) if dx==-1 else ((x+1,z),(x+1,z+1))))
            draw.line((*xy(a[0]*step,a[1]*step),*xy(b[0]*step,b[1]*step)),fill='white',width=2)
    tick = max(1024, math.ceil(max(hiX-loX,hiZ-loZ)/8192)*1024)
    for x in range(math.ceil(loX/tick)*tick,hiX,tick):
        px,py=xy(x,hiZ)
        draw.line((px,py,px,py+7),fill='#526277',width=2)
        text((px,py+10),str(x),16,anchor='mt')
    for z in range(math.ceil(loZ/tick)*tick,hiZ,tick):
        px,py=xy(loX,z)
        draw.line((px-7,py,px,py),fill='#526277',width=2)
        text((px-12,py),str(z),16,anchor='rm')
    for i,city in enumerate(cities,1):
        b=city['bounds']; color='#b84a28' if city['capital'] else '#28366f'
        safe=city['protectionBounds']
        draw.rectangle((*xy(safe['minX'],safe['minZ']),*xy(safe['maxX']+1,safe['maxZ']+1)),outline='#a393a8',width=1)
        x1,y1=xy(b['minX'],b['minZ']); x2,y2=xy(b['maxX']+1,b['maxZ']+1)
        draw.rectangle((x1,y1,x2,y2),outline=color,width=4)
        cx,cy=(x1+x2)/2,(y1+y2)/2
        draw.ellipse((cx-15,cy-15,cx+15,cy+15),fill=color,outline='white',width=2)
        text((cx,cy),str(i),18,fill='white',anchor='mm')
        y=125+(i-1)*140
        draw.rounded_rectangle((1140,y,1625,y+129),radius=12,fill='white')
        text((1156,y+10),f'{i:02}  {city["name"]}  ·  '+('首都 / ' if city['capital'] else '')+city['theoreticalScale'],23,fill=color)
        for j,line in enumerate(wrap(city['role'])):
            text((1156,y+44+j*25),line,19)
        text((1156,y+101),f'规划半径 {city["radiusBlocks"]} / 边长 {2*city["radiusBlocks"]+1} 格',17,fill='#526277')
    y=height-72
    for i,(name,key) in enumerate([('低地','lowland'),('谷地','valley'),('高地','upland'),('山脊','ridge'),('岸地','shore')]):
        x=35+i*125;draw.rectangle((x,y,x+20,y+20),fill=COLORS[key]);text((x+27,y-3),name,18)
    text((690,y-3),'灰底：国土外未展示；白线：实际国界',18)
    text((35,height-37),'粗框：代码规划范围；细框：1.5倍保护范围。均非建成区；位置尚未通过游戏内选址验收。',18)
    output=source.with_suffix('.png');pic.save(output)
    print(json.dumps({'image':str(output),'cities':len(cities),'validation':report},ensure_ascii=False))
    return output

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('answer_json',type=Path)
    render(parser.parse_args().answer_json)
