# Ge Zhang Academic Hub：第一次上线操作（小白版）

## 你现在只需要理解 3 件事
1. **GitHub Pages**：负责把网站放到网上。
2. **Crossref 自动任务**：每天用你的 ORCID iD 精确找新 DOI 论文，自动加入网站。
3. **ORCID 手动同步任务**：当你刚往 ORCID 补了旧文章时，点一次按钮把 ORCID 当前公开作品重新读入网站。

## 第一次上传
把本文件夹 **里面的内容** 上传到 GitHub 仓库根目录。不要把外层文件夹本身再套一层。
上传后仓库顶层应直接看到：`index.html`、`publications.html`、`.github`、`scripts`、`data`、`papers` 等。

## 上线后还需要做的设置
### A. 给 GitHub Actions 写入权限
GitHub 仓库 → Settings → Actions → General → 滚到 `Workflow permissions` → 选择 `Read and write permissions` → Save。

### B. 开启 GitHub Pages
GitHub 仓库 → Settings → Pages → Build and deployment → Source 选择 `Deploy from a branch` → Branch 选择 `main` → Folder 选择 `/ (root)` → Save。

### C. 每日自动更新
`.github/workflows/daily-publications.yml` 已经设置好了。正常情况下不用点任何按钮。

### D. ORCID 手动同步（后面再配置，一次即可）
ORCID Public API 需要你自己的 Public API Client ID 和 Client Secret。不要把 Secret 发给 ChatGPT，也不要写进公开文件。
配置好两个 GitHub Repository Secrets 后，Actions 页面里的 `Reconcile with ORCID public works` 才能一键运行。

## 以后新论文怎么更新
- 出版社把你的 ORCID 写进 DOI metadata → Crossref 能找到 → 网站每天自动更新。
- 论文已经手工加到 ORCID，但 Crossref 没带 ORCID → 手动运行一次 ORCID Reconcile。
- 特别重要、想重点提高 AI 可发现性的论文 → 再做独立 GEO 深度页。
