# Routing Aliases

Use this file before the full taxonomy when a request names a concrete tool, artifact, or common Chinese security phrase.

## Tool-First Routing

- `jadx`, `APK decompile`, `安卓反编译`: open `jadx` first, then `reverse-engineering-android-malware-with-jadx`.
- `apktool`, `AndroidManifest`, `smali`: open `apktool` first, then `analyzing-android-malware-with-apktool`.
- `Frida`, `hook`, `证书绑定`, `certificate pinning`: open `rev-frida` first, then `performing-mobile-app-certificate-pinning-bypass`.
- `IDA`, `IDAPython`, `idb`: open `rev-idapython` first.
- `Unicorn`, `emulate`, `模拟执行`: open `rev-unicorn-debug` first.
- `Volatility`, `内存 dump`, `memory dump`: open `memory-forensics` first, then `analyzing-memory-dumps-with-volatility` or `performing-memory-forensics-with-volatility3`.
- `Wireshark`, `tshark`, `pcap`, `TCP stream`, `流量包`: open `wireshark-analysis` or `wireshark-network-traffic-analysis` first, then network traffic skills.
- `hashcat`, `NTLM`, `Kerberos`, `密码哈希`: open `hashcat-crack` first.
- `X-Ways`, `E01`, `取证镜像`: prefer the available X-Ways MCP workflow when present, then digital-forensics skills.

## Task-First Routing

- `CTF`, `flag`, `题目`: open `solve-challenge` first.
- `Web题`, `SQL注入`, `SSTI`, `SSRF`, `JWT`: open `ctf-web` for CTF context; otherwise use web/API security skills.
- `勒索`, `勒索软件`, `恢复`: open ransomware response/recovery skills, then incident-response skills.
- `钓鱼`, `邮件头`, `SPF`, `DKIM`, `DMARC`: open phishing/email-header skills.
- `AWS S3`, `bucket公开`: open `auditing-aws-s3-bucket-permissions`.
- `Kubernetes RBAC`, `k8s权限`: open `auditing-kubernetes-cluster-rbac`.
- `Active Directory ACL`, `域内权限`: open `analyzing-active-directory-acl-abuse`.
- `工控`, `PLC`, `SCADA`, `OT`, `ICS`: open OT/ICS security skills.
