# ComfyUI × MCP × Claude — Research Notes

Research into connecting [ComfyUI](https://www.comfy.org/) (node-based Stable Diffusion /
generative media engine) to Claude via the **Model Context Protocol (MCP)**, so that image,
video, and audio generation can be driven from natural language in Claude Code or Claude
Desktop.

_Last updated: 2026-07-02_

---

## What MCP gives you here

MCP is an open protocol that lets Claude call external "tool servers." A ComfyUI MCP server
sits between Claude and a ComfyUI instance's HTTP/WebSocket API. Once registered, Claude can:

- Generate images/video/audio from a prompt ("make me a 1024×1024 icon of a robot vacuum")
- Run, edit, and author ComfyUI workflow graphs in natural language
- Manage models, checkpoints, LoRAs, and custom nodes
- Iterate: inspect a result, tweak parameters, regenerate

## The main implementations

### 1. Comfy Cloud MCP (official, hosted — no GPU needed)

- Hosted by Comfy-Org at `https://cloud.comfy.org/mcp`; workflows execute on Comfy Cloud GPUs.
- OAuth authentication — no API keys to manage.
- Setup docs: <https://docs.comfy.org/development/cloud/mcp-server> (one command for Claude
  Code, a few clicks for Claude Desktop). The old installer repo
  [Comfy-Org/comfy-cloud-mcp](https://github.com/Comfy-Org/comfy-cloud-mcp) is archived.
- **Caveat:** Comfy Cloud is in closed beta (waitlist), and generation runs on paid cloud GPUs.

Claude Code registration:

```bash
claude mcp add --transport http comfy-cloud https://cloud.comfy.org/mcp
```

### 2. artokun/comfyui-mcp (most complete local option)

<https://github.com/artokun/comfyui-mcp> — "local-first, agent-native control plane."

- **108 MCP tools + 29 AI skills** (Flux, WAN, LTX video, Qwen, Z-Image), plus a Claude Code
  plugin layer (slash commands, skills, agents, hooks).
- Author/execute/validate/visualize workflows, edit the live graph, model & custom-node
  management, VRAM monitoring, error diagnostics.
- Requires Node.js ≥ 22 and a reachable ComfyUI instance (local, LAN, VPS, or Comfy Cloud).
- Auto-detects local ComfyUI on ports 8188/8000; `COMFYUI_URL` points it at a remote host.

Claude Code / Claude Desktop config:

```json
{
  "mcpServers": {
    "comfyui": {
      "command": "npx",
      "args": ["-y", "comfyui-mcp"],
      "env": {
        "COMFYUI_URL": "http://<gpu-box-ip>:8188"
      }
    }
  }
}
```

### 3. joenorton/comfyui-mcp-server (lightweight, workflow-driven)

<https://github.com/joenorton/comfyui-mcp-server> — small Python server.

- Drop workflow JSON exports into a `workflows/` directory; each file automatically becomes an
  MCP tool (filename → tool name). Parameters are declared with placeholders like
  `PARAM_PROMPT`, `PARAM_INT_STEPS`, `PARAM_FLOAT_CFG`.
- Runs as a streamable-HTTP MCP server on `http://127.0.0.1:9000/mcp`; Python 3.8+ and a local
  ComfyUI on port 8188.

Project-scoped `.mcp.json` for Claude Code:

```json
{
  "mcpServers": {
    "comfyui-mcp-server": {
      "type": "streamable-http",
      "url": "http://127.0.0.1:9000/mcp"
    }
  }
}
```

### 4. Other notable options

| Repo | Angle |
|---|---|
| [shawnrushefsky/comfyui-mcp](https://github.com/shawnrushefsky/comfyui-mcp) | Image, video, audio, and 3D generation |
| [hybridindie/comfyui_mcp](https://github.com/hybridindie/comfyui_mcp) | Security-focused: workflow inspection, path sanitization, rate limiting, audit logging |
| [Peleke/comfyui-mcp](https://github.com/Peleke/comfyui-mcp) | Upscaling, ControlNet, inpainting/outpainting, IP-Adapter style transfer, TTS, talking-head video |
| [alecc08/comfyui-mcp](https://github.com/alecc08/comfyui-mcp) | Minimal: text-to-image, img2img, resize |
| [Nikolaibibo/claude-comfyui-mcp](https://github.com/Nikolaibibo/claude-comfyui-mcp) | Simple Claude Desktop ↔ local ComfyUI bridge |

## Fit for this project

The Raspberry Pi 5 running Home Assistant **cannot host ComfyUI** — SD/Flux inference needs a
discrete GPU (≈8 GB+ VRAM for SDXL/Flux). Realistic deployment shapes:

1. **GPU PC on the LAN** runs ComfyUI (`--listen 0.0.0.0`); the MCP server runs wherever Claude
   runs and points at `http://<gpu-box-ip>:8188`. Best latency, no cloud dependency — matches
   this repo's "prefer local APIs" convention.
2. **Comfy Cloud MCP** if no GPU hardware is available — zero maintenance, but closed beta,
   paid, and cloud-dependent.

Possible Home Assistant tie-ins once a server is up:

- Generate dashboard art/icons for the room tablet clients on demand.
- A Claude Code session maintaining this repo could generate imagery for Lovelace dashboards
  (`dashboards/`) as part of the same workflow.
- HA automations could hit the same ComfyUI API directly (via `rest_command`) for scheduled
  imagery, independent of MCP.

## Recommended path

1. Stand up ComfyUI on a LAN machine with a GPU and verify the web UI at `http://<ip>:8188`.
2. Start with **artokun/comfyui-mcp** (`npx -y comfyui-mcp`, `COMFYUI_URL` set) — broadest
   tool coverage and an actively maintained Claude Code plugin.
3. If it feels heavyweight, fall back to **joenorton/comfyui-mcp-server** and expose only the
   specific workflow JSONs you actually use.
4. Register the server with `claude mcp add` (Claude Code) or `claude_desktop_config.json`
   (Claude Desktop), then test with a simple "generate an image of …" prompt.
