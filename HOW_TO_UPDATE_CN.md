# 以后怎么维护：你只需要记住这些

## 平时
不用管网站。GitHub 每天会用 ORCID iD `0000-0002-3116-3246` 在 Crossref 精确查找带有这个 ORCID 的新 DOI 论文，然后自动更新网站。

## 如果你刚手动往 ORCID 添加了一篇旧文章
GitHub 仓库 → Actions → `Reconcile with ORCID public works` → `Run workflow`。

这是一键重新读取 ORCID，不需要重新上传整套网站。

## 如果新论文没有自动出现
通常是出版社注册 DOI 时没有把 ORCID 写进 Crossref metadata。
做法：
1. 把论文加入 ORCID；
2. 将该 Work 的可见性设为 Everyone/Public；
3. 手动运行 `Reconcile with ORCID public works`；
4. 仍没出现，再把 DOI 发给 ChatGPT 排查。

## 重点 GEO 论文
普通论文自动进入 Publications。
特别重要、想重点推引用的文章，再让 ChatGPT 增加独立 GEO 深度页。

## 为什么不按 “Ge Zhang + 单位” 自动识别
因为 Ge Zhang 同名很多，而且单位写法会变化。
自动发现优先使用唯一 ORCID，不依赖姓名或单位猜测。
