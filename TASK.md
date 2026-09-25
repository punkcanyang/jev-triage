# Jev 工单／邮件分流 · 任务卡

更新日期：2026-09-21（上海）  
状态：Gateway wired；live eval **blocked** by Vercel credit-card verification  
备注：Gateway abandoned；key only via env if ever needed；Grok session unchanged (`(local Grok session)`)  
来源：商务拓展交接；老板口头「好像可以」；两周自用、$0；Chatseek 不砍。

## Grok session
- session id：`(local Grok session)`
- 标题：`jev-triage`
- 续作：`cd /path/to/jev-triage && grok --resume 01a0c168-c41a-7761-aff2-c04fc8d64065` 或 `grok -c`
- 禁止：同一任务每轮新开；禁止 Fast（`default_reasoning_effort=high`；Gateway 勿设 `speed:'fast'` / `*-fast` slug）
- 备注：kickoff 用 `grok -p` 非交互拿 session id；MVP 实现由 executor 在同目录落地（产品 READY 优先）

## 目标
丢工单／邮件正文 → 结构化结果：
- 队列标签（固定 6 个，见 README）
- urgency score
- refund / escalate 类 noul
- 置信度；低置信 → 人工审核
- **不写回复**；不收买方大模型 Key（只握 Jev／Gateway）

## 两周验收
1. 200–500 条脱敏样例 + 人工标签对照
2. 固定队列 + urgency + refund/escalate
3. 走 **TypeSafe 直连**（老板 2026-09-21 定：Gateway 放弃）；禁止 Fast
4. 对照报告：自动进队准确率、「该进审核却误自动」率
5. README 写达标阈值；不达标就停（不上转发邮箱壳）

## 不做
自动回复、Zendesk 全家桶、收用户 ChatGPT／Claude Key、上架／收费、公开仓（除非老板另说）

## 阻塞
- Gateway：**已放弃**（老板 2026-09-21）。只走 TypeSafe 直连。
- 2026-09-21：老板书面允许 TypeSafe 直连自用评测；Gateway 绑卡后再测

- Gateway Key：已放弃；勿再依赖 box-secrets。
- Vercel AI Gateway：**`systemone` 返回 403 `customer_verification_required`** — 账号需绑信用卡才能解锁 free credits（models 列表可用，说明 Key 有效）。
- TypeSafe Python SDK 直连仍可用（`TYPESAFE_API_KEY`）。
- Gateway 适配器已接好：`adapters/gateway/classify.mjs`（SDK `experimental_evaluate` + REST fallback）；评测：`scripts/eval_gateway.mjs`。

## 达标线
- 自动进队准确率 ≥ 80%（对照人工主队列）
- 「该进审核却误自动」率 ≤ 5%
- 低置信阈值：confidence < 0.55 → 强制人工（`needs_review=true`）

## 交付
本地可跑：`classify(text) → JSON` + 评测脚本／报告。见 README。
