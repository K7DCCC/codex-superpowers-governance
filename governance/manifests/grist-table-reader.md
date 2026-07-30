# Grist SEO 工作台 能力卡

仅用于：用户点名本地 SEO Grist 数据读取或受控写回
不要用于：未给 ClientID/WebsiteID、Grist 未关闭、或用户未确认写回

## 基本信息

- Capability ID：`grist-table-reader`
- 类型：Skill
- 平台：Codex
- 来源：user-local
- 能力槽：用户点名本地 SEO Grist 数据读取或受控写回

## 冷库处置

- 管理状态：cold
- 健康状态：unverified
- 风险：high
- 隔离：false
- 重复组：见一级路由中的相邻候选

## 路由

- Need gate：已有信息足够时先用 `baseline-direct`
- 触发条件：用户点名本地 SEO Grist 数据读取或受控写回
- 禁用条件：未给 ClientID/WebsiteID、Grist 未关闭、或用户未确认写回
- 替代方案：一级路由中同类候选

## 激活与回滚

- 激活方式：仅在明确 Grist 任务中显式加载
- 健康检查：先运行只读 status；写回必须 preview 后 verify
- 停用方式：停止本地桥或不执行 apply
- 回滚方式：依赖备份并用 verify 核验

## 验证与安全

- 本轮验证：未执行真实任务；仅确认本会话暴露与本地定义存在
- 最近验证：2026-07-21
- 权限范围：A2 只读；写回为 A3
- 凭据：不读取或记录凭据值
- 外部副作用：可能启动本地桥、修改本地数据库
- 备注：自定义能力，建议下一轮优先做只读健康检查。

