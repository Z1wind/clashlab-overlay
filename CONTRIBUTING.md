# 贡献指南 / Contributing

## 社区维护 / Community

这个项目欢迎任何人接手维护和补充：阵型标注（`bases/` 或 `out/annotate/`）、布局 JSON、识别样本、算法与文档改进，都可以直接提交 Issue / PR。提交前先跑一遍测试，并在 PR 里贴真实输出。

Anyone is welcome to maintain and extend this project: base annotations (`bases/` or `out/annotate/`), layout JSON, recognition samples, algorithm or doc improvements — just open an Issue / PR. Run the tests first and paste real output in the PR.

## 中文

1. Fork & 创建分支（`feat/xxx`）；
2. 先跑通基线：`python -m unittest discover -s tests`（应全部通过，当前约 94 项）；
3. 改代码请**测试先行**（先写会失败的测试，再实现），并附真实运行输出；
4. 不提交 `out/`、`dist/`、`*.bak_*`、密钥或本机绝对路径；
5. PR 描述里写清：改了什么、怎么验证、失败项/限制。

## English

1. Fork and branch (`feat/xxx`);
2. Baseline first: `python -m unittest discover -s tests` (all green, ~94 tests);
3. Test-first changes, with real command output in the PR;
4. Never commit `out/`, `dist/`, backups, secrets or absolute local paths;
5. Describe what changed, how it was verified, and remaining limitations.
