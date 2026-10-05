"""Build web/data/*.js from the Rhino FBX exports in /models (metres, Z-up).
Usage (from the repo root):
    python tools/build_data.py                      # uses models/261004_*.fbx + models/*structure*.fbx
    python tools/build_data.py <base.fbx> <core_restroom.fbx> [<structure.fbx>] [--out web/data]
Pure Python, no extra packages."""
import json, sys, os, base64, struct, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fbxparse import read_fbx, find

ARGS = sys.argv[1:]
OUT = os.path.join(HERE, '..', 'web', 'data')
if '--out' in ARGS: i = ARGS.index('--out'); OUT = os.path.abspath(ARGS[i + 1]); del ARGS[i:i + 2]
sys.argv = [sys.argv[0]] + ARGS
BASE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'models', '261004_base-program.fbx')
DETAIL = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(BASE)), '261004_core_restroom_mod.fbx')
import glob
STRUCT = sys.argv[3] if len(sys.argv) > 3 else (sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(BASE)), '*structure*.fbx'))) or [None])[-1]

def pack_layers(groups, origin):
    ox, oy, oz = origin; out = []
    for (grp, name), g in groups.items():
        q = []
        for i in range(0, len(g['v']), 3): q += [int(round((g['v'][i] - ox) * 100)), int(round((g['v'][i + 1] - oy) * 100)), int(round((g['v'][i + 2] - oz) * 100))]
        out.append({'name': name, 'group': grp, 'nv': len(q) // 3, 'nt': len(g['t']) // 3,
                    'v': base64.b64encode(struct.pack('<%dh' % len(q), *q)).decode(), 't': base64.b64encode(struct.pack('<%dI' % len(g['t']), *g['t'])).decode()})
    return out

# layer name -> program category (zones that get HVAC/electrical/sprinklers)
CAT = {'immersive spaces/gallery': 'immersive', 'exhibition/gallery': 'gallery', 'food-court - events': 'food',
       'lobby/cafe/cloakroom': 'lobby', 'musem shop - library': 'shop', 'terrace': 'terrace', 'OFFICES': 'office',
       'auditorium': 'auditorium', 'roof-technical-space': 'technical'}
SLAB_LAYERS = {'slabs', 'slab-cut'}

def load(path, full_path=False):
    N = read_fbx(path)
    O = [n for n in N if n[0] == 'Objects'][0]; objs = {k[1][0]: k for k in O[2]}
    par = {}
    for c in find([n for n in N if n[0] == 'Connections'][0], 'C'):
        if c[1][0] == 'OO': par.setdefault(c[1][1], c[1][2])
    nm = lambda i: objs[i][1][1].split('\x00')[0] if i in objs else 'root'
    out = []
    for gid, g in objs.items():
        if g[0] != 'Geometry': continue
        v = find(g, 'Vertices')[0][1][0]; pi = find(g, 'PolygonVertexIndex')[0][1][0]
        model = par[gid]; layer = nm(par.get(model, 0)); parent = nm(par.get(par.get(model, 0), 0))
        if full_path:  # top-level layer = group, everything below joined as the sublayer name
            chain = []; p = par.get(model, 0)
            while p in objs: chain.append(nm(p)); p = par.get(p, 0)
            chain.reverse(); parent = chain[0] if chain else 'root'; layer = '::'.join(chain[1:]) or chain[0]
        tris = []; cur = []
        for i in pi:
            if i < 0:
                cur.append(~i)
                for k in range(1, len(cur) - 1): tris += [cur[0], cur[k], cur[k + 1]]
                cur = []
            else: cur.append(i)
        out.append(dict(name=nm(model), layer=layer, parent=parent, v=v, t=tris))
    return out

def bbox(v):
    xs, ys, zs = v[0::3], v[1::3], v[2::3]
    return [round(min(xs), 2), round(min(ys), 2), round(min(zs), 2), round(max(xs), 2), round(max(ys), 2), round(max(zs), 2)]
def cr(ax, ay, bx, by): return ax * by - ay * bx
def tri_area(t): return abs(cr(t[2] - t[0], t[3] - t[1], t[4] - t[0], t[5] - t[1])) / 2
def inside(tris, x, y):
    for t in tris:
        d1 = cr(t[2] - t[0], t[3] - t[1], x - t[0], y - t[1]); d2 = cr(t[4] - t[2], t[5] - t[3], x - t[2], y - t[3]); d3 = cr(t[0] - t[4], t[1] - t[5], x - t[4], y - t[5])
        if (d1 >= 0 and d2 >= 0 and d3 >= 0) or (d1 <= 0 and d2 <= 0 and d3 <= 0): return True
    return False
def rv(v): return [round(c, 3) for c in v]

M = load(BASE)
# ---- levels from slabs
levels = {}
for m in M:
    if m['layer'] not in SLAB_LAYERS: continue
    v = m['v']; z = round(sum(v[2::3]) / (len(v) // 3), 2)
    key = min(levels, key=lambda k: abs(k - z)) if levels and min(abs(k - z) for k in levels) < 0.2 else z
    L = levels.setdefault(key, [])
    for i in range(0, len(m['t']), 3):
        a, b, c = m['t'][i:i + 3]
        L.append([round(v[a * 3], 2), round(v[a * 3 + 1], 2), round(v[b * 3], 2), round(v[b * 3 + 1], 2), round(v[c * 3], 2), round(v[c * 3 + 1], 2)])
zs = sorted(levels)
lv = [dict(z=z, area=round(sum(tri_area(t) for t in levels[z]), 1), tris=levels[z]) for z in zs]

# ---- program volumes
vols = []
for m in M:
    if m['layer'] not in CAT: continue
    v = m['v']; b = bbox(v); zmin = b[2]
    a = 0
    for i in range(0, len(m['t']), 3):
        idx = m['t'][i:i + 3]; P = [v[j * 3:j * 3 + 3] for j in idx]
        if all(abs(p[2] - zmin) < 0.05 for p in P): a += abs(cr(P[1][0] - P[0][0], P[1][1] - P[0][1], P[2][0] - P[0][0], P[2][1] - P[0][1])) / 2
    fl = min(range(len(zs)), key=lambda i: abs(zs[i] - zmin))
    n = len(v) // 3
    vols.append(dict(id=m['name'], cat=CAT[m['layer']], layer=m['layer'], floor=fl, zmin=zmin, zmax=b[5], area=round(a, 1), bbox=b,
                     c=[round(sum(v[0::3]) / n, 2), round(sum(v[1::3]) / n, 2), zmin]))

# ---- MEP / core layers (new in 261004 export)
by = lambda name: [m for m in M if m['layer'] == name]
shafts = [dict(id=m['name'], bbox=bbox(m['v'])) for m in by('shaft')]
cores = [dict(id=m['name'], bbox=bbox(m['v'])) for m in by('CORES')]
restrooms = [dict(id=m['name'], bbox=bbox(m['v'])) for m in by('RESTROOM')]
tech = []
for m in by('technical_room_availability_basement'):
    b = bbox(m['v']); tech.append(dict(id=m['name'], bbox=b, area=round((b[3] - b[0]) * (b[4] - b[1]), 1)))
basementZ = min([t['bbox'][2] for t in tech] + [c['bbox'][2] for c in cores] + [zs[0]])

# ---- detail model: fixtures, risers, stairs, elevators + visualization meshes
detail = None; fixtures = {}; stairs = []; elev = {'passenger': 0, 'freight': 0, 'top': None}; riserPts = []
if os.path.exists(DETAIL):
    D = load(DETAIL)
    kinds = [('WC', re.compile(r'WC bowl', re.I)), ('lav', re.compile(r'Lavatory', re.I)), ('urinal', re.compile(r'urinal', re.I)),
             ('ss', re.compile(r'Service sink', re.I)), ('baby', re.compile(r'Baby', re.I)), ('df', re.compile(r'fountain|bottle', re.I))]
    for m in D:
        b = bbox(m['v'])
        if m['layer'].endswith('FIXTURE'):
            k = next((k for k, r in kinds if r.search(m['name'])), None)
            if not k: continue
            fl = min(range(len(zs)), key=lambda i: abs(zs[i] - b[2]))
            fixtures.setdefault(fl, {}).setdefault(k, 0); fixtures[fl][k] += 1
        if m['layer'].endswith('RISER'): riserPts.append([round((b[0] + b[3]) / 2, 2), round((b[1] + b[4]) / 2, 2)])
        if m['layer'] in ('02_PASSENGER_ELEVATORS', '03_FREIGHT_ELEVATOR') and b[5] - b[2] > 10:  # hoistway walls
            pass
        if m['layer'] in ('02_PASSENGER_ELEVATORS', '03_FREIGHT_ELEVATOR') and b[5] - b[2] < 0.2:  # pit/floor plate = one car
            elev['passenger' if 'PASS' in m['layer'] else 'freight'] += 1
            elev['top'] = max(elev['top'] or 0, max(x[5] for x in [bbox(q['v']) for q in D if q['layer'] == m['layer']]))
    # stairs: cluster 01_STAIRS by plan position (2.5 m grid, merged)
    pts = [bbox(m['v']) for m in D if m['layer'] == '01_STAIRS']
    for c in cores:
        cb = c['bbox']; inn = [b for b in pts if cb[0] - 0.5 <= (b[0] + b[3]) / 2 <= cb[3] + 0.5 and cb[1] - 0.5 <= (b[1] + b[4]) / 2 <= cb[4] + 0.5]
        if len(inn) > 50:
            stairs.append(dict(id='S' + str(len(stairs) + 1), core=c['id'], bbox=[min(b[0] for b in inn), min(b[1] for b in inn), min(b[2] for b in inn), max(b[3] for b in inn), max(b[4] for b in inn), max(b[5] for b in inn)]))
    # visualization: merge per layer, quantize to cm (int16 around an origin), base64
    groups = {}
    for m in D:
        key = m['layer'] if m['parent'] == '00_CORES' else m['layer'].split('_')[-1].replace('BAR', 'GRAB_BAR')
        if key == 'GRAB_GRAB_BAR': key = 'GRAB_BAR'
        g = groups.setdefault(key, {'v': [], 't': [], 'parent': m['parent']})
        off = len(g['v']) // 3; g['v'] += m['v']; g['t'] += [i + off for i in m['t']]
    ox, oy, oz = 50.0, 0.0, 25.0
    detail = {'origin': [ox, oy, oz], 'layers': []}
    for k, g in groups.items():
        q = []
        for i in range(0, len(g['v']), 3): q += [int(round((g['v'][i] - ox) * 100)), int(round((g['v'][i + 1] - oy) * 100)), int(round((g['v'][i + 2] - oz) * 100))]
        detail['layers'].append({'name': k, 'group': g['parent'], 'nv': len(q) // 3, 'nt': len(g['t']) // 3,
                                 'v': base64.b64encode(struct.pack('<%dh' % len(q), *q)).decode(), 't': base64.b64encode(struct.pack('<%dI' % len(g['t']), *g['t'])).decode()})

structure = None
if STRUCT and os.path.exists(STRUCT):
    S = load(STRUCT, full_path=True); groups = {}
    for m in S:
        g = groups.setdefault((m['parent'], m['layer']), {'v': [], 't': []})
        off = len(g['v']) // 3; g['v'] += m['v']; g['t'] += [i + off for i in m['t']]
    structure = {'origin': [50.0, 0.0, 30.0], 'source': os.path.basename(STRUCT), 'layers': pack_layers(groups, (50.0, 0.0, 30.0))}

data = dict(name='2GBX Hyperobject Media Museum', address='260 12th Avenue, Manhattan, NY', units='m', source=os.path.basename(BASE),
            levels=lv, volumes=vols, basementZ=basementZ,
            mep=dict(shafts=shafts, cores=cores, restrooms=restrooms, tech=tech, stairs=stairs, elevators=elev, risers=riserPts,
                     fixtures={str(k): v for k, v in fixtures.items()}),
            serviceEntry=dict(x=83.0, y=12.0),
            shell=[dict(name=m['name'], layer=m['layer'], v=rv(m['v']), t=m['t']) for m in M if m['layer'] in ('shell', 'basement')],
            context=[dict(name=m['name'], layer=m['layer'], v=rv(m['v']), t=m['t']) for m in M if m['layer'] in ('CORES', 'shaft', 'RESTROOM', 'technical_room_availability_basement')],
            volMeshes=[dict(id=m['name'], v=rv(m['v']), t=m['t']) for m in M if m['layer'] in CAT])
# legacy fields for fallback
c0 = shafts[0]['bbox'] if shafts else [55, 10, 0, 64, 15, 0]
data['core'] = dict(x=round((c0[0] + c0[3]) / 2, 2), y=round((c0[1] + c0[4]) / 2, 2))
data['stair2'] = dict(x=stairs[1]['bbox'][0] if len(stairs) > 1 else 77, y=stairs[1]['bbox'][1] if len(stairs) > 1 else -9)

os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, 'project-data.js'), 'w').write('window.PROJECT=' + json.dumps(data, separators=(',', ':')) + ';')
if detail: open(os.path.join(OUT, 'detail-data.js'), 'w').write('window.DETAIL=' + json.dumps(detail, separators=(',', ':')) + ';')
if structure: open(os.path.join(OUT, 'structure-data.js'), 'w').write('window.STRUCTURE=' + json.dumps(structure, separators=(',', ':')) + ';')
data_layers = [(l['group'], l['name'], l['nt']) for l in structure['layers']] if structure else []
open(os.path.join(OUT, 'project-data.js'), 'a').write('window.PROJECT.structureLayers=' + json.dumps(data_layers) + ';')
print('levels', [(l['z'], l['area']) for l in lv])
print('volumes', len(vols), '| shafts', [s['bbox'] for s in shafts])
print('stairs', [(s['id'], s['bbox']) for s in stairs]); print('elevators', elev, '| risers', riserPts)
print('fixtures', fixtures); print('tech rooms m2', [t['area'] for t in tech], 'basement z', basementZ)
if detail: print('detail layers', [(l['name'], l['nv'], l['nt']) for l in detail['layers']])
