---
summary: Generates or edits raster images through the codex CLI's built-in image tool and saves them to a path, on your Codex login's quota and with no API key.
---

# codex-image-gen

`codex-image-gen` generates raster images (illustrations, photos, icons, mockups, logo concepts, transparent cutouts), or edits existing ones, through the `codex` CLI's built-in image tool, and saves them where you ask. It runs on your Codex login's quota and needs no API key.

## Why

`codex exec` has no option to write an image to a path, and a plain request often returns prose or an ImageMagick drawing instead of a generated image. This skill gets a real generated image written to the path you gave, or tells you why there is none.

It never falls back to a metered API when Codex fails or is out of quota.

## Installation

```bash
npx skills add MrBogomips/skills --skill codex-image-gen
```

It is the same skill as in the `skills` plugin, installed under the name `codex-image-gen` instead of `skills:codex-image-gen`.

## Usage

Ask your agent for an image, or for a change to an existing one ("make the sky purple"). It is the default skill for image requests; in Claude Code with the plugin you can also call `/skills:codex-image-gen`. The agent runs the bundled script from the skill's folder:

```bash
python3 scripts/codex_image.py -p "a lone red bicycle against a wet stone wall at dusk, cinematic photograph" -o bike.png
```

This saves `bike.png` and prints the path. A run takes about 30 to 60 seconds. The options for aspect ratio, reference images, edits, several takes and an exact pixel size are in [SKILL.md](SKILL.md).

## Inputs and outputs

- The image lands at the path given with `-o`. The extension follows the real format: PNG bytes asked for as `bike.jpg` are saved as `bike.png`.
- Several takes (`-n 3`) are saved as `opt.png`, `opt-2.png`, `opt-3.png`.
- `--fit WxH` always saves PNG.

## Requirements

- The `codex` CLI on `PATH` and logged in (`codex login`). `CODEX_BIN` points at another binary.
- Python 3.9 or later, standard library only. Pillow is needed only for `--fit`.

## Limitations

- An edit is a new generation, not a pixel patch: framing and detail drift, and each pass adds to it.
- `--aspect` is a hint to the model. Only `--fit` guarantees the size, by padding or cropping.
- The model may return fewer takes than you asked for, and sometimes gets text, counts or a requested detail wrong: check the result.
