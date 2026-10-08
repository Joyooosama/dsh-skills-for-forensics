# 火眼案件数据分析 Skill 使用说明

本文档面向外部智能体。该 skill 只分析已经打开并解析完成的案件数据。案件列表、
打开、初始化、添加检材和等待解析完成，使用 `ges-case-management`。

## 必需文件

火眼安装后建议提供以下文件：

```text
%APPDATA%\GoldenEyes\skills\ges-case-analysis\SKILL.md
%APPDATA%\GoldenEyes\skills\ges-case-analysis\USAGE.md
%APPDATA%\GoldenEyes\skills\ges-case-analysis\bin\ges.cmd
%APPDATA%\GoldenEyes\skills\ges-case-analysis\bin\ges
```

Linux 可使用同样的 skill 目录结构，例如：

```text
$HOME/.config/GoldenEyes/skills/ges-case-analysis/SKILL.md
$HOME/.config/GoldenEyes/skills/ges-case-analysis/USAGE.md
$HOME/.config/GoldenEyes/skills/ges-case-analysis/bin/ges
```

Windows 火眼本体安装目录需要包含：

```text
C:\Program Files\Honglian\GoldenEyesV4\Python311\python.exe
C:\Program Files\Honglian\GoldenEyesV4\pyplugin\pygesclient
```

Linux 火眼本体安装目录建议包含：

```text
/opt/Honglian/GoldenEyesV4/Python311/bin/python3
/opt/Honglian/GoldenEyesV4/pyplugin/pygesclient
```

如果火眼不在默认安装目录，调用前设置 `GOLDENEYES_HOME`。

Windows PowerShell：

```powershell
$env:GOLDENEYES_HOME = "D:\Apps\GoldenEyesV4"
```

Linux 命令行：

```bash
export GOLDENEYES_HOME=/opt/Honglian/GoldenEyesV4
```

也可以使用 `GE_HOME`，但优先推荐 `GOLDENEYES_HOME`。

## 使用前提

使用本 skill 前必须满足以下任一条件：

- 已通过 `ges-case-management` 执行 `ges case open <cid|case_number|case_name>`。
- 已通过 `ges-case-management` 执行 `ges evidence create ...` 并完成解析。
- 上游案件选择器已经给出明确的火眼实例和案件参数。

如果没有案件上下文，先切换到 `ges-case-management`，不要在本 skill 内猜测案件。

上游提供的案件参数包括：

- `cid`: GES 内部数字案件 ID
- `ges_url`: 火眼 GES 主服务 API 地址，例如 `http://127.0.0.1:8999`
- `storage_host`: 可选；单机版和平台版通常都能自动发现
- `ges_token`: 平台版通常需要；不要在日志或最终回答中输出令牌

平台只提供 URL/token 而没有案件参数时，先使用 `ges-case-management` 运行 `ges case ls`
并询问用户。不要默认选择第一个案件。

如果上游已经给出参数，先运行：

```powershell
%APPDATA%\GoldenEyes\skills\ges-case-analysis\bin\ges.cmd init --cid 1 --ges-url http://127.0.0.1:8999
```

Linux：

```bash
$HOME/.config/GoldenEyes/skills/ges-case-analysis/bin/ges init --cid 1 --ges-url http://127.0.0.1:8999
```

默认会在案件目录写入：

```text
<case_dir>\chat\ges-cli\config.json
```

同时会更新用户默认配置，因此随后可以在任意目录直接调用：

```powershell
%APPDATA%\GoldenEyes\skills\ges-case-analysis\bin\ges.cmd context
%APPDATA%\GoldenEyes\skills\ges-case-analysis\bin\ges.cmd ls /case/
%APPDATA%\GoldenEyes\skills\ges-case-analysis\bin\ges.cmd search potato
```

Linux：

```bash
$HOME/.config/GoldenEyes/skills/ges-case-analysis/bin/ges context
$HOME/.config/GoldenEyes/skills/ges-case-analysis/bin/ges ls /case/
$HOME/.config/GoldenEyes/skills/ges-case-analysis/bin/ges search potato
```

`init` 默认会预热守护进程和运行时。只想保存配置时使用：

```powershell
%APPDATA%\GoldenEyes\skills\ges-case-analysis\bin\ges.cmd init --cid 1 --ges-url http://127.0.0.1:8999 --no-warmup
```

Linux：

```bash
$HOME/.config/GoldenEyes/skills/ges-case-analysis/bin/ges init --cid 1 --ges-url http://127.0.0.1:8999 --no-warmup
```

重复运行 `init` 会默认覆盖当前案件配置和默认用户配置。需要防止覆盖时加
`--no-overwrite`。

## 多开规则

多开火眼时，不要使用共享的全局默认配置作为并发任务的上下文。

当前版本为了使用方便，`ges init` 会同步更新用户默认配置，因此默认同一时间只应
有一个生效的案件上下文。切换案件时重新运行 `ges init --overwrite`。

如果需要目录级隔离，可以使用 `--scope cwd`：

```powershell
ges.cmd init --scope cwd --cid 1 --ges-url http://127.0.0.1:8999
```

如果必须使用用户级命名配置：

```powershell
%APPDATA%\GoldenEyes\skills\ges-case-analysis\bin\ges.cmd init --scope user --profile case-1 --cid 1 --ges-url http://127.0.0.1:8999
%APPDATA%\GoldenEyes\skills\ges-case-analysis\bin\ges.cmd --profile case-1 context
```

Linux：

```bash
$HOME/.config/GoldenEyes/skills/ges-case-analysis/bin/ges init --scope user --profile case-1 --cid 1 --ges-url http://127.0.0.1:8999
$HOME/.config/GoldenEyes/skills/ges-case-analysis/bin/ges --profile case-1 context
```

## 命令流程

推荐工作流：

```powershell
ges.cmd context
ges.cmd ls /case/
ges.cmd grep "keyword" --path /case/
ges.cmd read /case/path/to/data.csv --offset 0 --limit 100
ges.cmd copy /case/path/to/data.csv
ges.cmd search "query" --max-results 10
```

如果还没有初始化，先补：

```powershell
ges.cmd init --cid <cid> --ges-url <url>
ges.cmd context
```

添加检材、等待解析或未来的案件创建/打开/列表操作，必须使用 `ges-case-management`
skill。本 skill 只负责分析已经解析出的案件数据。

使用本地代码、pandas、sqlite3 或其他工具分析 `/case/`、`/evidence_mounts/`
内容前，先用 `ges copy` 复制到当前工作目录。

批量复制检材目录时应一次完成，不要逐文件循环调用：

```powershell
ges.cmd copy "/evidence_mounts/eid-2/分区4(恢复的文件)/" --recursive --glob "**/*.xls" --glob "**/*.xlsx" --dest .\recovered --max-files 1000 --skip-existing --manifest .\recovered-copy.jsonl --async
ges.cmd job status <job-id> --json
```

路径包含中文、空格或括号时必须整体加引号。`--glob` 可重复，`--include` 是完全等价的兼容别名；递归筛选推荐使用 `**/*.xlsx` 这类明确模式。`--skip-existing`
用于中断续传，不能与 `--overwrite` 同时使用。递归复制默认限制为 200 个文件和 256 MiB，
超过已确认规模时再显式提高 `--max-files` 或 `--max-total-bytes`。

`--async` 会立即返回 `job_id`。使用 `ges.cmd job status <job-id> --json` 轮询，或用
`ges.cmd job cancel <job-id> --json` 请求取消。相同参数的活动任务和已完成任务会复用原
`job_id`；明确重跑时添加 `--force-new-job`。写入同一目标目录或父子目录的不同任务会被目标锁拒绝。

## 排障

- 找不到火眼安装目录：设置 `GOLDENEYES_HOME`。
- 找不到 `pygesclient`：确认 `pygesclient` 位于 `%GOLDENEYES_HOME%\pyplugin`。
- 缺少 `cid` 或 `ges_url`：先使用 `ges-case-management` 打开案件，或由上游提供参数后运行 `ges init`。
- 还没有添加检材或检材未解析完成：切换到 `ges-case-management` 执行 `ges evidence create ...`。
- 切换案件后仍返回旧内容：在任务目录重新运行 `ges init ...`，或执行 `ges daemon restart`。
- 不希望使用守护进程：在命令前加全局参数 `--no-daemon`，例如 `ges.cmd --no-daemon context`。
- Linux 封装脚本不可执行：运行 `chmod +x bin/ges`，或用 `sh bin/ges ...` 调用。
