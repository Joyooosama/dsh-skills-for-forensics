---
name: thunder-app-analysis
description: 当用户要求分析 APK、XAPK、IPA、小程序包、iOS 隐私报告、URL 等移动应用证据，查询包名、权限、第三方 SDK、加固或源码时使用。也适用于查询当前连接的设备或其他可用设备，以及执行动态监控、网络抓包和 Frida/Hook 定向分析，包括观察加解密参数、Key/IV、明文与密文、哈希、数据库操作、Native/JNI 调用、TLS Pinning 等运行数据。该 skill 使用 thunder-app-cli 连接 Thunder-App-Analysis 后端，提供案件、证据、设备、静态分析和动态分析能力。
---

# Thunder App CLI

Use `thunder-app-cli.exe` to interact with a running `Thunder-App-Analysis` backend service.

## Executable Path Rule

Every command MUST start with the resolved `thunder-app-cli.exe` path wrapped in double quotes (`"`).

Resolve the executable path in this order:
1. Use the `thunder-app-cli.exe` in the same directory as this `SKILL.md` when available.
2. If `./thunder-app-cli.exe` exists in the current directory, use `"./thunder-app-cli.exe"`.
3. If none of these paths works, ask the user for the absolute path.

Verify the CLI by running the resolved `thunder-app-cli.exe` with the `--help` flag.

Default backend endpoint: `http://127.0.0.1:9112`.

## Requirements

- The master backend must already be running.
- Do not invent CLI results. Base every answer on the JSON returned by the command.

## Command Reference

Run the resolved CLI with `--help` to see all available commands and flags. Help output is the source of truth for supported commands:

```shell
"./thunder-app-cli.exe" --help
"./thunder-app-cli.exe" <command> --help
"./thunder-app-cli.exe" <command> <subcommand> --help
```

Use `--server` only when the backend is not on the default endpoint.

## Syntax

Flags use long options:

```shell
"./thunder-app-cli.exe" case detail --cid 1
```

Quote paths and values that contain spaces:

```shell
"./thunder-app-cli.exe" evidence add --cid 1 --file "D:\samples\test app.apk"
```

Durations use Go-style values:

```shell
"./thunder-app-cli.exe" --timeout 60s evidence add --cid 1 --file "D:\samples\test.apk"
```

## Targeting

- Cases are targeted by `cid`.
- Evidence apps are targeted by `cid` plus `aid`.
- Static analysis queries are targeted by `cid` plus `aid`.
- Unpack operations are targeted by `cid` plus `aid`.
- Source decompile is targeted by `cid` plus `aid`.
- Dynamic monitoring is targeted by `cid` plus `aid`; `tid` optionally selects one monitoring task.
- Network capture is targeted by `cid` plus `aid`; `tid` optionally selects one capture task.
- Frida operations are targeted by `cid` plus `aid`; `tid` identifies one Frida task and its runtime output.
- Most evidence and analysis operations require an opened case context in master. Run `case open --cid <cid>` before adding evidence or preparing later analysis tasks.
- `case open --cid <cid>` changes the current case inside master.
- `case open --case-path <case_db_path>` opens a known `.taac` case database path; prefer `--cid` when the case ID is known.
- `device select --id <device_id>` changes the current selected device inside master.
- `device disconnect` clears the current selected device inside master.
- `evidence add --file <path-or-url>` passes a local path or downloadable URL to master. Local paths must be accessible to the master process; this is not a file upload.
- APK unpacking requires a selected Android device that satisfies the backend unpacking requirements. IPA unpacking requires a selected iOS device that satisfies the backend unpacking requirements.
- Dynamic monitoring requires supported Android/iOS app evidence and a selected compatible device with ROOT or jailbreak privileges. A running analysis task may temporarily block startup.
- Network capture requires compatible evidence and a selected device. Android capture modes require ROOT; iOS proxy capture requires the user to configure the returned master proxy address and trust its certificate.
- Frida execution requires supported Android/iOS app evidence and a selected compatible device with ROOT or jailbreak privileges. It does not require completed static analysis, but another running analysis task may block startup.

## Output Handling

All commands return JSON with this shape:

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

On failure:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Failure message",
    "suggestion": "Optional suggestion"
  }
}
```

Rules:

- Treat `success=true` as the only success signal.
- If `success=false`, report `error.code`, `error.message`, and `error.suggestion` when present.
- For paginated outputs, `page` is the current page, `pageSize` is the requested maximum page size, `count` is the number of items returned in the current page, and `total` is the total number of matching items. If `hasMore` is present, use it to decide whether another page is available.
- Do not parse human text from stderr/stdout when JSON fields are available.
- Summarize only fields returned in `data`; do not infer missing values.

## Quick Examples

These examples show command shape only. Use the decision workflow below to choose the correct command for the user's intent.

```shell
"./thunder-app-cli.exe" health
"./thunder-app-cli.exe" case current
"./thunder-app-cli.exe" evidence list --cid 1
"./thunder-app-cli.exe" evidence add --cid 1 --file "D:\samples\test.apk" --evidence-no "EV-001"
"./thunder-app-cli.exe" analysis basic --cid 1 --aid 2
"./thunder-app-cli.exe" analysis detail --cid 1 --aid 2
"./thunder-app-cli.exe" unpack start --cid 1 --aid 2
"./thunder-app-cli.exe" --timeout 5m source decompile --cid 1 --aid 2
"./thunder-app-cli.exe" dynamic overview --cid 1 --aid 2
"./thunder-app-cli.exe" capture overview --cid 1 --aid 2
"./thunder-app-cli.exe" device list --refresh
"./thunder-app-cli.exe" device info
```

## Decision Workflow

When the user asks whether Thunder is available:

1. Run `health`.
2. If it fails with a connection error, tell the user to start master and confirm port `9112`.

When the user asks to list or inspect cases:

1. Run `case list` or `case detail --cid <cid>`.
2. Report returned case IDs, case names, numbers, and paths.
3. Do not treat `case list` as an evidence/app list; use `evidence list --cid <cid>` for complete evidence apps.

When the user asks whether a case is already open:

1. Run `case current`.
2. Treat `data.opened=true` as the current opened case signal.
3. If `data.opened=false`, tell the user there is no opened case in master.

When creating a case:

1. `case create` requires `--name`, `--case-no`, and `--case-path`.
2. Use `--case-path` as the save root directory, not a `.taac` file path.
3. Use `--username`, `--investigator`, `--description`, or `--remark` only when the user provides those values.
4. The returned `casePath` is the generated backend database file path.

When the user provides supported app evidence and an existing case ID:

1. Run `case current`.
2. If `data.opened=true` and `data.cid` matches the target case ID, continue.
3. Otherwise run `case open --cid <cid>`.
4. Run `evidence add --cid <cid> --file "<path-or-url>"`.
5. Add `--name` or `--app-type` only when the user provided an evidence display name or app type.
6. Report `cid`, `aid`, app name, package name, platform, and analysis status if present.

When the user provides supported app evidence but no case:

1. Run `case current`.
2. If `data.opened=true`, use that case unless the user asked for a different one.
3. Otherwise run `case list` to find existing cases.
4. If there is no clear target case, ask the user for the case to use or the case name/number/path to create.
5. Do not add evidence until a case target is known.

When the user asks for one evidence record or full evidence metadata:

1. Identify the target `cid` and `aid`; use `evidence list --cid <cid>` when the app ID is unknown.
2. Run `evidence detail --cid <cid> --aid <aid>`.
3. Use `analysis basic --cid <cid> --aid <aid>` instead when the user asks for normalized app identity fields such as package name or app version.

When the user asks for package name, Application ID, app name, app version, evidence number, file size, or analysis status:

1. Identify the target `cid` and `aid`; use `evidence list --cid <cid>` when the app ID is unknown.
2. Run `analysis basic --cid <cid> --aid <aid>`.
3. For Android APKs, treat `data.basic.package_name` as the Application ID / package name.
4. Do not use `analysis detail` for package name or Application ID unless `analysis basic` is unavailable.

When the user asks for app static detail, hashes, signatures, Activity, hardening, dex, or so files:

1. Identify the target `cid` and `aid`; use `evidence list --cid <cid>` when the app ID is unknown.
2. Run `analysis detail --cid <cid> --aid <aid>`.
3. Answer from `data.detail` only.

When the user asks for static permissions:

1. Identify the target `cid` and `aid`.
2. Run `analysis permissions --cid <cid> --aid <aid>`.
3. Use `--level D` for dangerous permissions, `--level S` for signature permissions, or `--sensitive-only` for both.
4. Add `--keyword` to search permission names/descriptions and `--limit` to control returned item count.
5. Report `all_counts`, `filtered_counts`, `total`, and returned `items`.

When the user asks for third-party services, SDKs, packer/provider, suspected forensic values, or third-party clues:

1. Identify the target `cid` and `aid`.
2. Run `analysis third-party --cid <cid> --aid <aid>`.
3. Use `--category provider`, `--category sdk`, `--category suspected`, or `--category clue` when the user asks for a specific type.
4. Add `--keyword` to search returned provider/SDK/clue text and `--limit` to control returned item count.
5. Report results grouped by `provider`, `sdks`, `suspected_sdks`, and `clues`.

When the user asks to unpack, dump, or extract runtime APK/IPA code:

1. Identify the target `cid` and `aid`; use `evidence list --cid <cid>` when the app ID is unknown.
2. Check `device info` if the user has not confirmed a usable device.
3. Run `unpack start --cid <cid> --aid <aid>`.
4. If `data.started=true`, report returned `tid`, `status_name`, `platform`, `precheck`, and `next`.
5. If `data.skipped=true`, report `precheck.reason` and `precheck.suggestion`; do not retry `unpack start` unless the user explicitly asks to force it. If they do, add `--force`.
6. Use `unpack files --cid <cid> --aid <aid>` when the user asks for produced files or after the task is expected to have completed.
7. Use `unpack stop --tid <tid>` only when the user asks to stop a running unpack task.

When the user asks to decompile APK source or inspect code structure:

1. Identify the target `cid` and `aid`; use `evidence list --cid <cid>` when the app ID is unknown.
2. Run `source decompile --cid <cid> --aid <aid>`; use a larger global timeout such as `--timeout 5m` for large apps.
3. If `data.supported=false`, report `unsupported_reason` and do not fabricate source results.
4. If `data.decompiled=true`, report `tree_count`, `root`, `top_nodes`, `warnings`, and `next`.
5. Use the returned `root` and `top_nodes` with the agent's own file search/read tools to inspect decompiled source files.
6. Use `source stop --aid <aid>` only when the user asks to stop source decompilation.

When the user asks to dynamically monitor an app or analyze runtime behavior:

1. Identify the target `cid` and `aid`; import the evidence first if needed.
2. Use `dynamic overview --cid <cid> --aid <aid>` for readiness, current progress, or the latest monitoring summary. It does not start or stop a task.
3. Run `dynamic start --cid <cid> --aid <aid>` only when the user asks to perform or start dynamic monitoring.
4. If `data.started=false`, report `preflight.status`, failed checks, and `user_message`; do not repeatedly retry while the prerequisite or blocking task is unchanged.
5. Use `dynamic results --cid <cid> --aid <aid>` to read behavior records. Add `--tid` for a specific task, `--item-number` for precise server-side filtering, or `--category`/`--keyword` for exploratory analysis.
6. Treat `scan_limited=true` and `boundaries` as incomplete-result warnings. Prefer `--item-number` when exact pagination is required.
7. Use `dynamic stop --cid <cid> --aid <aid>` only when the user asks to stop monitoring. Do not attempt to stop a dynamic child task owned by automatic analysis.

When the user asks to capture or analyze app network traffic:

1. Identify the target `cid` and `aid`; import the evidence and select a compatible device first if needed.
2. Use `capture overview --cid <cid> --aid <aid>` for readiness, current progress, packet counts, and grouped summaries. It does not start or stop a task.
3. Run `capture start --cid <cid> --aid <aid>` only when the user asks to start capture. Use `--mode` only when the user requests a specific mode.
4. If `proxy_setup.status=proxy_ip_required`, ask the user to choose one returned candidate and retry with `--mode proxy --proxy-ip <ip>`.
5. If `proxy_setup.status=proxy_configuration_required`, report its IP and port. After the user explicitly confirms the iOS proxy and certificate setup, retry with `--mode proxy --proxy-ip <ip> --proxy-port <port> --proxy-ready`.
6. Use `capture results --cid <cid> --aid <aid>` to inspect packets. Add filters for focused analysis and `--include-content` only when request or response content is needed.
7. Treat `scan_limited=true` and `boundaries` as incomplete-result warnings.
8. Use `capture stop --cid <cid> --aid <aid>` only when the user asks to stop capture. Do not stop a capture child task owned by automatic analysis.

When the user asks to observe targeted runtime values or behavior with Frida/Hook:

1. Use Frida for specific runtime parameters, return values, call stacks, cryptographic data, database operations, Native/JNI calls, or runtime bypasses. Prefer `dynamic` for broad behavior observation and `capture` for ordinary network traffic.
2. Identify the target `cid` and `aid`, then run `frida catalog --cid <cid> --aid <aid> --goal "<the user's original goal>"` and select the smallest necessary set of returned stable capability IDs.
3. Do not guess script IDs. Treat `fallback_only=true`, behavior-changing hooks, keys, certificates, and plaintext capture as risk signals that must be explained before execution.
4. Use `frida start ... --dry-run` when the user asks for a plan or when risk needs confirmation. Run `frida start` without `--dry-run` only when the user explicitly requests execution.
5. For a custom script, register a local `.js` file with `frida add --file "<local-path>"`, then use the returned `custom:<id>` capability ID.
6. After startup, ask the user to perform the target app action. Use `frida results --tid <tid>` only when live output needs to be inspected; while the task is running, `eof=true` means only that the current end of the log has been reached.
7. When the user explicitly asks to stop, run `frida stop` immediately. Do not read output first unless the user explicitly asks to inspect live output before stopping. After the task is stopped, read and analyze the completed log when required by the current workflow, continuing from `next_offset` until `eof=true`.
8. `frida status` reports only a currently running task. Do not infer success merely from an empty log.

When the user asks to list available devices:

1. Run `device list --refresh`.
2. Report returned device IDs, names, OS, root status, and device type when present.
3. If the user wants to use one device, run `device select --id <device_id>`.

When the user asks about selected device state:

1. Run `device info`.
2. If the command fails with `NO_DEVICE_SELECTED`, run `device list --refresh` and ask the user which device ID to select if needed.
3. Use `device disconnect` only when the user asks to clear or disconnect the currently selected device.

When the user asks for a command group that is not shown by `--help`:

1. Run the relevant `--help` command if useful.
2. If the command is not available, say that the current CLI does not expose that command yet.
3. Do not fabricate a command.

## Response Rules

- Keep replies concise and action-oriented.
- Include the command outcome and the important returned identifiers.
- For successful case operations, mention `cid`, `caseNumber`, `name`, and `casePath` when present.
- For successful evidence operations, mention `cid`, `aid`, `appName`, `pkgName`, `appOs`, `fileFmt`, and `analysis` when present.
- For app basic information, mention `app_name`, `package_name`, `app_version`, `evidence_number`, `file_id`, and `analysis` when present.
- For static permission results, `D` means dangerous, `S` means signature, `N` means normal, and `O` means other.
- For unpack start results, mention `started`, `skipped`, `precheck.reason`, `precheck.hardening_name`, `tid`, `status_name`, `platform`, and `next` when present.
- For unpack file results, mention `count` and summarize returned file `type`, `name`, `path`, and `size_text`.
- For source decompile results, mention `supported`, `decompiled`, `tree_count`, `root`, `warnings`, and `next` when present.
- For dynamic monitoring, mention `started` or `stopped`, `tid`, `preflight.status`, `current_task.state`, `total_behaviors`, relevant categories, and result boundaries when present.
- For network capture, mention `started` or `stopped`, `tid`, `mode`, `preflight.status`, `proxy_setup`, packet counts, relevant groups, and result boundaries when present.
- For Frida, mention the selected capability IDs, plan warnings, `preflight.status`, `tid`, running/stopped state, and raw-log boundaries. Distinguish observed output, script errors, and no output.
- If `unsupported` or `boundaries` is returned, state it directly and do not infer missing analysis data.
- For failures, report the exact `error.code` and `error.message`.
- If the backend connection is refused, tell the user to start master and confirm the port is `9112`.
