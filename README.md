# Codex Superpowers 治理便携包

这是从一台已经通过新会话验证的 Codex 环境中整理出的脱敏便携包，用于把相同的 Superpowers 分层治理复制到其他电脑。

## 治理结果

- Superpowers 插件原始技能路径全部禁用，避免同一技能重复暴露。
- 14 个用户拥有的技能副本安装到用户技能目录。
- 13 个流程升级技能默认不允许隐式调用。
- `verification-before-completion` 保持条件自动调用。
- `brainstorming` 只有在最小检查后仍有实质歧义、直接修改可能明显返工，并获得用户确认后才调用。
- 全局 `AGENTS.md` 只注入一个带标记的受管区块，不覆盖原有个人规则。
- `config.toml` 只替换本包管理的 Superpowers 配置，不覆盖模型、MCP、项目信任或其他插件设置。

## 支持范围

- macOS、Linux、Windows
- Python 3.9 或更高版本，只使用标准库
- Codex 配置目录默认是 `$CODEX_HOME`；未设置时使用 `~/.codex`
- 用户技能目录默认是 `~/.agents/skills`
- 本包基于 Superpowers 6.2.0 整理。其他版本可先运行预检，再决定是否安装。

## 使用

先关闭 Codex，进入本仓库目录后运行：

```bash
python3 scripts/preflight.py
python3 scripts/install.py --dry-run
python3 scripts/install.py
```

macOS 或 Linux 也可以运行：

```bash
./scripts/install.sh
```

安装完成后重启 Codex，新建一个任务，再运行结构验证：

```bash
python3 scripts/verify.py
```

如果目标电脑使用了自定义目录：

```bash
python3 scripts/install.py \
  --codex-home "/path/to/.codex" \
  --agents-skills-dir "/path/to/.agents/skills"
```

## 新会话行为验收

在重启后的新任务中检查：

1. 普通的小型 UI 修改不应自动触发计划、子代理、TDD、worktree 或 `brainstorming`。
2. 输入 `$systematic-debugging` 时，该显式技能仍应可用。
3. 对确实存在结构性歧义的需求，Codex 应先检查项目上下文，再只询问一次是否启用需求梳理。
4. 完成修改前应做与改动规模相称的验证，但不应因此串联其他 Superpowers 流程。

## 回滚

先关闭 Codex，然后运行：

```bash
python3 scripts/rollback.py
```

回滚脚本会恢复最近一次安装前的 `config.toml`、`AGENTS.md`、治理文档和用户技能副本。当前安装内容会移动到带时间戳的隔离目录，不直接删除。

## 安全与隐私

本仓库不包含：

- `auth.json`、API Key、访问令牌或登录信息
- Codex 会话、状态数据库、日志或缓存
- 个人 `config.toml` 全文
- 本机用户名、项目路径或受信任项目列表
- 插件缓存的机器特定绝对路径

发布到远程 Git 仓库前运行：

```bash
python3 scripts/audit_bundle.py
git status --short
```

第三方 Superpowers 技能文件遵循其原始 MIT License，见
[`LICENSES/Superpowers-LICENSE`](LICENSES/Superpowers-LICENSE)。
来源和修改范围见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。
