---
name: vision-bridge
description: Give vision capability to non-vision LLMs (e.g. DeepSeek) by sending images to an external vision model (default agnes-2.5-flash, OpenAI-compatible) and returning text descriptions. 为无视觉能力的大模型（如 DeepSeek）提供识图能力：把图片发给外部视觉模型（默认 agnes-2.5-flash，OpenAI 兼容协议）并返回文字描述。Use this skill whenever the user shares a local image path or network image URL, a message contains "Saved attachments:", or the user asks to describe/recognize/analyze/interpret an image, extract text from an image (OCR), or understand screenshots, charts, tables, QR codes, or memes — do NOT use the Read tool to look at images (the underlying model has no vision). 当用户分享本地图片路径或网络图片 URL、消息中出现 "Saved attachments:"、用户要求描述/识别/分析/解读图片、提取图片中的文字（OCR）、理解截图/图表/表格/二维码/表情包，或任何需要"看图"的场景，都必须使用本 skill —— 不要用 Read 工具看图（底层模型无视觉能力）。The skill prompts for configuration once on first use when the vision API is not configured; afterwards it recognizes images automatically without asking again. skill 首次使用且视觉 API 未配置时，引导用户配置一次；配置后自动识图，不再询问。
---

# vision-bridge — Vision for non-vision LLMs

Your underlying model has no native vision capability. For anything that requires "seeing" an image, **do NOT use the Read tool** — call the bundled script `vision-bridge.py`, which asks an external vision model to "look" for you and returns text.

## When to trigger

- The user shares a **local image path** or **network image URL**
- The message contains `Saved attachments:` listing images
- The user asks to describe, recognize, analyze, interpret an image; extract text (OCR); understand screenshots, charts, tables, QR codes, memes, captchas
- Any task that needs information from an image

## Script location & modes

Script: `scripts/vision-bridge.py` in this skill. Requires only Python 3.9+ standard library — **zero third-party dependencies** (no pip install). Cross-platform: Windows / Linux / macOS / fish.

| Mode | Command | Purpose |
|---|---|---|
| Recognize (default) | `python vision-bridge.py <image-path> [more-images] [prompt] [options]` | Look at the image and return a text description |
| Recognize (URL) | `python vision-bridge.py --url <image-url> [prompt] [options]` | Look at a remote image |
| Check config | `python vision-bridge.py check` | Is the vision API configured? (exit 0=yes, 1=no) |
| Configure | `python vision-bridge.py config "<key>"` | Persist VISION_API_KEY across platforms |

If `python` is unavailable on Windows, use `py -3 vision-bridge.py ...` instead.

Common options: `--model <model>`, `--max-tokens <n>`, `--temperature <0~2>`, `--json` (raw JSON response), `config --region global|china` (pin a regional base URL).

## First use: configure once

**Principle**: the API key is only written to an environment variable — never into code, scripts, or any project file, to prevent leakage. Run `check` before recognizing; only guide the user when `VISION_API_KEY` is missing, and never ask again afterwards.

When not configured, guide the user (offer one of two options):

1. Run `python vision-bridge.py check`, confirm `configured=false`.
2. Tell the user a vision model API key is needed (default agnes, model `agnes-2.5-flash`); ask them to choose **one** way:
   - **Method A (user hands the key over)**: ask the user to paste the API key into the chat; when received, run `python vision-bridge.py config "<user key>"` to persist it. **Do not repeat the key in plaintext in the session afterwards.**
   - **Method B (user configures it themselves)**: send the user this command — they only replace the placeholder inside the quotes:
     ```
     python vision-bridge.py config "your-vision-api-key"
     ```
3. Ask the user to **restart the terminal** (system env vars only take effect for new processes), then verify with `python vision-bridge.py check`.
4. After configuration, immediately recognize the current image.

If the user already has a key and insists on pasting it, reject placeholders like `sk-xxx` or `your-vision-api-key` before persisting.

## Usage

Examples:

```bash
python vision-bridge.py "D:\photos\example.png" "Describe this image"
python vision-bridge.py --url "https://example.com/a.png" "Extract the text"
python vision-bridge.py "img1.png" "img2.png" "Compare these two images"
```

The script: base64-encodes local images → submits all images at once → timeout/retry/error classification (401=bad key, 404=wrong model/URL, 429=rate limited) → prints text to stdout. Surface stderr error messages to the user verbatim on failure.

## Regional base URLs

The default is agnes `agnes-2.5-flash` (free and unlimited; see the [Agnes docs](https://agnes-ai.com/doc/agnes-25-flash)) via an **auto-selected regional endpoint** (an apihub API key works on both):

| Region | Base URL | Note |
|---|---|---|
| Global | `https://apihub.agnes-ai.com/v1` | Faster for users outside mainland China |
| China | `https://api.agnes-ai.cn/v1` | Faster for users in mainland China |

Selection priority: `VISION_BASE_URL` (explicit) > system language (Chinese locale → `.cn`, otherwise → `.com`) > default `.com`.

To pin a region explicitly (e.g. a Chinese user on an English system), use:
```bash
python vision-bridge.py config --region china "your-key"   # writes VISION_BASE_URL too
python vision-bridge.py config --region global "your-key"
```

To use any other OpenAI-compatible vision service:
```bash
# Windows
setx VISION_BASE_URL "https://your-provider/v1"
setx VISION_MODEL "your-vision-model"
# Linux / macOS (write to ~/.bashrc or ~/.zshrc)
export VISION_BASE_URL="https://your-provider/v1"
export VISION_MODEL="your-vision-model"
```

## Notes

- Bilingual UI: script output auto-switches Chinese/English based on system language; force with `VISION_LANG=zh` or `VISION_LANG=en`.
- Images over 10MB trigger a warning (some APIs reject very large images).
- `agnes-2.5-flash` is a **thinking model**: recognition may take 10–90 s (script timeout is 120 s). To use a faster model, set `VISION_MODEL`.
- The script auto-extracts the final answer from the thinking output (when `content` is empty, it takes the conclusion in `reasoning_content`); default output is clean text, `--json` outputs the raw API response.
- `config` writes to **system environment variables**; the script re-reads system config, so it works in the current session immediately — but a **new terminal** is where each shell actually loads the variable. Restart the terminal if another program does not see it.
- Windows writes via `winreg` directly to the registry (not setx): supports special characters like `& ^ %` and has no 1024-char limit.
- `config` never prints the plaintext key, so it is safe to copy for the user.
- 401 = bad/expired key; 404 = wrong model or API URL; 429 = rate limited.
