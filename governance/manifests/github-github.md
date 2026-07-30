# GitHub 路由 能力卡

仅用于：GitHub 仓库、Issue、PR 的定向读取与路由
不要用于：未经确认的外部写入、发布或权限变更

## 基本信息

- Capability ID：`github:github`
- 类型：Skill
- 平台：Codex
- 来源：openai-curated-remote/github 0.1.8
- 能力槽：GitHub 仓库、Issue、PR 的定向读取与路由

## 冷库处置

- 管理状态：active
- 健康状态：healthy
- 风险：medium
- 隔离：false
- 重复组：见一级路由中的相邻候选

## 路由

- Need gate：已有信息足够时先用 `baseline-direct`
- 触发条件：GitHub 仓库、Issue、PR 的定向读取与路由
- 禁用条件：未经确认的外部写入、发布或权限变更
- 替代方案：一级路由中同类候选

## 激活与回滚

- 激活方式：GitHub 任务命中时加载
- 健康检查：读取一个公开仓库并核对 README
- 停用方式：不调用写操作
- 回滚方式：回退公开 GitHub 页面或本地 git

## 验证与安全

- 本轮验证：已成功加载并用于读取 GitHub 项目说明
- 最近验证：2026-07-21
- 权限范围：A2 只读；写入升到 A3
- 凭据：不读取或记录凭据值
- 外部副作用：PR/Issue/评论/标签等写操作
- 备注：首次隔离试跑生成；需要真实任务时再做最小执行验证。

