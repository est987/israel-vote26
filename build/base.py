import json,collections
from shapely.geometry import shape, box, mapping
from shapely.ops import unary_union
B=box(33.6,29.3,36.5,33.6)
def rnd(x): return [rnd(y) for y in x] if isinstance(x[0],(list,tuple)) else [round(x[0],4),round(x[1],4)]
def gj(g): m=mapping(g); return {'type':m['type'],'coordinates':rnd(m['coordinates'])}
NE='/home/claude/data/ext/ne/geojson/'
land=[]
for f in json.load(open(NE+'ne_10m_admin_0_countries.geojson'))['features']:
    g=shape(f['geometry'])
    if g.intersects(B): land.append({'type':'Feature','properties':{'n':f['properties'].get('NAME_HE') or f['properties']['NAME']},'geometry':gj(g.intersection(B).simplify(0.003))})
lakes=[]
for f in json.load(open(NE+'ne_10m_lakes.geojson'))['features']:
    g=shape(f['geometry'])
    if g.intersects(B): lakes.append({'type':'Feature','properties':{},'geometry':gj(g.intersection(B).simplify(0.002))})
fs=json.load(open('/home/claude/data/nbhd/neighbourhoods.geojson'))['features']
by=collections.defaultdict(list)
for f in fs:
    g=shape(f['geometry']); g=g if g.is_valid else g.buffer(0)
    by[(f['properties'].get('setl_name') or '').strip()].append(g)
towns=[]
for t,gs in by.items():
    if not t: continue
    u=unary_union(gs).buffer(0.0003).buffer(-0.0003).simplify(0.0004)
    lp=u.representative_point()
    towns.append({'type':'Feature','properties':{'t':t,'lx':round(lp.x,4),'ly':round(lp.y,4),'a':round(u.area*1e4,2)},'geometry':gj(u)})
# pseudo-neighbourhood towns (from the built nbhd.json)
pf=[f for f in json.load(open('/home/claude/app/data/nbhd.json'))['features'] if f['properties'].get('pseudo')]
byp=collections.defaultdict(list)
for f in pf: byp[f['properties']['town']].append(shape(f['geometry']).buffer(0))
have={t['properties']['t'] for t in towns}
for t,gs in byp.items():
    if t in have: continue
    u=unary_union(gs).simplify(0.0004); lp=u.representative_point()
    towns.append({'type':'Feature','properties':{'t':t,'lx':round(lp.x,4),'ly':round(lp.y,4),'a':round(u.area*1e4*0.3,2),'p':1},'geometry':gj(u)})
json.dump({'land':land,'lakes':lakes,'towns':towns},open('/home/claude/app/data/base.json','w'),ensure_ascii=False,separators=(',',':'))
print(len(land),len(lakes),len(towns))
