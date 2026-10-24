"""Read-only alpha analysis: substantial detached pieces must not appear in a rig.
No image files are edited. Shoulder anchor geometry is checked separately by JS.
"""
import json
import argparse
import re
from collections import deque
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--round',default='round03');args=parser.parse_args()
if not re.fullmatch(r'round\d{2}',args.round):raise ValueError('輪次必須為round加兩位數字')
frames = json.loads((root / f'work/{args.round}/continuity-frames.json').read_text(encoding='utf-8'))
reports = []
failures = []
for item in frames:
    im = Image.open(root / item['file'])
    w, h = im.size
    alpha = im.getchannel('A')
    solid = bytearray(1 if v >= 100 else 0 for v in alpha.get_flattened_data())
    components = []
    for idx in range(w*h):
        if not solid[idx]:
            continue
        solid[idx] = 0
        queue = deque([idx])
        count = 0
        while queue:
            current = queue.popleft()
            count += 1
            x, y = current % w, current // w
            for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if 0 <= nx < w and 0 <= ny < h:
                    n = ny*w+nx
                    if solid[n]:
                        solid[n] = 0
                        queue.append(n)
        components.append(count)
    significant = sorted((n for n in components if n >= 40), reverse=True)
    row = {'mode':item['mode'], 'time':item['time'], 'significant_components':significant,
           'max_shoulder_anchor_gap_px':max(p['gap'] for p in item['anchors'].values())}
    reports.append(row)
    if len(significant) != 1:
        failures.append(row)
summary = {'alpha_threshold':100,'detached_piece_threshold_pixels':40,'frames':len(reports),
           'failures':failures,'results':reports,
           'limitation':'Connectivity and stationary shoulder anchors do not establish anatomical realism or subjective acceptance.'}
(root / f'work/{args.round}/arm-continuity-verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({'frames':len(reports),'failures':failures},indent=2))
if failures:
    raise SystemExit(1)
