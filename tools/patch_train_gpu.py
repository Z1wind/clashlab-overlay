# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "train_synth_level.py")
t = open(p, encoding="utf-8").read()
if "cuda" in t:
    print("already patched")
else:
    t = t.replace('    ap.add_argument("--batch", type=int, default=64)',
                  '    ap.add_argument("--batch", type=int, default=64)\n'
                  '    ap.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")\n'
                  '    ap.add_argument("--amp", action="store_true", default=True)')
    t = t.replace('    torch.set_num_threads(min(os.cpu_count() or 4, 8))',
                  '    torch.set_num_threads(min(os.cpu_count() or 4, 8))\n'
                  '    use_cuda = torch.cuda.is_available() and a.device in ("auto", "cuda")\n'
                  '    dev = torch.device("cuda" if use_cuda else "cpu")\n'
                  '    print("[device]", dev, "| cuda:", torch.version.cuda, flush=True)')
    t = t.replace('    net = Net(len(types))', '    net = Net(len(types)).to(dev)')
    t = t.replace('    yt_t = torch.from_numpy(y_t[tr]); yl_t = torch.from_numpy(y_l[tr])\n'
                  '    yt_v = torch.from_numpy(y_t[val]); yl_v = torch.from_numpy(y_l[val])',
                  '    yt_t = torch.from_numpy(y_t[tr]).to(dev); yl_t = torch.from_numpy(y_l[tr]).to(dev)\n'
                  '    yt_v = torch.from_numpy(y_t[val]).to(dev); yl_v = torch.from_numpy(y_l[val]).to(dev)\n'
                  '    X_v = X_v.to(dev)')
    t = t.replace('''            xb = X_t[b]
            if random.random() < 0.5:
                xb = torch.flip(xb, dims=[3])
            logits, lv = net(xb)
            loss = F.cross_entropy(logits, yt_t[b]) + 2.0 * F.smooth_l1_loss(lv, yl_t[b])''',
'''            xb = X_t[b].to(dev, non_blocking=True)
            if random.random() < 0.5:
                xb = torch.flip(xb, dims=[3])
            with torch.autocast(device_type=dev.type, dtype=torch.bfloat16, enabled=use_cuda):
                logits, lv = net(xb)
            loss = F.cross_entropy(logits.float(), yt_t[b]) + 2.0 * F.smooth_l1_loss(lv.float(), yl_t[b])''')
    t = t.replace('        if ep % 10 == 0 or ep == a.epochs - 1:',
                  '        if ep % 10 == 0 or ep == a.epochs - 1:')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("train script GPU patched")
