---
summary: Generates or edits raster images through the Google Gemini API ("Nano Banana" image models) with your own API key, and saves them to a path.
---

# google-image-gen

`google-image-gen` generates raster images, or edits existing ones, through the Google Gemini API and its "Nano Banana" image models, and saves them where you ask. It uses your own API key, and every call is billed to it.

## Why

Use it when you want Google's image models in particular. Because every call costs money on your key, the skill runs only when you ask for Google, Gemini, Nano Banana or Imagen, or say to use your Google key, and it does not loop or ask for extra variants "to be safe".

## Installation

```bash
npx skills add MrBogomips/skills --skill google-image-gen
```

It is the same skill as in the `skills` plugin, installed under the name `google-image-gen` instead of `skills:google-image-gen`.

## Usage

Set `GEMINI_API_KEY`, then ask your agent for an image and name Google or Gemini (`/skills:google-image-gen` in Claude Code with the plugin). The agent runs the bundled script from the skill's folder:

```bash
python3 scripts/google_image.py -p "a lone red bicycle against a wet stone wall at dusk, cinematic photograph" -o bike.png
```

This saves the image and prints its path. Add `--print-prompt` to see the request without making a call. The options for aspect ratio, reference images, edits, several takes, an exact pixel size and another model are in [SKILL.md](SKILL.md).

## Inputs and outputs

- The image lands at the path given with `-o`. The extension follows the returned format: JPEG bytes asked for as `bike.png` are saved as `bike.jpg`.
- Several takes (`-n 3`) are saved as `opt.png`, `opt-2.png`, `opt-3.png`.
- `--fit WxH` always saves PNG.

## Requirements

- A Gemini API key in `GEMINI_API_KEY` or `GOOGLE_API_KEY`. Image models usually need a billed Google project.
- Python 3.9 or later, standard library only, and network access. Pillow is needed only for `--fit`.
- The default model is `gemini-nano-banana-2.1`; pass `--model <id>` or set `GOOGLE_IMAGE_MODEL` to use another.

## Limitations

- Every call is billed: `-n 3` is three billed calls.
- The API rejects an aspect ratio the model lacks. `--fit` guarantees exact pixels afterwards, by padding or cropping.
- An edit is a new generation: detail drifts, so change one thing per pass.
- For ordinary image requests the default is `codex-image-gen`, which needs no API key.
