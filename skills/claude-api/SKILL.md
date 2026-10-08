---
name: claude-api
description: "Build apps with the Claude API or Anthropic SDK. TRIGGER when: code imports `anthropic`/`@anthropic-ai/sdk`/`claude_agent_sdk`, or user asks to use Claude API, Anthropic SDKs, or Agent SDK. DO NOT TRIGGER when: code imports `openai`/other AI SDK, general programming, or ML/data-science tasks."
license: Complete terms in LICENSE.txt
---

# Building LLM-Powered Applications with Claude

Use this skill when the task matches the description above.
Keep the initial response concise and only open bundled references or scripts when clearly needed.

## Quick cues

- **Look at project files** to infer the language:
- `*.py`, `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile` → **Python** — read from `python/`
- `*.ts`, `*.tsx`, `package.json`, `tsconfig.json` → **TypeScript** — read from `typescript/`
- `*.js`, `*.jsx` (no `.ts` files present) → **TypeScript** — JS uses the same SDK, read from `typescript/`
- `*.java`, `pom.xml`, `build.gradle` → **Java** — read from `java/`
- `*.kt`, `*.kts`, `build.gradle.kts` → **Java** — Kotlin uses the Java SDK, read from `java/`
- `*.scala`, `build.sbt` → **Java** — Scala uses the Java SDK, read from `java/`
- `*.go`, `go.mod` → **Go** — read from `go/`

## Available sections

- Building LLM-Powered Applications with Claude
- Defaults
- Language Detection
- Language-Specific Feature Support
- Which Surface Should I Use?
- Decision Tree
- Should I Build an Agent?
- Architecture
- Current Models (cached: 2026-02-17)
- Thinking & Effort (Quick Reference)
- Compaction (Quick Reference)
- Reading Guide

## Bundled resources

- csharp
- curl
- go
- java
- LICENSE.txt
- php
- python
- ruby
- shared
- typescript
