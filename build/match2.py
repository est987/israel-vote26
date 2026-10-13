"""Resolve one location per Knesset 25 polling SITE (settlement + ריכוז), since all boxes in a site
share a building. Evidence from member boxes, strongest first:
  exact   K26 same settlement+box           weight 4
  k24     Knesset 24 geocode same box        weight 2
  base    K26 same base number, one site     weight 1
  cluster K26 same cluster code, one site    weight 1
Candidates within 80 m are pooled; the heaviest pool wins. Confidence = best evidence in the winning pool.
"""
import sys,collections; sys.path.insert(0,'/home/claude/build')
import match as M
W={'exact':4,'k24':2,'base':1,'cluster':1}
def evidence(o):
    s,b=o['row']['סמל ישוב'],o['row']['קלפי']; ev=[]
    if (s,b) in M.ex: p=M.ex[(s,b)]; ev.append(('exact',p['_xy'],p))
    if (s,b) in M.k24: ev.append(('k24',M.k24[(s,b)],None))
    bb=M.base.get((s,b.split('.')[0])); p=M.one_site(bb) if bb else None
    if p and not (s,b) in M.ex: ev.append(('base',p['_xy'],p))
    cc=M.clu.get((s,o['row']['ריכוז'])); p=M.one_site(cc) if cc else None
    if p: ev.append(('cluster',p['_xy'],p))
    return ev
sites=collections.defaultdict(list)
for o in M.out: sites[(o['row']['סמל ישוב'],o['row']['ריכוז'])].append(o)
resolved={}
for key,boxes in sites.items():
    ev=[e for o in boxes for e in evidence(o)]
    pools=[]
    for e in ev:
        for pl in pools:
            if M.dist(pl['xy'],e[1])<80: pl['ev'].append(e); pl['w']+=W[e[0]]; break
        else: pools.append({'xy':e[1],'ev':[e],'w':W[e[0]]})
    if not pools: resolved[key]=None; continue
    pl=max(pools,key=lambda p:p['w'])
    best=min(pl['ev'],key=lambda e:-W[e[0]])
    k26=next((e[2] for e in pl['ev'] if e[2]),None)
    xy=next((e[1] for e in pl['ev'] if e[0]=='exact'),None) or (k26['_xy'] if k26 else best[1])  # prefer official K26 point
    resolved[key]=dict(xy=xy,conf=best[0],k26=k26,support=pl['w'],total=sum(p['w'] for p in pools),boxes=boxes)
if __name__=='__main__':
    tot=sum(int(o['row']['כשרים']) for o in M.out)
    c=collections.Counter(); 
    for k,r in resolved.items():
        v=sum(int(o['row']['כשרים']) for o in sites[k])
        c[r['conf'] if r else 'none']+=v
    for t in ('exact','k24','base','cluster','none'): print('%-8s %5.1f%% of votes'%(t,100*c[t]/tot))
    # holdout check: base/cluster-confidence sites vs K24 where K24 exists for a member
    for t in ('exact','base','cluster'):
        ds=[]
        for k,r in resolved.items():
            if r and r['conf']==t:
                for o in sites[k]:
                    kk=(o['row']['סמל ישוב'],o['row']['קלפי'])
                    if kk in M.k24: ds.append(M.dist(r['xy'],M.k24[kk])); break
        if ds: print(t,'vs K24 n=%d <300m %.0f%% <1km %.0f%%'%(len(ds),100*sum(d<300 for d in ds)/len(ds),100*sum(d<1000 for d in ds)/len(ds)))
    print('contested sites (winner <60% of evidence):',sum(1 for r in resolved.values() if r and r['support']<0.6*r['total']))
