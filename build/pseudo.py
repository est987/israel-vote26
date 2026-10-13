"""Pseudo-neighbourhoods for polling sites outside the neighbourhood layer.
Voronoi cells around those sites (metric ITM), each capped at R m, minus real neighbourhoods, clipped to land.
Towns with <= GROUP_MAX sites -> one area; larger towns -> k-means groups of ~GROUP_SIZE sites."""
import json,math,collections
import numpy as np
from shapely.geometry import Point, MultiPoint, shape, mapping
from shapely.ops import voronoi_diagram, unary_union, transform
from shapely.strtree import STRtree
from pyproj import Transformer
R=600; GROUP_MAX=4; GROUP_SIZE=4
to_itm=Transformer.from_crs(4326,2039,always_xy=True).transform
to_wgs=Transformer.from_crs(2039,4326,always_xy=True).transform
def kmeans(X,k,it=50):
    idx=np.linspace(0,len(X)-1,k).astype(int); C=X[np.argsort(X[:,0])][idx].copy()
    for _ in range(it):
        L=((X[:,None,:]-C[None])**2).sum(-1).argmin(1)
        C2=np.array([X[L==j].mean(0) if (L==j).any() else C[j] for j in range(k)])
        if np.allclose(C2,C): break
        C=C2
    return L
def build(sites,nb_geoms_wgs,town_names):
    out=[s for s in sites if s['n'] is None]
    P=[Point(to_itm(*s['xy'])) for s in out]
    vd=voronoi_diagram(MultiPoint(P),envelope=MultiPoint(P).envelope.buffer(5000))
    cells=list(vd.geoms); T=STRtree(cells)
    cell_of=[]
    for p in P:
        c=next((cells[j] for j in T.query(p) if cells[j].contains(p) or cells[j].touches(p)),None)
        cell_of.append(c)
    # obstacles: real neighbourhoods + sea (land = NE countries)
    nbu=unary_union([transform(to_itm,g) for g in nb_geoms_wgs]).buffer(0)
    land=None
    for f in json.load(open('/home/claude/data/ext/ne/geojson/ne_10m_admin_0_countries.geojson'))['features']:
        if f['properties']['NAME'] in ('Israel','Palestine'):
            g=transform(to_itm,shape(f['geometry'])); land=g if land is None else land.union(g)
    lakes=unary_union([transform(to_itm,shape(f['geometry'])) for f in json.load(open('/home/claude/data/ext/ne/geojson/ne_10m_lakes.geojson'))['features'] if shape(f['geometry']).intersects(Point(35.5,31.8).buffer(2))])
    land=land.difference(lakes)
    piece=[]
    for p,c in zip(P,cell_of):
        g=p.buffer(R,quad_segs=8)
        if c is not None: g=g.intersection(c)
        g=g.difference(nbu).intersection(land)
        piece.append(g)
    # groups
    byt=collections.defaultdict(list)
    for k,s in enumerate(out): byt[s['t']].append(k)
    groups=[]
    for t,ks in byt.items():
        if len(ks)<=GROUP_MAX: groups.append((t,ks,None)); continue
        X=np.array([[P[k].x,P[k].y] for k in ks]); k=math.ceil(len(ks)/GROUP_SIZE)
        L=kmeans(X,k); parts=[[ks[i] for i in range(len(ks)) if L[i]==j] for j in range(k)]
        parts=[q for q in parts if q]
        # order areas north->south for stable naming
        parts.sort(key=lambda q:-np.mean([P[i].y for i in q]))
        for j,q in enumerate(parts): groups.append((t,q,j+1))
    res=[]
    for t,ks,num in groups:
        g=unary_union([piece[k] for k in ks if not piece[k].is_empty])
        if g.is_empty: g=unary_union([P[k].buffer(150) for k in ks])
        g=g.buffer(1).buffer(-1).simplify(8)
        res.append(dict(town=t,name=(town_names[t]+(f' — אזור {num}' if num else '')),num=num,geom=transform(to_wgs,g),sites=[out[k] for k in ks]))
    return res
