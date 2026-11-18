# Project store initialization

Create `.personal-voice/` only after the user confirms. Outside a git
repository, ask only whether to create it. In a git repository, first explain
the choice in the user's language, covering these points:

> The project store keeps this project's terms and document conventions. It can
> stay personal or be versioned with the project.
>
> - **Personal (default)**: only you see it. It is listed in
>   `.git/info/exclude`, a local file git never shares, so it never shows up in
>   `git status` and never reaches the remote. The project's `.gitignore` is not
>   touched.
> - **Versioned**: it is committed like any other file. Then:
>   - **Readers**: everyone who can read the repository can read it, which
>     includes the whole internet for a public repository.
>   - **History**: once committed, its content stays in the git history even if
>     you delete the folder later.
>   - **Status noise**: every recorded observation shows up as a change in
>     `git status` and in your diffs.
>   - **Merge conflicts**: teammates or branches that record observations at the
>     same time can conflict on the same files.
>   - **Client names**: client terms and names in the glossary become visible to
>     anyone with access, and stay in the history.
>
> Keep it personal, version it, or skip the project store?

Then:

- **Personal**, or a plain yes that names no option: create `.personal-voice/` and append
  the line `.personal-voice/` to the repository's exclude file, creating it if it
  is missing, with the Edit or Write tool rather than a shell command. Claude
  Code protects `.git/`, so this edit asks for permission. Get the exclude
  file's path from `git rev-parse --git-path info/exclude`, run in the project
  root: it prints `.git/info/exclude` in an ordinary clone, and the right path
  in a linked worktree or submodule, where `.git` is a file.
- **Versioned**: create `.personal-voice/` and touch no ignore file.
- **Skip**: create nothing, record no project observations, and do not ask
  again in this session. A later session may offer it again.
- Never write to `.gitignore` for the project store.
