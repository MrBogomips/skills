---
summary: Generates or edits raster images and saves them to a path, through the codex CLI on your Codex quota or, when you ask, the Google Gemini API on your key.
---

# image-gen

`image-gen` generates or edits raster images (illustrations, photos, icons, mockups, logo concepts and transparent cutouts) and saves them to the path you specify. By default it uses the `codex` CLI's built-in image tool on your Codex login quota; on request it uses Google's Gemini image models ("Nano Banana"), billed to your API key.

## Why

`codex exec` has no option to write an image to a file path, and a plain request often returns prose or an ImageMagick drawing instead of a generated image. This skill writes a generated image to the path you specify, or reports why none was produced.

Money stays under your control: the Gemini API is used only when you ask for Google, Gemini, Nano Banana or Imagen, or agree to it after Codex fails. It never loops or requests extra variants just in case, and never falls back to the OpenAI API.

## Installation

```bash
npx skills add MrBogomips/skills --skill image-gen
```

This installs the same skill included in the `skills` plugin, under the name `image-gen` instead of `skills:image-gen`.

## Usage

Ask your agent to generate an image or edit an existing one ("make the sky purple"); mention Google or Gemini to use your API key instead of Codex. In Claude Code with the plugin you can also invoke `/skills:image-gen`. The agent runs the bundled script from the skill's folder:

```bash
python3 scripts/image_gen.py -p "a lone red bicycle against a wet stone wall at dusk, cinematic photograph" -o bike.png
python3 scripts/image_gen.py --backend api -p "a lone red bicycle at dusk" -o bike.png
```

Each command saves `bike.png` and prints the path. Pass `--print-prompt` to see what would be sent without spending anything. See [SKILL.md](SKILL.md) for aspect ratio, reference images, edits, multiple takes, exact pixel size and model selection.

## Inputs and outputs

- The image is saved to the path passed to `-o`. The extension matches the actual format: PNG output requested as `bike.jpg` is saved as `bike.png`.
- Multiple takes (`-n 3`) are saved as `opt.png`, `opt-2.png` and `opt-3.png`.
- `--fit WxH` always saves a PNG file.

## Requirements

- Python 3.9 or later, standard library only. Pillow is required only for `--fit`.
- Codex backend (default): the `codex` CLI on `PATH`, logged in via `codex login`. Set `CODEX_BIN` to use a different binary.
- API backend: network access and a Gemini API key in `GEMINI_API_KEY` or `GOOGLE_API_KEY`, usually on a Google project with billing enabled. The default model is `gemini-nano-banana-2.1`; pass `--model <id>` or set `GOOGLE_IMAGE_MODEL` to choose another.

## Limitations

- Each edit generates a new image rather than patching pixels, so framing and detail drift with each pass.
- With Codex, `--aspect` is only a hint; the API rejects ratios its model lacks. Only `--fit` guarantees the exact size, by padding or cropping.
- With the API, every take is a separate billed call (`-n 3` is three calls, at most 8). With Codex, the model may return fewer takes than requested.
- Models sometimes get text, counts or requested details wrong. Check the result.
