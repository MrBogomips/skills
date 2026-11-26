---
name: image-gen
description: >-
  Generates or edits raster images (illustrations, photos, icons, mockups, logo concepts, transparent cutouts)
  and saves them to a path, through the codex CLI's built-in image tool (Codex login quota, the default) or the
  Google Gemini API ("Nano Banana" models, billed to the user's API key). Use whenever an image is to be
  generated or an existing one changed ("make the sky purple"), including when the user names Codex, ChatGPT or
  OpenAI image generation, or Google, Gemini, Nano Banana or Imagen, or says to use their Google/Gemini API key.
license: MIT
compatibility: >-
  Needs Python 3.9+ (standard library; Pillow only for --fit) and either the codex CLI on PATH, logged in
  (codex login; uses the Codex account's quota), or network access and a Gemini API key in GEMINI_API_KEY or
  GOOGLE_API_KEY (every call billed to that key).
---

# Image generation

`scripts/image_gen.py` makes one image request and writes the result where you ask; if no image comes back it
writes nothing and says why. **Always use the script**: a hand-rolled `codex exec "draw a cat"` often returns
prose or an ImageMagick drawing, and `codex exec` cannot write to a chosen path.

## Choose the backend

- **`codex`** (default): the codex CLI's image tool, on the user's Codex login quota, no API key.
- **`api`** (`--backend api`): the Gemini API with `GEMINI_API_KEY` (or `GOOGLE_API_KEY`). **Every call costs
  money on the user's key.** Use it only when the user asks for Google, Gemini, Nano Banana, Imagen or their
  Google/Gemini key.
- If codex is missing, not logged in or out of quota, report the error and **ask** whether to use the `api`
  backend, saying it bills their key. Run it only on a yes. Never use the OpenAI SDK or `OPENAI_API_KEY`.
- Do not loop or ask for extra variants "to be safe", on either backend.

## Usage

Run from the skill directory or give the script's absolute path. A codex run takes about 30-60 seconds.

```bash
python3 scripts/image_gen.py -p "a lone red bicycle against a wet stone wall at dusk, cinematic photograph" -o bike.png
python3 scripts/image_gen.py --backend api -p "..." -o bike.png
```

| Goal | Command |
|---|---|
| Aspect ratio | `-p "..." -o out.png --aspect 9:16` |
| Reference image(s) | `-p "..." -o out.png -r ref.png [-r ref2.png]` |
| Edit an image | `--edit v1.png -p "make the sky purple" -o v2.png` |
| Several takes | `-p "..." -o opt.png -n 3` (saves `opt.png`, `opt-2.png`, `opt-3.png`) |
| Exact pixel size | `-p "..." -o cover.png --aspect 9:16 --fit 1080x1920` |
| Long prompt | `--prompt-file prompt.md -o out.png` |
| See the prompt or request, spend nothing | add `--print-prompt` (api: no key shown, no call made) |
| Another Gemini model (api only) | `--model <id>` or env `GOOGLE_IMAGE_MODEL` |

- The output extension follows the real format: PNG bytes asked for as `bike.jpg` land in `bike.png`. The script
  prints each path it wrote.
- `--aspect`: a hint in the prompt with codex; the API's own setting with api (for example `1:1`, `3:2`, `4:5`,
  `16:9`, `21:9`), which rejects ratios the model lacks. `--fit WxH` guarantees the size afterwards by padding
  with black bars (`--fit-mode pad`, default) or center-cropping (`--fit-mode crop`), and always saves PNG. It
  needs Pillow, checked before anything is spent.
- `-n`: codex asks for N takes in one run and may return fewer; api makes N billed calls (at most 8).
- api's default model is `gemini-nano-banana-2.1`. If the API reports an unknown model, list the models the key
  can use (`GET /v1beta/models`) and pass one with `--model`.
- `--timeout`: seconds for the codex run (default 900) or each API call (default 300).

Describe only the picture (subject, scene, style, lighting; quote short text that must appear; say what must not).
For `--edit`, name the change and what must stay, one change per pass: an edit re-generates, so detail drifts.

Check the result before handing it over, with whatever means you have to look at an image; re-run or `--edit`
if it misses.

## Failures

The script exits non-zero with a clear message and writes nothing.

- **codex not found / not logged in**: install codex and run `codex login`; `CODEX_BIN` points at another
  binary. Then see the backend rule above.
- **codex out of quota**: wait for the reset codex reports or use another account; do not retry in a loop.
- **codex produced no image**: it answered in text; its reply is shown. Re-run with a plainer picture request.
- **Missing key (exit 2)**: set `GEMINI_API_KEY`.
- **401/403**: the key is wrong, restricted, or the project has no access to image models (they usually need a
  billed project). **402**: prepaid credit used up; the user tops it up in Google AI Studio.
- **429**: rate limit or quota; wait, the script does not retry it. **400**: often an unknown model or an
  unsupported aspect ratio; the API's message is shown. **5xx or timeout**: retried once, then reported.
- **No image (api)**: the model replied in text or the prompt was blocked; the reason is shown.
- **Timed out (codex)**: raise `--timeout` only if the run was merely slow.
- **Pillow missing with `--fit`**: `pip install Pillow`, or drop `--fit`.
