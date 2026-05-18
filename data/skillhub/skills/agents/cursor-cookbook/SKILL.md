---
name: cursor-cookbook
description: Cursor SDK examples — build apps and scripts with the Cursor coding agent API. Covers quickstart, coding-agent CLI, kanban board, and app builder. Use when working with Cursor SDK, CURSOR_API_KEY, cloud agents, or programmatic Cursor automation.
author: Cursor
version: 1.0.0
category: dev
tags: [cursor, sdk, agent, automation, typescript]
source: https://github.com/cursor/cookbook
---

# Cursor Cookbook

Official Cursor SDK examples for building with the Cursor coding agent API.

## Setup

Requires Node.js 22+. Get an API key from [cursor.com/dashboard/integrations](https://cursor.com/dashboard/integrations), then:

```bash
export CURSOR_API_KEY="crsr_..."
```

## Examples

### Quickstart (`sdk/quickstart`)

Minimal example — creates one agent, sends a prompt, streams response to stdout.

```bash
cd sdk/quickstart
pnpm install && pnpm dev
```

### Coding Agent CLI (`sdk/coding-agent-cli`)

Terminal app with one-shot prompts or interactive TUI. Supports local and cloud execution, model selection, session reset.

```bash
cd sdk/coding-agent-cli
pnpm install

# One-shot
pnpm dev -- "Explain how this project is structured"

# Interactive TUI (type / for command menu)
pnpm dev
```

### App Builder (`sdk/app-builder`)

Web app for spinning up agents to scaffold new projects in a sandboxed cloud environment.

### Kanban Board (`sdk/agent-kanban`)

Web UI for viewing Cursor Cloud Agents — group by status or repo, preview artifacts, create new agents.

## Cursor SDK Key Concepts

- `CursorClient` — main entry point, authenticates via `CURSOR_API_KEY`
- `agent.run(prompt)` — starts a run and returns an async iterable of events
- Local runtime: runs in current workspace; Cloud runtime: sandboxed environment
- Events: `text-delta`, `tool-call`, `tool-result`, `run-finished`

```typescript
import { CursorClient } from "@cursor/sdk";

const client = new CursorClient({ apiKey: process.env.CURSOR_API_KEY });
const agent = client.agent({ workspacePath: process.cwd() });

for await (const event of agent.run("Refactor the auth module")) {
  if (event.type === "text-delta") process.stdout.write(event.text);
}
```

## Docs

- SDK Reference: https://cursor.com/docs/api/sdk/typescript.md
- Repo: https://github.com/cursor/cookbook
