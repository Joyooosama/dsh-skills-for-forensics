---
name: cybersecurity-skill-router
description: Route cybersecurity tasks to the best installed specialist skill, including Chinese requests about 应急响应, 取证, 恶意软件, 逆向, 云安全, Web/API 安全, 权限/IAM, SOC, CTF, 渗透测试, 勒索软件, 钓鱼邮件, 流量分析, 内存分析, APK 分析, and 工控/OT.
domain: skill-index
subdomain: router
tags:
- cybersecurity
- skill-routing
- index
- taxonomy
---

# Cybersecurity Skill Router

Use this skill when the user asks for cybersecurity work and no more specific installed skill has already been selected.

## Routing Rules

1. If the request is a CTF/challenge, start with the existing local `solve-challenge` skill, then route to `ctf-*`, `forensics-tools`, `hashcat-crack`, or reverse-engineering helper skills as needed.
2. If the request names a specific tool or artifact type, prefer the matching specialist skill first. Examples: `jadx`, `apktool`, `rev-frida`, `memory-forensics`, `wireshark-analysis`, `server-audit`.
3. For enterprise/security-operations work, use the Anthropic cybersecurity skill taxonomy in `references/skill-taxonomy.md`, then open only the exact matching skill's `SKILL.md`.
4. Prefer existing local skills for broad workflows and tool operation; prefer Anthropic cybersecurity skills for domain playbooks, checklists, and task-specific security procedures.
5. Keep the active context small. Load the category index first, then the specific skill and only its directly referenced scripts or references.

## Chinese Routing Cues

- `CTF`, `题目`, `flag`, `misc`, `web题`, `pwn`, `crypto`, `逆向题`: use `solve-challenge`, then the matching `ctf-*` skill.
- `APK`, `安卓`, `jadx`, `apktool`, `Frida`, `hook`, `脱壳`, `反调试`: use local reverse-engineering skills first, then Android/mobile malware skills.
- `内存`, `dump`, `Volatility`, `进程`, `凭据`, `lsass`: use memory forensics and malware/endpoint skills.
- `pcap`, `流量`, `Wireshark`, `tshark`, `DNS外传`, `TCP stream`: use Wireshark/network forensics skills.
- `勒索`, `勒索软件`, `恢复`, `加密文件`, `赎金`: use ransomware response, recovery, and incident-response skills.
- `钓鱼`, `邮件头`, `SPF`, `DKIM`, `DMARC`, `恶意链接`: use phishing/email-header investigation skills.
- `云安全`, `AWS`, `Azure`, `GCP`, `S3`, `CloudTrail`, `Kubernetes`, `容器`: use cloud/container/DevSecOps skills.
- `域`, `AD`, `Active Directory`, `ACL`, `权限提升`, `IAM`, `零信任`: use identity/IAM/zero-trust skills.
- `Web渗透`, `SQL注入`, `XSS`, `SSRF`, `JWT`, `OAuth`, `API安全`: use web/API security or CTF web skills depending on context.
- `工控`, `OT`, `ICS`, `PLC`, `SCADA`: use network and OT/ICS security skills.

## Index Files

- `references/skill-taxonomy.md` - functional tree with counts and routing guidance.
- `references/routing-aliases.md` - deterministic tool/artifact aliases and preferred first skills.
- `references/anthropic-cybersecurity-skills-by-subdomain.md` - full tree of the 754 Anthropic cybersecurity skills grouped by subdomain.
- `references/existing-local-skills.md` - existing non-Anthropic skills grouped by function.
- `references/all-skills-index.json` - machine-readable index for all installed user-level skills.
