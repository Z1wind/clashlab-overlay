# 放兵线 / 放兵区域（deploy）

把「一个放兵点」升级成「一条边上的线或小区域」，然后在候选里挑摧毁率最高的一条。

## 用法

```powershell
python tools\deploy_cli.py --layout bases\th16\03\layout.json \
  --army '{"giant":10,"wizard":12}' --mode line --trials 10 --seed 1
```

- `--mode point`：单点投放（旧行为，作对照）；
- `--mode line`：每条边 3 段、每段 4 个点，共 12 条候选线；
- `--mode region`：四条边中点附近的 2×2 区域，共 4 个候选；
- `--mode all`：全部 22 个候选。

## 实测（base 03，`{giant:10, wizard:12}`，trials=10，seed=1）

```
点基线 = 17.89%
最佳   = line-south-2 点列 [(22,42),(27,42),(32,42),(37,42)] → mean 24.74%（+6.85）
第二名 = line-north-2 19.74%；最差 line-south-1 12.11%
```

结论：同一套军队，**换成长线撒兵后摧毁率从 17.9% 提到 24.7%**；具体最优线随阵型变化，故提供候选枚举 + 自动挑选。

## 实现

- `clashlab/deploy.py`：`point_candidates / line_candidates / region_candidates / evaluate / optimize`；
- `clashlab/wargame.py`：`simulate_once(spawn=...)` 现在接受**点列表**，军队按人数均分到各点后分别展开（同一 seed 确定性）；
- 所有候选评估走 `simulate_once(..., collect_events=False)`，默认 10 trials；CLI 输出 JSON 可接面板。

## 局限

- 候选是固定几何模板，没有做连续优化（可以后续加爬山/贝叶斯）；
- 数值来自近似 wargame 引擎，结论用于「哪条线更好」的相对比较；
- 面板端尚未接线（按分工由 Lead 后续接）。
