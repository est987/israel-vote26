"""Build app data: sites.json, nbhd.json (simplified polygons + aggregates), towns.json, meta.json"""
import sys,json,collections,csv,os; sys.path.insert(0,'/home/claude/build')
import match2 as R, match as M
from shapely.geometry import shape, Point, mapping
from shapely.strtree import STRtree
OUT='/home/claude/app/data'; os.makedirs(OUT,exist_ok=True)
PARTIES=[('מחל','הליכוד','coal'),('פה','יש עתיד','opp'),('ט','הציונות הדתית','coal'),('כן','המחנה הממלכתי','opp'),
 ('שס','ש"ס','coal'),('ג','יהדות התורה','coal'),('ל','ישראל ביתנו','opp'),('עם','רע"ם','arab'),('ום','חד"ש-תע"ל','arab'),
 ('אמת+מרצ','הדמוקרטים','opp'),('ד','בל"ד','arab'),('ב','הבית היהודי','opp')]
ALL=list(M.V[0].keys())[11:]
USED={c for k,_,_ in PARTIES for c in k.split('+')}
OTHER=[p for p in ALL if p not in USED]
KEYS=[k for k,_,_ in PARTIES]+['oth']
def vec(rows):
    """[eligible, voters, invalid, valid, p1..p13, other]"""
    n=lambda r,c:int(float(r[c] or 0))
    v=[sum(n(r,c) for r in rows) for c in ('בזב','מצביעים','פסולים','כשרים')]
    v+=[sum(n(r,c) for r in rows for c in k.split('+')) for k,_,_ in PARTIES]+[sum(n(r,c) for r in rows for c in OTHER)]
    return v
def add(a,b): return [x+y for x,y in zip(a,b)] if a else list(b)
# neighbourhoods
fs=json.load(open('/home/claude/data/nbhd/neighbourhoods.geojson'))['features']
G=[shape(f['geometry']) for f in fs]; G=[g if g.is_valid else g.buffer(0) for g in G]; T=STRtree(G)
def nb(xy):
    pt=Point(xy)
    for i in T.query(pt):
        if G[i].contains(pt): return int(i)
    return None
CONF={'exact':3,'k24':2,'base':1,'cluster':1}
sites=[];nagg={};nmeta=collections.defaultdict(lambda:{'sites':0,'uncertain':0,'conf':collections.Counter()})
towns={}
for (s,c),r in R.resolved.items():
    boxes=R.sites[(s,c)]; rows=[o['row'] for o in boxes]; v=vec(rows)
    tname=rows[0]['שם ישוב'].replace('  ',' ').strip()
    t=towns.setdefault(s,{'name':tname,'v':None,'vin':None,'unplaced':0}); t['v']=add(t['v'],v)
    if not r: t['unplaced']+=v[3]; continue
    n=nb(r['xy'])
    uncertain=False
    if n is not None:
        alts={nb(e[1]) for o in boxes for e in R.evidence(o)}; uncertain=len(alts)>1
        nagg[n]=add(nagg.get(n),v); m=nmeta[n]; m['sites']+=1; m['uncertain']+=v[3] if uncertain else 0; m['conf'][r['conf']]+=v[3]
        t['vin']=add(t['vin'],v)
    k=r['k26']
    sites.append({'id':f'{s}-{c}','t':s,'xy':[round(r['xy'][0],5),round(r['xy'][1],5)],'n':n,
      'name':(k['polling_station_location'].strip() if k else ''),'addr':(k['polling_station_address'].strip().rstrip(',') if k else ''),
      'boxes':sorted([o['row']['קלפי'] for o in boxes],key=lambda b:[float(x) for x in b.split('.')]),'conf':r['conf'],'unc':uncertain,'v':v})
# polygons: keep only those with votes? keep all, mark empty
feats=[]
for i,f in enumerate(fs):
    p=f['properties']; g=G[i].simplify(0.00004,preserve_topology=True)
    gj=mapping(g)
    def rnd(x): return [rnd(y) for y in x] if isinstance(x[0],(list,tuple)) else [round(x[0],5),round(x[1],5)]
    gj={'type':gj['type'],'coordinates':rnd(gj['coordinates'])}
    m=nmeta.get(i)
    feats.append({'type':'Feature','geometry':gj,'properties':{'i':i,'name':(p.get('fname') or '').strip(),'town':(p.get('setl_name') or '').strip(),
      'v':nagg.get(i),'sites':m['sites'] if m else 0,'unc':m['uncertain'] if m else 0,
      'exact':m['conf']['exact'] if m else 0}})
# ---- pseudo-neighbourhoods for sites outside the layer
import pseudo
K26N={}
for f in json.load(open('/home/claude/data/k26/k26.geojson'))['features']:
    K26N.setdefault(str(f['properties']['settlement_code']),' '.join(f['properties']['settlement_name'].split()))
for c,t in towns.items():
    if c in K26N: t['name']=K26N[c]   # vote file strips hyphens/brackets; 2026 list has proper names
tn={c:t['name'] for c,t in towns.items()}
for c in tn: tn[c]=' '.join(tn[c].split())
for ps in pseudo.build(sites,G,tn):
    i=len(feats); g=ps['geom'].buffer(0)
    gj=mapping(g)
    def rnd(x): return [rnd(y) for y in x] if isinstance(x[0],(list,tuple)) else [round(x[0],5),round(x[1],5)]
    v=None;ex=0
    for s in ps['sites']:
        s['n']=i; v=add(v,s['v']); ex+=s['v'][3] if s['conf']=='exact' else 0
        t=towns[s['t']]; t['vin']=add(t['vin'],s['v'])
    feats.append({'type':'Feature','geometry':{'type':gj['type'],'coordinates':rnd(gj['coordinates'])},
      'properties':{'i':i,'name':ps['name'],'town':tn[ps['town']],'v':v,'sites':len(ps['sites']),'unc':0,'exact':ex,'pseudo':1}})
print('pseudo neighbourhoods',len(feats)-len(fs))
json.dump({'type':'FeatureCollection','features':feats},open(OUT+'/nbhd.json','w'),ensure_ascii=False,separators=(',',':'))
json.dump(sites,open(OUT+'/sites.json','w'),ensure_ascii=False,separators=(',',':'))
# double envelopes
de=vec([x for x in csv.DictReader(open('/home/claude/data/votes/expb.csv',encoding='utf-8-sig')) if x['סמל ישוב']=='9999'])
nat=vec([x for x in csv.DictReader(open('/home/claude/data/votes/expb.csv',encoding='utf-8-sig'))])
json.dump({'towns':towns,'parties':[{'k':k,'name':n,'bloc':b} for k,n,b in PARTIES]+[{'k':'oth','name':'אחרים','bloc':'other'}],
  'national':nat,'double':de},open(OUT+'/meta.json','w'),ensure_ascii=False,separators=(',',':'))
print('sites',len(sites),'nbhd with votes',len(nagg),'of',len(fs))
for f in os.listdir(OUT): print(f, os.path.getsize(OUT+'/'+f)//1024,'KB')
