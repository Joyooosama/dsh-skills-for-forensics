---
name: server-audit
description: >
  远程服务器安全巡检和环境报告工具。
  通过 SSH 免密登录远程主机，全面检查系统信息、运行服务、开放端口、
  Web 服务器配置、数据库配置、安全设置（SSH/防火墙/SELinux）、可疑进程和定时任务，
  生成结构化的巡检报告。Use when 用户需要检查服务器安全、排查服务器环境、
  了解服务器上运行了什么服务、生成巡检报告、或提及"巡检"、"安全检查"、"服务器检查"。
---

# server-audit — 远程服务器巡检

Use this skill when the task matches the description above.
Keep the initial response concise and only open bundled references or scripts when clearly needed.

## Quick cues

- 已通过 `ssh-ops` skill 配置好免密登录
- 或手动配置了 SSH 密钥认证
- **系统信息**: OS、内核、CPU、内存、磁盘、Swap
- **运行服务**: systemd running services
- **开放端口**: 所有 TCP 监听端口
- **防火墙**: firewalld 状态和规则、SELinux 状态
- **Web 服务**: Nginx/PHP-FPM/MariaDB/Node/Docker 版本和状态
- **Nginx 虚拟主机**: server_name、root、listen

## Available sections

- server-audit — 远程服务器巡检
- 前提条件
- 工作流程
- 1. 运行巡检脚本
- 2. 基于脚本输出生成详细报告
- 服务器巡检报告
- 1. 基础信息
- 2. 已安装服务
- 3. 开放端口（标注风险）
- 4. 安全问题（🔴严重/⚠️警告/💡建议）
- 5. 快速修复命令
- 安全判定规则

## Bundled resources

- _meta.json
- CHANGELOG.md
- scripts
