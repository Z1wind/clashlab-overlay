# 贡献指南 / Contributing

## 中文

1. Fork & 创建分支（`feat/xxx`）；
2. 先跑通基线：`python -m unittest discover -s tests`（应 86 项全绿）；
3. 改代码请**测试先行**（先写会失败的测试，再实现），并附真实运行输出；
4. 不提交 `out/`、`dist/`、`*.bak_*`、密钥或本机绝对路径；
5. PR 描述里写清：改了什么、怎么验证、失败项/限制。

## English

1. Fork and branch (`feat/xxx`);
2. Baseline first: `python -m unittest discover -s tests` (86 tests green);
3. Test-first changes, with real command output in the PR;
4. Never commit `out/`, `dist/`, backups, secrets or absolute local paths;
5. Describe what changed, how it was verified, and remaining limitations.
