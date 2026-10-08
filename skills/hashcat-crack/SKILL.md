---
name: hashcat-crack
description: "使用 hashcat 进行密码哈希离线破解。当获取到密码哈希（NTLM/NTLMv2/Kerberos TGS/AS-REP/SHA/MD5/bcrypt/NetNTLMv2）需要还原明文密码时使用。hashcat 是 GPU 加速的密码破解工具，比 john 快几十倍。覆盖哈希类型识别、字典攻击、规则攻击、掩码攻击、组合攻击。拿到 hashdump/secretsdump/Kerberoast/AS-REP 输出后必用此技能"
metadata:
  tags: "hashcat,crack,hash,password,ntlm,kerberos,tgs,md5,sha,密码,破解,GPU,john,哈希"
  category: "tool"
---

# hashcat 密码哈希离线破解

Use this skill when the task matches the description above.
Keep the initial response concise and only open bundled references or scripts when clearly needed.

## Available sections

- hashcat 密码哈希离线破解
- 哈希类型识别（-m 参数）
- 攻击模式
- 字典攻击（最常用）
- 基本字典攻击
- 加规则（变形字典，如 password → Password1!）
- 常用规则文件
- best64.rule — 64 条高效规则，速度和效果平衡
- rockyou-30000.rule — 大规则集，覆盖更多变形
- OneRuleToRuleThemAll.rule — 社区最强规则集
- 掩码攻击（已知密码模式）
- 8 位纯数字
