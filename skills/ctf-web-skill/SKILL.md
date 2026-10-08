---
name: CTF Web Solver
description: |
  当用户正在进行 CTF 比赛或练习，遇到 Web 类型题目时触发此 Skill。
  适用场景包括：
  - 用户描述了 SQL 注入、XSS、SSRF、SSTI、XXE、文件包含、命令执行等 Web 安全问题
  - 用户需要进行信息搜集、目录扫描、端口扫描等渗透前期工作
  - 用户遇到 PHP 特性利用、反序列化、JWT 伪造等高级攻击场景
  - 用户提及 "CTF"、"Web"、"渗透"、"注入"、"绕过"、"漏洞" 等关键词
  - 用户需要分析 Java 代码审计、区块链安全、组件漏洞利用等问题
  - 用户需要构造 payload、编写 exploit、分析 WAF 绕过策略
---

# CTF Web Solver Skill

Use this skill when the task matches the description above.
Keep the initial response concise and only open bundled references or scripts when clearly needed.

## Quick cues

- **系统性分析** 目标应用的技术栈和潜在漏洞点
- **精准定位** 漏洞类型并构造有效的攻击 payload
- **自动化测试** 生成可执行的 exploit 脚本
- **绕过防护** 分析 WAF/过滤规则并提供绕过方案
- **逐层渗透** 从信息搜集到获取 flag 的完整攻击链
- 提供详细的 payload 和绕过技巧
- 先在本文件中完成核心分析和思路
- 在需要详细利用方法时，才参考对应 module

## Available sections

- CTF Web Solver Skill
- 🎯 Core Objective
- 🧠 题目类型识别与调度规则
- 自动识别流程
- Modules 调用规则
- 📋 标准解题流程（Universal Workflow）
- Phase 1: 信息搜集（Reconnaissance）
- 1. 基础信息收集
- 2. 目录扫描
- 3. 敏感文件探测
- 4. 子域名枚举
- Phase 2: 分类深入分析

## Bundled resources

- docs
- modules
