---
name: codex-image-gen
description: >-
  Generates or edits raster images (illustrations, photos, icons, textures, mockups, posters, logo concepts,
  transparent cutouts, placeholder assets) by driving the codex CLI's built-in image tool, and saves them to a
  path. Use by default whenever an image is to be generated or an existing one changed ("make the sky purple"),
  and when the user names Codex, ChatGPT or OpenAI image generation. Runs on the Codex login's quota, with no
  API key. For Google/Gemini image generation with an API key, use google-image-gen instead.
license: MIT
compatibility: >-
  Needs the codex CLI on PATH and logged in (codex login), and Python 3.9+ (standard library; Pillow only for
  --fit). Image generation uses the Codex account's quota.
---

# Image generation via the codex CLI

`codex exec` has no "write the image to this path" option: it saves what it generates under
`$CODEX_HOME/generated_images/<session id>/`. `scripts/codex_image.py` runs one non-interactive turn, collects
only the images of that exact session and writes them where you ask. If no image came back it writes nothing.

**Always use the script.** A hand-rolled `codex exec "draw a cat"` often returns prose or an ImageMagick drawing
and leaves you hunting for the output.

**Never fall back to a metered API.** Do not use the OpenAI SDK or `OPENAI_API_KEY`, even when codex fails or is
out of quota. Report the failure and stop. For Google's metered API, only use `google-image-gen`, and only when
the user asked for it.

## Usage

Run from the skill directory or give the script's absolute path. A run takes about 30-60 seconds.

```bash
python3 scripts/codex_image.py -p "a lone red bicycle against a wet stone wall at dusk, cinematic photograph" -o bike.png
```

| Goal | Command |
|---|---|
| Aspect ratio (a hint to the model) | `-p "..." -o out.png --aspect 9:16` |
| Reference image(s) | `-p "..." -o out.png -r ref.png [-r ref2.png]` |
| Edit an image | `--edit v1.png -p "make the sky purple" -o v2.png` |
| Several takes | `-p "..." -o opt.png -n 3` (saves `opt.png`, `opt-2.png`, `opt-3.png`) |
| Exact pixel size | `-p "..." -o cover.png --aspect 9:16 --fit 1080x1920` |
| Long prompt | `--prompt-file prompt.md -o out.png` |
| See the prompt, spend nothing | add `--print-prompt` |

- The output extension follows the real format: PNG bytes asked for as `bike.jpg` land in `bike.png`. The script
  prints each path it wrote.
- `--aspect` only shapes the result. `--fit WxH` guarantees the size afterwards: it pads with black bars
  (`--fit-mode pad`, default) or center-crops (`--fit-mode crop`), and always saves PNG. Match `--aspect` to the
  target so there is little to pad or crop. `--fit` needs Pillow, checked before codex runs.
- `-n` asks for N takes in one run; the model may return fewer, and the script saves what it got.
- `--edit` attaches the image as the target and tells the model to change only what the prompt asks.

## Writing the prompt

The script adds the wording that forces a real image-tool call, so `--prompt` is only about the picture. A short
labelled spec works well:

```
Subject: a lone red bicycle, paint worn to bare metal at the edges
Scene: leaning on a wet stone harbour wall, town lights beyond
Style: cinematic photograph, shallow depth of field
Lighting: dusk, low warm sun, reflections on wet stone
Text (verbatim): "NO SPARE"
Avoid: people, watermarks, extra bicycles
```

- Quote text that must appear and keep it short; long strings come back misspelled.
- State what must not appear. For a transparent cutout, ask for a transparent background and save as `.png`.
- For `--edit`, write the *change* ("remove the lamp post") and name what must stay ("keep the bicycle, framing
  and lighting"). Change one thing per pass.
- An edit is a re-generation, not a pixel patch: framing and detail drift, and each pass compounds it. Keep chains
  short, and composite back anything that must survive untouched.

## After generating

Check the result before handing it over, using whatever means you have to look at an image: the model sometimes
gets text, counts or a requested detail wrong. If it misses, re-run with a sharper prompt or refine with `--edit`.

## Failures

The script exits non-zero with one clear message and writes nothing.

- **codex CLI not found / not logged in**: install codex and run `codex login`; `CODEX_BIN` points at another binary.
- **Out of quota**: wait for the reset codex reports or use another account. Do not retry in a loop.
- **No image produced**: the model answered in text. Its reply is shown; re-run with a plainer picture request.
- **Timed out**: raise `--timeout` (default 900 s) only if the run was merely slow.
- **Pillow missing with `--fit`**: `pip install Pillow`, or drop `--fit`.
