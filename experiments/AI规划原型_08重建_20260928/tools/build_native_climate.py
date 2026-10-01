"""Render native RTF climate after the upgraded mod has completed 08 backfill."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1] / 'data/第一题_国度设定'
SOURCE=Path(r'D:\PCL2-2.8.12\.minecraft\versions\1.20.1-Forge_47.4.23\saves\geometia_beta2_08 (1)\realm_debug\provider_ffffffff825a07bd_r19200')
FONT='C:/Windows/Fonts/msyh.ttc'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def font(n): return ImageFont.truetype(FONT,n)
def main():
    manifest=read(SOURCE/'world_climate_manifest.json')
    survey=read(SOURCE/'world_survey_context.json')
    assert manifest['sealed'] and manifest['configHash']==survey['configHash']
    assert manifest['worldSeed']==survey['worldSeed']=='-2108028995'
    assert manifest['sourceFingerprint']==survey['source']['terrainProvider']['sourceFingerprint']
    for name,sha in manifest['artifactSha256'].items():
        assert hashlib.sha256((SOURCE/name).read_bytes()).hexdigest()==sha
    grid=read(SOURCE/'world_climate_grid.json')
    assert grid['columns']==['gridX','gridZ','blockX','blockZ','regionTemperature','regionMoisture','temperature','moisture','water']
    assert grid['previewTemperatureField']=='regionTemperature' and grid['previewMoistureField']=='regionMoisture'
    assert grid['sampleCount']==len(grid['cells'])==92416
    assert len({(r[0],r[1]) for r in grid['cells']})==92416
    assert grid['cellStepBlocks']==128 and grid['sampleOffsetBlocks']==64
    assert all(r[2]==r[0]*128+64 and r[3]==r[1]*128+64 for r in grid['cells'])
    dest=ROOT/'01_世界GIS'
    continents=read(dest/'W05_主要陆块事实.json')['continents']
    for column,name,title,colors,ends in [
        (4,'W07_RTF原生温度.png','W07｜08 重建 RTF 原生温度 · regionTemperature',['#a6bce7','#76b7cf','#8cbd8a','#e3c579','#cc6555'],('偏冷','偏热')),
        (5,'W08_RTF原生湿度.png','W08｜08 重建 RTF 原生湿度 · regionMoisture',['#d6b786','#c4c88f','#9abd8b','#63a687','#287f79'],('偏干','偏湿'))]:
        raw=Image.new('RGB',(304,304))
        for r in grid['cells']:
            index=max(0,min(4,int(r[column]*5)))
            raw.putpixel((r[0]+152,r[1]+152),tuple(bytes.fromhex(('#2a60a4' if r[8] else colors[index])[1:])))
        im=Image.new('RGB',(1400,1170),'#f4f3ee');d=ImageDraw.Draw(im)
        d.text((35,20),title,font=font(29),fill='#233042')
        d.text((35,66),'直接读取 RTF 字段；每个 W 粗格中心单点采样；无量纲参数，不是摄氏度或实际降雨量。',font=font(17),fill='#526277')
        im.paste(raw.resize((960,960),Image.Resampling.NEAREST),(90,140))
        for i in range(20):
            q=round(i*960/19);d.line((90+q,140,90+q,1100),fill='#a0a7a4');d.line((90,140+q,1050,140+q),fill='#a0a7a4')
        for i in range(19):
            q=(i+.5)*960/19;d.text((90+q,117),chr(65+i),font=font(19),anchor='mm',fill='#233042');d.text((61,140+q),f'{i+1:02d}',font=font(19),anchor='mm',fill='#233042')
        for c in continents:
            a=c['mapLabelAnchorBlock'];x=90+(a['x']+19456+64)/38912*960;y=140+(a['z']+19456+64)/38912*960
            label='C'+c['continentId'].split('_')[-1];box=d.textbbox((x,y),label,font=font(21),anchor='mm')
            d.rounded_rectangle((box[0]-6,box[1]-4,box[2]+6,box[3]+4),radius=4,fill='#17263b',outline='white');d.text((x,y),label,font=font(21),anchor='mm',fill='white')
        y=160
        for i,color in enumerate(colors):
            d.rectangle((1080,y,1100,y+20),fill=color)
            suffix=' '+ends[0] if i==0 else ' '+ends[1] if i==4 else ''
            d.text((1110,y),f'{i/5:.1f}–{(i+1)/5:.1f}'+suffix,font=font(17),fill='#233042');y+=36
        d.rectangle((1080,y,1100,y+20),fill='#2a60a4');d.text((1110,y),'水域：图上遮盖',font=font(17),fill='#233042');y+=55
        for line in ['上北 / 下南 / 左西 / 右东','X、Z：[-19456,19456)','每个参考大格：2048 方块','采样位置：128 粗格中心','不是格内 16 点平均','','与 RTF 预览取相同字段','配色由本图独立定义','没有根据群系反推','水域气候值仍保存在 JSON','最终 temperature/moisture','另列保存，不用于这张图']:
            d.text((1080,y),line,font=font(16),fill='#526277');y+=30
        d.text((90,1125),'08 重建世界原生气候补采 · 与 W 世界图相同范围 · 生成器参数不是实时天气或资源产量证明',font=font(17),fill='#526277')
        im.save(dest/name)
    shutil.copy2(SOURCE/'world_climate_grid.json',dest/'W09_RTF原生气候数据.json')
    shutil.copy2(SOURCE/'world_climate_manifest.json',dest/'W10_RTF原生气候来源.json')
    print(json.dumps({'world':'geometia_beta2_08 (1)','nativeClimate':True,'samples':92416,'maps':2},ensure_ascii=False))
if __name__=='__main__':main()
