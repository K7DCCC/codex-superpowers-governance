# Superpowers 总入口 能力卡

仅用于：只有用户显式 allowlist 并要求整套方法论路由时
不要用于：普通任务开场、无需方法论接管的问答或实现

## 基本信息

- Capability ID：`superpowers:using-superpowers`
- 类型：manager-type Skill
- 平台：Codex
- 来源：openai-curated-remote/superpowers 6.1.1
- 能力槽：只有用户显式 allowlist 并要求整套方法论路由时

## 冷库处置

- 管理状态：disabled
- 健康状态：unverified
- 风险：high
- 隔离：false
- 重复组：见一级路由中的相邻候选

## 路由

- Need gate：已有信息足够时先用 `baseline-direct`
- 触发条件：只有用户显式 allowlist 并要求整套方法论路由时
- 禁用条件：普通任务开场、无需方法论接管的问答或实现
- 替代方案：一级路由中同类候选

## 激活与回滚

- 激活方式：默认不激活；需显式 allowlist
- 健康检查：在隔离会话测量其触发、后续同族调用与上下文影响
- 停用方式：保持 disabled/explicit-only
- 回滚方式：回退 Codex 原生流程与单个具体技能

## 验证与安全

- 本轮验证：未执行真实任务；仅确认本会话暴露与本地定义存在
- 最近验证：2026-07-21
- 权限范围：A0-A3，取决于被继续路由的子技能
- 凭据：不读取或记录凭据值
- 外部副作用：可能改写默认工作流并自我强化调用同族技能
- 备注：命中启动型宽触发与方法论接管特征，属于 P1 治理项。

