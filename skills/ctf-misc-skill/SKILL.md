---
name: CTF Misc Solver
description: |
  当用户正在进行 CTF 比赛或练习，遇到 Misc 类型题目时触发此 Skill。
  适用场景包括：
  - 用户上传或提及了音频文件（wav/mp3/flac）、图片文件（png/jpg/bmp/gif）、压缩包、pcap 流量包、内存镜像（raw/vmem/dmp）等
  - 用户描述了隐写、编码、套娃、文件分析、内存取证相关问题
  - 用户明确说"CTF"、"Misc"、"隐写"、"找 flag"、"这是一道题"、"内存取证"、"Volatility"等关键词
  - 用户提供了 base64/hex/binary 等编码字符串需要解码
  - 用户需要分析可疑文件、提取隐藏数据、还原协议内容、分析内存镜像
---

# CTF Misc Solver Skill

Use this skill when the task matches the description above.
Keep the initial response concise and only open bundled references or scripts when clearly needed.

## Quick cues

- **系统性拆解** 题目结构，识别所有可能的隐藏层
- **自动推理** 出题人意图和隐写/编码路径
- **生成可执行脚本** 进行自动化提取和验证
- **逐层剥离** 直到找到 flag 或穷尽所有合理路径
- 包含 Base64/Hex/Binary 特征 → modules/encoding.md
- 纯文本但有编码特征 → modules/encoding.md
- 题目描述提到"编码"/"加密" → modules/encoding.md
- 89 50 4E 47 → PNG (modules/image.md)

## Available sections

- CTF Misc Solver Skill
- 🎯 Core Objective
- 🧠 题目类型识别与调度规则
- 自动识别流程
- Modules 调用规则
- 📋 标准解题流程（Universal Workflow）
- Phase 1: 初始侦察（Reconnaissance）
- 1. 文件类型识别
- 2. 元数据提取
- 3. 快速隐写扫描（根据类型选择）
- Phase 2: 分类深入分析
- 🖼️ 图片类核心检查

## Bundled resources

- docs
- modules
