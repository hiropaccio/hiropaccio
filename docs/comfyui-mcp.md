# ComfyUI × MCP × Claude — Research Notes

Research into connecting [ComfyUI](https://www.comfy.org/) (node-based Stable Diffusion /
generative media engine) to Claude via the **Model Context Protocol (MCP)**, so that image,
video, and audio generation can be driven from natural language in Claude Code or Claude
Desktop.

> **Note:** This is a standalone project, separate from the Raspberry Pi 5 / Home Assistant
> setup documented elsewhere in this repo. Target hardware is a PC with an
> **NVIDIA RTX 5060 16 GB**.

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

## Hardware notes: RTX 5060 16 GB

16 GB of VRAM is a comfortable budget for local generation:

- **SDXL / SD 1.5** — runs easily, fast iterations.
- **Flux.1 dev/schnell** — use the **fp8** checkpoint (or GGUF quants); fits in 16 GB.
- **Qwen-Image, Z-Image** — quantized variants fit.
- **Video (WAN, LTX-Video)** — workable at modest resolutions/lengths with model offloading;
  expect slower generation than images.

### Blackwell (RTX 50-series) gotchas

The RTX 5060 is Blackwell (compute capability `sm_120`) and **requires a PyTorch build with
CUDA 12.8 or newer** — older torch builds fail with "no kernel image available" errors:

- Easiest: use the current **ComfyUI Windows portable** package or the **ComfyUI desktop app**,
  which bundle a Blackwell-compatible PyTorch. See the
  [official 50-series support thread](https://github.com/Comfy-Org/ComfyUI/discussions/6643).
- Manual installs: install torch from the cu128+ wheel index
  (`pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128`).
- **Watch custom nodes:** some list `torch` in their `requirements.txt`, and pip can silently
  replace your cu128 build with an incompatible one. After installing nodes, verify with
  `python -c "import torch; print(torch.__version__)"`. Avoid old `xformers` builds for the
  same reason.

## Recommended path

Everything runs on the one PC — ComfyUI, the MCP server, and Claude — so no LAN/remote
configuration is needed; the MCP server auto-detects ComfyUI on `localhost:8188`.

1. Install ComfyUI on the PC (Windows portable or desktop app, Blackwell-ready build) and
   verify the web UI at `http://127.0.0.1:8188`. Do a manual test render first.
2. Grab starter models: SDXL or Flux fp8 checkpoint via ComfyUI's built-in model manager.
3. Start with **artokun/comfyui-mcp** — broadest tool coverage and an actively maintained
   Claude Code plugin. Register it (requires Node.js ≥ 22):
   ```bash
   claude mcp add comfyui -- npx -y comfyui-mcp
   ```
   or add the JSON block above to `claude_desktop_config.json` for Claude Desktop.
4. Test with a simple "generate an image of …" prompt in Claude.
5. If it feels heavyweight, fall back to **joenorton/comfyui-mcp-server** and expose only the
   specific workflow JSONs you actually use.
