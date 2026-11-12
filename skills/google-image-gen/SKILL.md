---
name: google-image-gen
description: >-
  Generates or edits raster images through the Google Gemini API ("Nano Banana" image models) with the user's
  API key, and saves them to a path. Use only when the user asks for Google, Gemini, Nano Banana or Imagen image
  generation, or says to use their Google/Gemini API key. It bills a metered API key; for ordinary image
  requests use codex-image-gen instead.
license: MIT
compatibility: >-
  Needs Python 3.9+ (standard library; Pillow only for --fit), network access, and a Gemini API key in
  GEMINI_API_KEY or GOOGLE_API_KEY. Every call is billed to that key.
---

# Image generation via the Gemini API

`scripts/google_image.py` sends one request to the Gemini API per image and writes the result where you ask. If
no image comes back it writes nothing and shows the model's text reply or the block reason.

**Every call costs money on the user's key.** Do not loop, and do not ask for variants "to be safe". The default
alternative is `codex-image-gen`, which runs on the Codex login with no API key.

## Setup

Set `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in the environment. The script sends it only in the `x-goog-api-key`
header and never prints it. With no key it exits with status 2 and names the variable. Image models usually need
a billed Google project: a 403 or 429 often means that.

## Usage

Run from the skill directory or give the script's absolute path.

```bash
python3 scripts/google_image.py -p "a lone red bicycle against a wet stone wall at dusk, cinematic photograph" -o bike.png
```

| Goal | Command |
|---|---|
| Aspect ratio (sent to the API) | `-p "..." -o out.png --aspect 9:16` |
| Reference image(s) | `-p "..." -o out.png -r ref.png [-r ref2.png]` |
| Edit an image | `--edit v1.png -p "make the sky purple" -o v2.png` |
| Several takes | `-p "..." -o opt.png -n 3` (3 billed calls; saves `opt.png`, `opt-2.png`, `opt-3.png`) |
| Exact pixel size | `-p "..." -o cover.png --aspect 9:16 --fit 1080x1920` |
| Long prompt | `--prompt-file prompt.md -o out.png` |
| See the request, spend nothing | add `--print-prompt` (no key shown, no call made) |
| Another model | `--model <id>` or env `GOOGLE_IMAGE_MODEL` |

- The default model is `gemini-nano-banana-2.1`, Google's current general-purpose image model for generation and
  conversational editing. Model ids change: if the API reports an unknown model, list the models the key can use
  (`GET /v1beta/models`) and pass one with `--model`.
- The output extension follows the returned format: JPEG bytes asked for as `bike.png` land in `bike.jpg`. The
  script prints each path it wrote.
- `--aspect W:H` uses the API's own aspect-ratio setting (for example `1:1`, `3:2`, `4:5`, `16:9`, `21:9`); the
  API rejects ratios the model lacks. `--fit WxH` guarantees exact pixels afterwards: it pads with black bars
  (`--fit-mode pad`, default) or center-crops (`--fit-mode crop`), and always saves PNG. `--fit` needs Pillow,
  checked before any call.
- `--edit` attaches the image as the target and tells the model to change only what the prompt asks.

## Writing the prompt

Describe the picture in full sentences: subject, scene, style, lighting, composition. Quote any text that must
appear and keep it short. State what must not appear. For `--edit`, write the change and name what must stay;
change one thing per pass, because an edit is a re-generation and detail drifts.

## After generating

Check the result before handing it over, using whatever means you have to look at an image. If it misses,
re-run with a sharper prompt or refine with `--edit`.

## Failures

The script exits non-zero with one line and writes nothing.

- **Missing key (exit 2)**: set `GEMINI_API_KEY`.
- **401/403**: the key is wrong, restricted, or the project has no access to image models.
- **429**: rate limit or quota. Wait; the script does not retry it.
- **400**: bad request, often an unknown model or an aspect ratio the model lacks; the API's message is shown.
- **5xx or timeout**: retried once, then reported.
- **No image**: the model replied in text or the prompt was blocked; the reason is shown. Rephrase the prompt.

Adapted from [zazencodes/skills](https://github.com/zazencodes/skills) (MIT, see LICENSE-upstream).
