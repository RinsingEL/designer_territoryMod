"""Build discovery materials from author metadata and existing renders; never a runtime catalog.
Usage: python build_d4_material_packet.py --implementation /path/to/StructureBinder
Requires Pillow and a Chinese font (override --font).
"""
import argparse, collections, hashlib, json, os, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
p=argparse.ArgumentParser(); p.add_argument('--implementation', type=Path, required=True); p.add_argument('--font',default='/System/Library/Fonts/STHeiti Medium.ttc'); args=p.parse_args()
impl=args.implementation.resolve(); exp=Path(__file__).resolve().parents[1]; out=exp/'data/第三题_选材材料'; out.mkdir(exist_ok=True)
(out/'功能树').mkdir(exist_ok=True); (out/'代表图').mkdir(exist_ok=True)
root=impl/'asset_catalogs/original_civilizations'
def link(path): return '<'+os.path.relpath(path,out).replace(os.sep,'/')+'>'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def safe(s): return str(s).replace('|','／').replace('\n',' ')
source=(root/'文明命名.md').read_text(); specs={}
for line in source.splitlines():
 m=re.match(r'\| ([A-Z]{2}) \| .*? \| \[([^]]+)\].*? \| (.*?) \|$',line)
 if m: specs[m[1]]=(m[2],m[3])
rows=[]; cards=[]; index=[]; groups=[]
for folder in sorted(root.glob('[0-9]*')):
 authors=[]
 for f in sorted(folder.glob('models/*/author.json')):
  a=json.loads(f.read_text()); a['_path']=f; authors.append(a)
 prefix=next((a['id'].split('-')[0] for a in authors),'XC'); style,desc=specs[prefix]
 if not authors: continue
 rep=next((a for a in authors if (a['_path'].parent/'previews/front.png').exists()),None)
 assert rep, folder
 rp=rep['_path'].parent/'previews/front.png'; dest=out/'代表图'/f'{prefix}.png'
 with Image.open(rp) as im: im.thumbnail((760,520)); im.convert('RGB').save(dest)
 tree=out/'功能树'/f'{prefix}_{style}.md'; funcs=collections.defaultdict(list)
 for a in authors:
  for term in a.get('function_terms') or ['用途待补标']: funcs[term].append(a)
  index.append({'id':a['id'],'style':style,'name':a['name'],'size':a.get('size'),'functions':a.get('function_terms',[]),'author':os.path.relpath(a['_path'],out),'author_sha256':sha(a['_path']),'nbt_sha256':sha(a['_path'].parent/'structure.nbt') if (a['_path'].parent/'structure.nbt').exists() else None,'runtime_status':'unverified','reskin_status':'unannotated'})
 text=[f'# {style}：功能 → 结构',f'共 {len(authors)} 个独立作者记录；多功能条目会重复展示，分组数量不能相加。功能名原样取自作者 function_terms，表示空间用途，不能证明交易、生产或居民行为已接入。', '先找城市需要的功能，再打开少量候选的作者信息与预览。角色仅作参考；池成员仍须在提交时显式核对。换皮标注未整理，所有条目当前均为“未确认可换皮”。']
 for term,items in sorted(funcs.items()):
  text += [f'\n## {term}（{len(items)}）','| ID／名称 | 尺寸 X×Y×Z | 作者角色 | 资料 |','| --- | --- | --- | --- |']
  for a in items:
   base=a['_path'].parent; rel=lambda x:'<'+os.path.relpath(x,tree.parent)+'>'
   pic=base/'previews/front.png'; links=f'[作者]({rel(a["_path"])})'
   if pic.exists(): links+=f' · [正面]({rel(pic)})'
   text.append(f'| {a["id"]} {safe(a["name"])} | {"×".join(map(str,a.get("size",[])))} | {safe(a.get("planning_role","未标"))} | {links} |')
 tree.write_text('\n\n'.join(text[:3])+'\n'+'\n'.join(text[3:])+'\n')
 rows.append(f'| {style} | {safe(desc)} | {len(authors)} | {rep["id"]} {safe(rep["name"])} | [展开](功能树/{tree.name}) |')
 cards.append((style,f'{rep["id"]} · {rep["name"]}',dest)); groups.append({'style':style,'count':len(authors),'representative':rep['id'],'source_preview':os.path.relpath(rp,out),'source_preview_sha256':sha(rp)})
for style,note in [('中式','原创库暂无成品图'),('日式','原创库暂无成品图'),('欧洲中世纪','原创库暂无成品图；外部318条名称索引'),('跨风格组合','组合归属，无独立统一风格图')]:
 cards.append((style,note,None))
 rows.append(f'| {style} | '+{'中式':'坡屋顶、出檐、木构开间、院落、门廊；斗拱是待核对构件，不是全库已具备能力','日式':'深檐、木构、轻隔断、缘侧、错落屋面','欧洲中世纪':'山墙、陡坡顶、外露木构或厚石墙；外部中世纪索引仅有名称证据','跨风格组合':'按两种已选风格组合，不独立选作统一外观'}[style]+' | 0 | 待补实物预览 | — |')
(out/'风格表.md').write_text('# 风格表\n\n先看风格语言和代表图，再选主风格与辅助细节。代表图只是现有样本，不是全套风格验收。数量是本地作者记录数，不是运行时可用数。\n\n| 风格 | 识别构件／形体与材料语言 | 原创记录数 | 代表结构 | 功能树 |\n| --- | --- | ---: | --- | --- |\n'+'\n'.join(rows)+f'\n\n来源：[风格定义]({link(root/"文明命名.md")})。外部素材单列：[中世纪名称索引]({link(impl/"asset_catalogs/construction_pack/README.md")})，318 条尚未验证外观、尺寸与运行时可用性，不并入原创 534 条。\n')
w,h=1920,1640; canvas=Image.new('RGB',(w,h),'#eef1f4'); draw=ImageDraw.Draw(canvas)
font=lambda size:ImageFont.truetype(args.font,size)
draw.text((28,18),'第三题 · 风格总览',font=font(34),fill='#182533'); draw.text((28,66),'现有模型样本，不代表风格验收或运行时可用；空位明确展示素材缺口。',font=font(22),fill='#465566')
for i,(style,label,img) in enumerate(cards):
 x=20+(i%4)*475; y=112+(i//4)*378
 draw.rounded_rectangle((x,y,x+460,y+362),radius=12,fill='white')
 draw.text((x+14,y+10),style,font=font(25),fill='#182533')
 if img:
  im=ImageOps.contain(Image.open(img).convert('RGB'),(432,264)); canvas.paste(im,(x+(460-im.width)//2,y+49+(264-im.height)//2))
 else: draw.text((x+35,y+160),'暂无对应实物预览',font=font(25),fill='#8c6544')
 # wrap the label by measured pixel width
 lines=['']
 for c in label:
  if draw.textlength(lines[-1]+c,font=font(17))>430: lines.append('')
  lines[-1]+=c
 for j,line in enumerate(lines[:2]): draw.text((x+14,y+315+22*j),line,font=font(17),fill='#465566')
canvas.save(out/'风格总览.png')
(out/'素材索引.json').write_text(json.dumps({'scope':'local_author_discovery_only','assets':index,'style_representatives':groups},ensure_ascii=False,indent=2)+'\n')
assert len({a['id'] for a in index})==len(index)
print(json.dumps({'author_count':len(index),'styles':len(groups),'cards':len(cards),'output':str(out)},ensure_ascii=False))
