# jev-triage README beautify — preview

## 改了什么
- Whole README：Hero（含 n=220 live 数字）→ 证明表 → 队列 → JSON → Backend → 用法 → Eval
- SVG：`docs/readme-assets/hero.svg`、`output-shape.svg`
- 写入真实评测：live 88.2% / 99.2% / 0.0%（n=220）；dry 并列
- 去掉 box 绝对路径与会话 id 噪音；Gateway 标明已放弃
- 未改分类代码；未 commit／push

## 预览怎么看
1. 打开 `README.md` Markdown 预览
2. 打开 `docs/readme-assets/*.svg`
3. `python3 ~/.grok/skills/beautify-github-readme/scripts/audit_readme.py /workspace/saas-scout/jev-triage/README.md`

## 已知限制
- 尚未推远程；预览仅本地
- hero 数字来自既有报告，非本次重跑评测
