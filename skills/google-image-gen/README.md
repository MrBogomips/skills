---
summary: Generates or edits raster images through the Google Gemini API ("Nano Banana" image models) with your own API key, and saves them to a path.
---

# google-image-gen

`google-image-gen` generates and edits raster images through the Google Gemini API ("Nano Banana" image models) and saves the output to the path you specify. Every call uses your own API key and is billed to it.

## Why

Use this skill when you specifically want Google's image models. Because every call costs money on your key, the skill runs only when you ask for Google, Gemini, Nano Banana, or Imagen, or ask to use your Google key. It does not loop or request extra variants just in case.

## Installation

```bash
npx skills add MrBogomips/skills --skill google-image-gen
```

This is the same skill included in the `skills` plugin, installed as `google-image-gen` instead of `skills:google-image-gen`.

## Usage

Set `GEMINI_API_KEY`, then ask your agent for an image and mention Google or Gemini (or invoke `/skills:google-image-gen` in Claude Code with the plugin). The agent runs the bundled script from the skill directory:

```bash
python3 scripts/google_image.py -p "a lone red bicycle against a wet stone wall at dusk, cinematic photograph" -o bike.png
```

The command saves the image and prints its path. Pass `--print-prompt` to inspect the request without making an API call. See [SKILL.md](SKILL.md) for options covering aspect ratios, reference images, edits, multiple takes, exact pixel dimensions, and model selection.

## Inputs and outputs

- The image is saved to the path passed to `-o`. The file extension matches the returned image format, so JPEG data requested as `bike.png` is saved as `bike.jpg`.
- Multiple takes (for example, `-n 3`) are saved as `opt.png`, `opt-2.png`, and `opt-3.png`.
- `--fit WxH` always saves as PNG.

## Requirements

- A Gemini API key in `GEMINI_API_KEY` or `GOOGLE_API_KEY`. Image models usually require a Google project with billing enabled.
- Python 3.9 or later (standard library only) and network access. Pillow is required only when using `--fit`.
- The default model is `gemini-nano-banana-2.1`; pass `--model <id>` or set `GOOGLE_IMAGE_MODEL` to select another.

## Limitations

- Every call is billed separately, so `-n 3` counts as three billed calls.
- The API rejects aspect ratios the selected model does not support. Use `--fit` to guarantee exact pixel dimensions afterward by padding or cropping.
- Each edit is a new generation, so details drift; change one thing per pass.
- For ordinary image requests, the default is `codex-image-gen`, which requires no API key.