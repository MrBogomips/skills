# Packaging

These commands leave the user's staged content, working tree and branches unchanged. `git fetch` updates only
remote-tracking refs, and `GIT_OPTIONAL_LOCKS=0` keeps `git status` from taking the index lock while another
session or an IDE uses the repository.

Shell variables may not survive between tool calls. Set every variable a snippet uses in the same command, and
guard paths that must not be empty with `${VAR:?}`.

## Remote and base

Run from the repository root. Pick one remote, `R`: the current branch's upstream remote, otherwise `origin`.
The base, the URL in the header and the apply commands all use `R`.

| Question | Command |
|---|---|
| Repository root | `git rev-parse --show-toplevel`; if it fails there is no git, and every file is at risk for a recipient elsewhere |
| The remote `R` | `git config --get "branch.$(git branch --show-current).remote"`, otherwise `origin` |
| Up-to-date view of `R` | `git fetch --prune --quiet "$R"` when the network is available |
| Local-only commits | `git log --oneline HEAD --not --remotes="$R"` |
| Last pushed commit (the base) | `OLDEST=$(git rev-list HEAD --not --remotes="$R" \| tail -1)`; the base is `$OLDEST^` when `OLDEST` is set, otherwise `HEAD` |
| Remote branch that holds the base | `git branch -r --contains <base>` |
| Uncommitted and untracked files | `GIT_OPTIONAL_LOCKS=0 git status --porcelain=v1 --untracked-files=all` |
| Is a file tracked | `git ls-files --error-unmatch -- <file>` |
| Remote URL | `git remote get-url "$R"` (strip credentials, see [sensitive-data.md](sensitive-data.md)) |

A tracked file is reachable when `git diff --quiet <base> -- <file>` succeeds: it is identical to the base, which
is on `R`.

**No base.** If `$OLDEST^` does not exist (nothing was ever pushed to `R`), if `R` does not exist, or if there is
no git, nothing can be patched:

- a zip holds full copies (`--no-patch`) and the apply check is skipped;
- for a text-only remote session, offer the push. If the user declines, the report says that the recipient
  cannot get the work from a prompt alone.

## Patch

Create the staging directory first, for a zip and for an inline diff alike: `STAGE=$(mktemp -d)`.

Only topic files go into the patch. Run the tracked diff only when there are tracked topic files: with an empty
list, `git diff <base> --` would diff the whole repository. Untracked files are added with `--no-index`, which
leaves the index alone; its exit status 1 is normal.

```bash
git diff --binary <base> -- <tracked topic files> > "${STAGE:?}/changes.patch"
for f in <untracked topic files>; do
  git diff --binary --no-index /dev/null "$f" >> "${STAGE:?}/changes.patch"
done
```

Apply the confidentiality decisions to the patch before the apply check. Anonymize only `+` lines: context and
`-` lines must match the base, which is already on the remote. If a file cannot be anonymized that way, ship an
anonymized full copy of it instead of its hunk.

Then check the final patch on the base in a throwaway clone:

```bash
tmp=$(mktemp -d) &&
git clone -q --no-checkout "$(git rev-parse --show-toplevel)" "$tmp/c" &&
git -C "$tmp/c" checkout -q <base> &&
git -C "$tmp/c" apply --check "${STAGE:?}/changes.patch"
rm -rf "$tmp"
```

**Inline diff.** Paste the checked patch into the prompt as a `diff` block. Fence it with more backticks than the
longest run of backticks inside the diff: four or more when it touches Markdown. Binary hunks cannot travel as
text; name those files instead.

## Zip

Copy the content into `$STAGE`, so that `HANDOFF.md` sits at the root of the zip:

```text
<slug>-handoff.zip
├── HANDOFF.md
├── changes.patch                 only with --patch, when there are changes
└── assets/
    ├── <repo-relative path>      full copies
    └── external/<readable name>  files from outside the repository
```

| Cited file | Automatic zip (default `--patch`) | Explicit `--zip` (default `--no-patch`) |
|---|---|---|
| In the repository, unchanged, on the remote | not included; cited by path and commit | full copy |
| In the repository, changed or in local-only commits | in `changes.patch` | full copy of the current version |
| New, untracked | in `changes.patch` | full copy |
| Outside the repository | full copy | full copy |

`--patch` and `--no-patch` override the second and third rows in both columns. Only items that passed the
confidentiality check go in.

`$OUT` is the absolute path of the zip in the user's current directory, chosen without overwriting anything.
Archive from inside the staging directory, in a subshell that fails if `STAGE` is empty, with the first tool
that works:

```bash
( cd "${STAGE:?}" && zip -qr "${OUT:?}" . )                                   # Info-ZIP
( cd "${STAGE:?}" && python3 -m zipfile -c "${OUT:?}" HANDOFF.md assets changes.patch )   # only existing entries
( cd "${STAGE:?}" && tar -a -cf "${OUT:?}" HANDOFF.md assets changes.patch )   # only if `tar --version` says bsdtar
```

GNU tar does not write zip files: with `-a` and a `.zip` name it writes a plain tar and still succeeds. On
Windows without these tools, use PowerShell: `Compress-Archive -Path "<stage>\*" -DestinationPath "<out>"`; from
WSL, convert both paths with `wslpath -w`.

Confirm the result with a zip reader (`unzip -l "$OUT"` or `python3 -m zipfile -l "$OUT"`), then delete `$STAGE`.
If no tool works, stop and say so; do not leave loose files in its place.

## Clipboard

Write the text to a temporary file, pipe it to the first command that exists, and check its exit status.

| System | Command |
|---|---|
| macOS | `pbcopy < "$FILE"` |
| Linux, Wayland (`$WAYLAND_DISPLAY` set) | `wl-copy < "$FILE" >/dev/null 2>&1` |
| Linux, X11 (`$DISPLAY` set) | `xclip -selection clipboard -i < "$FILE" >/dev/null 2>&1` or `xsel --clipboard --input < "$FILE" >/dev/null 2>&1` |
| Windows, WSL | `clip.exe < "$FILE"`; for accented letters prefer PowerShell: `Get-Content -Raw -Encoding UTF8 <path> \| Set-Clipboard`, with the path from `wslpath -w` on WSL |

The redirects matter: `xclip` keeps running in the background to serve the clipboard, and without them the
command waits for it.

If no command exists or it fails, write `<slug>-handoff.md` as with `--file` and say so in the report.

Delete the temporary text file afterwards. The only file the handoff leaves behind is its output.
