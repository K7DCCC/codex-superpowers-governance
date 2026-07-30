# 一级薄路由与二级 Registry（首次试跑）

> 这是软决策层：它没有隐藏、禁用或强制显式调用任何 Codex 原生能力。安装、登录、外发、删除、改配置均需另行确认。
>
> Need Gate：已给信息足够时优先 `baseline-direct`；只有缺口明确时才加载 Top-1 能力卡。

## Level 1：一级薄路由

| 任务类型 | 一句话边界 | 候选（按顺序） |
| --- | --- | --- |
| 直接回答 | 已给信息足够；不调用额外能力、不读全量目录 | `baseline-direct` |
| 公开资料检索 | 仅公开网页与官方文档；不要读取登录态数据 | `openai-docs`, `browser:control-in-app-browser`, `baseline-direct` |
| 软件构建与调试 | 仅对明确技术栈加载一项；不要让总管型流程接管普通问答 | `build-web-apps:frontend-app-builder`, `build-ios-apps:ios-debugger-agent`, `build-macos-apps:build-run-debug` |
| 文档与数据交付 | 仅为目标格式加载；不要同时加载重叠的文档能力 | `documents:documents`, `spreadsheets:Spreadsheets`, `pdf:pdf` |
| 设计与视觉 | 仅在用户要设计、图片或 Figma 时用；不要用于普通前端修复 | `product-design:index`, `imagegen`, `figma:figma-use` |
| 仓库与协作 | 外部写入前确认目标；只读摘要可直接执行 | `github:github`, `google-drive:google-drive`, `slack:slack` |
| 数据分析 | 仅在结构化分析或报告任务使用；不要对简单计算加载整套家族 | `data-analytics:index`, `spreadsheets:Spreadsheets`, `baseline-direct` |
| 商务与垂直域 | 仅在明确域名中加载单一入口；不要跨域混用 | `shopify:shopify-dev`, `public-equity-investing:public-equity-investing`, `seo-content-engine` |
| Agent 与集成开发 | 仅在创建 Skill/Plugin/MCP/Agent 时使用；安装和改配置前停下确认 | `skill-creator`, `build-mcp-apps:build-mcp-apps`, `openai-developers:agents-sdk` |
| 工程流程升级 | 普通修改不调用；设计、计划、子代理、TDD、worktree 和收尾须先过治理门 | `baseline-direct`, `superpowers-governance-gate` |

未命中时先选 `baseline-direct`；确有缺口才查 Catalog，不扫描整库。

## Level 2：薄 Registry

| ID | 能力槽 | 类型/平台 | 部署与健康 | 调用策略 | 触发 + 禁用条件 | 风险与回退 | 卡片 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline-direct | 用已有信息直接完成 | baseline / Codex | built-in / healthy | auto | 仅用于信息足够的任务；不要在需要外部事实或文件操作时假装已验证 | low；回退到匹配类别 Top-1 | [卡](./manifests/baseline-direct.md) |
| openai-docs | 查 OpenAI 官方资料 | Skill / Codex | visible / unverified | conditional | 仅用于 OpenAI 产品与 API；不要用于泛网页研究 | low；回退公开浏览 | — |
| browser:control-in-app-browser | 控制内置浏览器 | Skill / Codex | visible / unverified | explicit-only | 仅用于需要真实网页交互；不要用于已有信息足够的问答 | medium；回退公开网页读取 | [卡](./manifests/browser-control-in-app-browser.md) |
| github:github | GitHub 仓库与 PR 路由 | Skill / Codex | visible / healthy | conditional | 仅用于 GitHub 上下文；不要把外部写入当作已授权 | medium；回退本地 git/公开网页 | [卡](./manifests/github-github.md) |
| grist-table-reader | 读取/受控写回本地 Grist | Skill / Codex | visible / unverified | explicit-only | 仅用于用户点名的 SEO Grist；不要读取密钥值或未经确认写回 | high；回退只读文件检查 | [卡](./manifests/grist-table-reader.md) |
| product-design:index | 产品设计任务路由 | manager-type Skill / Codex | visible / unverified | explicit-only | 仅用于明确产品设计任务；不要用于普通 UI 小修或泛问答 | medium；回退具体设计子技能 | [卡](./manifests/product-design-index.md) |
| data-analytics:index | 数据分析任务路由 | manager-type Skill / Codex | visible / unverified | explicit-only | 仅用于明确分析任务；不要为简单计算加载整套分析流程 | medium；回退表格或直接回答 | — |
| superpowers:using-superpowers | 开场方法论路由 | manager-type Skill / Codex | visible / unverified | disabled-candidate | 不应常驻普通任务；不要在未显式 allowlist 时改写默认工作流 | high；回退原生任务流程 | [卡](./manifests/superpowers-using-superpowers.md) |
| documents:documents | 生成/编辑文档 | Skill / Codex | visible / unverified | conditional | 仅用于文档文件；不要用于纯文本回答 | medium；回退 Markdown | — |
| spreadsheets:Spreadsheets | 生成/分析表格 | Skill / Codex | visible / unverified | conditional | 仅用于表格文件；不要与 Google Sheets 能力重复加载 | medium；回退 CSV/直接分析 | — |
| imagegen | 生成或编辑图片 | Skill / Codex | visible / unverified | conditional | 仅用于用户要图像生成/编辑；不要用于普通设计建议 | medium；回退文字方案 | — |
| shopify:shopify-dev | Shopify 文档兜底检索 | Skill / Codex | visible / unverified | conditional | 仅在无更具体 Shopify API skill 时用；不要抢占明确 API 入口 | low；回退具体 Shopify skill | — |
| seo-content-engine | 生成 SEO 内容产物 | Skill / Codex | visible / unverified | explicit-only | 仅用于用户 SEO 工作台产物；不要在未给业务上下文时臆造数据 | medium；回退通用写作 | — |
| superpowers-governance-gate | 判断软件任务是否需要升级工程流程 | policy / Codex | configured / unverified | conditional | 仅在考虑 Superpowers 流程升级时使用；普通修改可从项目上下文解决时不要使用 | medium；回退 `baseline-direct` 和普通软件路由 | [规则](./superpowers-governance.md) |
