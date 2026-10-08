---
name: mcp-builder
description: Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).
license: Complete terms in LICENSE.txt
---

# MCP Server Development Guide

Use this skill when the task matches the description above.
Keep the initial response concise and only open bundled references or scripts when clearly needed.

## Quick cues

- Specification overview and architecture
- Transport mechanisms (streamable HTTP, stdio)
- Tool, resource, and prompt definitions
- **MCP Best Practices**: [📋 View Best Practices](./reference/mcp_best_practices.md) - Core guidelines
- **TypeScript SDK**: Use WebFetch to load `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md`
- [⚡ TypeScript Guide](./reference/node_mcp_server.md) - TypeScript patterns and examples
- **Python SDK**: Use WebFetch to load `https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md`
- [🐍 Python Guide](./reference/python_mcp_server.md) - Python patterns and examples

## Available sections

- MCP Server Development Guide
- Overview
- Process
- 🚀 High-Level Workflow
- Phase 1: Deep Research and Planning
- 1.1 Understand Modern MCP Design
- 1.2 Study MCP Protocol Documentation
- 1.3 Study Framework Documentation
- 1.4 Plan Your Implementation
- Phase 2: Implementation
- 2.1 Set Up Project Structure
- 2.2 Implement Core Infrastructure

## Bundled resources

- LICENSE.txt
- reference
- scripts
