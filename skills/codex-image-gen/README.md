---
summary: Generates or edits raster images through the codex CLI's built-in image tool and saves them to a path, on your Codex login's quota and with no API key.
---

# codex-image-gen

`codex-image-gen` generates or edits raster images (illustrations, photos, icons, mockups, logo concepts, and transparent cutouts) using the `codex` CLI's built-in image tool and saves them to the path you specify. It uses your Codex login quota and requires no API key.

## Why

`codex exec` has no option to write an image to a file path, and a plain request often returns prose or an ImageMagick drawing instead of a generated image. This skill writes a generated image to the path you specify, or reports why none was produced.

It never falls back to a metered API when Codex fails or runs out of quota.

## Installation

```bash
npx skills add MrBogomips/skills --skill codex-image-gen
```

This installs the same skill included in the `skills` plugin, under the name `codex-image-gen` instead of `skills:codex-image-gen`.

## Usage

Ask your agent to generate an image or edit an existing one ("make the sky purple"). This is the default skill for image requests; when using the plugin in Claude Code, you can also invoke `/skills:codex-image-gen` directly. The agent runs the bundled script from the skill's folder:

```bash
python3 scripts/codex_image.py -p "a lone red bicycle against a wet stone wall at dusk, cinematic photograph" -o bike.png
```

This command saves `bike.png` and prints the output path. A run takes about 30 to 60 seconds. See [SKILL.md](SKILL.md) for options covering aspect ratio, reference images, edits, multiple takes, and exact pixel size.

## Inputs and outputs

- The generated image is saved to the path passed to `-o`. The file extension matches the actual format: PNG output requested as `bike.jpg` is saved as `bike.png`.
- Multiple takes (`-n 3`) are numbered sequentially, such as `opt.png`, `opt-2.png`, and `opt-3.png`.
- `--fit WxH` always saves a PNG file.

## Requirements

- The `codex` CLI on `PATH`, logged in via `codex login`. Set `CODEX_BIN` to point to a different binary.
- Python 3.9 or later, standard library only. Pillow is required only for `--fit`.

## Limitations

- Each edit generates a new image rather than patching pixels, so framing and detail drift further with each pass.
- `--aspect` is a hint to the model. Only `--fit` guarantees the exact size, by padding or cropping.
- The model may return fewer takes than requested and sometimes gets text, counts, or requested details wrong. Check the result.