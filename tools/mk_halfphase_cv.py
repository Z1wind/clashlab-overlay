# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
src = os.path.join(BASE, 'tools', 'train_hybrid_cv.py')
lines = open(src, encoding='utf-8').read().split('\n')
start = next(i for i,s in enumerate(lines) if s.strip() == 'cells = [(cx, cy) for cx in range(2,42) for cy in range(2,42)]')
end = next(i for i,s in enumerate(lines) if s.strip() == 'cand.sort(reverse=True)')
block = [
    '        cells = [(x + off, y + off) for off in (0.0, 0.5) for x in range(2,42) for y in range(2,42)]',
    '        gate_prob, embs = {}, {}',
    '        with torch.no_grad():',
    '            for i in range(0, len(cells), 128):',
    '                cs = cells[i:i+128]',
    '                xs = np.stack([warp(img, cal, cx, cy) for (cx,cy) in cs])[:,:,:,::-1].copy()',
    '                x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)',
    '                gp = torch.softmax(gate(x), 1)[:,1].cpu().numpy()',
    '                e = emb(x).cpu().numpy()',
    '                for k, cell in enumerate(cs):',
    '                    gate_prob[cell] = float(gp[k]); embs[cell] = e[k]',
    '        best = None',
    '        for gth in (0.5,0.6,0.7,0.8,0.9):',
    '            cand = []',
    '            for cell in cells:',
    '                if gate_prob[cell] < gth: continue',
    '                e = embs[cell]; sim = P @ e',
    '                bidx = int(sim.argmax()); cls = int(PC[bidx]); bs = float(sim[bidx])',
    '                bgmax = float(sim[PC == BG].max()) if (PC == BG).any() else -1',
    '                cand.append((bs, bs - bgmax, cls, cell[0]+.5, cell[1]+.5))',
    '            cand.sort(reverse=True)',
]
lines = lines[:start] + block + lines[end+1:]
out = os.path.join(BASE, 'tools', 'train_hybrid_halfphase_cv.py')
open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
print('halfphase cv written, lines replaced', start, end)