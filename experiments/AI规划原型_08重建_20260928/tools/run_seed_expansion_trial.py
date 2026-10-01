import json, urllib.request, urllib.error, datetime, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'archive/旧结果'/'T3实机扩张_20260929'
OUT.mkdir(parents=True,exist_ok=True)
RUN='provider_ffffffff825a07bd_r19200'
def save(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def call(name,path,body=None):
    save(name+'_request.json',{'path':path,'body':body,'time':datetime.datetime.now().isoformat()})
    req=urllib.request.Request('http://localhost:5000'+path,data=None if body is None else json.dumps(body,ensure_ascii=False).encode(),headers={'Content-Type':'application/json','X-Geomantia-Agent-View':'true'})
    try:
        with urllib.request.urlopen(req,timeout=180) as response: result=json.load(response)
    except urllib.error.HTTPError as e:
        raw=e.read().decode();
        try: result=json.loads(raw)
        except: result={'ok':False,'httpStatus':e.code,'error':raw}
    save(name+'_response.json',result)
    print(name,json.dumps(result,ensure_ascii=False)[:1800],flush=True)
    return result
if __name__=='__main__':
    status=call('00_status','/realm/status')
    assert status['debugRoot'].endswith('geometia_beta2_08 (1)\\realm_debug')
    seeds=json.loads((ROOT/'archive/旧结果/T1扩张起点建议/扩张起点建议.json').read_text(encoding='utf-8'))['seeds']
    t1=(ROOT/'result/T1_文化圈与国度_20260928_本次/T1_文化圈与国度设计.md').read_text(encoding='utf-8')
    ratios=[.22,.30,.28,.65,.38,.42,.40,.40,.65,.65,.65]
    ids=['savira','aoren','skaien','harvi','nashir','yucen','belesa','tashilan','weilen','qinglan','merisa']
    cultures=['萨莱海岸','维伦工匠','哈尔长厅','哈尔长厅','纳哈尔围院','岑岚庭园','萨莱海岸','纳哈尔围院','维伦工匠','岑岚庭园','萨莱海岸']
    industries=[['渔事','修船','食品'],['机械','工具','维修'],['补给','修补','小农'],['修船','钓具','木作'],['织毡','陶作','畜群照护'],['园艺','料理','魔法'],['船具','园艺','访学'],['织物','陶作','仪式'],['加工','库存','工具'],['园艺','料理','观察旅行'],['修补','备餐','远征补给']]
    profiles=[]
    for i,s in enumerate(seeds):
        coast=i in [0,3,6,10]; garden=i in [5,9]; dry=i in [4,7]
        row=next(line for line in t1.splitlines() if line.startswith('| **'+s['name']+'**'))
        ratio=ratios[i]
        profiles.append({'realmId':'realm_'+ids[i],'name':s['name'],'targetContinentId':s['continentId'],'theme':row,'cultureTags':[cultures[i]],'industryTags':industries[i],'materialTags':['木造','石造','陶瓦'] if not dry else ['陶土','石造','织物'],'landformPreferences':['shore','valley','lowland'] if coast else ['valley','lowland','upland'],'avoidLandforms':['cliff'],'scalePlan':{'priority':'normal','normalizationGroup':s['continentId'],'targetAreaRatio':ratio,'minAreaRatio':round(ratio*.65,3),'maxAreaRatio':min(.85,round(ratio*1.2,3))},'expansionStyle':{'waterAffinity':.8 if coast else .45,'compactness':.45 if coast else .65,'coastalBias':.85 if coast else .2,'resourceSeeking':.5,'borderPressure':.3,'mountainAffinity':.1 if i in [1,2,8] else -.2,'forestAffinity':.55 if garden else .1,'seaCrossingPolicy':'none'}})
    body={'runId':RUN,'realmProfiles':profiles,'realmCount':11}
    result=call('01_t1','/realm/t1/prepare',body)
    if not result.get('ok'): raise SystemExit('T1 rejected; inspect saved response')
    for i,(s,p) in enumerate(zip(seeds,profiles)):
        result=call(f'{i+2:02d}_t2_'+ids[i],'/realm/t2/select_coordinate',{'runId':RUN,'realmId':p['realmId'],'gridX':s['gridX'],'gridZ':s['gridZ'],'selectedBy':'debug','allowSnap':False,'reason':'用户确认的 W 粗格起点简化路线实验；不经过 Top Patch。'+s['reason']})
        if not result.get('ok') or result.get('status')=='failed': raise SystemExit('T2 rejected; inspect saved response')
    result=call('13_t3','/realm/t3/expand',{'runId':RUN,'allowUnclaimedLand':True,'qualityMode':'strict','expansionModel':'action_budget'})
    save('实验说明.json',{'purpose':'用户授权的 W 起点直接扩张实验；使用 T2 调试兼容入口，不代表标准 Patch Explorer 链验收','addedParameters':'同大陆 C6 占比 .22/.30/.28，C82 .38/.42，C56 .40/.40；独占大陆 .65；允许荒野。所有国度不跨海。其余性格依据 T1 生计补充，完整参数见 01_t1_request.json。','lastResult':result.get('status'),'ok':result.get('ok')})
