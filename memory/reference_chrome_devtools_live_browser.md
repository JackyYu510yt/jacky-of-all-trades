---
name: reference-chrome-devtools-live-browser
description: "How to connect Claude to the user's live Chrome browser via chrome-devtools-mcp (the working setup + the three gotchas)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 3d5f0b0d-ff46-43c4-b59f-aba0bd134f3f
---

Claude connects to the user's **live, logged-in Chrome** through the `chrome-devtools` MCP server (configured in `~/.claude.json` → `mcpServers.chrome-devtools`, runs `npx -y chrome-devtools-mcp@latest`). Verified working 2026-06-15: could list tabs, switch pages, and screenshot the real browser.

Three things must all be true (each one silently blocked us once):

1. **Chrome's built-in toggle ON** — `chrome://inspect#remote-debugging` → "Allow remote debugging for this browser instance" (server runs at `127.0.0.1:9222`). This is the NEW locked-down mode; `http://127.0.0.1:9222/json/version` returns **404** and that is EXPECTED — classic discovery is blocked on purpose.

2. **The matching MCP flag is `--autoConnect`, NOT `--browserUrl`.** `--browserUrl` needs the classic `--remote-debugging-port` launch flag (requires fully closing/relaunching Chrome). The toggle in #1 pairs only with `--autoConnect` (Chrome 144+; user is on 149). With `--autoConnect`, Chrome shows a one-time "allow connection?" permission dialog — the user must click allow.

3. **Node must be ≥ 22.12.0.** chrome-devtools-mcp hard-refuses older Node ("does not support Node vX"). User was on 22.11.0 → upgraded via `winget upgrade OpenJS.NodeJS.22` to 22.22.3. The server crashes instantly on startup if Node is too old, so NO browser tools load and the failure looks like "MCP not connecting."

After any config/Node change: **fully restart Claude Code** (MCP flags load only at boot). Tradeoff: with `--autoConnect` set globally, sessions where the toggle is off will just fail to attach. Backup of pre-edit config saved at `~/.claude.json.bak-debugattach`.
