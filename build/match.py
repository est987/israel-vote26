"""Assign a location to every Knesset 25 ballot box. Tiers (first hit wins):
 1 exact   : K26 same settlement + same box number
 2 base    : K26 same settlement + same base number (109.3 -> 109), all K26 hits at one site
 3 k24     : Knesset 24 geocoded location, same settlement + box (GitHub Israel-Data)
 4 cluster : K26 same settlement + same cluster code, single site
 5 none    : not placed (kept at settlement level)
"""
import json,csv,collections,math,sys
D='/home/claude/data/'
bx=lambda v:(lambda f:str(int(f)) if f==int(f) else '%g'%f)(float(v))
def dist(a,b): return math.hypot((a[0]-b[0])*94.6,(a[1]-b[1])*111.0)*1000
S=[f['properties']|{'_xy':tuple(f['geometry']['coordinates'][0])} for f in json.load(open(D+'k26/k26.geojson'))['features']]
V=[x for x in csv.DictReader(open(D+'votes/expb.csv',encoding='utf-8-sig')) if x['סמל ישוב']!='9999']
L=[x for x in csv.DictReader(open(D+'ext/Israel-Data/output/locations/24.tsv'),delimiter='\t') if x['Latitude']]
k24={(str(int(float(x['Settlement Number']))),bx(x['Booth Number'])):(float(x['Longitude']),float(x['Latitude'])) for x in L}
ex={};base=collections.defaultdict(list);clu=collections.defaultdict(list)
for p in S:
    s=str(p['settlement_code']);b=bx(p['polling_station_code'])
    ex[(s,b)]=p; base[(s,b.split('.')[0])].append(p); clu[(s,str(p['cluster_code']))].append(p)
def one_site(ps,tol=60):
    xy=ps[0]['_xy']
    return ps[0] if all(dist(xy,q['_xy'])<tol for q in ps) else None
out=[]
for x in V:
    s,b=x['סמל ישוב'],x['קלפי']; k=(s,b); hit=None
    if k in ex: hit=('exact',ex[k])
    elif (s,b.split('.')[0]) in base and one_site(base[(s,b.split('.')[0])]): hit=('base',one_site(base[(s,b.split('.')[0])]))
    elif k in k24: hit=('k24',None)
    elif (s,x['ריכוז']) in clu and one_site(clu[(s,x['ריכוז'])]): hit=('cluster',one_site(clu[(s,x['ריכוז'])]))
    t,p=hit if hit else ('none',None)
    xy=p['_xy'] if p else (k24[k] if t=='k24' else None)
    out.append(dict(row=x,tier=t,xy=xy,site=(p['polling_station_location'].strip(),p['polling_station_address'].strip()) if p else None,k26elig=p['eligible_voters'] if p else None))
if __name__=='__main__':
    tot=sum(int(o['row']['כשרים']) for o in out)
    for t in ('exact','base','k24','cluster','none'):
        o=[o for o in out if o['tier']==t]; v=sum(int(q['row']['כשרים']) for q in o)
        ds=sorted(dist(q['xy'],k24[(q['row']['סמל ישוב'],q['row']['קלפי'])]) for q in o if q['xy'] and t!='k24' and (q['row']['סמל ישוב'],q['row']['קלפי']) in k24)
        chk=('vs K24 n=%d <300m %.0f%% <1km %.0f%%'%(len(ds),100*sum(d<300 for d in ds)/len(ds),100*sum(d<1000 for d in ds)/len(ds))) if ds else ''
        print('%-8s boxes %5d votes %5.1f%%  %s'%(t,len(o),100*v/tot,chk))
    print('none by settlement',collections.Counter(o['row']['שם ישוב'] for o in out if o['tier']=='none').most_common(10))
