---
name: create-vm
description: 用火眼仿真取证软件(BootMagix)把本地镜像文件创建为可启动的虚拟机,并可查询虚拟机 IP。输入镜像路径,自动完成挂载、操作系统识别、虚拟机创建并启动,实时输出每个阶段的 NDJSON 进度;另提供 get-ip 子命令通过 VMware DHCP 租约反查虚拟机 IP 地址。需要 BootMagix 已在本机处于运行状态。
metadata: 
  version: 4.7.1.2882
---

# 创建虚拟机 Skill

## 何时使用

当用户希望把一个磁盘镜像"启动起来"看一下、用 BootMagix 做仿真取证、或描述类似下面这些需求时使用本 skill:

- "用火眼把这个 E01 镜像启动起来"
- "把 D:/samples/win10.vmdk 创建成虚拟机"
- "仿真这块镜像看一下用户都登录过哪些账号"

## 前置条件

1. **操作系统**:Windows
2. **BootMagix 已运行**:用户已经启动 BootMagix(以管理员权限),master 进程已就绪
3. **CLI 已就位**:`bootmagix-cli.exe` 与本文件在**同级目录**

## 调用方式

通过 Bash 工具执行(单镜像):

```
.claude/skills/create-vm/bootmagix-cli.exe create --image "<绝对路径>"
```

**多镜像**(系统盘 + 数据盘,常见场景)— `--image` 可重复传入,**第一块为系统盘**:

```
.claude/skills/create-vm/bootmagix-cli.exe create \
  --image "D:\samples\disk0.e01" \
  --image "D:\samples\disk1.e01" \
  --image "D:\samples\disk2.e01"
```

常用可选参数:
- `--image <path>` **必填,可重复传入多块磁盘**;第一块为系统盘,后续为数据盘
- `--name <name>` 自定义虚拟机名(默认取第一块镜像文件名)
- `--cpu <n>` CPU 核数(默认 2)
- `--memory <mb>` 内存 MB(默认 4096)
- `--connection nat|bridge|hostonly|""` 网络模式(默认 `hostonly`)
- `--guest-os "<name>"` 显式指定 GuestOS(如自动识别失败)
- `--account-action prompt|keep|reset|skip` Windows 账户密码处理策略(默认 `prompt`,有密码时停下询问)
- `--clear-password` 重置用户密码(等价于 `--account-action reset`;Linux 等未检测到账户时也会自动重置)
- `--skip-password` 跳过 Windows 登录密码(等价于 `--account-action skip`)
- `--no-start` 仅创建不启动

> 操作系统识别和账户检测**只在系统盘**(第一块 `--image`)上做,数据盘只挂载、不分析。

## 输出格式

CLI 把进度通过 stdout 写成 **NDJSON 行流**,每行一条 JSON 事件。**必须按行解析**。字段:

| 字段 | 说明 |
|---|---|
| `ts` | ISO8601 时间戳 |
| `type` | `stage`(阶段开始) / `progress`(后端创建进度 10/30/50/80/85/90) / `info`(信息) / `warn`(非致命警告) / `error`(致命) / `prompt`(需要用户决策,后跟 exit 10) / `result`(终态) |
| `stage` | 阶段名,见下表 |
| `progress` | 0-100,仅 `type=progress` 有 |
| `message` | 中文提示 |
| `code` | `type=error` 时的错误码 |
| `need` | `type=prompt` 时的决策项目(目前仅 `account_action`) |
| `accounts` | `type=prompt` 时检测到的账户列表(含 username/password/nthash/lastLoginTime) |
| `options` | `type=prompt` 时可接受的选项,如 `["keep","reset","skip"]` |
| `vm` | `type=result` 时返回创建的虚拟机详情 |
| `started` | `type=result` 时表明是否已启动 |
| `sshPorts` | `type=result` 时返回 Linux 镜像的 SSH 监听端口数组(如 `[2222]` 或 `[22]`);Windows 或未找到 sshd_config 时缺省(Windows 固定 22) |

### 阶段(stage)

依次出现:

```
discovering          发现 master 端口
connecting           连接 master HTTP + WebSocket
auth                 登录
env_check            检查 VMware/Hyper-V 环境
mounting             挂载镜像(多镜像时按顺序逐个挂载,每个一行 info 报告挂载点)
detecting_os         识别 GuestOS
detecting_ssh        检测 Linux 镜像 SSH 监听端口(解析 /etc/ssh/sshd_config;Windows 跳过)
detecting_account    检测系统账户(Windows 下可能检测到本地账户;Linux/无账户时自动重置密码)
creating             创建虚拟磁盘与 .vmx(后端推 progress 10→30→50→80,可能 85→90)
starting             启动虚拟机(若未传 --no-start)
resolving_ip         (get-ip 子命令)通过 vmx + DHCP 租约反查 IP
done                 结束
```

### 错误码(error.code)

- `discovery_failed` — 无法连接 BootMagix 服务器,提示用户先启动 BootMagix
- `auth_failed` — 登录失败
- `env_check_failed` — VMware/Hyper-V 冲突,提示用户在 BootMagix UI 中处理
- `mount_failed` — 挂载失败(镜像损坏 / 磁盘空间不足 / 联机磁盘需脱机)
- `guest_os_unknown` — 自动识别失败,建议用 `--guest-os` 重试
- `vm_dir_exists` — 目标目录 `<savePath>/<name>` 已存在,改用 `--name` 或删除该目录后重试
- `create_failed` / `start_failed` — 后端业务错误,`message` 字段含详情
- `save_path_empty` — 用户未指定且全局设置为空,建议传 `--save-path`

### 退出码

- `0` 成功
- `1` 业务失败
- `2` 参数错误
- `3` master 未运行(此时也会输出 `error` 行 + `discovery_failed`)
- `10` 检测到 Windows 账户密码,**需要用户选择处理方式后重跑**(见下一节)

## 账户密码决策(两段式调用)

当检测到 Windows 账户**明文密码**(master 字典还原成功的 `password` 字段非空)时,CLI **不会擅自决定如何处理**,而是停下来等用户/调用方决策。

> 仅有 NTHash 没还原出明文的情况,因为用户无法知晓原密码,"保留"无实际意义 → CLI **自动按重置密码处理**,不打扰用户(会输出 `info` 行:"检测到 NTHash 但字典未还原明文,自动重置密码")。

流程:

1. **第一次调用**(不传 `--account-action`,或传 `prompt`):
   ```
   bootmagix-cli create --image "<path>"
   ```
   CLI 跑到 `detecting_account` 阶段,如果发现**明文**密码,会输出一行 `type=prompt` 然后 **以 exit code 10 退出**:
   ```jsonc
   {
     "ts":"...","type":"prompt","stage":"detecting_account",
     "need":"account_action",
     "message":"检测到 Windows 账户明文密码,请确认处理方式后用 --account-action 重新运行",
     "accounts":[
       {"username":"Administrator","password":"P@ssw0rd","nthash":"...","lastLoginTime":"..."}
     ],
     "options":["keep","reset","skip"]
   }
   ```
2. **大模型/调用方读取 prompt 行后**,把账户列表友好地呈现给用户,并询问处理方式:
   - **keep** — 保留原密码(用户能用原密码登录虚拟机)
   - **reset** — 重置所有密码为空(进入虚拟机无需密码,**会修改虚拟机内的 SAM**)
   - **skip** — 不重置密码但用补丁绕过 Windows 登录验证(**会修改启动逻辑**)
3. **第二次调用**,带 `--account-action <用户选择>` 重新运行:
   ```
   bootmagix-cli create --image "<path>" --account-action keep
   ```
   CLI 走完剩余阶段(master 端 mount 有 cache,重跑几乎无开销)。

如果没检测到明文密码(包括镜像非 Windows、无本地账户、字典未还原出明文等场景),CLI 不会输出 prompt,直接继续。

> **未检测到账户时的默认行为**:对于 Linux 或其他未检测到本地账户的镜像,CLI 会自动设置 `ClearPassword=true`,由后端重置密码并修复启动故障。这与显式传入 `--clear-password` 或 `--account-action reset` 效果相同。

重置后的凭据规则:Windows 虚拟机在用户选择 **reset** 后,账户密码会被重置为空;Linux 虚拟机默认重置后的账户密码为 `123456`。

## 查询虚拟机 IP

虚拟机启动后,可以用 `get-ip` 子命令通过 **VMware DHCP 租约文件**反查 IP 地址。**不修改 guest**,纯主机端解析,取证友好。

创建出的 Windows 虚拟机会自动启用 OpenSSH 服务(端口固定 **22**);Linux 虚拟机如果镜像内已有 SSH 服务或启动后服务可用,也可以尝试连接。**SSH 端口**:`create` 的 result 事件会返回 Linux 镜像的 `sshPorts` 数组(如 `[2222]` 或 `[22]`)——部分 Linux 服务器会把 sshd 配置成非 22 端口,此时必须用 `ssh -p <port>` 才能连上;未返回 `sshPorts` 时按默认 22 处理。拿到 IP 和端口后,后续 AI 可结合已知账户/密码处理结果,通过 SSH 与虚拟机建立连接并执行命令。

### 用法

任选一种方式定位虚拟机:

```
# 方式 1: 已知 vmx 路径(create 的 result 行里 vm.location + "\\vm.vmx")
.claude/skills/create-vm/bootmagix-cli.exe get-ip --vmx "D:\\vms\\win11\\vm.vmx"

# 方式 2: 已知虚拟机 ID(自动通过 master 反查 vmx 路径)
.claude/skills/create-vm/bootmagix-cli.exe get-ip --vm-id 42
```

### 输出格式

```jsonc
{"type":"stage","stage":"resolving_ip","message":"读取 vmx 提取网卡 MAC 地址"}
{"type":"info","stage":"resolving_ip","message":"找到 1 张网卡"}
{"type":"info","stage":"resolving_ip","message":"租约中发现 88 条 MAC 记录"}
{"type":"info","stage":"resolving_ip","message":"命中 1 张网卡的 IP"}
{
  "type":"result","status":"success",
  "vmx":"D:\\vms\\win11\\vm.vmx",
  "interfaces":[
    {
      "name":"ethernet0",
      "mac":"00:0c:29:8d:39:b3",
      "connectionType":"hostonly",
      "ip":"192.168.74.205",
      "leaseEnds":"2026-05-17T07:47:16Z",
      "expired":false
    }
  ]
}
```

字段:`name` 是 vmx 中的网卡索引(ethernet0/1/...),`mac` 永远小写冒号分隔,`ip` 为空表示该 MAC 不在租约中(客机未启动 / 未获取 DHCP / 或网络模式是 bridge)。

### 何时拿不到 IP

| 场景 | 行为 | 建议 |
|---|---|---|
| 虚拟机刚启动 | `ip` 字段空 + warn 行 | 等 30~60 秒重试,等客机 DHCP 完成 |
| 网络模式 = `bridge` | 拿不到(IP 来自宿主网络的 DHCP) | 改用 ARP 扫描,或登入客机查 |
| 网络模式 = `""`(禁用网卡) | 永远拿不到 | 显然,本来就无网卡 |
| 客机静态 IP 配置 | 拿不到 | DHCP 租约里没有,需登入客机查 |



每收到一行 NDJSON,**立刻**把它转成对用户友好的中文进度回复,不要等全部跑完再总结。示例对应关系:

| NDJSON | 给用户的回复 |
|---|---|
| `{"type":"stage","stage":"discovering",...}` | "正在连接火眼仿真后端..." |
| `{"type":"stage","stage":"mounting",...}` | "正在挂载镜像..." |
| `{"type":"info","stage":"mounting","message":"挂载点: \\\\.\\..."}` | (可省略,挂载点对用户没价值) |
| `{"type":"stage","stage":"detecting_os",...}` | "正在识别操作系统..." |
| `{"type":"info","stage":"detecting_os","message":"识别到 Windows 10 x64"}` | "识别为 Windows 10 x64" |
| `{"type":"info","stage":"detecting_ssh","message":"SSH 监听端口: 2222"}` | "镜像 SSH 端口为 2222(连接时需 `ssh -p 2222`)" |
| `{"type":"info","stage":"detecting_account","message":"检测到 3 个账户"}` | "找到 3 个本机账户" |
| `{"type":"info","stage":"detecting_account","message":"未检测到账户...,自动重置密码"}` | "未检测到账户,自动重置密码" |
| `{"type":"stage","stage":"creating",...}` | "正在创建虚拟机..." |
| `{"type":"progress","stage":"creating","progress":30}` | "创建中 30% — 正在生成虚拟磁盘" |
| `{"type":"progress","stage":"creating","progress":80}` | "创建中 80% — 虚拟机配置完成" |
| `{"type":"stage","stage":"starting",...}` | "正在启动虚拟机..." |
| `{"type":"result","status":"success","vm":{"id":42,"displayName":"win10","location":"D:\\vms\\win10"},"started":true}` | "完成,虚拟机 win10 已启动 (ID 42,目录 D:\\vms\\win10)" |
| `{"type":"error","stage":"discovering","code":"discovery_failed","message":"BootMagix 未运行..."}` | 失败原因 + 建议:"BootMagix 未运行,请先启动它再重试" |

## 示例对话

### 镜像无密码(单次完成)

> **用户**:用火眼仿真把 `D:\samples\win10.e01` 启动起来

> **Claude**:好的,正在通过 BootMagix 创建虚拟机...
>
> *(调用 `bootmagix-cli.exe create --image D:\samples\win10.e01`,边读 NDJSON 边汇报)*
>
> - 连接 master 后端 ✓
> - 挂载镜像 ✓
> - 识别为 Windows 10 x64 ✓
> - 创建虚拟机... 30% → 50% → 80%
> - 启动虚拟机 ✓
>
> 已创建虚拟机 `win10`(ID 42),位于 `D:\vms\win10`,VMware 窗口应已弹出。

### 镜像有 Windows 密码(两段式)

> **用户**:用火眼把 `D:\samples\win11.vhdx` 启动起来

> **Claude**:好的,正在分析镜像...
>
> *(第一次调用,跑到 detecting_account 后看到 `type=prompt`,exit 10)*
>
> 检测到 Windows 账户密码:
>
> | 用户名 | 密码 | 最后登录时间 |
> |---|---|---|
> | Administrator | `P@ssw0rd` | 2026-04-12 09:30 |
>
> 请问你希望:
> 1. **保留原密码**(进入虚拟机用 `P@ssw0rd` 登录)
> 2. **重置所有密码为空**(无需密码,会修改 SAM)
> 3. **跳过登录密码**(用补丁绕过)

> **用户**:保留就行

> **Claude**:好的,继续创建...
>
> *(第二次调用,带 `--account-action keep`,跑完后续阶段)*
>
> - 创建虚拟机... 30% → 50% → 80% ✓
> - 启动虚拟机 ✓
>
> 已创建虚拟机 `win11`(ID 43),目录 `D:\vms\win11`。

### 多镜像(系统盘 + 数据盘)

> **用户**:用火眼把这三个镜像启动起来,`disk0.e01` 是系统盘,后两个是数据盘

> **Claude**:好的,正在创建多盘虚拟机...
>
> *(调用 `bootmagix-cli.exe create --image disk0.e01 --image disk1.e01 --image disk2.e01`)*
>
> - 连接 master 后端 ✓
> - 挂载镜像 [1/3] disk0.e01 ✓
> - 挂载镜像 [2/3] disk1.e01 ✓
> - 挂载镜像 [3/3] disk2.e01 ✓
> - 识别系统盘为 Windows 10 x64 ✓
> - 创建虚拟机(3 块磁盘)... 30% → 50% → 80% ✓
> - 启动虚拟机 ✓
>
> 已创建虚拟机,系统盘为 `disk0.e01`,另挂 2 块数据盘。

## 范围之外(本 skill 暂不处理)

- RAID 重组、BitLocker 解密(需要用户在 BootMagix UI 中先处理)
- 物理盘脱机(只支持镜像文件)
- gho 转 vmdk、vhdx 修复等(请用 BootMagix 工具箱)

遇到这些场景,引导用户回到 BootMagix UI 完成。
